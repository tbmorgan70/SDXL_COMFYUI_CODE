import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

import customtkinter as ctk  # noqa: E402
from PIL import Image  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

from gui import TriageWindow  # noqa: E402
from sorters.crop_tool import DEFAULT_CROP_PRESET  # noqa: E402
from sorters.manual_sorter import ManualSorter  # noqa: E402

FACE = (700, 300, 800, 420, 0.9)


class FakeDetector:
    available = True

    def detect(self, img):
        return [FACE]


class StubUpscaler:
    name = "stub"

    def __init__(self, delay=0.0):
        self.delay = delay

    def upscale(self, img):
        time.sleep(self.delay)
        return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


@pytest.fixture(scope="module")
def root():
    r = ctk.CTk()
    r.withdraw()
    yield r
    r.destroy()


def pump(root, cond, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        root.update()
        if cond():
            return True
        time.sleep(0.01)
    return False


def key(k, state=0):
    return SimpleNamespace(keysym=k, char=k, state=state)


def make_images(folder, n=3, size=(600, 600)):
    for name in "abcdefgh"[:n]:
        info = PngInfo()
        info.add_text("parameters", f"prompt {name}\nSteps: 20, Size: {size[0]}x{size[1]}")
        Image.new("RGB", size, (90, 120, 150)).save(folder / f"{name}.png", pnginfo=info)


def crop_defaults(upscaler=None):
    up = upscaler or StubUpscaler()
    return {"preset": DEFAULT_CROP_PRESET, "ai": True, "model": Path("stub.pth"),
            "face_detector_factory": FakeDetector, "upscaler_factory": lambda p: up}


@pytest.fixture
def open_window(root, tmp_path):
    made = []

    def _open(crop_only=False, upscaler=None, n=3):
        make_images(tmp_path, n)
        logs = []
        win = TriageWindow(root, ManualSorter(None, tmp_path, ["Keep"]), logs.append,
                           crop_only=crop_only, crop_defaults=crop_defaults(upscaler))
        pump(root, lambda: False, timeout=0.3)
        made.append(win)
        return win

    yield _open
    for win in made:
        if win.winfo_exists():
            if win.crop_editor is not None:
                win.crop_editor.shutdown()
            win.destroy()
    root.update()


def pump_until_loaded(root, win):
    assert pump(root, lambda: win.crop_editor is not None and win.crop_editor.rect is not None)


def badge_text(win, path):
    pair = win.thumb_widgets.get(path)
    if pair is None:
        return None
    for child in pair[0].winfo_children():
        text = child.cget("text") if hasattr(child, "cget") else ""
        if isinstance(text, str) and text.startswith("✂"):
            return text
    return None


def test_c_toggles_crop_mode_only_in_viewer(root, open_window):
    win = open_window()
    win._on_keypress(key("c"))
    assert win.crop_mode is False                         # gallery: ignored
    win._open_viewer(0)
    win._on_keypress(key("c"))
    root.update()
    assert win.crop_mode is True
    assert win.crop_editor.winfo_ismapped() and not win.viewer_label.winfo_ismapped()
    win._on_keypress(key("Escape"))
    root.update()
    assert win.crop_mode is False and win.current_index == 0
    assert win.viewer_label.winfo_ismapped()


def test_enter_saves_navigates_and_badges(root, open_window, tmp_path):
    win = open_window()
    win._open_viewer(0)
    win._on_keypress(key("c"))
    pump_until_loaded(root, win)
    first = win.sorter.images[0]
    assert win._on_keypress(key("Return")) == "break"
    assert win.current_index == 1
    assert pump(root, lambda: win.crop_counts.get(first) == 1)
    assert (tmp_path / "cropped__1024x1024" / first.name).exists()
    assert win.status_label.cget("text").endswith("✂ 1 crop")
    win._show_gallery()
    win._render_page()
    root.update()
    assert badge_text(win, first) == "✂ 1"


def test_bucket_keys_work_in_crop_mode(root, open_window):
    win = open_window()
    win._open_viewer(0)
    win._on_keypress(key("c"))
    pump_until_loaded(root, win)
    first = win.sorter.images[0]
    win._on_keypress(key("1"))
    assert win.sorter.get_assignment(first) == "Keep"
    assert win.current_index == 1
    assert win.crop_editor.path == win.sorter.images[1]


def test_plain_right_navigates_without_saving_in_crop_mode(root, open_window, tmp_path):
    win = open_window()
    win._open_viewer(0)
    win._on_keypress(key("c"))
    pump_until_loaded(root, win)
    win._on_keypress(key("Right"))
    assert win.current_index == 1
    pump(root, lambda: False, timeout=0.4)
    assert not (tmp_path / "cropped__1024x1024").exists()


def test_crop_only_hides_buckets_and_opens_in_crop_mode(root, open_window):
    win = open_window(crop_only=True)
    root.update()
    assert not any(b.winfo_ismapped() for b in win.bucket_buttons.values())
    assert not win.execute_btn.winfo_ismapped()
    win._open_viewer(0)
    root.update()
    assert win.crop_mode is True and win.crop_editor.winfo_ismapped()
    pump_until_loaded(root, win)
    win._on_keypress(key("1"))
    assert win.sorter.assignments == {}


def test_close_waits_for_pending_saves(root, open_window, tmp_path):
    win = open_window(crop_only=True, upscaler=StubUpscaler(delay=0.4), n=1)
    win._open_viewer(0)
    pump_until_loaded(root, win)
    win._on_keypress(key("Return", 0x1))
    win._on_close()
    assert win.winfo_exists()
    assert win.status_label.cget("text").startswith("Finishing")
    assert pump(root, lambda: not win.winfo_exists())
    assert (tmp_path / "cropped__1024x1024" / "a.png").exists()


MODE_CHECK = """
from gui import SorterGUI
from sorters.crop_tool import DEFAULT_CROP_PRESET
app = SorterGUI()
app.withdraw()
app.mode_var.set("Manual Crop")
app._switch_mode()
app.update()
assert app.crop_frame.winfo_manager() == "pack"
assert app.crop_preset_var.get() == DEFAULT_CROP_PRESET
assert "Manual Crop" in app.mode_menu.cget("values")
app.destroy()
print("MODE-OK")
"""


def test_manual_crop_mode_switches_form():
    # The full app is a Tk root of its own; a second root in this process
    # intermittently fails Tcl initialisation (tcl_findLibrary), so it runs
    # in a fresh interpreter, as the real app does.
    sorter_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter"))
    done = subprocess.run([sys.executable, "-c", MODE_CHECK], cwd=sorter_dir,
                          capture_output=True, text=True, timeout=120)
    assert "MODE-OK" in done.stdout, done.stderr[-2000:]


def test_execute_waits_for_pending_crop_saves(root, open_window, tmp_path, monkeypatch):
    import gui
    monkeypatch.setattr(gui.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)
    win = open_window(upscaler=StubUpscaler(delay=0.5), n=2)
    win._open_viewer(0)
    win._on_keypress(key("c"))
    pump_until_loaded(root, win)
    first = win.sorter.images[0]
    win._on_keypress(key("Return", 0x1))     # save & stay (AI, slow)
    win._on_keypress(key("1"))               # then Keep
    win._execute()
    assert first.exists()                    # not moved while its crop is queued
    assert pump(root, lambda: (tmp_path / "Keep" / first.name).exists())
    assert (tmp_path / "cropped__1024x1024" / first.name).exists()
