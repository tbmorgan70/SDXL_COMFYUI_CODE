import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from sorters.crop_tool import (  # noqa: E402
    CROP_SIZE_PRESETS,
    DEFAULT_CROP_PRESET,
    FACE_CENTER_Y,
    MIN_CROP_SIDE,
    CropRect,
    clamp,
    face_seed,
    grade,
    largest_fit,
    pan,
    zoom_at,
)


# ---------------------------------------------------------------- geometry

def test_largest_fit_portrait_ar_on_landscape_image():
    r = largest_fit(1600, 1200, 832 / 1216)
    assert r.h == 1200 and r.y == 0
    assert abs(r.w - 1200 * 832 / 1216) < 1e-6
    assert abs(r.x - (1600 - r.w) / 2) < 1e-6


def test_largest_fit_exact_ratio_for_every_preset():
    for size in (v for v in CROP_SIZE_PRESETS.values() if isinstance(v, tuple)):
        r = largest_fit(3000, 2000, size[0] / size[1])
        assert abs(r.w / r.h - size[0] / size[1]) < 1e-9


@pytest.mark.parametrize("x,y", [(-500, 300), (300, -500), (5000, 300), (300, 5000)])
def test_clamp_keeps_rect_inside_each_edge(x, y):
    r = clamp(CropRect(x, y, 400, 400), 1600, 1200, 1.0)
    assert r.x >= 0 and r.y >= 0
    assert r.x + r.w <= 1600 and r.y + r.h <= 1200


def test_clamp_enforces_minimum_short_side():
    r = clamp(CropRect(100, 100, 10, 10), 1600, 1200, 1.0)
    assert min(r.w, r.h) == MIN_CROP_SIDE


def test_clamp_caps_at_largest_fit_keeping_position():
    big = largest_fit(1600, 1200, 1.0)
    r = clamp(CropRect(0, 0, 9000, 9000), 1600, 1200, 1.0)
    assert (r.w, r.h) == (big.w, big.h)
    assert r.x == 1600 - big.w and r.y == 0      # pushed inside, not re-centred


def test_clamp_tiny_image_falls_back_to_largest_fit():
    big = largest_fit(50, 40, 1.0)
    r = clamp(CropRect(0, 0, 64, 64), 50, 40, 1.0)
    assert (r.w, r.h) == (big.w, big.h)
    assert 0 <= r.x <= 50 - r.w and r.y == 0


def test_zoom_at_keeps_anchor_fixed():
    r0 = CropRect(400, 300, 400, 400)
    r1 = zoom_at(r0, 0.5, 500, 400, 1600, 1200, 1.0)
    assert abs((500 - r1.x) / r1.w - (500 - r0.x) / r0.w) < 1e-9
    assert abs((400 - r1.y) / r1.h - (400 - r0.y) / r0.h) < 1e-9
    assert abs(r1.w - 200) < 1e-9


def test_pan_stops_at_edges():
    r = pan(CropRect(100, 100, 400, 400), -1000, 0, 1600, 1200, 1.0)
    assert r.x == 0 and r.y == 100


def test_face_seed_places_face_centre_at_42_percent():
    r = face_seed(2000, 2000, 1.0, (700, 900, 800, 1000))
    assert abs(r.h - 220) < 1e-9
    assert abs((950 - r.y) / r.h - FACE_CENTER_Y) < 1e-9
    assert abs((750 - r.x) / r.w - 0.5) < 1e-9


def test_face_seed_corner_face_stays_in_bounds():
    r = face_seed(1600, 1200, 832 / 1216, (0, 0, 120, 140))
    assert r.x >= 0 and r.y >= 0
    assert r.x + r.w <= 1600 and r.y + r.h <= 1200


def test_face_seed_huge_face_shrinks_to_largest_fit():
    assert face_seed(1000, 800, 1.0, (0, 0, 1000, 800)) == largest_fit(1000, 800, 1.0)


# ---------------------------------------------------------------- grading

@pytest.mark.parametrize("w,level,ai,label", [
    (1024, "native", True, "Native pixels"),
    (1023.9, "upscale", True, "1.0x — AI upscale"),
    (512, "upscale", False, "2.0x — resize"),
    (500, "soft", True, "2.0x — will be soft, widen the frame"),
])
def test_grade_thresholds_and_labels(w, level, ai, label):
    g = grade(CropRect(0, 0, w, w), 1024, 1024, ai)
    assert g.level == level and g.label == label


# ---------------------------------------------------------------- presets

def test_presets_have_sdxl_sizes_custom_and_no_duplicate_sizes():
    sizes = [v for v in CROP_SIZE_PRESETS.values() if isinstance(v, tuple)]
    assert (832, 1216) in sizes and (1536, 640) in sizes
    assert len(sizes) == len(set(sizes))
    assert CROP_SIZE_PRESETS["Custom..."] == "custom"
    assert DEFAULT_CROP_PRESET in CROP_SIZE_PRESETS
