"""
Image Extractor Sorter — Extract images from documents and archives.

Supported containers: PDF, EPUB, MOBI/AZW, CBZ/CBR/CB7/CBT, and plain
ZIP/RAR/7Z/TAR. The real container format is detected by magic bytes, not
extension — many ".cbr" files in the wild are actually ZIPs (and vice
versa), and this handles them transparently.

Supports auto-crop to standard aspect ratios with optional face-centered cropping.
"""

import io
import os
import shutil
import tarfile
import zipfile
from pathlib import Path

from PIL import Image

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

# Where to look for a YOLO face model (first hit wins). ComfyUI users
# typically already have face_yolov8m.pt for FaceDetailer/Impact Pack.
YOLO_FACE_MODEL_PATHS = [
    r"D:\ComfyUI_windows_portable\ComfyUI\models\ultralytics\bbox\face_yolov8m.pt",
    r"D:\ComfyUI_windows_portable\ComfyUI\models\ultralytics\bbox\face_yolov8n.pt",
    r"D:\ComfyUI_windows_portable\ComfyUI\models\ultralytics\bbox\face_yolov8s.pt",
]

SUPPORTED_EXTENSIONS = {'.pdf', '.epub', '.mobi', '.azw', '.azw3',
                        '.cbr', '.cbz', '.cb7', '.cbt',
                        '.zip', '.rar', '.7z', '.tar'}

ARCHIVE_EXTENSIONS = {'.cbr', '.cbz', '.cb7', '.cbt', '.zip', '.rar', '.7z', '.tar'}

ARCHIVE_IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')


def sniff_format(filepath) -> str:
    """Detect the real container format by magic bytes.

    Returns one of 'zip', 'rar', '7z', 'tar', 'pdf', 'mobi', or ''.
    Extensions lie constantly in the comic/ebook world — trust the bytes.
    """
    try:
        with open(filepath, 'rb') as f:
            head = f.read(8)
            f.seek(60)
            mobi_sig = f.read(8)
            f.seek(257)
            tar_sig = f.read(5)
    except OSError:
        return ''
    if head.startswith(b'PK\x03\x04') or head.startswith(b'PK\x05\x06'):
        return 'zip'
    if head.startswith(b'Rar!'):
        return 'rar'
    if head.startswith(b'7z\xbc\xaf\x27\x1c'):
        return '7z'
    if head.startswith(b'%PDF'):
        return 'pdf'
    if mobi_sig in (b'BOOKMOBI', b'TEXtREAd'):
        return 'mobi'
    if tar_sig == b'ustar':
        return 'tar'
    return ''


class FaceDetector:
    """Face detection with automatic backend selection.

    Tries backends in descending order of quality and reports which one it
    picked, so the log always explains what you're getting:

      1. YOLO  — ultralytics + a face_yolov8*.pt model (best on angled,
                 partial and stylized faces; GPU-accelerated when available)
      2. Haar  — OpenCV cascade, bundled with opencv (frontal faces only)

    NOTE: mediapipe is deliberately not used. Its legacy `mp.solutions`
    face API was removed in 0.10.x, and the replacement Tasks API needs a
    separate model download — YOLO is both better and already present for
    most ComfyUI users.

    detect() returns a list of (x1, y1, x2, y2, confidence) in pixels.
    """

    def __init__(self, model_path=None, min_confidence: float = 0.35, log=None):
        self.min_confidence = min_confidence
        self.backend = None
        self._model = None
        self._log = log or (lambda m: None)
        self._init_backend(model_path)

    def _init_backend(self, model_path):
        # 1. YOLO face model
        if HAS_ULTRALYTICS:
            candidates = ([model_path] if model_path else []) + YOLO_FACE_MODEL_PATHS
            for path in candidates:
                if path and os.path.isfile(path):
                    try:
                        self._model = YOLO(path)
                        self.backend = 'yolo'
                        self._log(f"  Face detection: YOLO ({Path(path).name})")
                        return
                    except Exception as e:
                        self._log(f"  YOLO model failed to load ({e}); trying next backend")

        # 2. OpenCV Haar cascade
        if HAS_CV2:
            try:
                cascade_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.isfile(cascade_file):
                    self._model = cv2.CascadeClassifier(cascade_file)
                    if not self._model.empty():
                        self.backend = 'haar'
                        self._log("  Face detection: OpenCV Haar cascade "
                                  "(frontal faces only — install ultralytics "
                                  "and a face_yolov8*.pt model for better results)")
                        return
            except Exception:
                pass

        self._log("  Face detection unavailable — face crop will use center crop")

    @property
    def available(self) -> bool:
        return self.backend is not None

    def detect(self, img: Image.Image):
        """Detect faces in a PIL image. Returns [(x1,y1,x2,y2,conf), ...]."""
        if not self.available:
            return []
        try:
            if self.backend == 'yolo':
                return self._detect_yolo(img)
            return self._detect_haar(img)
        except Exception as e:
            self._log(f"  Face detection error ({e})")
            return []

    def _detect_yolo(self, img: Image.Image):
        result = self._model.predict(source=img.convert('RGB'), verbose=False,
                                     conf=self.min_confidence)[0]
        if result.boxes is None:
            return []
        return [(float(x1), float(y1), float(x2), float(y2), float(c))
                for (x1, y1, x2, y2), c
                in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist())]

    def _detect_haar(self, img: Image.Image):
        import numpy as np
        gray = cv2.cvtColor(np.array(img.convert('RGB')), cv2.COLOR_RGB2GRAY)
        faces = self._model.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                             minSize=(40, 40))
        # Haar gives no confidence score; report 1.0
        return [(float(x), float(y), float(x + w), float(y + h), 1.0)
                for (x, y, w, h) in faces]


def setup_rar_backend() -> str:
    """Point rarfile at an available extraction tool.

    rarfile needs an external tool for real RAR archives. Probes PATH,
    then common Windows install locations for 7-Zip and WinRAR.
    Returns a status string ('' = ready, else a human-readable problem).
    """
    if not HAS_RARFILE:
        return "rarfile module not installed (pip install rarfile)"

    # Already available on PATH?
    for tool in ('unrar', 'unar', 'bsdtar', '7z', '7zz'):
        if shutil.which(tool):
            return ''

    # Common Windows install locations, including archive managers that
    # bundle their own 7z binary rather than installing one on PATH
    candidates = [
        (r"C:\Program Files\WinRAR\UnRAR.exe", 'unrar'),
        (r"C:\Program Files (x86)\WinRAR\UnRAR.exe", 'unrar'),
        (r"C:\Program Files\7-Zip\7z.exe", '7z'),
        (r"C:\Program Files (x86)\7-Zip\7z.exe", '7z'),
        # PeaZip ships 7z + unrar under res\bin
        (r"C:\Program Files\PeaZip\res\bin\7z\7z.exe", '7z'),
        (r"C:\Program Files (x86)\PeaZip\res\bin\7z\7z.exe", '7z'),
        (os.path.expandvars(r"%LOCALAPPDATA%\Programs\PeaZip\res\bin\7z\7z.exe"), '7z'),
        (r"C:\Program Files\PeaZip\res\bin\unrar\unrar.exe", 'unrar'),
        (r"C:\Program Files (x86)\PeaZip\res\bin\unrar\unrar.exe", 'unrar'),
        # NanaZip (Microsoft Store 7-Zip fork)
        (r"C:\Program Files\NanaZip\NanaZipC.exe", '7z'),
    ]
    for path, kind in candidates:
        if os.path.isfile(path):
            if kind == 'unrar':
                rarfile.UNRAR_TOOL = path
            else:
                rarfile.SEVENZIP_TOOL = path
            return ''

    return ("no RAR tool found — install 7-Zip (winget install 7zip.7zip), "
            "PeaZip, or WinRAR to enable RAR-based archives")

# Crop size presets: display label → (width, height) or None
CROP_PRESETS = {
    "None (keep original)":           None,
    # SDXL training
    "512×512 — SDXL min":             (512,  512),
    "768×768 — SDXL medium":          (768,  768),
    "1024×1024 — SDXL native":        (1024, 1024),
    # Square / social
    "1080×1080 — 1:1 Social":         (1080, 1080),
    # Landscape
    "1920×1080 — 16:9 Full HD":       (1920, 1080),
    "1280×720 — 16:9 HD":             (1280, 720),
    # Vertical
    "1080×1920 — 9:16 Vertical":      (1080, 1920),
    "720×1280 — 9:16 HD Vertical":    (720,  1280),
    "1080×1350 — 4:5 Portrait":       (1080, 1350),
    # Classic
    "1024×768 — 4:3 Classic":         (1024, 768),
    "1080×720 — 3:2 Photography":     (1080, 720),
    # Ultrawide
    "2560×1080 — 21:9 Ultrawide":     (2560, 1080),
    "Custom...":                       "custom",
}

CROP_MODES = ["none", "center", "face"]

# How much of the subject to keep around a detected face, in plain terms.
# The number is the crop height measured in face-heights: 1.0 would be the
# face alone, so 2.2 leaves room for hair, neck and shoulders.
FACE_FRAMING_PRESETS = {
    "Close-up (face fills frame)":   1.4,
    "Portrait (head & shoulders)":   2.2,   # default
    "Upper body":                    3.5,
    "Half body":                     5.0,
    "Wide (full figure)":            8.0,
}
DEFAULT_FACE_FRAMING = "Portrait (head & shoulders)"

# How PDF pages are turned into images
PDF_MODES = {
    "Auto-stitch split pages (recommended)": "stitch",
    "Raw embedded images":                   "raw",
    "Render whole page":                     "render",
}


class ImageExtractorSorter:
    """Extract images from document/archive files with optional auto-crop."""

    def __init__(self, logger, min_width=512, min_height=512,
                 output_dir="extracted_images", folder_prefix="",
                 crop_size=None, crop_mode="center", face_model_path=None,
                 face_zoom=2.2, max_upscale=1.0,
                 pdf_mode="stitch", pdf_render_dpi=200):
        """
        Parameters
        ----------
        logger      : SortLogger instance (or None for stdout)
        min_width   : Discard images narrower than this
        min_height  : Discard images shorter than this
        output_dir  : Root output folder
        folder_prefix: Prepended to per-source subfolders
        crop_size   : (width, height) tuple or None to skip cropping
        crop_mode   : "none" | "center" | "face"
                      "face" detects the largest face and centers the crop
                      around it, falling back to center crop if none found.
        face_model_path : optional explicit YOLO face model (.pt)
        face_zoom   : how many face-heights tall the face crop should be
                      (higher = wider shot; 2.2 ~ head and shoulders)
        max_upscale : cap on enlarging the source for face framing; 1.0
                      keeps everything at native resolution or smaller
        pdf_mode    : "stitch" (default) reassembles pages that scanners
                      stored as several tiled strips; "raw" saves every
                      embedded image separately (old behaviour);
                      "render" rasterizes each page as it appears
        pdf_render_dpi : resolution used by pdf_mode="render"
        """
        self.logger = logger
        self.min_width = min_width
        self.min_height = min_height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.folder_prefix = folder_prefix
        self.crop_size = crop_size
        self.crop_mode = crop_mode if crop_size else "none"
        self.face_zoom = face_zoom      # crop height in face-heights
        self.max_upscale = max_upscale  # never enlarge past this x native
        self.pdf_mode = pdf_mode        # "stitch" | "raw" | "render"
        self.pdf_render_dpi = pdf_render_dpi

        self.total_extracted = 0
        self.current_source_dir = None
        self.current_file_counter = 0
        self._face_crops = 0
        self._framing_clamped = 0

        self._face_detector = None
        if self.crop_mode == "face":
            self._face_detector = FaceDetector(model_path=face_model_path,
                                               log=self._log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        if self.logger:
            self.logger.log_info(msg)
        else:
            print(msg)

    def _setup_source_folder(self, source_filename: str):
        base = Path(source_filename).stem
        base = "".join(c for c in base if c.isalnum() or c in (' ', '-', '_'))
        base = base.replace(' ', '_')[:50]
        if self.folder_prefix:
            base = f"{self.folder_prefix}_{base}"

        # Same-stem sources in one run (comic.cbz + comic.cbr) must not
        # overwrite each other's output
        if not hasattr(self, '_used_folder_names'):
            self._used_folder_names = set()
        name = base
        n = 2
        while name in self._used_folder_names:
            name = f"{base}_{n}"
            n += 1
        self._used_folder_names.add(name)

        self.current_source_dir = self.output_dir / name
        self.current_source_dir.mkdir(exist_ok=True)
        self.current_file_counter = 0

    # ------------------------------------------------------------------
    # Crop implementations
    # ------------------------------------------------------------------

    def _center_crop(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Scale to fill target, then center-crop the overflow."""
        src_w, src_h = img.size
        scale = max(target_w / src_w, target_h / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return img.crop((left, top, left + target_w, top + target_h))

    def _face_crop(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Crop around the primary (largest) face.

        Falls back to center crop when no detector is available or no face
        is found. The crop is padded to ~2.2x the face height so hair, neck
        and shoulders are included rather than a tight head shot.
        """
        if self._face_detector is None or not self._face_detector.available:
            return self._center_crop(img, target_w, target_h)

        faces = self._face_detector.detect(img)
        if not faces:
            return self._center_crop(img, target_w, target_h)

        src_w, src_h = img.size

        # Primary face = largest by area (matches "the subject" in practice)
        x1, y1, x2, y2, conf = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
        face_cx = (x1 + x2) / 2
        face_cy = (y1 + y2) / 2
        face_h = max(1.0, y2 - y1)

        # Ideal framing puts `face_zoom` face-heights in the crop, but a
        # small face (group shots, full-body at distance) would demand huge
        # upscaling. Clamp so we never enlarge past max_upscale of native —
        # a wider sharp crop beats a tight blurry one for training data.
        fill_scale = max(target_w / src_w, target_h / src_h)
        framing_scale = target_h / (face_h * self.face_zoom)
        scale = min(framing_scale, max(fill_scale, self.max_upscale))
        scale = max(scale, fill_scale)

        # Track when the source simply lacks the pixels for the requested
        # framing, so the summary can say so instead of silently ignoring it
        self._face_crops += 1
        if framing_scale > scale + 0.01:
            self._framing_clamped += 1

        new_w = max(target_w, int(src_w * scale))
        new_h = max(target_h, int(src_h * scale))
        img_scaled = img.resize((new_w, new_h), Image.LANCZOS)

        # Bias the crop slightly above the face centre so the subject's eyes
        # land nearer the upper third rather than dead centre.
        cx = int(face_cx * scale)
        cy = int(face_cy * scale - target_h * 0.08)

        left = max(0, min(cx - target_w // 2, new_w - target_w))
        top = max(0, min(cy - target_h // 2, new_h - target_h))

        if len(faces) > 1:
            self._log(f"    ({len(faces)} faces, using largest @ {conf:.2f})")

        return img_scaled.crop((left, top, left + target_w, top + target_h))

    def _apply_crop(self, img: Image.Image) -> Image.Image:
        if not self.crop_size:
            return img
        target_w, target_h = self.crop_size
        if self.crop_mode == "face":
            return self._face_crop(img, target_w, target_h)
        return self._center_crop(img, target_w, target_h)

    # ------------------------------------------------------------------
    # Image save
    # ------------------------------------------------------------------

    def _save_image(self, img_data: bytes) -> bool:
        """Save raw encoded image bytes (archive members, PDF XObjects)."""
        try:
            img = Image.open(io.BytesIO(img_data))
            img.load()  # force decode before format is lost
            return self._save_pil(img, fmt_hint=img.format)
        except Exception as e:
            self._log(f"  ✗ Image error: {e}")
            return False

    def _save_pil(self, img: Image.Image, fmt_hint=None) -> bool:
        """Size-filter, crop and write a PIL image."""
        try:
            if img.width < self.min_width or img.height < self.min_height:
                return False

            img = self._apply_crop(img)

            fmt = (fmt_hint or img.format or 'png').lower()
            if fmt == 'jpeg':
                fmt = 'jpg'
            if fmt not in ('jpg', 'png', 'gif', 'webp', 'bmp'):
                fmt = 'png'

            filename = f"{self.current_file_counter:04d}.{fmt}"
            filepath = self.current_source_dir / filename

            save_img = img.convert("RGB") if fmt == 'jpg' else img
            save_img.save(filepath)

            self._log(f"  ✓ {filename}  ({img.width}×{img.height})")
            self.total_extracted += 1
            self.current_file_counter += 1
            return True

        except Exception as e:
            self._log(f"  ✗ Image error: {e}")
            return False

    # ------------------------------------------------------------------
    # Format extractors
    # ------------------------------------------------------------------

    # --- PDF tiling helpers -------------------------------------------

    @staticmethod
    def _tiles_adjacent(a, b, tol: float = 2.0) -> bool:
        """True if two placement rects sit edge-to-edge like scan strips.

        Requires the shared edge to line up AND the perpendicular extent to
        match, so genuinely separate photos that merely touch aren't merged.
        """
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a, b
        # Vertically stacked: same left/right edges, one's bottom == other's top
        if abs(ax0 - bx0) <= tol and abs(ax1 - bx1) <= tol:
            if abs(ay1 - by0) <= tol or abs(by1 - ay0) <= tol:
                return True
        # Horizontally adjacent: same top/bottom edges, touching sides
        if abs(ay0 - by0) <= tol and abs(ay1 - by1) <= tol:
            if abs(ax1 - bx0) <= tol or abs(bx1 - ax0) <= tol:
                return True
        return False

    @classmethod
    def _group_tiles(cls, rects, tol: float = 2.0):
        """Union-find grouping of placement rects into tiled clusters."""
        n = len(rects)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for i in range(n):
            for j in range(i + 1, n):
                if cls._tiles_adjacent(rects[i], rects[j], tol):
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[rj] = ri

        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)
        return list(groups.values())

    def _stitch_tiles(self, doc, infos, idxs):
        """Reassemble tiled strips into the single image they represent.

        Returns a PIL image, or None if the tiles don't cleanly cover their
        bounding box (in which case the caller keeps them separate).
        """
        members = [infos[i] for i in idxs]
        rects = [m['bbox'] for m in members]
        x0 = min(r[0] for r in rects)
        y0 = min(r[1] for r in rects)
        x1 = max(r[2] for r in rects)
        y1 = max(r[3] for r in rects)
        union_w, union_h = x1 - x0, y1 - y0
        if union_w <= 0 or union_h <= 0:
            return None

        # Only stitch if the pieces actually tile the region (no gaps/overlaps)
        covered = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)
        if abs(covered - union_w * union_h) > 0.02 * union_w * union_h:
            return None

        # Pixels per PDF point, taken from the densest tile
        scale_x = max(m['width'] / max(1e-6, m['bbox'][2] - m['bbox'][0]) for m in members)
        scale_y = max(m['height'] / max(1e-6, m['bbox'][3] - m['bbox'][1]) for m in members)
        canvas_w = max(1, round(union_w * scale_x))
        canvas_h = max(1, round(union_h * scale_y))

        canvas = Image.new('RGB', (canvas_w, canvas_h))
        for m in members:
            raw = doc.extract_image(m['xref'])
            tile = Image.open(io.BytesIO(raw['image']))
            tile.load()
            tile = tile.convert('RGB')

            bx0, by0, bx1, by1 = m['bbox']
            px = round((bx0 - x0) * scale_x)
            py = round((by0 - y0) * scale_y)
            tw = max(1, round((bx1 - bx0) * scale_x))
            th = max(1, round((by1 - by0) * scale_y))
            if tile.size != (tw, th):
                tile = tile.resize((tw, th), Image.LANCZOS)
            canvas.paste(tile, (px, py))

        return canvas

    def extract_from_pdf(self, filepath: Path) -> int:
        if not HAS_PYMUPDF:
            self._log(f"Skipping PDF (PyMuPDF not installed): {filepath.name}")
            return 0
        self._log(f"\nProcessing PDF: {filepath.name}  (mode={self.pdf_mode})")
        self._setup_source_folder(filepath.name)

        stitched_pages = 0
        try:
            doc = fitz.open(filepath)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render mode: rasterize the whole page as it appears
                if self.pdf_mode == 'render':
                    pix = page.get_pixmap(dpi=self.pdf_render_dpi)
                    self._save_pil(Image.frombytes(
                        'RGB', (pix.width, pix.height), pix.samples), fmt_hint='png')
                    continue

                # Raw mode: every embedded image XObject, as-is
                if self.pdf_mode == 'raw':
                    for img in page.get_images():
                        self._save_image(doc.extract_image(img[0])['image'])
                    continue

                # Stitch mode (default): reassemble scan strips into pages
                try:
                    infos = page.get_image_info(xrefs=True)
                except Exception:
                    infos = []
                infos = [m for m in infos if m.get('xref')]

                if not infos:
                    for img in page.get_images():
                        self._save_image(doc.extract_image(img[0])['image'])
                    continue

                rects = [m['bbox'] for m in infos]
                for idxs in self._group_tiles(rects):
                    if len(idxs) > 1:
                        merged = self._stitch_tiles(doc, infos, idxs)
                        if merged is not None:
                            if self._save_pil(merged, fmt_hint='png'):
                                stitched_pages += 1
                            continue
                    # Single image, or tiles that didn't cleanly cover
                    for i in idxs:
                        self._save_image(doc.extract_image(infos[i]['xref'])['image'])

            doc.close()

            if stitched_pages:
                self._log(f"  ↳ reassembled {stitched_pages} tiled page(s) "
                          f"from split strips")

        except Exception as e:
            self._log(f"  Error reading PDF: {e}")
        return self.current_file_counter

    def extract_from_epub(self, filepath: Path) -> int:
        self._log(f"\nProcessing EPUB: {filepath.name}")
        self._setup_source_folder(filepath.name)
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for name in zf.namelist():
                    if any(name.lower().endswith(e) for e in ('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        self._save_image(zf.read(name))
        except Exception as e:
            self._log(f"  Error reading EPUB: {e}")
        return self.current_file_counter

    def extract_from_mobi(self, filepath: Path) -> int:
        self._log(f"\nProcessing MOBI: {filepath.name}")
        self._setup_source_folder(filepath.name)
        # AZW3/MOBI8 can be ZIP-like
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for name in zf.namelist():
                    if any(name.lower().endswith(e) for e in ('.jpg', '.jpeg', '.png', '.gif')):
                        self._save_image(zf.read(name))
            return self.current_file_counter
        except Exception:
            pass
        # Raw MOBI: scan for image byte signatures
        try:
            data = filepath.read_bytes()
            for sig, end_sig in (
                (b'\xFF\xD8\xFF', b'\xFF\xD9'),
                (b'\x89PNG\r\n\x1a\n', b'IEND\xaeB`\x82'),
            ):
                pos = 0
                while True:
                    pos = data.find(sig, pos)
                    if pos == -1:
                        break
                    end_pos = data.find(end_sig, pos + len(sig))
                    if end_pos != -1:
                        self._save_image(data[pos: end_pos + len(end_sig)])
                    pos += 1
        except Exception as e:
            self._log(f"  Error reading MOBI: {e}")
        return self.current_file_counter

    def extract_from_archive(self, filepath: Path) -> int:
        """Extract images from any archive container (CBZ/CBR/CB7/CBT,
        ZIP/RAR/7Z/TAR). The real format is sniffed from magic bytes, so
        mislabeled files ("cbr" that is really a zip, etc.) just work."""
        fmt = sniff_format(filepath)

        # Misnamed documents route to their real handlers
        if fmt == 'pdf':
            self._log(f"({filepath.name} is actually a PDF)")
            return self.extract_from_pdf(filepath)
        if fmt == 'mobi':
            self._log(f"({filepath.name} is actually a MOBI)")
            return self.extract_from_mobi(filepath)

        if not fmt:
            # Fall back to what the extension claims
            ext = filepath.suffix.lower()
            fmt = {'.cbz': 'zip', '.zip': 'zip', '.cbr': 'rar', '.rar': 'rar',
                   '.cb7': '7z', '.7z': '7z', '.cbt': 'tar', '.tar': 'tar'}.get(ext, '')
        if not fmt:
            self._log(f"Skipping {filepath.name}: unrecognized format")
            return 0

        self._log(f"\nProcessing archive ({fmt.upper()}): {filepath.name}")
        self._setup_source_folder(filepath.name)

        def is_image(name: str) -> bool:
            return name.lower().endswith(ARCHIVE_IMAGE_EXTS)

        try:
            if fmt == 'zip':
                with zipfile.ZipFile(filepath, 'r') as zf:
                    for name in sorted(zf.namelist()):
                        if is_image(name):
                            self._save_image(zf.read(name))

            elif fmt == 'rar':
                status = setup_rar_backend()
                if status:
                    self._log(f"  ✗ Cannot extract RAR: {status}")
                    return 0
                with rarfile.RarFile(filepath, 'r') as rf:
                    for name in sorted(rf.namelist()):
                        if is_image(name):
                            self._save_image(rf.read(name))

            elif fmt == '7z':
                if not HAS_PY7ZR:
                    self._log("  ✗ Cannot extract 7z: py7zr not installed (pip install py7zr)")
                    return 0
                import tempfile
                with py7zr.SevenZipFile(filepath, 'r') as zf:
                    targets = sorted(n for n in zf.getnames() if is_image(n))
                    if targets:
                        # py7zr 1.x extracts to disk only — use a temp dir
                        with tempfile.TemporaryDirectory() as tmp:
                            zf.extract(path=tmp, targets=targets)
                            for name in targets:
                                member = Path(tmp) / name
                                if member.is_file():
                                    self._save_image(member.read_bytes())

            elif fmt == 'tar':
                with tarfile.open(filepath, 'r:*') as tf:
                    for member in sorted(tf.getmembers(), key=lambda m: m.name):
                        if member.isfile() and is_image(member.name):
                            fobj = tf.extractfile(member)
                            if fobj:
                                self._save_image(fobj.read())

        except Exception as e:
            self._log(f"  Error reading archive: {e}")

        return self.current_file_counter

    def process_file(self, filepath: Path) -> int:
        ext = filepath.suffix.lower()
        if ext == '.pdf':
            return self.extract_from_pdf(filepath)
        if ext == '.epub':
            return self.extract_from_epub(filepath)
        if ext in ('.mobi', '.azw', '.azw3'):
            return self.extract_from_mobi(filepath)
        if ext in ARCHIVE_EXTENSIONS:
            return self.extract_from_archive(filepath)
        return 0

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process_paths(self, paths, progress_callback=None) -> dict:
        """Process a list of file paths and/or directories.

        Parameters
        ----------
        paths             : iterable of str/Path
        progress_callback : callable(completed, total, current_filename)

        Returns dict with total_files, total_extracted, output_dir.
        """
        file_list = []
        for p in paths:
            p = Path(p)
            if p.is_dir():
                file_list.extend(
                    f for f in p.rglob('*')
                    if f.suffix.lower() in SUPPORTED_EXTENSIONS
                )
            elif p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                file_list.append(p)

        total = len(file_list)
        self._log(f"Found {total} supported file(s) to process")

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i, total, filepath.name)
            self.process_file(filepath)

        if progress_callback:
            progress_callback(total, total, "")

        # Be explicit when the requested framing couldn't be honoured — the
        # source simply lacked pixels, and silently ignoring it looks like a bug
        if self._framing_clamped:
            pct = 100 * self._framing_clamped / max(1, self._face_crops)
            self._log(
                f"⚠️  {self._framing_clamped}/{self._face_crops} face crops ({pct:.0f}%) "
                f"were framed wider than requested — the source lacks the resolution "
                f"for this framing at {self.crop_size[0]}×{self.crop_size[1]}.")
            self._log(
                "    Fix: choose a smaller crop size, a wider framing preset, "
                "or enable 'Allow upscaling' to accept softer images.")

        return {
            "total_files":     total,
            "total_extracted": self.total_extracted,
            "output_dir":      str(self.output_dir.absolute()),
            "face_crops":      self._face_crops,
            "framing_clamped": self._framing_clamped,
        }
