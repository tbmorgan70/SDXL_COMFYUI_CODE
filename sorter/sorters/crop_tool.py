"""
Crop Tool — the UI-free half of Manual Crop.

Presets, crop-rectangle geometry, resolution grading and (further down)
saving crops with their metadata. The editor that drives this lives in
crop_editor.py; everything here works in float *source* pixels so it can
be tested without a window.
"""

import io
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo

from sorters.image_extractor import CROP_PRESETS

# Smallest crop allowed, measured on its short side, in source pixels
MIN_CROP_SIDE = 64

# Face framing for the starting frame: crop height in face-heights (Extract's
# "Portrait"), with the face-box centre this far down the frame so the eyes
# sit toward the upper third
FACE_FRAMING = 2.2
FACE_CENTER_Y = 0.42

# Upscale factor above which the result will look soft
SOFT_ABOVE = 2.0

# Source pixels kept around the crop before AI-upscaling it, so the model's
# edge artefacts fall outside the part that is kept
AI_REGION_MARGIN = 24

# Badge colours — the Triage palette
GRADE_COLORS = {"native": "#4CAF50", "upscale": "#FF9800", "soft": "#F44336"}

# SDXL training resolutions (~1 megapixel buckets)
SDXL_SIZE_PRESETS: Dict[str, Tuple[int, int]] = {
    "896×1152 — SDXL portrait 7:9":   (896, 1152),
    "1152×896 — SDXL landscape 9:7":  (1152, 896),
    "832×1216 — SDXL portrait 2:3":   (832, 1216),
    "1216×832 — SDXL landscape 3:2":  (1216, 832),
    "768×1344 — SDXL tall 4:7":       (768, 1344),
    "1344×768 — SDXL wide 7:4":       (1344, 768),
    "640×1536 — SDXL extra tall":     (640, 1536),
    "1536×640 — SDXL extra wide":     (1536, 640),
}


def _build_presets() -> Dict[str, Union[Tuple[int, int], str]]:
    presets: Dict[str, Union[Tuple[int, int], str]] = {}
    for label, size in CROP_PRESETS.items():
        if isinstance(size, tuple):
            presets[label] = size
    seen = set(presets.values())
    for label, size in SDXL_SIZE_PRESETS.items():
        if size not in seen:
            presets[label] = size
            seen.add(size)
    presets["Custom..."] = "custom"
    return presets


CROP_SIZE_PRESETS = _build_presets()
DEFAULT_CROP_PRESET = "1024×1024 — SDXL native"


# ----------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class CropRect:
    """A crop in source pixels. Floats: positions are only rounded on save."""
    x: float
    y: float
    w: float
    h: float


def largest_fit(src_w: int, src_h: int, ar: float) -> CropRect:
    """The biggest frame of aspect ratio `ar` (w/h) that fits, centred."""
    w = min(float(src_w), src_h * ar)
    h = w / ar
    return CropRect((src_w - w) / 2, (src_h - h) / 2, w, h)


def clamp(rect: CropRect, src_w: int, src_h: int, ar: float) -> CropRect:
    """The single place the frame's rules are enforced: exact aspect ratio,
    no larger than the image allows, short side at least MIN_CROP_SIDE (or
    the whole fit on images smaller than that), and entirely inside.

    The size changes about the rect's centre, then the rect is shifted inside.
    A frame capped at the largest fit keeps its position on the free axis
    rather than jumping back to the middle.
    """
    big = largest_fit(src_w, src_h, ar)
    min_w = MIN_CROP_SIDE * ar if ar >= 1 else MIN_CROP_SIDE
    w = max(min(rect.w, big.w), min(min_w, big.w))
    h = w / ar
    cx = rect.x + rect.w / 2
    cy = rect.y + rect.h / 2
    x = min(max(cx - w / 2, 0.0), src_w - w)
    y = min(max(cy - h / 2, 0.0), src_h - h)
    return CropRect(x, y, w, h)


def pan(rect: CropRect, dx: float, dy: float,
        src_w: int, src_h: int, ar: float) -> CropRect:
    """Move the frame by (dx, dy) source pixels, stopping at the edges."""
    return clamp(CropRect(rect.x + dx, rect.y + dy, rect.w, rect.h), src_w, src_h, ar)


def zoom_at(rect: CropRect, factor: float, ax: float, ay: float,
            src_w: int, src_h: int, ar: float) -> CropRect:
    """Scale the frame by `factor` (>1 grows it = zoom out) keeping the source
    point (ax, ay) at the same relative position inside the frame."""
    return clamp(CropRect(ax - (ax - rect.x) * factor, ay - (ay - rect.y) * factor,
                          rect.w * factor, rect.h * factor), src_w, src_h, ar)


def face_seed(src_w: int, src_h: int, ar: float,
              face_box: Tuple[float, float, float, float],
              framing: float = FACE_FRAMING) -> CropRect:
    """Starting frame around a face: `framing` face-heights tall, centred on
    the face horizontally, face centre FACE_CENTER_Y down the frame."""
    x1, y1, x2, y2 = face_box[:4]
    h = max(1.0, y2 - y1) * framing
    w = h * ar
    return clamp(CropRect((x1 + x2) / 2 - w / 2, (y1 + y2) / 2 - FACE_CENTER_Y * h, w, h),
                 src_w, src_h, ar)


# ----------------------------------------------------------------------
# Grading
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Grade:
    level: str      # "native" | "upscale" | "soft"
    factor: float   # output pixels per source pixel
    label: str


def grade(rect: CropRect, out_w: int, out_h: int, ai_enabled: bool) -> Grade:
    """How much the crop must be enlarged to reach the preset size."""
    factor = out_w / rect.w
    if factor <= 1.0:
        return Grade("native", factor, "Native pixels")
    if factor > SOFT_ABOVE:
        return Grade("soft", factor, f"{factor:.1f}x — will be soft, widen the frame")
    method = "AI upscale" if ai_enabled else "resize"
    return Grade("upscale", factor, f"{factor:.1f}x — {method}")


# ----------------------------------------------------------------------
# Saving
# ----------------------------------------------------------------------

MANIFEST_NAME = "_crop_info.txt"
EXIF_ORIENTATION = 274


@dataclass(frozen=True)
class SaveResult:
    path: Path
    factor: float
    method: str     # "native" | "resize" | "AI <model>" | "resize (AI failed: ...)"


def output_dir_for(source_dir: Path, out_w: int, out_h: int) -> Path:
    return Path(source_dir) / f"cropped__{out_w}x{out_h}"


def open_oriented(path: Path) -> Tuple[Image.Image, Image.Image]:
    """(as opened, as displayed). The first keeps .format and .info for the
    metadata; the second has EXIF rotation applied, which is what the editor
    shows and what crop rects refer to. Read from memory so no file handle
    stays open (Triage may move the file afterwards)."""
    orig = Image.open(io.BytesIO(Path(path).read_bytes()))
    orig.load()
    return orig, ImageOps.exif_transpose(orig)


def _workable(img: Image.Image) -> Image.Image:
    """A mode Lanczos resizing and every output format can handle, keeping alpha."""
    if img.mode.startswith("I") or img.mode == "F":
        arr = np.asarray(img, dtype=np.float64)
        if arr.max(initial=0) > 255:
            arr = arr / 257.0
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L").convert("RGB")
    if img.mode == "P":
        return img.convert("RGBA" if "transparency" in img.info else "RGB")
    if img.mode in ("1", "CMYK", "YCbCr", "LAB", "HSV"):
        return img.convert("RGB")
    return img


def save_with_metadata(img: Image.Image, src_img: Image.Image, dest_stem: Path) -> Path:
    """Write `img` next to `dest_stem` in the source's format family, carrying
    its PNG text chunks, EXIF (orientation reset) and ICC profile.
    Returns the path written; a clash becomes <stem>_2, <stem>_3, ..."""
    fmt = (src_img.format or "PNG").upper()
    kwargs = {}
    if fmt == "JPEG":
        ext, pil_fmt = ".jpg", "JPEG"
        kwargs.update(quality=95, subsampling=0)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    elif fmt == "WEBP":
        ext, pil_fmt = ".webp", "WEBP"
        kwargs["lossless"] = True
    else:
        ext, pil_fmt = ".png", "PNG"
        texts = {k: v for k, v in src_img.info.items() if isinstance(v, str)}
        if texts:
            info = PngInfo()
            for k, v in texts.items():
                info.add_text(k, v)
            kwargs["pnginfo"] = info

    icc = src_img.info.get("icc_profile")
    if icc:
        kwargs["icc_profile"] = icc
    exif = src_img.getexif()
    if len(exif):
        if EXIF_ORIENTATION in exif:
            exif[EXIF_ORIENTATION] = 1      # pixels are already upright
        kwargs["exif"] = exif.tobytes()

    dest = Path(str(dest_stem) + ext)
    n = 2
    while dest.exists():
        dest = Path(f"{dest_stem}_{n}{ext}")
        n += 1
    img.save(dest, pil_fmt, **kwargs)
    return dest


def _append_manifest(out_dir: Path, out_w: int, out_h: int, src: Path,
                     rect: CropRect, factor: float, method: str, dest: Path):
    path = out_dir / MANIFEST_NAME
    lines = []
    if not path.exists():
        lines += ["=== CROP INFO ===",
                  f"Output size : {out_w}x{out_h}",
                  f"Created     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  "",
                  "source | crop rect (x,y,w,h) | factor | method | output"]
    lines.append(f"{src.name} | {round(rect.x)},{round(rect.y)},{round(rect.w)},{round(rect.h)}"
                 f" | {factor:.2f}x | {method} | {dest.name}")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def save_crop(src_path: Path, rect: CropRect, out_w: int, out_h: int,
              upscaler=None, out_dir: Optional[Path] = None) -> SaveResult:
    """Cut `rect` (displayed-orientation source pixels) out of the full-
    resolution original and write it at exactly out_w x out_h.

    Enlarging uses the AI upscaler when one is given — on the crop plus a
    small margin only — falling back to Lanczos if it fails.
    """
    src_path = Path(src_path)
    orig, img = open_oriented(src_path)
    img = _workable(img)
    factor = out_w / rect.w
    box = (rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)

    if factor <= 1.0:
        result, method = img.resize((out_w, out_h), Image.LANCZOS, box=box), "native"
    elif upscaler is None:
        result, method = img.resize((out_w, out_h), Image.LANCZOS, box=box), "resize"
    else:
        try:
            m = AI_REGION_MARGIN
            rx0, ry0 = max(0, math.floor(rect.x - m)), max(0, math.floor(rect.y - m))
            rx1 = min(img.width, math.ceil(rect.x + rect.w + m))
            ry1 = min(img.height, math.ceil(rect.y + rect.h + m))
            up = upscaler.upscale(img.crop((rx0, ry0, rx1, ry1)))
            s = up.width / (rx1 - rx0)
            up_box = ((rect.x - rx0) * s, (rect.y - ry0) * s,
                      (rect.x - rx0 + rect.w) * s, (rect.y - ry0 + rect.h) * s)
            result = up.resize((out_w, out_h), Image.LANCZOS, box=up_box)
            method = f"AI {upscaler.name}"
        except Exception as e:
            result = img.resize((out_w, out_h), Image.LANCZOS, box=box)
            method = f"resize (AI failed: {e})"

    out_dir = Path(out_dir) if out_dir else output_dir_for(src_path.parent, out_w, out_h)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = save_with_metadata(result, orig, out_dir / src_path.stem)
    _append_manifest(out_dir, out_w, out_h, src_path, rect, factor, method, dest)
    return SaveResult(dest, factor, method)
