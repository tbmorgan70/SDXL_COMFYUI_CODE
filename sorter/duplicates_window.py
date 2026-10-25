"""
Duplicates Window — review what the Duplicate Finder found (Sorter 3.7).

Certain tab: a spot-check of identical sets and one button for all of them.
Probable tab: pages of look-alike sets, one row each, keeper ringed green,
pre-ticked when very close. Untick what isn't a duplicate, click another
thumbnail to keep it instead, then trash the ticked rows' extras.

Thumbnails come from the index (decoded on a worker thread; Tk images are
only made on the main thread). Trashing runs on a worker thread too.
"""

import io
import os
import queue
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, List, Optional

import customtkinter as ctk
from PIL import Image

from core.image_index import ImageIndex, ImageRow
from sorters.duplicate_finder import DupSet, TrashResult, trash_sets, with_keeper

KEEPER_COLOR = "#4CAF50"
THUMB_SIZE = 150
POLL_MS = 40


def _gb(n: int) -> float:
    return n / 1e9


class DuplicatesWindow(ctk.CTkToplevel):
    PAGE_SIZE = 15
    SPOT_CHECK = 30

    def __init__(self, parent, index: ImageIndex, certain: List[DupSet],
                 probable: List[DupSet], log_fn: Callable[[str], None]):
        super().__init__(parent)
        self.index = index
        self.certain = certain
        self.probable = probable
        self.log_fn = log_fn
        self.page = 0
        self.ticked: Dict[int, bool] = {i: s.pretick for i, s in enumerate(probable)}
        self.summary_text = ""
        self._busy = False
        self._tab = "Certain" if certain else "Probable"
        self._thumbs: Dict[str, ctk.CTkImage] = {}      # path -> CTkImage (main thread)
        self._waiting: Dict[str, List[ctk.CTkLabel]] = {}
        self._requested = set()
        self._thumb_q: "queue.Queue" = queue.Queue()
        self._done_q: "queue.Queue" = queue.Queue()
        self._loader_q: "queue.Queue" = queue.Queue()
        self._closed = False

        self.title("🔍 Duplicates")
        self.geometry("1280x900")
        self._build_ui()
        self.bind("<KeyPress>", self.on_key)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        threading.Thread(target=self._thumb_worker, daemon=True).start()
        self._poll_job = self.after(POLL_MS, self._poll)
        self._refresh()

    # ------------------------------------------------------------------ layout

    def _build_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 5))
        self.summary_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.summary_label.pack(side="left", padx=10, pady=8)
        self.tabs = ctk.CTkSegmentedButton(top, values=["Certain", "Probable"],
                                           command=self.show_tab)
        self.tabs.pack(side="right", padx=10)

        self.body = ctk.CTkScrollableFrame(self)
        self.body.pack(fill="both", expand=True, padx=10, pady=5)

        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=10, pady=(5, 10))
        self.prev_btn = ctk.CTkButton(bar, text="◀ Prev", width=80,
                                      command=lambda: self.change_page(-1))
        self.page_label = ctk.CTkLabel(bar, text="")
        self.next_btn = ctk.CTkButton(bar, text="Next ▶", width=80,
                                      command=lambda: self.change_page(1))
        self.action_btn = ctk.CTkButton(bar, text="", fg_color="#B71C1C", hover_color="#7F0000",
                                        command=self._on_action)
        self.status_label = ctk.CTkLabel(bar, text="", text_color="#aaa")
        self.prev_btn.pack(side="left", padx=4)
        self.page_label.pack(side="left", padx=8)
        self.next_btn.pack(side="left", padx=4)
        self.action_btn.pack(side="right", padx=8)
        self.status_label.pack(side="right", padx=8)

    # ------------------------------------------------------------------ public API

    def show_tab(self, name: str) -> None:
        self._tab = name
        self._render()

    def page_indices(self) -> List[int]:
        start = self.page * self.PAGE_SIZE
        return list(range(start, min(start + self.PAGE_SIZE, len(self.probable))))

    def set_keeper(self, set_index: int, row: ImageRow) -> None:
        self.probable[set_index] = with_keeper(self.probable[set_index], row)
        self._render()

    def mark_not_duplicates(self, set_index: int) -> None:
        s = self.probable[set_index]
        for extra in s.extras:
            self.index.mark_not_duplicates(s.keeper.pixel_sha256, extra.pixel_sha256)
        self._remove_probable({set_index})
        self.log_fn(f"↩ Not duplicates: {Path(s.keeper.path).name} "
                    f"(+{len(s.extras)}) won't be offered again")
        self._refresh()

    def change_page(self, delta: int) -> None:
        last = max(0, (len(self.probable) - 1) // self.PAGE_SIZE)
        self.page = min(max(self.page + delta, 0), last)
        self._render()

    def on_key(self, event) -> Optional[str]:
        if event.keysym == "Next":
            self.change_page(1)
            return "break"
        if event.keysym == "Prior":
            self.change_page(-1)
            return "break"
        return None

    def open_image(self, path: str) -> None:
        os.startfile(path)

    def busy(self) -> bool:
        return self._busy

    def trash_certain(self, confirm: bool = True) -> None:
        sets = list(self.certain)
        if not sets or self._busy:
            return
        n, size = sum(len(s.extras) for s in sets), sum(s.reclaim_bytes for s in sets)
        if confirm and not messagebox.askyesno(
                "Trash certain duplicates",
                f"Move {n} identical copies ({_gb(size):.2f} GB) to _duplicates_trash?\n\n"
                "The best copy of each stays where it is. You can restore them later.",
                parent=self):
            return
        self._start_trash("certain", sets, list(range(len(sets))))

    def trash_ticked_page(self, confirm: bool = True) -> None:
        if self._busy:
            return
        chosen = [i for i in self.page_indices() if self.ticked.get(i)]
        if not chosen:
            return
        sets = [self.probable[i] for i in chosen]
        n, size = sum(len(s.extras) for s in sets), sum(s.reclaim_bytes for s in sets)
        if confirm and not messagebox.askyesno(
                "Trash look-alikes",
                f"Move {n} extras from {len(sets)} ticked sets ({_gb(size):.2f} GB) "
                "to _duplicates_trash?", parent=self):
            return
        self._start_trash("probable", sets, chosen)

    # ------------------------------------------------------------------ trashing

    def _start_trash(self, kind: str, sets: List[DupSet], indices: List[int]) -> None:
        self._busy = True
        self.action_btn.configure(state="disabled")
        self.status_label.configure(text="Moving…")

        def run():
            try:
                result = trash_sets(sets)
            except Exception as e:          # never leave the window stuck "busy"
                result = TrashResult(skipped=[("", f"error: {e}")])
            self._done_q.put((kind, sets, indices, result))

        threading.Thread(target=run, daemon=True).start()

    def _finish_trash(self, kind: str, sets: List[DupSet], indices: List[int],
                      result: TrashResult) -> None:
        moved = set(result.moved)
        self.index.drop(result.moved)
        keep: Dict[int, DupSet] = {}
        for i, s in zip(indices, sets):
            left = [e for e in s.extras if e.path not in moved]
            if left:
                keep[i] = DupSet(s.kind, s.keeper, left, s.distance, s.pretick)
        if kind == "certain":
            self.certain = [keep[i] for i in sorted(keep)]
        else:
            for i, s in keep.items():
                self.probable[i] = s
            self._remove_probable(set(indices) - set(keep))
            if self.page and self.page * self.PAGE_SIZE >= len(self.probable):
                self.page -= 1
        self.log_fn(f"🗑 Trashed {len(result.moved)} files ({_gb(result.bytes):.2f} GB)")
        for path, reason in result.skipped:
            self.log_fn(f"  ⚠ Skipped {Path(path).name}: {reason}")
        self._busy = False
        self.action_btn.configure(state="normal")
        self.status_label.configure(
            text=f"Trashed {len(result.moved)}" + (f", skipped {len(result.skipped)}"
                                                   if result.skipped else ""))
        self._refresh()

    def _remove_probable(self, gone) -> None:
        kept = [(i, s) for i, s in enumerate(self.probable) if i not in gone]
        self.ticked = {n: self.ticked.get(i, False) for n, (i, _s) in enumerate(kept)}
        self.probable = [s for _i, s in kept]

    # ------------------------------------------------------------------ rendering

    def _refresh(self) -> None:
        c_files = sum(len(s.extras) for s in self.certain)
        c_bytes = sum(s.reclaim_bytes for s in self.certain)
        p_files = sum(len(s.extras) for s in self.probable)
        p_bytes = sum(s.reclaim_bytes for s in self.probable)
        self.summary_text = (
            f"Certain: {len(self.certain)} sets · {c_files} extra files · {_gb(c_bytes):.1f} GB | "
            f"Probable: {len(self.probable)} sets · {p_files} extra files · {_gb(p_bytes):.1f} GB")
        self.summary_label.configure(text=self.summary_text)
        self.title(f"🔍 Duplicates — {self.summary_text}")
        self._render()

    def _render(self) -> None:
        self.tabs.set(self._tab)
        for w in self.body.winfo_children():
            w.destroy()
        self._waiting.clear()
        if self._tab == "Certain":
            self._render_certain()
        else:
            self._render_probable()

    def _render_certain(self) -> None:
        for w in (self.prev_btn, self.next_btn):
            w.configure(state="disabled")
        self.page_label.configure(text="")
        n = sum(len(s.extras) for s in self.certain)
        size = sum(s.reclaim_bytes for s in self.certain)
        self.action_btn.configure(text=f"🗑 Trash {n} extras ({_gb(size):.2f} GB)",
                                  state="normal" if n and not self._busy else "disabled")
        if not self.certain:
            ctk.CTkLabel(self.body, text="No identical copies left.").pack(pady=20)
            return
        shown = self.certain[:self.SPOT_CHECK]
        ctk.CTkLabel(self.body, text=f"Spot-check: {len(shown)} of {len(self.certain)} sets. "
                                     "The green one in each set is kept.",
                     text_color="#aaa").pack(anchor="w", pady=(0, 6))
        for s in shown:
            self._render_set_row(self.body, s, None)

    def _render_probable(self) -> None:
        pages = max(1, (len(self.probable) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.configure(text=f"Page {self.page + 1} / {pages}")
        self.prev_btn.configure(state="normal" if self.page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.page < pages - 1 else "disabled")
        idx = self.page_indices()
        chosen = [i for i in idx if self.ticked.get(i)]
        n = sum(len(self.probable[i].extras) for i in chosen)
        size = sum(self.probable[i].reclaim_bytes for i in chosen)
        self.action_btn.configure(
            text=f"🗑 Trash extras of ticked rows ({n} files · {_gb(size):.2f} GB)",
            state="normal" if n and not self._busy else "disabled")
        if not self.probable:
            ctk.CTkLabel(self.body, text="No look-alikes left.").pack(pady=20)
            return
        for i in idx:
            self._render_set_row(self.body, self.probable[i], i)

    def _render_set_row(self, parent, s: DupSet, set_index: Optional[int]) -> None:
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4)
        if set_index is not None:
            var = ctk.BooleanVar(value=self.ticked.get(set_index, False))

            def toggle(i=set_index, v=var):
                self.ticked[i] = bool(v.get())
                self._render_probable_bar()

            ctk.CTkCheckBox(row, text="", width=24, variable=var, command=toggle
                            ).pack(side="left", padx=(8, 4))
        for member in [s.keeper] + s.extras:
            self._render_thumb(row, member, member is s.keeper, s, set_index)
        if set_index is not None:
            ctk.CTkButton(row, text="Not duplicates", width=120, fg_color="#555",
                          command=lambda i=set_index: self.mark_not_duplicates(i)
                          ).pack(side="right", padx=8)
            ctk.CTkLabel(row, text=f"distance {s.distance}", text_color="#888"
                         ).pack(side="right", padx=8)

    def _render_probable_bar(self) -> None:
        idx = self.page_indices()
        chosen = [i for i in idx if self.ticked.get(i)]
        n = sum(len(self.probable[i].extras) for i in chosen)
        size = sum(self.probable[i].reclaim_bytes for i in chosen)
        self.action_btn.configure(
            text=f"🗑 Trash extras of ticked rows ({n} files · {_gb(size):.2f} GB)",
            state="normal" if n and not self._busy else "disabled")

    def _render_thumb(self, parent, member: ImageRow, is_keeper: bool, s: DupSet,
                      set_index: Optional[int]) -> None:
        cell = ctk.CTkFrame(parent, fg_color=KEEPER_COLOR if is_keeper else "transparent",
                            corner_radius=6)
        cell.pack(side="left", padx=4, pady=4)
        img = self._thumbs.get(member.path)
        label = ctk.CTkLabel(cell, text="" if img else "…", image=img,
                             width=THUMB_SIZE, height=THUMB_SIZE)
        label.pack(padx=3, pady=(3, 0))
        caption = (f"{member.width}×{member.height} · {member.size / 1e6:.1f} MB · "
                   f"{Path(member.path).parent.name}")
        ctk.CTkLabel(cell, text=caption, font=ctk.CTkFont(size=10)).pack(padx=3, pady=(0, 3))
        if set_index is not None and not is_keeper:
            label.bind("<Button-1>", lambda e, i=set_index, r=member: self.set_keeper(i, r))
        label.bind("<Double-Button-1>", lambda e, p=member.path: self.open_image(p))
        if img is None:
            self._waiting.setdefault(member.path, []).append(label)
            if member.path not in self._requested:
                self._requested.add(member.path)
                self._loader_q.put(member.path)

    # ------------------------------------------------------------------ threads

    def _thumb_worker(self) -> None:
        while True:
            path = self._loader_q.get()
            if path is None:
                return
            try:
                blob = self.index.thumbnail(path)
                pil = Image.open(io.BytesIO(blob)).convert("RGB") if blob else None
            except Exception:
                pil = None
            self._thumb_q.put((path, pil))

    def _poll(self) -> None:
        try:
            while True:
                try:
                    path, pil = self._thumb_q.get_nowait()
                except queue.Empty:
                    break
                if pil is None:
                    continue
                pil.thumbnail((THUMB_SIZE, THUMB_SIZE))
                img = ctk.CTkImage(light_image=pil, size=pil.size)
                self._thumbs[path] = img
                for label in self._waiting.pop(path, []):
                    if label.winfo_exists():
                        label.configure(image=img, text="")
            while True:
                try:
                    self._finish_trash(*self._done_q.get_nowait())
                except queue.Empty:
                    break
        finally:
            if not self._closed:
                self._poll_job = self.after(POLL_MS, self._poll)

    def _on_action(self) -> None:
        if self._tab == "Certain":
            self.trash_certain()
        else:
            self.trash_ticked_page()

    def _on_close(self) -> None:
        if self._busy:
            self.status_label.configure(text="Finishing the move…")
            self.after(200, self._on_close)
            return
        self.destroy()

    def destroy(self):
        self._closed = True
        self._loader_q.put(None)
        try:
            self.after_cancel(self._poll_job)
        except Exception:
            pass
        super().destroy()
