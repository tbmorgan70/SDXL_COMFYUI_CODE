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


# ================================================================ saving

from pathlib import Path  # noqa: E402

from PIL import Image, ImageCms  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

from sorters.crop_tool import AI_REGION_MARGIN, save_crop  # noqa: E402


def make_png(path, size, chunks=None, mode="RGB", color=(128, 128, 128)):
    img = Image.new(mode, size, color if mode != "I;16" else 1000)
    info = None
    if chunks:
        info = PngInfo()
        for k, v in chunks.items():
            info.add_text(k, v)
    img.save(path, "PNG", pnginfo=info)
    return Path(path)


def make_split(path, size, fmt="PNG", **save_kw):
    """Left half red, right half blue."""
    w, h = size
    img = Image.new("RGB", size, (0, 0, 255))
    img.paste((255, 0, 0), (0, 0, w // 2, h))
    img.save(path, fmt, **save_kw)
    return Path(path)


class StubUpscaler:
    name = "stub"

    def __init__(self, scale=2, fail=None):
        self.scale, self.fail, self.calls = scale, fail, []

    def upscale(self, img):
        self.calls.append(img.size)
        if self.fail:
            raise RuntimeError(self.fail)
        return img.resize((img.width * self.scale, img.height * self.scale), Image.NEAREST)


def test_png_exact_size_and_text_chunks(tmp_path):
    src = make_png(tmp_path / "a.png", (1600, 1200),
                   {"parameters": "p", "prompt": "{}", "workflow": "{}"})
    res = save_crop(src, CropRect(100, 0, 821, 1200), 832, 1216)
    out = Image.open(res.path)
    assert out.size == (832, 1216) and res.path.parent.name == "cropped__832x1216"
    assert {k: out.info[k] for k in ("parameters", "prompt", "workflow")} == \
        {"parameters": "p", "prompt": "{}", "workflow": "{}"}


def test_jpeg_keeps_format_and_exif(tmp_path):
    exif = Image.Exif()
    exif[270] = "hello"
    src = make_split(tmp_path / "j.jpg", (800, 600), "JPEG", exif=exif.tobytes())
    res = save_crop(src, CropRect(0, 0, 600, 600), 512, 512)
    assert res.path.suffix == ".jpg"
    assert Image.open(res.path).getexif()[270] == "hello"


def test_icc_profile_preserved(tmp_path):
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    src = tmp_path / "icc.png"
    Image.new("RGB", (600, 600), (10, 20, 30)).save(src, "PNG", icc_profile=icc)
    res = save_crop(src, CropRect(0, 0, 600, 600), 512, 512)
    assert Image.open(res.path).info["icc_profile"] == icc


def test_exif_rotated_jpeg_crops_what_is_shown(tmp_path):
    exif = Image.Exif()
    exif[274] = 6                       # displays rotated 90° clockwise: red on top
    src = make_split(tmp_path / "rot.jpg", (400, 200), "JPEG", exif=exif.tobytes(), quality=95)
    res = save_crop(src, CropRect(0, 0, 200, 200), 128, 128)   # top half of the 200x400 view
    out = Image.open(res.path)
    assert out.getexif().get(274) == 1
    r, g, b = out.convert("RGB").getpixel((64, 64))
    assert r > 200 and b < 60


def test_rgba_and_16bit_sources_save(tmp_path):
    rgba = Image.new("RGBA", (300, 300), (255, 0, 0, 255))
    rgba.paste((0, 0, 0, 0), (0, 0, 120, 120))
    rgba.save(tmp_path / "alpha.png")
    out = Image.open(save_crop(tmp_path / "alpha.png", CropRect(0, 0, 300, 300), 300, 300).path)
    assert out.mode == "RGBA" and out.getpixel((10, 10))[3] == 0

    deep = make_png(tmp_path / "deep.png", (300, 300), mode="I;16")
    assert Image.open(save_crop(deep, CropRect(0, 0, 300, 300), 256, 256).path).mode == "RGB"


def test_gif_source_written_as_png(tmp_path):
    src = tmp_path / "g.gif"
    Image.new("P", (300, 300), 3).save(src)
    assert save_crop(src, CropRect(0, 0, 300, 300), 256, 256).path.suffix == ".png"


def test_name_clash_appends_2(tmp_path):
    src = make_png(tmp_path / "c.png", (600, 600))
    save_crop(src, CropRect(0, 0, 600, 600), 512, 512)
    second = save_crop(src, CropRect(0, 0, 600, 600), 512, 512)
    assert second.path.stem.endswith("_2")


def test_manifest_header_once_one_line_per_crop_utf8(tmp_path):
    src = make_png(tmp_path / "Feelin' Lucky ✨.png", (1200, 1200))
    save_crop(src, CropRect(0, 0, 1200, 1200), 1024, 1024)
    save_crop(src, CropRect(0, 0, 1200, 1200), 1024, 1024)
    text = (tmp_path / "cropped__1024x1024" / "_crop_info.txt").read_text(encoding="utf-8")
    assert text.count("=== CROP INFO ===") == 1
    assert text.count("Feelin' Lucky ✨.png |") == 2


def test_native_when_factor_le_1_skips_upscaler(tmp_path):
    up = StubUpscaler()
    src = make_png(tmp_path / "n.png", (2048, 2048))
    res = save_crop(src, CropRect(0, 0, 2048, 2048), 1024, 1024, up)
    assert res.method == "native" and up.calls == []


def test_resize_without_upscaler(tmp_path):
    src = make_png(tmp_path / "s.png", (600, 600))
    res = save_crop(src, CropRect(0, 0, 600, 600), 1024, 1024)
    assert res.method == "resize" and Image.open(res.path).size == (1024, 1024)


def test_ai_path_upscales_region_and_lands_exact(tmp_path):
    src = make_split(tmp_path / "ai.png", (800, 400))
    up = StubUpscaler()
    res = save_crop(src, CropRect(300, 100, 200, 200), 1024, 1024, up)
    assert res.method == "AI stub" and Image.open(res.path).size == (1024, 1024)
    assert up.calls == [(200 + 2 * AI_REGION_MARGIN, 200 + 2 * AI_REGION_MARGIN)]
    out = Image.open(res.path).convert("RGB")
    assert out.getpixel((100, 512)) == (255, 0, 0)
    assert out.getpixel((924, 512)) == (0, 0, 255)


def test_ai_failure_falls_back_to_resize(tmp_path):
    src = make_png(tmp_path / "f.png", (600, 600))
    res = save_crop(src, CropRect(0, 0, 300, 300), 1024, 1024, StubUpscaler(fail="CUDA OOM"))
    assert res.method == "resize (AI failed: CUDA OOM)"
    assert Image.open(res.path).size == (1024, 1024)


def _a_real_comfyui_png():
    """Any ComfyUI output PNG carrying both the workflow and Image Saver's
    A1111 `parameters` text (so the original is known to have a prompt)."""
    root = Path(r"D:\ComfyUI_windows_portable\ComfyUI\output")
    if not root.is_dir():
        return None
    for path in sorted(root.rglob("*.png"))[:3000]:
        try:
            with Image.open(path) as im:
                if "prompt" in im.info and "parameters" in im.info:
                    return path
        except OSError:
            continue
    return None


def test_real_comfyui_png_metadata_roundtrip(tmp_path):
    src = _a_real_comfyui_png()
    if src is None:
        pytest.skip("user's ComfyUI output not available")
    from sorters.civitai_prep import CivitaiPrep
    w, h = Image.open(src).size
    res = save_crop(src, largest_fit(w, h, 832 / 1216), 832, 1216, out_dir=tmp_path)
    prep = CivitaiPrep(None, r"D:\ComfyUI_windows_portable\ComfyUI\models", api_lookup=False)
    a = prep.analyze_image(str(src), compute_hashes=False)
    b = prep.analyze_image(str(res.path), compute_hashes=False)
    assert a["prompts"]["positive"] and a["prompts"]["positive"] == b["prompts"]["positive"]
    assert (a["checkpoint"] or {}).get("name") == (b["checkpoint"] or {}).get("name")
    assert [x["name"] for x in a["loras"]] == [x["name"] for x in b["loras"]]


# ================================================================ review fixes

AWKWARD_SIZES = [(1344, 768), (1536, 640), (3000, 4000), (1360, 768), (768, 1360),
                 (1328, 1944), (2432, 1664), (6000, 4000)]


@pytest.mark.parametrize("size", AWKWARD_SIZES)
def test_largest_fit_stays_inside_image_for_every_preset(size):
    w, h = size
    for preset in (v for v in CROP_SIZE_PRESETS.values() if isinstance(v, tuple)):
        ar = preset[0] / preset[1]
        for r in (largest_fit(w, h, ar), clamp(largest_fit(w, h, ar), w, h, ar),
                  zoom_at(largest_fit(w, h, ar), 10.0, w / 2, h / 2, w, h, ar)):
            assert r.x >= 0 and r.y >= 0, (size, preset, r)
            assert r.x + r.w <= w and r.y + r.h <= h, (size, preset, r)


@pytest.mark.parametrize("size,out", [((1344, 768), (1080, 1350)), ((1536, 640), (1920, 1080)),
                                      ((3000, 4000), (768, 1344))])
def test_save_largest_frame_on_awkward_sizes(tmp_path, size, out):
    src = make_png(tmp_path / "w.png", size)
    rect = clamp(largest_fit(*size, out[0] / out[1]), *size, out[0] / out[1])
    res = save_crop(src, rect, *out)
    assert Image.open(res.path).size == out


def test_mpo_phone_jpeg_saved_as_jpeg(tmp_path):
    src = tmp_path / "phone.jpg"
    a = Image.new("RGB", (800, 600), (200, 50, 50))
    a.save(src, "MPO", save_all=True, append_images=[Image.new("RGB", (200, 150))])
    assert Image.open(src).format == "MPO"
    res = save_crop(src, CropRect(0, 0, 600, 600), 512, 512)
    assert res.path.suffix == ".jpg" and Image.open(res.path).format == "JPEG"


# ================================================================ 3.6.1: more portraits, Tab cycling

from sorters.crop_tool import flipped, orientation, step_preset  # noqa: E402

NEW_PORTRAITS = [(1152, 1536), (1024, 1536), (1080, 1512), (1100, 1400), (1086, 1536),
                 (1344, 1728), (1248, 1824), (1152, 2016), (960, 2304)]


def sized():
    return {k: v for k, v in CROP_SIZE_PRESETS.items() if isinstance(v, tuple)}


def test_new_portrait_presets_present():
    sizes = list(sized().values())
    for size in NEW_PORTRAITS:
        assert size in sizes, size


def test_dropdown_grouped_square_portrait_landscape():
    kinds = [orientation(v) for v in sized().values()]
    first_portrait, first_landscape = kinds.index("portrait"), kinds.index("landscape")
    assert set(kinds[:first_portrait]) == {"square"}
    assert set(kinds[first_portrait:first_landscape]) == {"portrait"}
    assert set(kinds[first_landscape:]) == {"landscape"}
    portraits = [w / h for w, h in sized().values() if h > w]
    assert portraits == sorted(portraits)                     # tallest first
    assert list(CROP_SIZE_PRESETS)[-1] == "Custom..."


def label_of(size):
    return next(k for k, v in sized().items() if v == size)


def test_tab_steps_portraits_tallest_to_squarest_then_squares_and_wraps():
    presets = sized()
    first = next(k for k, v in presets.items() if orientation(v) == "portrait")
    order, label = [], first
    for _ in range(40):
        order.append(presets[label])
        label = step_preset(presets, label, +1)
        if label == first:
            break
    portraits = [s for s in order if s[1] > s[0]]
    squares = [s for s in order if s[0] == s[1]]
    assert order[:len(portraits)] == portraits and order[len(portraits):] == squares
    assert all(orientation(s) != "landscape" for s in order)
    assert len(portraits) == sum(1 for v in presets.values() if v[1] > v[0])


def test_shift_tab_goes_back():
    presets = sized()
    start = label_of((832, 1216))
    assert step_preset(presets, step_preset(presets, start, +1), -1) == start


def test_tab_from_square_enters_portraits_and_landscape_stays_landscape():
    presets = sized()
    assert orientation(presets[step_preset(presets, label_of((1024, 1024)), +1)]) != "landscape"
    nxt = step_preset(presets, label_of((1920, 1080)), +1)
    assert orientation(presets[nxt]) in ("landscape", "square")


def test_flipped_swaps_sides():
    assert flipped((832, 1216)) == (1216, 832)
