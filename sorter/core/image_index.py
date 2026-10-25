"""
Image Index — a SQLite record of every image under the folders you scan.

One row per file: size and modified time (to skip unchanged files on the
next scan), resolution, three hashes and a small thumbnail.

  file_sha256   "are these the exact same bytes?"
  pixel_sha256  "are these the exact same picture?" — survives metadata
                edits and re-saves, not resizes
  dhash         "does this look like the same picture?" — survives resizing
                and re-encoding (64-bit difference hash)

The Duplicate Finder groups on these; the Source Finder will search the
same rows. Hashing runs in a process pool: every image has to be fully
decoded once, which is the slow part on a 200 GB library.
"""

import hashlib
import io
import os
import sqlite3
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple

import numpy as np
from PIL import Image, ImageOps

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
TRASH_DIR = "_duplicates_trash"
THUMB_EDGE = 256
THUMB_QUALITY = 80
DEFAULT_DB = Path(__file__).resolve().parent.parent / "image_index.db"
# Each worker can hold ~1 GB while decoding a 150 MP image, and re-imports
# the launching script on Windows; more than 8 rarely helps a disk-bound scan
MAX_WORKERS = 8


def default_workers() -> int:
    return max(1, min(MAX_WORKERS, (os.cpu_count() or 2) - 1))

# Sorter's own output folders are deliberate copies, never duplicates
_EXCLUDED_PREFIXES = ("cropped__", "upscaled__")
_EXCLUDED_NAMES = {"civitai_ready", TRASH_DIR}
_BATCH = 200
_META_KEYS = ("prompt", "workflow", "parameters")
_EXIF_IFD, _USER_COMMENT = 0x8769, 37510
_EXIF_MAKE, _EXIF_MODEL = 0x010F, 0x0110       # where ComfyUI puts the workflow in WEBP/JPEG


def is_excluded_dir(name: str) -> bool:
    return name in _EXCLUDED_NAMES or name.startswith(_EXCLUDED_PREFIXES)


@dataclass(frozen=True)
class ImageRow:
    path: str
    root: str
    size: int
    mtime: float
    width: int
    height: int
    file_sha256: str
    pixel_sha256: str
    dhash: int              # unsigned 64-bit
    has_meta: bool
    parameters: Optional[str]

    @property
    def pixels(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class ScanStats:
    found: int
    hashed: int
    cached: int
    errors: int
    removed: int
    missing_folders: Tuple[str, ...]
    cancelled: bool


class IndexCorrupt(Exception):
    """The index file exists but isn't a usable SQLite database."""


# ----------------------------------------------------------------------
# Hashing (runs in worker processes — keep it module-level and import-light)
# ----------------------------------------------------------------------

def _rgb(img: Image.Image) -> Image.Image:
    if img.mode.startswith("I") or img.mode == "F":
        arr = np.asarray(img, dtype=np.float64)
        if arr.max(initial=0) > 255:
            arr = arr / 257.0
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L").convert("RGB")
    if img.mode == "P":
        img = img.convert("RGBA")
    return img if img.mode == "RGB" else img.convert("RGB")


def pixel_sha256(img: Image.Image) -> str:
    rgb = _rgb(ImageOps.exif_transpose(img))
    digest = hashlib.sha256(f"{rgb.width}x{rgb.height}|".encode("ascii"))
    digest.update(rgb.tobytes())
    return digest.hexdigest()


def dhash64(img: Image.Image) -> int:
    small = _rgb(img).convert("L").resize((9, 8), Image.LANCZOS)
    px = list(small.getdata())
    value = 0
    for y in range(8):
        row = px[y * 9:(y + 1) * 9]
        for x in range(8):
            value = (value << 1) | (1 if row[x] > row[x + 1] else 0)
    return value


def _has_meta(img: Image.Image) -> bool:
    if any(isinstance(img.info.get(k), str) and img.info.get(k) for k in _META_KEYS):
        return True
    try:
        exif = img.getexif()
        comment = exif.get_ifd(_EXIF_IFD).get(_USER_COMMENT)
        if comment and str(comment).strip("\x00 ").replace("ASCII", "").strip("\x00 "):
            return True
        for tag in (_EXIF_MAKE, _EXIF_MODEL):
            text = str(exif.get(tag) or "").lower()
            if text.startswith(("prompt:", "workflow:")):
                return True
    except Exception:
        pass
    return False


def hash_image(path: str) -> dict:
    """Everything the index stores about one file. Never raises."""
    out = {"path": path, "size": 0, "mtime": 0.0, "width": 0, "height": 0,
           "file_sha256": None, "pixel_sha256": None, "dhash": None,
           "has_meta": False, "parameters": None, "thumb": None, "error": None}
    try:
        st = os.stat(path)
        out["size"], out["mtime"] = st.st_size, st.st_mtime
        data = Path(path).read_bytes()
        out["file_sha256"] = hashlib.sha256(data).hexdigest()
        img = Image.open(io.BytesIO(data))
        img.load()
        out["has_meta"] = _has_meta(img)
        params = img.info.get("parameters")
        out["parameters"] = params if isinstance(params, str) else None
        oriented = ImageOps.exif_transpose(img)
        out["width"], out["height"] = oriented.size
        rgb = _rgb(oriented)
        out["pixel_sha256"] = pixel_sha256(rgb)
        out["dhash"] = dhash64(rgb)
        thumb = rgb.copy()
        thumb.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.LANCZOS)
        buf = io.BytesIO()
        thumb.save(buf, "JPEG", quality=THUMB_QUALITY)
        out["thumb"] = buf.getvalue()
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        out["file_sha256"] = out["pixel_sha256"] = out["dhash"] = None
    return out


# ----------------------------------------------------------------------
# The index
# ----------------------------------------------------------------------

def _signed(v: Optional[int]) -> Optional[int]:
    return None if v is None else (v - (1 << 64) if v >= (1 << 63) else v)


def _unsigned(v: Optional[int]) -> Optional[int]:
    return None if v is None else (v + (1 << 64) if v < 0 else v)


def _norm(folder: str) -> str:
    return str(Path(folder).resolve())


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("\\/") + os.sep)


def walk_images(folder: str) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not is_excluded_dir(d)]
        for name in filenames:
            if os.path.splitext(name)[1].lower() in IMAGE_EXTS:
                yield os.path.join(dirpath, name)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    path TEXT PRIMARY KEY, root TEXT, size INTEGER, mtime REAL,
    width INTEGER, height INTEGER, file_sha256 TEXT, pixel_sha256 TEXT,
    dhash INTEGER, has_meta INTEGER, parameters TEXT, thumb BLOB, error TEXT);
CREATE INDEX IF NOT EXISTS images_pixel ON images(pixel_sha256);
CREATE TABLE IF NOT EXISTS not_duplicates (a TEXT, b TEXT, PRIMARY KEY (a, b));
"""
_COLUMNS = ("path", "root", "size", "mtime", "width", "height", "file_sha256",
            "pixel_sha256", "dhash", "has_meta", "parameters", "thumb", "error")


def rebuild_index(db_path: Path = DEFAULT_DB) -> Path:
    """Move a damaged index aside (with its -wal/-shm files) so a new one
    can be built. Returns where the old file went."""
    db_path = Path(db_path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    aside = db_path.with_name(f"image_index.broken-{stamp}.db")
    if db_path.exists():
        os.replace(db_path, aside)
    for suffix in ("-wal", "-shm"):
        extra = Path(str(db_path) + suffix)
        if extra.exists():
            os.replace(extra, Path(str(aside) + suffix))
    return aside


class ImageIndex:
    """Thread-safe: one connection, every call under one lock."""

    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        try:
            conn.executescript(_SCHEMA)
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError as e:
            conn.close()
            raise IndexCorrupt(str(e)) from e
        self._conn = conn

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------ scan

    def scan(self, folders: List[str], progress: Optional[Callable[[int, int, str], None]] = None,
             cancel: Optional[Callable[[], bool]] = None,
             workers: Optional[int] = None) -> ScanStats:
        roots = sorted({_norm(f) for f in folders}, key=len)
        missing = tuple(r for r in roots if not os.path.isdir(r))
        outer: List[str] = []
        for r in roots:
            if r not in missing and not any(_under(r, o) for o in outer):
                outer.append(r)

        files: Dict[str, Tuple[str, os.stat_result]] = {}
        for root in outer:
            for path in walk_images(root):
                try:
                    files[path] = (root, os.stat(path))
                except OSError:
                    continue

        with self._lock:
            known = {row[0]: row[1:] for row in self._conn.execute(
                "SELECT path, size, mtime, root FROM images")}
        known = {p: v for p, v in known.items() if any(_under(p, r) for r in outer)}

        todo, cached, reroot = [], 0, []
        for path, (root, st) in files.items():
            prev = known.get(path)
            if prev and prev[0] == st.st_size and prev[1] == st.st_mtime:
                cached += 1
                if prev[2] != root:
                    reroot.append((root, path))
            else:
                todo.append(path)
        gone = [p for p in known if p not in files]

        with self._lock:
            if gone:
                self._conn.executemany("DELETE FROM images WHERE path = ?", [(p,) for p in gone])
            if reroot:
                self._conn.executemany("UPDATE images SET root = ? WHERE path = ?", reroot)
            self._conn.commit()

        hashed = errors = 0
        cancelled = False
        batch: List[tuple] = []

        def store(result: dict):
            nonlocal hashed, errors
            hashed += 1
            if result["error"]:
                errors += 1
            result["root"] = files[result["path"]][0]
            result["dhash"] = _signed(result["dhash"])
            result["has_meta"] = int(bool(result["has_meta"]))
            batch.append(tuple(result[c] for c in _COLUMNS))
            if len(batch) >= _BATCH:
                self._flush(batch)

        workers = workers or default_workers()
        total = len(todo)
        if workers <= 1 or total <= 1:
            for path in todo:
                store(hash_image(path))
                if progress:
                    progress(hashed, total, os.path.basename(path))
                if cancel and cancel():
                    cancelled = True
                    break
        else:
            pool = ProcessPoolExecutor(max_workers=min(workers, total))
            try:
                futures = [pool.submit(hash_image, p) for p in todo]
                for fut in as_completed(futures):
                    result = fut.result()
                    store(result)
                    if progress:
                        progress(hashed, total, os.path.basename(result["path"]))
                    if cancel and cancel():
                        cancelled = True
                        break
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
        self._flush(batch)

        return ScanStats(found=len(files), hashed=hashed, cached=cached, errors=errors,
                         removed=len(gone), missing_folders=missing, cancelled=cancelled)

    def _flush(self, batch: List[tuple]) -> None:
        if not batch:
            return
        marks = ",".join("?" * len(_COLUMNS))
        with self._lock:
            self._conn.executemany(
                f"INSERT OR REPLACE INTO images ({','.join(_COLUMNS)}) VALUES ({marks})", batch)
            self._conn.commit()
        batch.clear()

    # ------------------------------------------------------------------ queries

    def rows(self, folders: List[str]) -> List[ImageRow]:
        roots = [_norm(f) for f in folders]
        with self._lock:
            found = self._conn.execute(
                "SELECT path, root, size, mtime, width, height, file_sha256, pixel_sha256, "
                "dhash, has_meta, parameters FROM images WHERE error IS NULL").fetchall()
        return [ImageRow(path=r[0], root=r[1], size=r[2], mtime=r[3], width=r[4], height=r[5],
                         file_sha256=r[6], pixel_sha256=r[7], dhash=_unsigned(r[8]),
                         has_meta=bool(r[9]), parameters=r[10])
                for r in found if any(_under(r[0], root) for root in roots)]

    def thumbnail(self, path: str) -> Optional[bytes]:
        with self._lock:
            row = self._conn.execute("SELECT thumb FROM images WHERE path = ?", (path,)).fetchone()
        return row[0] if row else None

    def drop(self, paths: Iterable[str]) -> None:
        with self._lock:
            self._conn.executemany("DELETE FROM images WHERE path = ?", [(p,) for p in paths])
            self._conn.commit()

    def mark_not_duplicates(self, pixel_a: str, pixel_b: str) -> None:
        a, b = sorted((pixel_a, pixel_b))
        with self._lock:
            self._conn.execute("INSERT OR IGNORE INTO not_duplicates (a, b) VALUES (?, ?)", (a, b))
            self._conn.commit()

    def not_duplicate_pairs(self) -> Set[Tuple[str, str]]:
        with self._lock:
            return {(a, b) for a, b in self._conn.execute("SELECT a, b FROM not_duplicates")}
