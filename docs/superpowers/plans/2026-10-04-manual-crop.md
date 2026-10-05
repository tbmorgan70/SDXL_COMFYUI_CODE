# Manual Crop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A fixed-frame crop editor (image floats under an exact-size preset frame) reachable from Triage with the C key and from a new "Manual Crop" mode, saving metadata-preserving copies with a native/upscale/soft resolution badge.

**Architecture:** `sorter/sorters/crop_tool.py` holds all UI-free logic (presets, crop-rect geometry, grading, saving). `sorter/crop_editor.py` is one `CropEditor` CTkFrame (toolbar + Tk Canvas viewport renderer + loader/save worker threads). `sorter/gui.py` embeds it in `TriageWindow` and adds the menu mode.

**Tech Stack:** Python 3.11.9, Pillow, customtkinter/Tk, numpy; existing `FaceDetector` (image_extractor) and `Upscaler` (upscaler); pytest.

**Spec:** `docs/superpowers/specs/2026-10-04-manual-crop-design.md`

## Global Constraints

- Run Python as `python` (3.11.9). Never `py -3` (3.13, missing deps).
- All work and commits happen in the worktree `.claude/worktrees/wizardly-feistel-efc537`; run commands from its root. Do not push.
- Tests live in `tests/`; each test file starts with `sys.path.insert(0, <repo>/sorter)` then imports `sorters.crop_tool` / `crop_editor` / `gui`.
- Tk/CTk image objects are created on the main thread only; worker threads hand PIL images over a `queue.Queue` drained by an `after()` poller.
- No new dependencies.
- Source images are never modified; outputs go to `<source folder>/cropped__<W>x<H>/`.
- Badge labels exactly: `Native pixels`, `{f:.1f}x — AI upscale`, `{f:.1f}x — resize`, `{f:.1f}x — will be soft, widen the frame`.
- Thresholds: native when factor ≤ 1.0; amber when 1.0 < factor ≤ 2.0; red when factor > 2.0. Red warns only, never blocks.
- Badge colours reuse the Triage palette: native `#4CAF50`, upscale `#FF9800`, soft `#F44336`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **EXIF-rotated JPEGs** (phone photos): what you frame must be what gets saved. Both proxy and save use `ImageOps.exif_transpose`, and the saved EXIF Orientation is reset to 1 (Task 2 test).
2. **Unusual pixel modes** (RGBA, LA, P with transparency, 16-bit `I;16` PNGs): saving must not crash and must keep alpha (Task 2 test).
3. **Enter pressed before the next image has loaded**: must not save the previous image's frame onto the new image. Ignore it and show `Still loading…` (Task 3 test).
4. **Non-ASCII filenames** (`Feelin' Lucky`, `✨`): the manifest is written as UTF-8 and the output name keeps the stem (Task 2 test).
5. **Images smaller than the 64 px minimum**: geometry falls back to the largest fit without errors (Task 1 test).

---

### Task 1: Crop geometry, presets and grading

**Files:**
- Create: `sorter/sorters/crop_tool.py`
- Test: `tests/test_crop_tool.py`

**Interfaces:**
- Consumes: `CROP_PRESETS` from `sorters.image_extractor`.
- Produces:
  - `MIN_CROP_SIDE = 64`, `FACE_FRAMING = 2.2`, `FACE_CENTER_Y = 0.42`, `SOFT_ABOVE = 2.0`, `AI_REGION_MARGIN = 24`
  - `GRADE_COLORS = {"native": "#4CAF50", "upscale": "#FF9800", "soft": "#F44336"}`
  - `SDXL_SIZE_PRESETS: dict[str, tuple[int, int]]`: labels like `"832×1216 — SDXL portrait"`, sizes 896×1152, 1152×896, 832×1216, 1216×832, 768×1344, 1344×768, 640×1536, 1536×640.
  - `CROP_SIZE_PRESETS: dict[str, tuple[int, int] | str]`: Extract's sized entries in order (skip `None` and `"custom"`), then the SDXL entries whose size is not already present, then `"Custom...": "custom"`.
  - `DEFAULT_CROP_PRESET = "1024×1024 — SDXL native"`
  - `@dataclass(frozen=True) class CropRect: x: float; y: float; w: float; h: float`
  - `largest_fit(src_w: int, src_h: int, ar: float) -> CropRect`: centred.
  - `clamp(rect: CropRect, src_w: int, src_h: int, ar: float) -> CropRect`: keeps the rect centre, forces `h = w / ar`, caps size at the largest fit, enforces short side ≥ `MIN_CROP_SIDE` (or the largest fit if the image is smaller), then shifts the rect inside the image.
  - `pan(rect, dx: float, dy: float, src_w, src_h, ar) -> CropRect`
  - `zoom_at(rect, factor: float, ax: float, ay: float, src_w, src_h, ar) -> CropRect`: factor > 1 grows the frame (zoom out), factor < 1 shrinks it (zoom in). The source point `(ax, ay)` keeps its relative position in the frame: `x' = ax - (ax - x) * factor`. Then clamp.
  - `face_seed(src_w, src_h, ar, face_box: tuple[float, float, float, float], framing: float = FACE_FRAMING) -> CropRect`: `h = face_h * framing`, `w = h * ar`, horizontally centred on the face, face-box centre at `FACE_CENTER_Y` of the frame height from its top. Then clamp.
  - `@dataclass(frozen=True) class Grade: level: str; factor: float; label: str` (level is `"native"`, `"upscale"` or `"soft"`)
  - `grade(rect: CropRect, out_w: int, out_h: int, ai_enabled: bool) -> Grade`, with `factor = out_w / rect.w`.

- [ ] **Step 1: Write the failing tests** in `tests/test_crop_tool.py`:

```python
def test_largest_fit_portrait_ar_on_landscape_image():
    r = largest_fit(1600, 1200, 832 / 1216)
    assert r.h == 1200 and r.y == 0
    assert abs(r.w - 1200 * 832 / 1216) < 1e-6 and abs(r.x - (1600 - r.w) / 2) < 1e-6

def test_largest_fit_exact_ratio_for_every_preset():
    for size in (v for v in CROP_SIZE_PRESETS.values() if isinstance(v, tuple)):
        r = largest_fit(3000, 2000, size[0] / size[1])
        assert abs(r.w / r.h - size[0] / size[1]) < 1e-9

@pytest.mark.parametrize("x,y", [(-500, 300), (300, -500), (5000, 300), (300, 5000)])
def test_clamp_keeps_rect_inside_each_edge(x, y):
    r = clamp(CropRect(x, y, 400, 400), 1600, 1200, 1.0)
    assert r.x >= 0 and r.y >= 0 and r.x + r.w <= 1600 and r.y + r.h <= 1200

def test_clamp_enforces_minimum_short_side():
    r = clamp(CropRect(100, 100, 10, 10), 1600, 1200, 1.0)
    assert min(r.w, r.h) == MIN_CROP_SIDE

def test_clamp_caps_at_largest_fit():
    assert clamp(CropRect(0, 0, 9000, 9000), 1600, 1200, 1.0) == largest_fit(1600, 1200, 1.0)

def test_clamp_tiny_image_falls_back_to_largest_fit():          # Review Focus 5
    assert clamp(CropRect(0, 0, 64, 64), 50, 40, 1.0) == largest_fit(50, 40, 1.0)

def test_zoom_at_keeps_anchor_fixed():
    r0 = CropRect(400, 300, 400, 400)
    r1 = zoom_at(r0, 0.5, 500, 400, 1600, 1200, 1.0)
    assert abs((500 - r1.x) / r1.w - (500 - r0.x) / r0.w) < 1e-9
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

def test_face_seed_huge_face_shrinks_to_largest_fit():
    assert face_seed(1000, 800, 1.0, (0, 0, 1000, 800)) == largest_fit(1000, 800, 1.0)

@pytest.mark.parametrize("w,level,ai,label", [
    (1024, "native", True, "Native pixels"),
    (1023.9, "upscale", True, "1.0x — AI upscale"),
    (512, "upscale", False, "2.0x — resize"),
    (500, "soft", True, "2.0x — will be soft, widen the frame"),
])
def test_grade_thresholds_and_labels(w, level, ai, label):
    g = grade(CropRect(0, 0, w, w), 1024, 1024, ai)
    assert g.level == level and g.label == label

def test_presets_have_sdxl_sizes_custom_and_no_duplicate_sizes():
    sizes = [v for v in CROP_SIZE_PRESETS.values() if isinstance(v, tuple)]
    assert (832, 1216) in sizes and (1536, 640) in sizes
    assert len(sizes) == len(set(sizes))
    assert CROP_SIZE_PRESETS["Custom..."] == "custom"
    assert DEFAULT_CROP_PRESET in CROP_SIZE_PRESETS
```

(500 px gives factor 2.048. Its label rounds to `2.0x`, but the level is `soft` because 2.048 > 2.0.)

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_crop_tool.py -v`
Expected: collection error, `ModuleNotFoundError: No module named 'sorters.crop_tool'`

- [ ] **Step 3: Implement** the constants, dataclasses and functions listed in the Interfaces block, in `sorter/sorters/crop_tool.py`. All geometry stays in float source pixels. `clamp` is the single place that enforces the invariants; `pan`, `zoom_at` and `face_seed` build a candidate rect and return `clamp(...)` of it.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_crop_tool.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sorter/sorters/crop_tool.py tests/test_crop_tool.py
git commit -m "Crop tool: presets, crop-rect geometry and resolution grading"
```

---

### Task 2: Saving crops with metadata

**Files:**
- Modify: `sorter/sorters/crop_tool.py`
- Test: `tests/test_crop_tool.py` (append)

**Interfaces:**
- Consumes: `CropRect` and `AI_REGION_MARGIN` from Task 1. The upscaler duck type is any object with `.name: str` and `.upscale(img) -> Image`; the real `sorters.upscaler.Upscaler` satisfies it.
- Produces:
  - `output_dir_for(source_dir: Path, out_w: int, out_h: int) -> Path` returns `source_dir / f"cropped__{out_w}x{out_h}"`.
  - `open_oriented(path: Path) -> tuple[Image.Image, Image.Image]` returns `(original_as_opened, exif_transposed)`. The original keeps `.info` and `.format` for metadata.
  - `@dataclass(frozen=True) class SaveResult: path: Path; factor: float; method: str`. `method` is `"native"`, `"resize"`, `f"AI {upscaler.name}"`, or `f"resize (AI failed: {err})"`.
  - `save_crop(src_path: Path, rect: CropRect, out_w: int, out_h: int, upscaler=None, out_dir: Path | None = None) -> SaveResult`. `rect` is in oriented (transposed) source pixels. `out_dir` defaults to `output_dir_for(src_path.parent, out_w, out_h)`.
  - `save_with_metadata(img: Image.Image, src_img: Image.Image, dest_stem: Path) -> Path`. It appends the right suffix and returns the written path.
- Format rules:
  - PNG, GIF and BMP sources are written as `.png`, with every `str` value in `src_img.info` as a text chunk.
  - JPEG becomes `.jpg` at `quality=95, subsampling=0`.
  - WEBP becomes `.webp` with `lossless=True`.
  - Every format also passes `icc_profile` when present, and `exif` with Orientation (tag 274) set to 1 when present.
  - Mode conversion: JPEG targets `RGB`, and `I;16`/`I` images are converted to `RGB` for every target. Anything else keeps its mode, so alpha survives.
- Name clashes: `<stem>.<ext>`, then `<stem>_2.<ext>`, `<stem>_3.<ext>`, and so on.
- Manifest `out_dir/_crop_info.txt`, written with UTF-8 encoding. The header is written only when the file doesn't exist:

```
=== CROP INFO ===
Output size : {out_w}x{out_h}
Created     : {YYYY-mm-dd HH:MM:SS}

source | crop rect (x,y,w,h) | factor | method | output
```

  After the header, one line per crop: `f"{src.name} | {x},{y},{w},{h} | {factor:.2f}x | {method} | {dest.name}"`, with the rect values rounded to int.

- [ ] **Step 1: Write the failing tests** (append). Helper `make_png(path, size, chunks=None, mode="RGB")` writes a synthetic image; `StubUpscaler(scale=2, fail=None)` records the size of each image passed to `upscale`, returns a NEAREST resize ×2, and raises `RuntimeError(fail)` when `fail` is set.

```python
def test_png_exact_size_and_text_chunks(tmp_path):
    src = make_png(tmp_path / "a.png", (1600, 1200),
                   {"parameters": "p", "prompt": "{}", "workflow": "{}"})
    res = save_crop(src, CropRect(100, 0, 821, 1200), 832, 1216)
    out = Image.open(res.path)
    assert out.size == (832, 1216) and res.path.parent.name == "cropped__832x1216"
    assert {k: out.info[k] for k in ("parameters", "prompt", "workflow")} == \
           {"parameters": "p", "prompt": "{}", "workflow": "{}"}

def test_jpeg_keeps_format_and_exif(tmp_path): ...
    # EXIF ImageDescription "hello" in -> out suffix ".jpg", out.getexif()[270] == "hello"

def test_icc_profile_preserved(tmp_path): ...
    # src saved with icc_profile=b"..." (ImageCms sRGB) -> out.info["icc_profile"] equals it

def test_exif_rotated_jpeg_crops_what_is_shown(tmp_path):        # Review Focus 1
    # 400x200 JPEG, left half red, right half blue, EXIF Orientation 6 (displays 200x400, red on top)
    # crop the top half of the *displayed* image -> output is red; out.getexif().get(274) == 1

def test_rgba_and_16bit_sources_save(tmp_path):                  # Review Focus 2
    # RGBA PNG with a transparent pixel -> output mode "RGBA" and that pixel's alpha == 0
    # I;16 PNG -> saves without error, mode "RGB"

def test_gif_source_written_as_png(tmp_path): ...                 # suffix ".png"

def test_name_clash_appends_2(tmp_path):
    # save the same src+rect twice -> second path stem endswith "_2"

def test_manifest_header_once_one_line_per_crop_utf8(tmp_path):   # Review Focus 4
    src = make_png(tmp_path / "Feelin' Lucky ✨.png", (1200, 1200))
    save_crop(src, CropRect(0, 0, 1200, 1200), 1024, 1024)
    save_crop(src, CropRect(0, 0, 1200, 1200), 1024, 1024)
    text = (tmp_path / "cropped__1024x1024" / "_crop_info.txt").read_text(encoding="utf-8")
    assert text.count("=== CROP INFO ===") == 1
    assert text.count("Feelin' Lucky ✨.png |") == 2

def test_native_when_factor_le_1_skips_upscaler(tmp_path):
    up = StubUpscaler()
    res = save_crop(make_png(tmp_path / "n.png", (2048, 2048)), CropRect(0, 0, 2048, 2048), 1024, 1024, up)
    assert res.method == "native" and up.calls == []

def test_ai_path_upscales_region_and_lands_exact(tmp_path):
    # 800x400 image: left half red, right half blue. rect = CropRect(300, 100, 200, 200) -> 1024x1024 (factor 5.12)
    up = StubUpscaler()
    res = save_crop(src, rect, 1024, 1024, up)
    assert res.method == "AI stub" and Image.open(res.path).size == (1024, 1024)
    assert up.calls == [(200 + 2 * AI_REGION_MARGIN, 200 + 2 * AI_REGION_MARGIN)]
    out = Image.open(res.path).convert("RGB")
    assert out.getpixel((100, 512)) == (255, 0, 0) and out.getpixel((924, 512)) == (0, 0, 255)

def test_ai_failure_falls_back_to_resize(tmp_path):
    res = save_crop(src, small_rect, 1024, 1024, StubUpscaler(fail="CUDA OOM"))
    assert res.method == "resize (AI failed: CUDA OOM)"

def test_real_comfyui_png_metadata_roundtrip(tmp_path):
    src = Path(r"D:\ComfyUI_windows_portable\ComfyUI\output\New Vintage Girls_Posted\unposted\NEW_TEST__00160_.png")
    if not src.exists():
        pytest.skip("user's ComfyUI output not available")
    # crop with largest_fit(...) to 832x1216; CivitaiPrep(None, models_dir, api_lookup=False)
    # .analyze_image(..., compute_hashes=False) on original and crop:
    # prompts["positive"], checkpoint["name"], [l["name"] for l in loras] are equal
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_crop_tool.py -v`
Expected: the new tests FAIL with `ImportError: cannot import name 'save_crop'`; the Task 1 tests still PASS.

- [ ] **Step 3: Implement** `output_dir_for`, `open_oriented`, `SaveResult`, `save_with_metadata` and `save_crop` in `crop_tool.py`. The AI path mirrors `ImageExtractorSorter._face_crop_ai`:

```python
# region = rect grown by AI_REGION_MARGIN, clamped to the image (ints)
up = upscaler.upscale(oriented.crop(region)); s = up.width / region_width
box = ((rect.x - rx0) * s, (rect.y - ry0) * s, (rect.x - rx0 + rect.w) * s, (rect.y - ry0 + rect.h) * s)
result = up.crop(rounded box).resize((out_w, out_h), Image.LANCZOS)
```

Use `rect.w * s < out_w` only to decide the log wording. The final step is always the exact Lanczos resize.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_crop_tool.py -v`
Expected: all PASS (the real-file test passes on the user's machine; elsewhere it SKIPs).

- [ ] **Step 5: Commit**

```bash
git add sorter/sorters/crop_tool.py tests/test_crop_tool.py
git commit -m "Crop tool: save crops with metadata, AI region upscale, manifest"
```

---

### Task 3: CropEditor widget

**Files:**
- Create: `sorter/crop_editor.py`
- Test: `tests/test_crop_editor.py`

**Interfaces:**
- Consumes:
  - From Tasks 1 and 2: `CROP_SIZE_PRESETS`, `CropRect`, `largest_fit`, `clamp`, `pan`, `zoom_at`, `face_seed`, `grade`, `GRADE_COLORS`, `open_oriented`, `save_crop`, `SaveResult`.
  - From existing modules: `sorters.image_extractor.FaceDetector`, `sorters.upscaler.Upscaler`, `list_upscale_models`, `DEFAULT_MODELS_DIR`.
- Produces: `class CropEditor(ctk.CTkFrame)` with:

```python
def __init__(self, master, *, preset_label: str, ai_enabled: bool, model_path: Path | None,
             face_detector_factory: Callable[[], object] | None = None,   # default: lambda: FaceDetector(log=log)
             upscaler_factory: Callable[[Path], object] | None = None,   # default: lambda p: Upscaler(p, log=log)
             on_saved: Callable[[Path, SaveResult], None] | None = None, # (source path, result)
             on_error: Callable[[Path, str], None] | None = None,
             on_advance: Callable[[], None] | None = None,               # Enter asks the host to go to the next image
             log: Callable[[str], None] | None = None)
PROXY_MAX = 2048
def load(self, path: Path, prefetch: Path | None = None) -> None
def set_preset(self, label: str) -> None          # keeps the frame centre, re-fits to the new aspect ratio
def save(self, advance: bool) -> bool             # False (and status "Still loading…") when no rect is ready
def handle_key(self, event) -> bool               # True = consumed
def on_press(self, event) -> None; def on_drag(self, event) -> None
def on_release(self, event) -> None; def on_wheel(self, event) -> None
def pending_saves(self) -> int
def shutdown(self) -> None                        # stop workers after the save queue drains
# Read-only state used by the host and the tests:
path: Path | None; rect: CropRect | None; src_size: tuple[int, int] | None
face_box: tuple | None; out_size: tuple[int, int]; current_grade: Grade | None
last_render_ms: float; status_text: str
```

- Key map in `handle_key`, using `event.keysym` and `event.state` (Shift 0x1, Control 0x4):
  - `Return`/`KP_Enter` calls `save(advance=not shift)` and always returns True.
  - Shift+arrows nudge by 1% of `rect.w`; Ctrl+Shift+arrows nudge by 10%.
  - `plus`/`equal`/`KP_Add` call `zoom_at(factor 1/1.1)` about the frame centre; `minus`/`KP_Subtract` use factor 1.1.
  - `f`/`F` re-run `face_seed` (status `No face found` when `face_box` is None); `r`/`R` reset to `largest_fit`.
  - Everything else returns False, including unshifted arrows, digits, `Delete`, `Escape` and `c`.
- Mouse:
  - Dragging pans by `-dx / scale` (the image moves with the cursor).
  - The wheel (`event.delta`, ±120 on Windows) calls `zoom_at` with factor `1/1.1` per notch up and `1.1` per notch down, anchored at the source point under the cursor.
- Rendering:
  - Frame on canvas: `F` is centred in the canvas with a 40 px margin at the preset aspect ratio. `scale = F.w / rect.w` (canvas px per source px).
  - Visible source window: `sx0 = rect.x - F.x/scale`, `sy0 = rect.y - F.y/scale`, `sx1 = sx0 + cw/scale`, `sy1 = sy0 + ch/scale`. Intersect it with the image, crop that from the proxy (multiply coords by `proxy_w / src_w`), resize it to its canvas footprint (BILINEAR while dragging, LANCZOS 150 ms after the last motion), and paste it onto a background-coloured canvas-size image.
  - Dim everything outside `F` to 45% by pasting the un-dimmed frame region back onto a darkened copy. Show the result with one `ImageTk.PhotoImage` canvas item.
  - Move the vector items: frame outline (white, 2 px), thirds lines, and the face box (dotted `#EF9F27`). Record `last_render_ms`.
- Threads:
  - A loader thread produces `(path, proxy, src_size, face_box | None, error | None)`. The face is detected on the proxy and scaled back to source pixels.
  - A save thread runs `save_crop` sequentially and creates the upscaler lazily, only when the factor is above 1, AI is enabled and a model path is set.
  - A single `after(30)` poller drains both result queues. Results for a path other than `self.path` go to a 3-entry cache.
- Toolbar: preset `CTkOptionMenu` (choosing `Custom...` opens `ctk.CTkInputDialog` for `WxH` and adds a `Custom W×H` entry), `AI upscale when needed` checkbox, model `CTkOptionMenu` (model stems), grade badge `CTkLabel` coloured from `GRADE_COLORS`, and a status label.

- [ ] **Step 1: Write the failing tests** in `tests/test_crop_editor.py`.
  - Module fixture: `root = ctk.CTk(); root.geometry("1000x760+40+40")`. Fixture `editor(tmp_path)` packs a `CropEditor` with fakes:
    - `FakeDetector(boxes)` has `.available = True` and `.detect` returning those boxes at proxy scale.
    - `StubUpscaler` is the same as in Task 2.
    - Callbacks are recorded into lists.
  - Helper `pump(root, cond, timeout=5)` calls `root.update()` until `cond()` holds.
  - Events are `SimpleNamespace(x=, y=, delta=, keysym=, state=)`.

```python
def test_load_seeds_frame_on_face(editor, tmp_path): ...
    # FakeDetector([(700, 300, 800, 420, 0.9)]) on a 1600x1200 PNG, preset 1024x1024
    # -> after pump: editor.rect == face_seed(1600, 1200, 1.0, (700, 300, 800, 420)) (±0.5 px)

def test_load_without_face_uses_largest_fit(editor, tmp_path): ...

def test_drag_moves_image_with_cursor(editor, tmp_path):
    # x0 = editor.rect.x; on_press(x=500,y=350); on_drag(x=600,y=350); on_release(...)
    # assert editor.rect.x == pytest.approx(x0 - 100 / scale)   # scale = frame_w / rect.w

def test_wheel_zoom_keeps_point_under_cursor(editor, tmp_path): ...

def test_enter_saves_and_advances(editor, tmp_path):
    # handle_key(keysym="Return", state=0) -> True; on_advance called once
    # pump until on_saved recorded -> file exists in cropped__1024x1024 with size (1024, 1024)

def test_shift_enter_saves_and_stays(editor, tmp_path): ...   # state=0x1 -> on_advance not called, on_saved once

def test_enter_before_load_does_not_save(editor, tmp_path):   # Review Focus 3
    # editor.load(p1); pump loaded; editor.load(p2) and IMMEDIATELY handle_key(Return)
    # -> returns True, editor.status_text == "Still loading…", pending_saves() == 0

def test_shift_arrow_nudges_1_and_10_percent(editor, tmp_path): ...

def test_plain_arrows_and_digits_fall_through(editor, tmp_path):
    for k in ("Right", "Left", "1", "Delete", "Escape", "c"):
        assert editor.handle_key(SimpleNamespace(keysym=k, state=0, char=k)) is False

def test_f_and_r_keys(editor, tmp_path): ...

def test_set_preset_keeps_centre_and_exact_ratio(editor, tmp_path):
    # centre before == centre after (±1 px) and rect.w / rect.h == 1920 / 1080

def test_badge_reflects_grade(editor, tmp_path):
    # small crop -> current_grade.level == "soft" and badge fg_color == "#F44336"

def test_unreadable_image_reports_and_keys_fall_through(editor, tmp_path):
    # garbage bytes in bad.png -> status_text startswith "Cannot open"; handle_key(Right) is False

def test_render_under_30ms_on_4k(editor, tmp_path):
    # 3840x2160 noise PNG; 20 on_drag steps -> max of last_render_ms over the drags < 30

def test_shutdown_waits_for_pending_saves(editor, tmp_path): ...
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_crop_editor.py -v`
Expected: collection error, `ModuleNotFoundError: No module named 'crop_editor'`

- [ ] **Step 3: Implement** `sorter/crop_editor.py` per the Interfaces block. The canvas binds `<ButtonPress-1>`, `<B1-Motion>`, `<ButtonRelease-1>` and `<MouseWheel>` to the public handlers, and `<Configure>` to a re-render.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_crop_editor.py -v`
Expected: all PASS. If the 4K render test fails, lower the proxy work (crop before resize) rather than relaxing the 30 ms target.

- [ ] **Step 5: Commit**

```bash
git add sorter/crop_editor.py tests/test_crop_editor.py
git commit -m "CropEditor: fixed-frame canvas editor with background load/save"
```

---

### Task 4: Triage integration, Manual Crop mode, version 3.6.0

**Files:**
- Modify: `sorter/gui.py`
  - imports (lines 25-43)
  - `TriageWindow` (273-618): `__init__`, `_build_ui`, `_render_page`, `_show_gallery`, `_open_viewer`, `_show_current`, key bindings and `_on_close`
  - mode list (684), frame creation and build calls (692-723)
  - `_choose_directory` (1677), `_switch_mode` (1731), `run_operation` (1774)
  - window title, and the new `_build_crop_form`/`manual_crop` methods
- Modify: `sorter/version.py`, `sorter/CHANGELOG.md`, `VERSION.md`, `README.md`, `sorter/README.md`
- Test: `tests/test_triage_crop.py`

**Interfaces:**
- Consumes: `CropEditor` (Task 3) and `CROP_SIZE_PRESETS`/`DEFAULT_CROP_PRESET` (Task 1).
- Produces:
  - `TriageWindow.__init__(self, parent, sorter, log_fn, crop_only: bool = False, crop_defaults: dict | None = None)`. `crop_defaults` has the keys `preset`, `ai`, `model`, plus the optional `face_detector_factory` and `upscaler_factory`, which are passed through to `CropEditor`.
  - `TriageWindow.crop_mode: bool`, `TriageWindow.crop_editor: CropEditor | None`, `TriageWindow.crop_counts: dict[Path, int]`.
  - `TriageWindow._on_keypress(event) -> str | None`: the single `<KeyPress>` binding, replacing the per-key binds.
    1. In crop mode, `crop_editor.handle_key(event)` is tried first; a consumed key returns `"break"`.
    2. Then the existing map applies: Right/Left nav, Escape, Delete, 0–N buckets, Prior/Next pages.
    3. Finally `c`/`C`: when not `crop_only`, it toggles crop mode, but only while in the viewer.
    - Escape in crop mode (non-`crop_only`) leaves crop mode and stays in the viewer; otherwise it returns to the gallery.
    - In `crop_only` mode, bucket keys are ignored.
  - `SorterGUI.manual_crop()` and the `"Manual Crop"` mode, inserted right after `"Manual Sort (Triage)"` in the mode list. Its form state lives in `self.crop_frame`, `self.crop_src_label`, `self.crop_preset_var`, `self.crop_ai_var` (BooleanVar) and `self.crop_model_var` (model stem). `manual_sort()` passes the crop form's current values as `crop_defaults`, so C inside Triage uses them.
  - `CropEditor.load` keeps the current preset, so the chosen preset persists from image to image.
- Behaviour details:
  - In crop mode `viewer_label` is `pack_forget`-ed and the editor is packed. `_show_current` calls `crop_editor.load(path, prefetch=next path)`, and `on_advance` calls `self._nav(1)`.
  - `on_saved` increments `crop_counts[path]`, refreshes the thumbnail badge and logs `✂ Cropped {name} → {folder}/{file} ({method})`.
  - Badge: a `CTkLabel` with text `f"✂ {n}"`, placed at the top-right of the thumbnail cell. Created by `_refresh_badge(path)`, which is also called from `_render_page`.
  - `crop_only`: bucket buttons, Clear and Execute aren't packed; the status label reads `{n} crops saved`; gallery clicks open the viewer with crop mode already on.
  - `_on_close`: when `crop_editor.pending_saves() > 0`, the status shows `Finishing {n} saves…` and closing is retried every 200 ms. After that, the existing unsaved-assignment prompt runs, then `crop_editor.shutdown()`.
  - Crop form (`self.crop_frame`):
    - source folder button + label
    - preset `CTkOptionMenu` (`CROP_SIZE_PRESETS` keys, default `DEFAULT_CROP_PRESET`)
    - `AI upscale when needed` checkbox (default on)
    - model `CTkOptionMenu` of `list_upscale_models(DEFAULT_UPSCALE_MODELS_DIR)` stems, defaulting to `resolve_preset(DEFAULT_UPSCALE_PRESET)`
    - an info line: `✂ Frame stays fixed — drag the image under it, scroll to zoom. Enter saves a copy to cropped__<size>/ and moves on.`
    - `manual_crop()` validates the folder like `manual_sort()` does, then opens `TriageWindow(self, ManualSorter(self.logger, src, ["Keep"]), self.log_message, crop_only=True, crop_defaults=...)`.
  - Version: `VERSION = "3.6.0"`, `BUILD_DATE = "2026-10-04"`, `DESCRIPTION = "Advanced ComfyUI Image Organizer - Manual Crop"`. Add FEATURES entry `"Manual Crop (fixed frame, exact presets, metadata kept)",  # NEW in v3.6.0!` and update NOTES. Window title `"🚀 Sorter 3.6.0 - Advanced ComfyUI Image Organizer"`. Add a CHANGELOG `## [3.6.0] - 2026-10-04 - "Manual Crop" ✂️` section in the existing style, a VERSION.md repo 3.7.0 section, and a README mode-list line.

- [ ] **Step 1: Write the failing tests** in `tests/test_triage_crop.py`. Fixtures and helpers:
  - three synthetic 1600×1200 PNGs with a `parameters` chunk in `tmp_path`
  - `root = ctk.CTk()` withdrawn
  - the fake detector and upscaler, passed via `crop_defaults` with preset `DEFAULT_CROP_PRESET`
  - `key(k, state=0)` returns `SimpleNamespace(keysym=k, char=k, state=state)`
  - `pump(cond)` as in Task 3
  - `pump_until_loaded(win)` pumps until `win.crop_editor.rect is not None`
  - `badge_text(win, path)` returns the text of the `✂` label in that path's thumbnail cell, or None

```python
def test_c_toggles_crop_mode_only_in_viewer(win):
    win._on_keypress(key("c")); assert win.crop_mode is False          # gallery: ignored
    win._open_viewer(0); win._on_keypress(key("c"))
    assert win.crop_mode and win.crop_editor.winfo_ismapped() and not win.viewer_label.winfo_ismapped()
    win._on_keypress(key("Escape")); assert win.crop_mode is False and win.current_index == 0

def test_enter_saves_navigates_and_badges(win, tmp_path):
    win._open_viewer(0); win._on_keypress(key("c")); pump_until_loaded(win)
    assert win._on_keypress(key("Return")) == "break" and win.current_index == 1
    pump(lambda: win.crop_counts.get(win.sorter.images[0]) == 1)
    assert (tmp_path / "cropped__1024x1024" / win.sorter.images[0].name).exists()
    win._show_gallery(); win._render_page(); assert badge_text(win, win.sorter.images[0]) == "✂ 1"

def test_bucket_keys_work_in_crop_mode(win):
    # in crop mode, "1" -> assignment "Keep" and current_index advances; editor loads the next path

def test_plain_right_navigates_without_saving_in_crop_mode(win): ...

def test_crop_only_hides_buckets_and_opens_in_crop_mode(tmp_path):
    # TriageWindow(..., crop_only=True): no bucket button is mapped, execute_btn not mapped,
    # _open_viewer(0) -> crop_mode True; "1" -> no assignment

def test_close_waits_for_pending_saves(win): ...

def test_manual_crop_mode_switches_form():
    app = SorterGUI(); app.withdraw()
    app.mode_var.set("Manual Crop"); app._switch_mode()
    assert app.crop_frame.winfo_ismapped() and app.crop_preset_var.get() == DEFAULT_CROP_PRESET
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_triage_crop.py -v`
Expected: FAIL with `TypeError: TriageWindow.__init__() got an unexpected keyword argument 'crop_only'`.

- [ ] **Step 3: Implement** the TriageWindow changes, the crop form and mode wiring, and the version/docs updates, in `gui.py` and the doc files.

- [ ] **Step 4: Run the whole crop test set and confirm it passes**

Run: `python -m pytest tests/test_crop_tool.py tests/test_crop_editor.py tests/test_triage_crop.py -v`
Expected: all PASS.

- [ ] **Step 5: Visual check on real images.**
  1. Copy 5 PNGs from `D:\ComfyUI_windows_portable\ComfyUI\output` into a scratch folder.
  2. Open `TriageWindow` there with the real detector and upscaler; enter crop mode on image 1.
  3. Capture the window with `PIL.ImageGrab.grab(bbox=window rect)` into the scratchpad, then view it.

  Expected: the frame is centred, the outside is dimmed, the thirds grid and the dotted face box are on the face, and the badge is coloured. Press Enter once, then return to the gallery and confirm the ✂ badge shows.

- [ ] **Step 6: Launch check.** Run `python sorter/gui.py` for about 5 s and close it. Expected: the window title reads 3.6.0 and "Manual Crop" appears in the mode menu, with no traceback.

- [ ] **Step 7: Commit**

```bash
git add sorter/gui.py sorter/version.py sorter/CHANGELOG.md VERSION.md README.md sorter/README.md tests/test_triage_crop.py
git commit -m "Sorter 3.6: Manual Crop mode and C-key crop editing in Triage"
```
