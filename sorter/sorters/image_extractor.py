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
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

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


class ImageExtractorSorter:
    """Extract images from document/archive files with optional auto-crop."""

    def __init__(self, logger, min_width=512, min_height=512,
                 output_dir="extracted_images", folder_prefix="",
                 crop_size=None, crop_mode="center"):
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
        """
        self.logger = logger
        self.min_width = min_width
        self.min_height = min_height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.folder_prefix = folder_prefix
        self.crop_size = crop_size
        self.crop_mode = crop_mode if crop_size else "none"

        self.total_extracted = 0
        self.current_source_dir = None
        self.current_file_counter = 0

        self._face_detector = None
        if self.crop_mode == "face":
            if HAS_MEDIAPIPE:
                self._init_face_detector()
            else:
                self._log("Warning: mediapipe not installed — face crop will fall back to center crop.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_face_detector(self):
        mp_face = mp.solutions.face_detection
        # model_selection=1 uses the full-range model (better for varied angles/distances)
        self._face_detector = mp_face.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.5
        )

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
        """Detect largest face, center the crop around it.
        Falls back to center crop when no face is found or mediapipe unavailable."""
        if not HAS_MEDIAPIPE or self._face_detector is None:
            return self._center_crop(img, target_w, target_h)

        try:
            import numpy as np
            rgb = np.array(img.convert("RGB"))
            results = self._face_detector.process(rgb)

            if not results.detections:
                return self._center_crop(img, target_w, target_h)

            src_w, src_h = img.size

            # Pick the largest face by relative bounding box area
            best = max(
                results.detections,
                key=lambda d: (
                    d.location_data.relative_bounding_box.width *
                    d.location_data.relative_bounding_box.height
                )
            )
            bb = best.location_data.relative_bounding_box
            face_cx = (bb.xmin + bb.width / 2) * src_w
            face_cy = (bb.ymin + bb.height / 2) * src_h
            face_h_px = bb.height * src_h

            # Pad to ~1.8× face height so hair/neck are included
            needed_h = face_h_px * 1.8
            scale = max(target_w / src_w, target_h / src_h,
                        target_h / needed_h)

            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img_scaled = img.resize((new_w, new_h), Image.LANCZOS)

            cx = int(face_cx * scale)
            cy = int(face_cy * scale)

            left = max(0, min(cx - target_w // 2, new_w - target_w))
            top  = max(0, min(cy - target_h // 2, new_h - target_h))

            return img_scaled.crop((left, top, left + target_w, top + target_h))

        except Exception as e:
            self._log(f"  Face detection error ({e}), falling back to center crop")
            return self._center_crop(img, target_w, target_h)

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
        try:
            img = Image.open(io.BytesIO(img_data))
            img.load()  # force decode before format is lost

            if img.width < self.min_width or img.height < self.min_height:
                return False

            img = self._apply_crop(img)

            fmt = (img.format or 'png').lower()
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

    def extract_from_pdf(self, filepath: Path) -> int:
        if not HAS_PYMUPDF:
            self._log(f"Skipping PDF (PyMuPDF not installed): {filepath.name}")
            return 0
        self._log(f"\nProcessing PDF: {filepath.name}")
        self._setup_source_folder(filepath.name)
        try:
            doc = fitz.open(filepath)
            for page_num in range(len(doc)):
                for img in doc[page_num].get_images():
                    self._save_image(doc.extract_image(img[0])["image"])
            doc.close()
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

        return {
            "total_files":     total,
            "total_extracted": self.total_extracted,
            "output_dir":      str(self.output_dir.absolute()),
        }
