"""
Crop Tool — the UI-free half of Manual Crop.

Presets, crop-rectangle geometry, resolution grading and (further down)
saving crops with their metadata. The editor that drives this lives in
crop_editor.py; everything here works in float *source* pixels so it can
be tested without a window.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Union

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
