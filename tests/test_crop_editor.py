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

from crop_editor import CropEditor  # noqa: E402
from sorters.crop_tool import DEFAULT_CROP_PRESET, face_seed, largest_fit  # noqa: E402

FACE = (700, 300, 800, 420)


class FakeDetector:
    available = True

    def __init__(self, boxes):
        self.boxes = [tuple(b) + (0.9,) for b in boxes]

    def detect(self, img):
        return list(self.boxes)


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
    r.geometry("1000x760+40+40")
    r.update()
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


@pytest.fixture
def make_editor(root):
    made = []

    def _make(boxes=(), preset=DEFAULT_CROP_PRESET, upscaler=None):
        rec = SimpleNamespace(saved=[], errors=[], advances=0)
        det = FakeDetector(boxes)
        up = upscaler or StubUpscaler()

        def advance():
            rec.advances += 1

        ed = CropEditor(root, preset_label=preset, ai_enabled=True, model_path=Path("stub.pth"),
                        face_detector_factory=lambda: det,
                        upscaler_factory=lambda p: up,
                        on_saved=lambda p, r: rec.saved.append((p, r)),
                        on_error=lambda p, m: rec.errors.append((p, m)),
                        on_advance=advance)
        ed.pack(fill="both", expand=True)
        root.update()
        made.append(ed)
        return ed, rec

    yield _make
    for ed in made:
        ed.shutdown()
        ed.destroy()
    root.update()


def png(path, size=(1600, 1200)):
    Image.new("RGB", size, (90, 120, 150)).save(path)
    return Path(path)


def key(k, state=0):
    return SimpleNamespace(keysym=k, char=k, state=state)


def loaded(root, ed, path):
    ed.load(path)
    assert pump(root, lambda: ed.rect is not None), ed.status_text


def approx_rect(a, b, tol=0.5):
    return all(abs(getattr(a, f) - getattr(b, f)) <= tol for f in ("x", "y", "w", "h"))


# ---------------------------------------------------------------- loading

def test_load_seeds_frame_on_face(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    assert approx_rect(ed.rect, face_seed(1600, 1200, 1.0, FACE))


def test_load_without_face_uses_largest_fit(root, make_editor, tmp_path):
    ed, _ = make_editor()
    loaded(root, ed, png(tmp_path / "a.png"))
    assert approx_rect(ed.rect, largest_fit(1600, 1200, 1.0))


def test_unreadable_image_reports_and_keys_fall_through(root, make_editor, tmp_path):
    ed, _ = make_editor()
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    ed.load(bad)
    assert pump(root, lambda: ed.status_text.startswith("Cannot open"))
    assert ed.handle_key(key("Right")) is False


# ---------------------------------------------------------------- mouse

def test_drag_moves_image_with_cursor(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    x0, y0 = ed.rect.x, ed.rect.y
    scale = ed.frame_box()[2] / ed.rect.w
    ed.on_press(SimpleNamespace(x=500, y=350))
    ed.on_drag(SimpleNamespace(x=600, y=350))
    ed.on_release(SimpleNamespace(x=600, y=350))
    assert ed.rect.x == pytest.approx(x0 - 100 / scale)
    assert ed.rect.y == pytest.approx(y0)


def test_wheel_zoom_keeps_point_under_cursor(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    fx, fy, fw, _ = ed.frame_box()
    cx, cy = fx + fw * 0.3, fy + fw * 0.6
    s0 = fw / ed.rect.w
    before = (ed.rect.x + (cx - fx) / s0, ed.rect.y + (cy - fy) / s0)
    ed.on_wheel(SimpleNamespace(x=cx, y=cy, delta=120))
    fx, fy, fw, _ = ed.frame_box()
    s1 = fw / ed.rect.w
    after = (ed.rect.x + (cx - fx) / s1, ed.rect.y + (cy - fy) / s1)
    assert s1 > s0
    assert after == pytest.approx(before, abs=1e-6)


# ---------------------------------------------------------------- keys

def test_enter_saves_and_advances(root, make_editor, tmp_path):
    ed, rec = make_editor(boxes=[FACE])
    src = png(tmp_path / "a.png")
    loaded(root, ed, src)
    assert ed.handle_key(key("Return")) is True
    assert rec.advances == 1
    assert pump(root, lambda: rec.saved)
    out = tmp_path / "cropped__1024x1024" / "a.png"
    assert out.exists() and Image.open(out).size == (1024, 1024)
    assert rec.saved[0][0] == src


def test_shift_enter_saves_and_stays(root, make_editor, tmp_path):
    ed, rec = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    assert ed.handle_key(key("Return", 0x1)) is True
    assert pump(root, lambda: rec.saved)
    assert rec.advances == 0


def test_enter_before_load_does_not_save(root, make_editor, tmp_path):
    ed, rec = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    ed.load(png(tmp_path / "b.png"))
    assert ed.handle_key(key("Return")) is True
    assert ed.status_text == "Still loading…"
    assert ed.pending_saves() == 0
    pump(root, lambda: False, timeout=0.5)
    assert rec.saved == []


def test_shift_arrow_nudges_1_and_10_percent(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    x0, w = ed.rect.x, ed.rect.w
    assert ed.handle_key(key("Right", 0x1)) is True
    assert ed.rect.x == pytest.approx(x0 + 0.01 * w)
    assert ed.handle_key(key("Left", 0x5)) is True
    assert ed.rect.x == pytest.approx(x0 + 0.01 * w - 0.10 * w)


def test_plain_arrows_and_digits_fall_through(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    for k in ("Right", "Left", "1", "Delete", "Escape", "c"):
        assert ed.handle_key(key(k)) is False


def test_f_and_r_keys(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    assert ed.handle_key(key("r")) is True
    assert approx_rect(ed.rect, largest_fit(1600, 1200, 1.0))
    assert ed.handle_key(key("f")) is True
    assert approx_rect(ed.rect, face_seed(1600, 1200, 1.0, FACE))


def test_f_without_face_says_so(root, make_editor, tmp_path):
    ed, _ = make_editor()
    loaded(root, ed, png(tmp_path / "a.png"))
    assert ed.handle_key(key("f")) is True
    assert ed.status_text == "No face found"


# ---------------------------------------------------------------- presets / badge

def test_set_preset_keeps_centre_ratio_and_persists(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[FACE])
    loaded(root, ed, png(tmp_path / "a.png"))
    c0 = (ed.rect.x + ed.rect.w / 2, ed.rect.y + ed.rect.h / 2)
    ed.set_preset("1920×1080 — 16:9 Full HD")
    c1 = (ed.rect.x + ed.rect.w / 2, ed.rect.y + ed.rect.h / 2)
    assert c1 == pytest.approx(c0, abs=1.0)
    assert ed.rect.w / ed.rect.h == pytest.approx(1920 / 1080, abs=1e-9)
    loaded(root, ed, png(tmp_path / "b.png"))
    assert ed.out_size == (1920, 1080)


def test_badge_reflects_grade(root, make_editor, tmp_path):
    ed, _ = make_editor()
    loaded(root, ed, png(tmp_path / "small.png", (400, 400)))
    assert ed.current_grade.level == "soft"
    assert ed.badge.cget("fg_color") == "#F44336"


# ---------------------------------------------------------------- performance / shutdown

def test_render_under_30ms_on_4k(root, make_editor, tmp_path):
    ed, _ = make_editor(boxes=[(1800, 800, 2000, 1050)])
    noise = np.random.default_rng(0).integers(0, 255, (2160, 3840, 3), dtype=np.uint8)
    path = tmp_path / "k4.png"
    Image.fromarray(noise).save(path)
    loaded(root, ed, path)
    ed.on_press(SimpleNamespace(x=500, y=350))
    times = []
    for i in range(1, 21):
        ed.on_drag(SimpleNamespace(x=500 + i * 3, y=350 + i))
        times.append(ed.last_render_ms)
    ed.on_release(SimpleNamespace(x=560, y=370))
    assert max(times) < 30, times


def test_shutdown_waits_for_pending_saves(root, make_editor, tmp_path):
    ed, rec = make_editor(upscaler=StubUpscaler(delay=0.3))
    loaded(root, ed, png(tmp_path / "s.png", (600, 600)))        # 600 -> 1024 needs AI
    ed.handle_key(key("Return", 0x1))
    ed.handle_key(key("Return", 0x1))
    assert ed.pending_saves() == 2
    ed.shutdown()
    assert ed.pending_saves() == 0 and len(rec.saved) == 2
    assert all(r.method == "AI stub" for _, r in rec.saved)


# ---------------------------------------------------------------- review fixes

@pytest.mark.parametrize("size", [(2432, 1664), (1792, 2304), (6000, 4000)])
def test_large_non_square_images_render(root, make_editor, tmp_path, size):
    ed, _ = make_editor()
    loaded(root, ed, png(tmp_path / "big.png", size))
    ed.render(sharp=True)                    # must not raise
    ed.on_wheel(SimpleNamespace(x=300, y=300, delta=-120 * 5))   # zoom out to the edge
    ed.render(sharp=True)
    assert ed.canvas.itemcget(ed._img_item, "state") == "normal"


def test_destroying_host_with_pending_saves_does_not_raise(root, tmp_path):
    host = ctk.CTkToplevel(root)
    label = ctk.CTkLabel(host, text="")      # created first, so destroyed first
    label.pack()
    up = StubUpscaler(delay=0.3)
    ed = CropEditor(host, preset_label=DEFAULT_CROP_PRESET, ai_enabled=True,
                    model_path=Path("stub.pth"), face_detector_factory=lambda: FakeDetector([]),
                    upscaler_factory=lambda p: up,
                    on_saved=lambda p, r: label.configure(text=r.path.name))
    ed.pack(fill="both", expand=True)
    loaded(root, ed, png(tmp_path / "s.png", (600, 600)))
    ed.handle_key(key("Return", 0x1))
    ed.handle_key(key("Return", 0x1))
    host.destroy()                           # must not raise
    root.update()
    assert len(list((tmp_path / "cropped__1024x1024").glob("s*.png"))) == 2
