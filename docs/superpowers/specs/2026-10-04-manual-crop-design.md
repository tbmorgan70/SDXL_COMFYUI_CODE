# Manual Crop — Design

**Date:** 2026-10-04
**Target release:** Sorter 3.6.0 / repo 3.7.0
**Status:** Approved in conversation; awaiting spec review

## Goal

Let the user crop images by hand to exact preset sizes, with the image floating under a fixed
aspect-ratio frame, without leaving the Triage workflow they use constantly. Crops keep the
image's generation metadata so Civitai Prep (and tools like Livebound) still read them.

Success looks like: open Triage, press C, nudge a face-seeded frame, press Enter, and the next
image is ready instantly while the crop is written in the background — with a clear colour
signal whenever the crop lacks the native pixels for the chosen size.

## Decisions (from the user)

| Question | Decision |
|---|---|
| Where does cropping live? | Both: a crop mode inside Triage (C key) and a standalone "Manual Crop" menu mode |
| What does Enter do to files? | Save a copy immediately; the original is never touched |
| How is shape/size chosen? | Exact-size presets (Extract's sized presets + SDXL training sizes + Custom) |
| Crop smaller than the preset? | AI upscale when needed (toggle, default on), model picked once per session |
| Where does the frame start? | On the largest face (Portrait framing); largest centred frame if none |
| Rendering approach | Tk Canvas viewport rendering (approach A) |

## User-facing behaviour

### Entry points

- **Triage:** in the full-size viewer, **C** toggles crop mode. Crop mode is sticky while
  navigating; **Esc** or **C** leaves it.
- **Manual Crop mode** (main menu): folder picker, default preset, AI-upscale toggle and model.
  Opens the Triage window in crop-only form — no bucket bar, no Execute — and clicking a
  thumbnail opens directly into crop mode.

### Editor

- **Toolbar:** preset dropdown, "AI upscale when needed" checkbox + model dropdown, resolution
  badge. The chosen preset persists across images for the session.
- **Canvas:** the frame is fixed and centred; the image floats underneath. Outside the frame is
  dimmed (not hidden). A rule-of-thirds grid is drawn inside the frame; the detected face is a
  dotted amber box.
- **Mouse:** drag pans the image; the wheel zooms about the cursor.
- **Bounds:** the frame always lies entirely inside the image (no padding or letterboxing).
  The smallest allowed crop is 64 source pixels on its short side.
- **Starting frame:** largest detected face, framed at 2.2 face-heights (Extract's "Portrait"),
  with the face-box centre placed 42% of the frame height from the top so the eyes sit toward
  the upper third; clamped into the image and shrunk to fit if needed. No face → largest centred
  frame. (Extract's own 0.08 bias is applied with the opposite sign — the face lands at 58% —
  so it is not reused; that is noted for the user separately.)

### Keys in crop mode

| Key | Action |
|---|---|
| Enter | Save crop, advance to next image |
| Shift+Enter | Save crop, stay (to save another preset of the same image) |
| ← / → | Previous / next image without saving (unchanged from Triage) |
| Shift+arrows | Nudge the frame by 1% of the crop size; Ctrl+Shift+arrows by 10% |
| + / − | Zoom in / out about the frame centre |
| F | Re-snap to the face |
| R | Reset to the largest centred frame |
| 1–4, 0, Del | Bucket assignment exactly as today (Triage only, not crop-only mode) |

### Resolution badge

The upscale factor is `preset_width / crop_width_in_source_pixels` (identical to the height
ratio, since the frame has the preset's aspect ratio).

| Colour | Condition | Label |
|---|---|---|
| Green | factor ≤ 1.0 | Native pixels |
| Amber | 1.0 < factor ≤ 2.0 | "1.4x — AI upscale" (toggle on) / "1.4x — resize" (toggle off) |
| Red | factor > 2.0 | "2.6x — will be soft, widen the frame" |

Red is a warning only; saving is still allowed.

### Output

- Folder: `<source>/cropped__<W>x<H>/` (self-describing, like 3.4.1's output folders). Triage
  lists only top-level files, so crops never appear in the triage list.
- File: `<stem>.<source ext>`; a clash appends `_2`, `_3`, …
- Format follows the source: PNG → PNG, JPEG → JPEG (quality 95, no chroma subsampling),
  WebP → WebP (lossless). GIF and BMP sources are written as PNG.
- Metadata carried over: all PNG text chunks (ComfyUI `prompt`/`workflow`, A1111
  `parameters`, Civitai Prep fields), EXIF bytes, ICC profile. Generation metadata is copied
  verbatim — `Size` in `parameters` stays the generation size.
- `_crop_info.txt` in each output folder: header written on first use (preset, folder created),
  then one appended line per crop: source file, crop rect in source pixels, factor, method
  (native / resize / AI + model name), output file name.
- Gallery thumbnails of cropped images show a ✂ badge with the crop count for this session.

## Architecture

### `sorter/sorters/crop_tool.py` (new, UI-free)

- `SDXL_SIZE_PRESETS` and `CROP_SIZE_PRESETS`: Extract's sized entries from
  `image_extractor.CROP_PRESETS` (excluding "None" and "Custom...") plus the SDXL training sizes
  1024×1024, 896×1152, 1152×896, 832×1216, 1216×832, 768×1344, 1344×768, 640×1536, 1536×640,
  plus "Custom..." handled by the UI.
- `CropRect` dataclass (`x, y, w, h` floats, source pixels) and pure functions:
  - `largest_fit(src_w, src_h, ar) -> CropRect` (centred)
  - `clamp(rect, src_w, src_h, ar) -> CropRect` (enforces aspect, min size, inside image)
  - `pan(rect, dx, dy, src_w, src_h, ar)`
  - `zoom_at(rect, factor, ax, ay, src_w, src_h, ar)` — the source point `(ax, ay)` keeps its
    position relative to the frame
  - `face_seed(src_w, src_h, ar, face_box, framing=2.2) -> CropRect`
- `grade(rect, out_w, out_h, ai_enabled) -> Grade(level, factor, label)`
- `save_crop(src_path, rect, out_w, out_h, upscaler=None) -> SaveResult`:
  opens the full-resolution source, crops (region plus a 24 px margin when AI-upscaling, as in
  `ImageExtractorSorter._face_crop_ai`), AI-upscales only when factor > 1.0 and an upscaler is
  given, resizes to exactly `out_w × out_h` with Lanczos, writes with metadata, appends the
  manifest line. Returns the output path, factor and method.
- `save_with_metadata(img, src_img, dest)` helper for the format/metadata rules above.

### `sorter/crop_editor.py` (new)

`CropEditor(ctk.CTkFrame)` — the toolbar and canvas, used by both entry points.

- **Public API:** `load(path, prefetch_next=None)`, `save(advance: bool)`, `handle_key(event) -> bool`
  (True when consumed), `set_preset(label)`, callbacks `on_saved(path, result)` and
  `on_advance()`.
- **Loading:** a worker thread decodes a proxy (long edge ≤ 2048 px) and runs face detection;
  results go through a queue drained by a main-thread `after()` poller, which alone creates Tk
  images (per the Tkinter threading rule). The next image is prefetched the same way.
- **Rendering:** one canvas image item shows only the visible region of the proxy, scaled to
  the canvas — `Image.BILINEAR` during drag/zoom, `Image.LANCZOS` ~150 ms after motion stops.
  Tk canvas items have no alpha, so the dimming is applied to that rendered bitmap (outside the
  frame darkened to 45%); the frame outline, thirds lines and face box are canvas vector items
  that are only moved, never re-rasterised.
- **Saving:** a single save-worker thread consumes a queue of save jobs sequentially (no GPU
  contention); the badge shows "Saving…" until the job completes. Errors go to the status line
  and the session log.
- **Lazy resources:** `FaceDetector` (from `image_extractor`) is created once on first load;
  the `Upscaler` (from `upscaler`) is created on the first save that needs it, inside the save
  worker.

### `sorter/gui.py` (changed)

- `TriageWindow` gains `crop_only: bool = False` and a `crop_defaults` dict (preset, AI toggle,
  model path).
  - C toggles crop mode in the viewer: the plain viewer label is swapped for a `CropEditor`.
  - While crop mode is on, key events go to `CropEditor.handle_key` first; unconsumed keys fall
    through to the existing Triage bindings (so ←/→ and 1–4 keep working).
  - Thumbnails show a ✂ badge with the session crop count.
  - In crop-only mode the bucket bar and Execute button are hidden and gallery clicks open
    directly into crop mode.
- New main-menu mode **"Manual Crop"**: folder picker, default preset dropdown, AI toggle and
  model dropdown (populated by `upscaler.list_upscale_models`). Opens
  `TriageWindow(crop_only=True)` using a `ManualSorter` for the image list.

### Versioning and docs

Sorter 3.6.0 / repo 3.7.0: `sorter/version.py`, `sorter/CHANGELOG.md`, `VERSION.md`, README
mode list and window title.

## Error handling

- Unreadable image: the editor shows the error in place; ←/→ still navigate.
- No face detector available: start with the largest centred frame; F does nothing and says why.
- Upscaler fails to load or runs out of VRAM: the save falls back to a Lanczos resize, the
  manifest records "resize (AI failed: …)", and the status line reports it.
- Write failure (permissions, disk full): status line plus session log; the editor stays usable.
- Closing the window while saves are queued: wait for the queue to drain (with a "Finishing N
  saves…" status) before destroying the window.

## Testing

1. **pytest — `tests/test_crop_tool.py`:**
   - geometry: `largest_fit` exact aspect ratio; `clamp` keeps the rect inside at every edge and
     enforces the minimum size; `zoom_at` keeps the anchor point fixed; `face_seed` stays in
     bounds for faces at edges/corners and for faces too large for the frame
   - `grade` thresholds at 1.0 and 2.0, labels with the toggle on and off
   - `save_crop`: exact output size; PNG text chunks preserved; JPEG EXIF preserved; ICC
     preserved; `_2` naming; manifest header + lines; AI path with a stub upscaler (2× nearest)
     verifying region/margin maths and the final exact size
2. **Real files:** crop real ComfyUI PNGs from the user's output folder; Sorter's
   `MetadataExtractor` and `CivitaiPrep.analyze_image` return the same prompt and resources for
   the crop as for the original.
3. **GUI smoke test:** open `TriageWindow` on a temp folder of real images, drive C / drag /
   Enter / Shift+Enter programmatically, confirm output files, screenshot the window for a
   visual check (thumbnail badge, dim mask, grid, badge colours).
4. **Performance:** time the redraw during simulated drag on a 4K image; target < 30 ms per frame.

## Out of scope

Rotation; free-size crops without a preset; applying one crop to a batch; undo (delete the copy);
a duplicate finder (parked separately — keeper should default to the largest file).
