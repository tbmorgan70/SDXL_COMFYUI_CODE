"""
Crop Editor — the Manual Crop panel (Sorter 3.6).

A fixed frame in the middle of a canvas with the image floating underneath:
drag to move the image, scroll to zoom, Enter to save a copy at the preset
size. Used inside the Triage viewer (C key) and by the Manual Crop mode.

Threading follows the TriageWindow rule: image decoding, face detection and
saving run on worker threads, and only the main thread (an after() poller)
touches Tk objects — including log calls, which can reach the GUI.
"""

import gc
import queue
import re
import threading
import time
import tkinter as tk
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from sorters.crop_tool import (CROP_SIZE_PRESETS, GRADE_COLORS, CropRect, clamp, face_seed,
                               flipped, step_preset,
                               grade, largest_fit, open_oriented, pan, save_crop, workable,
                               zoom_at)
from sorters.upscaler import DEFAULT_MODELS_DIR, list_upscale_models

SHIFT, CONTROL = 0x1, 0x4
FRAME_MARGIN = 40          # canvas pixels around the frame
DIM = 0.45                 # brightness outside the frame
SHARPEN_AFTER_MS = 150     # Lanczos re-render once motion stops
POLL_MS = 30
CACHE_SIZE = 3
BUFFER_MARGIN = 0.25     # extra view-widths drawn around the view, for panning
ZOOM_STEP = 1.1
NUDGE, BIG_NUDGE = 0.01, 0.10
CANVAS_BG = (32, 32, 32)
FACE_COLOR = "#EF9F27"
NO_MODEL = "(no model)"
_ARROWS = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}
_SKIPPED = object()        # loader result marker: the image was navigated past


class _UnavailableUpscaler:
    """Stands in when the upscaler can't be created, so the save falls back
    to a plain resize and the manifest records why."""
    name = "unavailable"

    def __init__(self, err):
        self._err = err

    def upscale(self, img):
        raise RuntimeError(self._err)


def _default_face_detector(log):
    from sorters.image_extractor import FaceDetector
    return FaceDetector(log=log)


def _default_upscaler(path, log):
    from sorters.upscaler import Upscaler
    return Upscaler(path, log=log)


class CropEditor(ctk.CTkFrame):
    """Toolbar + canvas. The host feeds it images with load() and forwards
    key presses to handle_key(); everything else happens inside."""

    PROXY_MAX = 2048

    def __init__(self, master, *, preset_label: str, ai_enabled: bool,
                 model_path: Optional[Path],
                 face_detector_factory: Optional[Callable[[], object]] = None,
                 upscaler_factory: Optional[Callable[[Path], object]] = None,
                 on_saved: Optional[Callable] = None,
                 on_error: Optional[Callable] = None,
                 on_advance: Optional[Callable[[], None]] = None,
                 log: Optional[Callable[[str], None]] = None):
        super().__init__(master)
        self._log = log or (lambda m: None)
        self._log_q = queue.Queue()
        thread_log = self._log_q.put        # workers log through the poller
        self._face_factory = face_detector_factory or (lambda: _default_face_detector(thread_log))
        self._upscaler_factory = upscaler_factory or (lambda p: _default_upscaler(p, thread_log))
        self.on_saved, self.on_error, self.on_advance = on_saved, on_error, on_advance

        # Public state
        self.path: Optional[Path] = None
        self.rect: Optional[CropRect] = None
        self.src_size = None
        self.face_box = None
        self.current_grade = None
        self.last_render_ms = 0.0
        self.status_text = ""

        self._custom_sizes = {}
        self.preset_label = preset_label
        self.out_size = self._size_for(preset_label) or (1024, 1024)
        self.ai_enabled = ai_enabled
        self.model_path = Path(model_path) if model_path else None

        self._proxy = None
        self._cache = OrderedDict()          # path -> load result
        self._requested = set()
        self._wanted = frozenset()           # paths the loader should still bother with
        self._pending = 0
        self._closed = False
        self._host_gone = False
        self._drag_from = None
        self._sharpen_job = None
        self._photo = None
        self._buf = None                     # (source region, scale, sharp) of the drawn image
        self._overlay_key, self._overlay_photo = None, None
        self._detector = None                # loader thread only
        self._upscaler, self._upscaler_path = None, None    # save thread only

        self._load_q, self._load_results = queue.Queue(), queue.Queue()
        self._save_q, self._save_results = queue.Queue(), queue.Queue()

        self._build_ui()
        # Closed windows leave cyclic garbage that holds Tk objects. If one of
        # our worker threads' allocations triggers the collection, each Tk
        # __del__ runs on that thread and must wait for the main thread (up to
        # 1 s apiece outside mainloop). Collect it here, on the main thread,
        # before the workers start.
        gc.collect()
        self._loader_thread = threading.Thread(target=self._loader, daemon=True)
        self._saver_thread = threading.Thread(target=self._saver, daemon=True)
        self._loader_thread.start()
        self._saver_thread.start()
        self._poll_job = self.after(POLL_MS, self._poll)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=4, pady=(4, 2))

        labels = list(CROP_SIZE_PRESETS.keys())
        if self.preset_label not in labels:
            labels.insert(-1, self.preset_label)
        self.preset_menu = ctk.CTkOptionMenu(bar, values=labels, width=230,
                                             command=self._on_preset_menu)
        self.preset_menu.set(self.preset_label)
        self.preset_menu.pack(side="left", padx=4)

        self.ai_var = tk.BooleanVar(value=self.ai_enabled)
        ctk.CTkCheckBox(bar, text="AI upscale when needed", variable=self.ai_var,
                        command=self._on_ai_toggle).pack(side="left", padx=8)

        self._models = {p.stem: p for p in list_upscale_models(DEFAULT_MODELS_DIR)}
        if self.model_path is not None:
            self._models.setdefault(self.model_path.stem, self.model_path)
        names = list(self._models) or [NO_MODEL]
        self.model_menu = ctk.CTkOptionMenu(bar, values=names, width=190,
                                            command=self._on_model_menu)
        self.model_menu.set(self.model_path.stem if self.model_path else names[0])
        if self.model_path is None and self._models:
            self.model_path = self._models[names[0]]
        self.model_menu.pack(side="left", padx=4)

        self.badge = ctk.CTkLabel(bar, text="", width=230, corner_radius=6,
                                  fg_color="#555555", text_color="white")
        self.badge.pack(side="left", padx=8)

        self.status = ctk.CTkLabel(bar, text="", text_color="#aaaaaa", anchor="w")
        self.status.pack(side="left", padx=8, fill="x", expand=True)

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#%02x%02x%02x" % CANVAS_BG)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=(2, 4))
        self._img_item = self.canvas.create_image(0, 0, anchor="nw")
        self._overlay_item = self.canvas.create_image(0, 0, anchor="nw")
        self._thirds = [self.canvas.create_line(0, 0, 0, 0, fill="#ffffff", width=1,
                                                stipple="gray50") for _ in range(4)]
        self._face_item = self.canvas.create_rectangle(0, 0, 0, 0, outline=FACE_COLOR,
                                                       dash=(4, 4), width=2)
        self._frame_item = self.canvas.create_rectangle(0, 0, 0, 0, outline="#ffffff", width=2)
        self._msg_item = self.canvas.create_text(0, 0, text="", fill="#aaaaaa",
                                                 font=("Segoe UI", 14))

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Configure>", lambda e: self.render(sharp=True))

    def _set_status(self, text: str):
        self.status_text = text
        self.status.configure(text=text)

    def _show_message(self, text: str):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.coords(self._msg_item, cw / 2, ch / 2)
        self.canvas.itemconfigure(self._msg_item, text=text)
        for item in [self._img_item, self._overlay_item, self._face_item,
                     self._frame_item] + self._thirds:
            self.canvas.itemconfigure(item, state="hidden")

    # ------------------------------------------------------------------ presets

    def _size_for(self, label):
        size = self._custom_sizes.get(label) or CROP_SIZE_PRESETS.get(label)
        return size if isinstance(size, tuple) else None

    @property
    def _ar(self) -> float:
        return self.out_size[0] / self.out_size[1]

    def set_preset(self, label: str) -> None:
        size = self._size_for(label)
        if size is None:
            return
        self.preset_label, self.out_size = label, size
        if self.preset_menu.get() != label:
            self.preset_menu.set(label)
        if self.rect is not None:
            area = self.rect.w * self.rect.h
            w = (area * self._ar) ** 0.5
            h = w / self._ar
            cx, cy = self.rect.x + self.rect.w / 2, self.rect.y + self.rect.h / 2
            self.rect = clamp(CropRect(cx - w / 2, cy - h / 2, w, h), *self.src_size, self._ar)
        self._changed(sharp=True)

    def _on_preset_menu(self, choice):
        if CROP_SIZE_PRESETS.get(choice) != "custom":
            self.set_preset(choice)
            return
        answer = ctk.CTkInputDialog(text="Output size as WxH, e.g. 1200x1500",
                                    title="Custom crop size").get_input()
        m = re.match(r"^\s*(\d+)\s*[x×*]\s*(\d+)\s*$", answer or "")
        if not m or not all(16 <= int(v) <= 8192 for v in m.groups()):
            self.preset_menu.set(self.preset_label)
            if answer:
                self._set_status("Enter a size like 1200x1500")
            return
        self.set_preset(self._custom_label(int(m.group(1)), int(m.group(2))))

    def _custom_label(self, w: int, h: int) -> str:
        """A 'Custom W×H' preset, added to the menu if it isn't there yet."""
        label = f"Custom {w}×{h}"
        self._custom_sizes[label] = (w, h)
        values = list(self.preset_menu.cget("values"))
        if label not in values:
            values.insert(len(values) - 1, label)
            self.preset_menu.configure(values=values)
        return label

    def _all_sizes(self):
        sizes = {k: v for k, v in CROP_SIZE_PRESETS.items() if isinstance(v, tuple)}
        sizes.update(self._custom_sizes)
        return sizes

    def step_preset(self, step: int) -> None:
        """Tab / Shift+Tab: the next size of the same orientation."""
        self.set_preset(step_preset(self._all_sizes(), self.preset_label, step))

    def flip_orientation(self) -> None:
        """O: the same size turned portrait ↔ landscape."""
        target = flipped(self.out_size)
        label = next((k for k, v in self._all_sizes().items() if v == target), None)
        self.set_preset(label or self._custom_label(*target))

    def _on_ai_toggle(self):
        self.ai_enabled = bool(self.ai_var.get())
        self._update_grade()

    def _on_model_menu(self, stem):
        self.model_path = self._models.get(stem)

    # ------------------------------------------------------------------ loading

    def load(self, path: Path, prefetch: Optional[Path] = None) -> None:
        self.path = Path(path)
        # Anything still queued that isn't this image or the next is skipped
        self._wanted = frozenset(p for p in (self.path, Path(prefetch) if prefetch else None) if p)
        self.rect = self.src_size = self.face_box = self._proxy = None
        self.current_grade = None
        cached = self._cache.get(self.path)
        if cached is not None:
            self._apply_loaded(cached)
        else:
            self._request(self.path)
            self._set_status("Loading…")
            self._show_message("Loading…")
        if prefetch is not None and Path(prefetch) not in self._cache:
            self._request(Path(prefetch))

    def _request(self, path: Path):
        if path not in self._requested:
            self._requested.add(path)
            self._load_q.put(path)

    def _loader(self):
        while True:
            path = self._load_q.get()
            if path is None:
                return
            if path not in self._wanted:
                self._load_results.put((path, None, None, None, _SKIPPED))
                continue
            try:
                _orig, img = open_oriented(path)
                src_size = img.size
                proxy = workable(img).convert("RGB")
                proxy.thumbnail((self.PROXY_MAX, self.PROXY_MAX), Image.LANCZOS)
                face = None
                if self._detector is None:
                    try:
                        self._detector = self._face_factory()
                    except Exception as e:
                        self._log_q.put(f"  Face detection unavailable ({e})")
                        self._detector = False
                if self._detector and getattr(self._detector, "available", False):
                    faces = self._detector.detect(proxy)
                    if faces:
                        x1, y1, x2, y2 = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))[:4]
                        k = src_size[0] / proxy.width
                        face = (x1 * k, y1 * k, x2 * k, y2 * k)
                self._load_results.put((path, proxy, src_size, face, None))
            except Exception as e:
                self._load_results.put((path, None, None, None,
                                        f"Cannot open {Path(path).name}: {e}"))

    def _apply_loaded(self, result):
        path, proxy, src_size, face, error = result
        if error:
            self._set_status(error)
            self._show_message(error)
            return
        self._proxy, self.src_size, self.face_box = proxy, src_size, face
        self._buf = None
        if face is not None:
            self.rect = face_seed(*src_size, self._ar, face)
        else:
            self.rect = largest_fit(*src_size, self._ar)
        self._set_status("")
        self._changed(sharp=True)

    # ------------------------------------------------------------------ saving

    def save(self, advance: bool) -> bool:
        if self.rect is None or self.path is None:
            self._set_status("Still loading…")
            return False
        w, h = self.out_size
        use_ai = self.ai_enabled and self.model_path is not None
        self._pending += 1
        self._save_q.put((self.path, self.rect, w, h, use_ai, self.model_path))
        self._set_status(f"Saving… ({self._pending})")
        if advance and self.on_advance:
            self.on_advance()
        return True

    def _saver(self):
        while True:
            job = self._save_q.get()
            if job is None:
                return
            path, rect, w, h, use_ai, model_path = job
            up = None
            if use_ai and w / rect.w > 1.0:
                if self._upscaler is None or self._upscaler_path != model_path:
                    try:
                        self._upscaler = self._upscaler_factory(model_path)
                    except Exception as e:
                        self._upscaler = _UnavailableUpscaler(e)
                    self._upscaler_path = model_path
                up = self._upscaler
            try:
                self._save_results.put((path, save_crop(path, rect, w, h, upscaler=up), None))
            except Exception as e:
                self._save_results.put((path, None, f"Save failed for {path.name}: {e}"))

    def pending_saves(self) -> int:
        return self._pending

    def _deliver_save(self, item):
        path, result, error = item
        self._pending -= 1
        if self._host_gone:
            return      # the host is being torn down; its widgets may be gone
        if error:
            self._set_status(error)
            self._log(f"✗ {error}")
            if self.on_error:
                self.on_error(path, error)
            return
        self._set_status(f"✂ Saved {result.path.name} ({result.method})")
        if self.on_saved:
            self.on_saved(path, result)

    # ------------------------------------------------------------------ poller

    def _poll(self):
        try:
            while True:
                try:
                    result = self._load_results.get_nowait()
                except queue.Empty:
                    break
                path = result[0]
                self._requested.discard(path)
                if result[4] is _SKIPPED:
                    if path == self.path and self.rect is None:
                        self._request(path)     # navigated back to it meanwhile
                    continue
                self._cache[path] = result
                self._cache.move_to_end(path)
                while len(self._cache) > CACHE_SIZE:
                    oldest = next(iter(self._cache))
                    if oldest == self.path:
                        self._cache.move_to_end(oldest)
                        oldest = next(iter(self._cache))
                    self._cache.pop(oldest)
                if path == self.path and self.rect is None:
                    self._apply_loaded(result)
            while True:
                try:
                    self._deliver_save(self._save_results.get_nowait())
                except queue.Empty:
                    break
            while True:
                try:
                    self._log(self._log_q.get_nowait())
                except queue.Empty:
                    break
        finally:
            if not self._closed:
                self._poll_job = self.after(POLL_MS, self._poll)

    def shutdown(self) -> None:
        """Finish queued saves (delivering their callbacks), then stop."""
        if self._closed:
            return
        self._closed = True
        for job in (self._poll_job, self._sharpen_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        self._load_q.put(None)
        self._save_q.put(None)
        self._saver_thread.join()
        while not self._save_results.empty():
            self._deliver_save(self._save_results.get_nowait())
        while not self._log_q.empty():
            msg = self._log_q.get_nowait()
            if not self._host_gone:
                self._log(msg)

    def destroy(self):
        # Reached when a parent window is destroyed: queued saves still
        # finish, but nothing is reported back to widgets that may be gone
        self._host_gone = True
        self.shutdown()
        super().destroy()

    # ------------------------------------------------------------------ geometry + render

    def frame_box(self):
        """The fixed frame on the canvas: (x, y, w, h) in canvas pixels."""
        cw = max(self.canvas.winfo_width(), 2 * FRAME_MARGIN + 10)
        ch = max(self.canvas.winfo_height(), 2 * FRAME_MARGIN + 10)
        fw = min(cw - 2 * FRAME_MARGIN, (ch - 2 * FRAME_MARGIN) * self._ar)
        fh = fw / self._ar
        return (cw - fw) / 2, (ch - fh) / 2, fw, fh

    def _changed(self, sharp=False, margin=True):
        self._update_grade()
        self.render(sharp=sharp, margin=margin)
        if not sharp:
            if self._sharpen_job is not None:
                self.after_cancel(self._sharpen_job)
            self._sharpen_job = self.after(SHARPEN_AFTER_MS, self._sharpen)

    def _sharpen(self):
        self._sharpen_job = None
        self.render(sharp=True)

    def _update_grade(self):
        if self.rect is None:
            return
        g = grade(self.rect, *self.out_size, self.ai_enabled)
        if g.label != getattr(self.current_grade, "label", None):
            self.badge.configure(text=g.label, fg_color=GRADE_COLORS[g.level])
        self.current_grade = g

    def _ensure_overlay(self, cw: int, ch: int, box):
        """The dimming around the frame: one semi-transparent image that only
        changes with the canvas size or the preset, never while panning."""
        key = (cw, ch, box)
        if self._overlay_key == key:
            return
        ov = Image.new("RGBA", (cw, ch), (0, 0, 0, round(255 * (1 - DIM))))
        ov.paste((0, 0, 0, 0), box)
        self._overlay_photo = ImageTk.PhotoImage(ov)
        self.canvas.itemconfigure(self._overlay_item, image=self._overlay_photo)
        self._overlay_key = key

    def render(self, sharp: bool = False, margin: bool = True) -> None:
        """Panning only moves an already-drawn image item. The image is
        redrawn (the view plus a margin, at the current zoom) only when the
        view leaves it, the zoom changes, or a sharp version is wanted.
        Zoom steps skip the margin to stay quick; the sharp pass adds it."""
        if self._proxy is None or self.rect is None:
            return
        t0 = time.perf_counter()
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 10 or ch < 10:
            return
        fx, fy, fw, fh = self.frame_box()
        r = self.rect
        scale = fw / r.w                         # canvas px per source px
        sx0, sy0 = r.x - fx / scale, r.y - fy / scale
        sx1, sy1 = sx0 + cw / scale, sy0 + ch / scale
        src_w, src_h = self.src_size
        visible = (max(sx0, 0.0), max(sy0, 0.0), min(sx1, src_w), min(sy1, src_h))

        buf = self._buf
        reusable = (buf is not None and buf[1] == scale and (buf[2] or not sharp)
                    and buf[0][0] <= visible[0] and buf[0][1] <= visible[1]
                    and buf[0][2] >= visible[2] and buf[0][3] >= visible[3])
        if not reusable:
            pad = BUFFER_MARGIN if margin else 0.0
            mx, my = pad * cw / scale, pad * ch / scale
            region = (max(sx0 - mx, 0.0), max(sy0 - my, 0.0),
                      min(sx1 + mx, src_w), min(sy1 + my, src_h))
            # Per-axis: thumbnail() rounds each side, so one factor would
            # overrun the proxy's short side by up to a pixel
            pw, ph = self._proxy.size
            kx, ky = pw / src_w, ph / src_h
            size = (max(1, round((region[2] - region[0]) * scale)),
                    max(1, round((region[3] - region[1]) * scale)))
            box = (region[0] * kx, region[1] * ky,
                   min(region[2] * kx, pw), min(region[3] * ky, ph))
            img = self._proxy.resize(size, Image.LANCZOS if sharp else Image.BILINEAR, box=box)
            self._photo = ImageTk.PhotoImage(img)
            c.itemconfigure(self._img_item, image=self._photo)
            buf = self._buf = (region, scale, sharp)
        c.coords(self._img_item, (buf[0][0] - sx0) * scale, (buf[0][1] - sy0) * scale)

        box = (round(fx), round(fy), round(fx + fw), round(fy + fh))
        self._ensure_overlay(cw, ch, box)
        c.itemconfigure(self._msg_item, text="")
        for item in (self._img_item, self._overlay_item, self._frame_item):
            c.itemconfigure(item, state="normal")
        c.coords(self._frame_item, *box)
        for i, item in enumerate(self._thirds):
            t = (i % 2 + 1) / 3
            if i < 2:
                c.coords(item, fx + fw * t, fy, fx + fw * t, fy + fh)
            else:
                c.coords(item, fx, fy + fh * t, fx + fw, fy + fh * t)
            c.itemconfigure(item, state="normal")
        if self.face_box is not None:
            x1, y1, x2, y2 = self.face_box
            c.coords(self._face_item, fx + (x1 - r.x) * scale, fy + (y1 - r.y) * scale,
                     fx + (x2 - r.x) * scale, fy + (y2 - r.y) * scale)
            c.itemconfigure(self._face_item, state="normal")
        else:
            c.itemconfigure(self._face_item, state="hidden")
        self.last_render_ms = (time.perf_counter() - t0) * 1000

    # ------------------------------------------------------------------ input

    def on_press(self, event) -> None:
        self._drag_from = (event.x, event.y)

    def on_drag(self, event) -> None:
        if self._drag_from is None or self.rect is None:
            return
        scale = self.frame_box()[2] / self.rect.w
        dx = (event.x - self._drag_from[0]) / scale
        dy = (event.y - self._drag_from[1]) / scale
        self._drag_from = (event.x, event.y)
        # The image moves with the cursor, so the frame moves the other way
        self.rect = pan(self.rect, -dx, -dy, *self.src_size, self._ar)
        self._changed()

    def on_release(self, event) -> None:
        self._drag_from = None

    def on_wheel(self, event) -> None:
        if self.rect is None:
            return
        fx, fy, fw, _ = self.frame_box()
        scale = fw / self.rect.w
        ax = self.rect.x + (event.x - fx) / scale
        ay = self.rect.y + (event.y - fy) / scale
        notches = event.delta / 120 if event.delta else 0
        self.rect = zoom_at(self.rect, ZOOM_STEP ** -notches, ax, ay, *self.src_size, self._ar)
        self._changed(margin=False)

    def _zoom_centre(self, factor):
        r = self.rect
        self.rect = zoom_at(r, factor, r.x + r.w / 2, r.y + r.h / 2, *self.src_size, self._ar)
        self._changed(margin=False)

    def handle_key(self, event) -> bool:
        k = event.keysym
        state = getattr(event, "state", 0) or 0
        shift, ctrl = bool(state & SHIFT), bool(state & CONTROL)
        if k in ("Return", "KP_Enter"):
            self.save(advance=not shift)
            return True
        if k in ("Tab", "ISO_Left_Tab"):
            self.step_preset(-1 if (shift or k == "ISO_Left_Tab") else 1)
            return True
        if k in ("o", "O"):
            self.flip_orientation()
            return True
        if self.rect is None:
            return False
        if shift and k in _ARROWS:
            step = (BIG_NUDGE if ctrl else NUDGE) * self.rect.w
            dx, dy = _ARROWS[k]
            self.rect = pan(self.rect, dx * step, dy * step, *self.src_size, self._ar)
            self._changed()
            return True
        if k in ("plus", "equal", "KP_Add"):
            self._zoom_centre(1 / ZOOM_STEP)
            return True
        if k in ("minus", "KP_Subtract"):
            self._zoom_centre(ZOOM_STEP)
            return True
        if k in ("f", "F"):
            if self.face_box is None:
                self._set_status("No face found")
            else:
                self.rect = face_seed(*self.src_size, self._ar, self.face_box)
                self._changed(sharp=True)
            return True
        if k in ("r", "R"):
            self.rect = largest_fit(*self.src_size, self._ar)
            self._changed(sharp=True)
            return True
        return False
