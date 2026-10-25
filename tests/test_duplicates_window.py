import gc
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

import customtkinter as ctk  # noqa: E402
from PIL import Image  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

import duplicates_window  # noqa: E402
from core.image_index import TRASH_DIR, ImageIndex  # noqa: E402
from duplicates_window import DuplicatesWindow  # noqa: E402
from sorters.duplicate_finder import find_sets  # noqa: E402


@pytest.fixture(scope="module")
def root():
    r = ctk.CTk()
    r.withdraw()
    yield r
    r.destroy()


def pump(root, cond, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        root.update()
        if cond():
            return True
        time.sleep(0.01)
    return False


def base_image(seed):
    """Smooth and distinct per seed: a random 3x4 colour grid blown up."""
    tiny = np.random.default_rng(seed).integers(0, 255, (4, 3, 3), dtype=np.uint8)
    return Image.fromarray(tiny).resize((120, 160), Image.BICUBIC)


@pytest.fixture
def lib(tmp_path):
    folder = tmp_path / "lib"
    (folder / "pairs").mkdir(parents=True)
    (folder / "copies").mkdir()
    for i in range(20):                                   # post_sampler + 4x upscale
        img = base_image(i)
        img.save(folder / "pairs" / f"p{i:02d}_small.png")
        img.resize((480, 640), Image.LANCZOS).save(folder / "pairs" / f"p{i:02d}_big.png")
    for i in range(3):                                    # same pixels, one with metadata
        img = base_image(100 + i)
        info = PngInfo()
        info.add_text("parameters", "prompt")
        img.save(folder / "copies" / f"c{i}_orig.png", pnginfo=info)
        img.save(folder / "copies" / f"c{i}_copy.png")
    index = ImageIndex(tmp_path / "idx.db")
    index.scan([str(folder)], workers=1)
    certain, probable = find_sets(index.rows([str(folder)]))
    assert len(certain) == 3 and len(probable) == 20
    yield SimpleNamespace(folder=folder, index=index, certain=certain, probable=probable)
    index.close()


@pytest.fixture
def win(root, lib):
    logs = []
    w = DuplicatesWindow(root, lib.index, list(lib.certain), list(lib.probable), logs.append)
    w.logs = logs
    pump(root, lambda: False, timeout=0.3)
    yield w
    if w.winfo_exists():
        w.destroy()
    root.update()
    gc.collect()


def gb(n):
    return n / 1e9


def test_summary_line(lib, win):
    c_bytes = sum(s.reclaim_bytes for s in lib.certain)
    p_bytes = sum(s.reclaim_bytes for s in lib.probable)
    p_files = sum(len(s.extras) for s in lib.probable)
    assert win.summary_text == (f"Certain: 3 sets · 3 extra files · {gb(c_bytes):.1f} GB | "
                                f"Probable: 20 sets · {p_files} extra files · {gb(p_bytes):.1f} GB")


def test_first_page_has_15_rows_preticked(win):
    win.show_tab("Probable")
    assert win.page_indices() == list(range(15))
    assert all(win.ticked[i] for i in win.page_indices())


def test_set_keeper_swaps(win):
    other = win.probable[0].extras[0]
    win.set_keeper(0, other)
    assert win.probable[0].keeper.path == other.path


def test_trash_ticked_page_moves_and_advances(root, lib, win):
    win.show_tab("Probable")
    kept_extra = Path(win.probable[0].extras[0].path)
    expected = sum(len(win.probable[i].extras) for i in range(1, 15))
    win.ticked[0] = False
    win.trash_ticked_page(confirm=False)
    assert pump(root, lambda: not win.busy())
    trashed = list((lib.folder / TRASH_DIR).rglob("*.png"))
    assert len(trashed) == expected and kept_extra.exists()
    assert len(win.probable) == 6 and win.page == 0


def test_not_duplicates_hides_and_persists(lib, win):
    s = win.probable[0]
    win.mark_not_duplicates(0)
    assert len(win.probable) == 19
    pair = tuple(sorted((s.keeper.pixel_sha256, s.extras[0].pixel_sha256)))
    assert pair in lib.index.not_duplicate_pairs()


def test_trash_certain(root, lib, win):
    win.trash_certain(confirm=False)
    assert pump(root, lambda: not win.busy())
    assert not any((lib.folder / "copies").glob("*_copy.png"))
    assert len(list((lib.folder / TRASH_DIR / "copies").glob("*_copy.png"))) == 3
    assert win.certain == []


def test_page_keys(win):
    win.show_tab("Probable")
    win.on_key(SimpleNamespace(keysym="Next"))
    assert win.page == 1 and win.page_indices() == list(range(15, 20))
    win.on_key(SimpleNamespace(keysym="Prior"))
    assert win.page == 0


def extra_label(win, set_index=0):
    s = win.probable[set_index]
    return s, win.thumb_labels[(set_index, s.extras[0].path)]


def test_single_click_on_extra_makes_it_keeper(root, win):
    win.show_tab("Probable")
    root.update()
    s, label = extra_label(win)
    label._label.event_generate("<Button-1>", x=5, y=5)
    pump(root, lambda: False, timeout=0.5)
    assert win.probable[0].keeper.path == s.extras[0].path


def test_double_click_on_extra_opens_it_and_keeps_keeper(root, win, monkeypatch):
    opened = []
    monkeypatch.setattr(duplicates_window.os, "startfile", opened.append, raising=False)
    win.show_tab("Probable")
    root.update()
    s, label = extra_label(win)
    t0 = int(time.time() * 1000) & 0x7FFFFFFF
    for t in (t0, t0 + 100):                    # two presses, 100 ms apart = a double-click
        label._label.event_generate("<ButtonPress-1>", x=5, y=5, time=t)
        label._label.event_generate("<ButtonRelease-1>", x=5, y=5, time=t + 10)
    pump(root, lambda: False, timeout=0.5)
    assert opened == [s.extras[0].path]
    assert win.probable[0].keeper.path == s.keeper.path


def slow_trash(monkeypatch, delay=0.6, fail=None):
    real = duplicates_window.trash_sets

    def slow(sets, *a, **k):
        time.sleep(delay)
        return real(sets, *a, **k)
    monkeypatch.setattr(duplicates_window, "trash_sets", slow)


def test_edits_are_ignored_while_a_batch_is_moving(root, win, monkeypatch):
    slow_trash(monkeypatch)
    win.show_tab("Probable")
    before = (win.probable[1].keeper.path, len(win.probable))
    win.trash_ticked_page(confirm=False)
    assert win.busy()
    win.set_keeper(1, win.probable[1].extras[0])
    win.mark_not_duplicates(1)
    assert (win.probable[1].keeper.path, len(win.probable)) == before
    assert pump(root, lambda: not win.busy())


def test_busy_clears_even_if_finishing_fails(root, win, monkeypatch):
    def boom(_paths):
        raise RuntimeError("index unavailable")
    monkeypatch.setattr(win.index, "drop", boom)
    win.trash_certain(confirm=False)
    assert pump(root, lambda: not win.busy())


def test_certain_confirm_says_where_extras_come_from(win, monkeypatch):
    asked = []
    monkeypatch.setattr(duplicates_window.messagebox, "askyesno",
                        lambda title, msg, **k: asked.append(msg) or False)
    win.trash_certain(confirm=True)
    assert asked and "3 × " in asked[0] and "copies" in asked[0]


def test_double_click_opens_file(win, monkeypatch):
    opened = []
    monkeypatch.setattr(duplicates_window.os, "startfile", opened.append, raising=False)
    path = win.probable[0].keeper.path
    win.open_image(path)
    assert opened == [path]
