import io
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from PIL import Image, ImageDraw  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

from core.image_index import (  # noqa: E402
    ImageIndex,
    IndexCorrupt,
    dhash64,
    hash_image,
    pixel_sha256,
    rebuild_index,
)


def noise(path, size=(320, 240), seed=1, mode="RGB", **save_kw):
    arr = np.random.default_rng(seed).integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    img = Image.fromarray(arr).convert(mode) if mode != "RGB" else Image.fromarray(arr)
    img.save(path, **save_kw)
    return Path(path)


def scene(size=(300, 400), seed=0):
    """A smooth picture with structure, so its dHash is stable under resizing."""
    w, h = size
    x = np.linspace(0, 255, w)[None, :].repeat(h, 0)
    y = np.linspace(0, 255, h)[:, None].repeat(w, 1)
    img = Image.fromarray(np.stack([x, y, 255 - x], -1).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    for _ in range(6):
        cx, cy, r = rng.integers(0, w), rng.integers(0, h), rng.integers(20, 80)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tuple(int(v) for v in rng.integers(0, 255, 3)))
    return img


def ham(a, b):
    return bin(a ^ b).count("1")


def open_(path):
    return Image.open(path)


# ---------------------------------------------------------------- hashing

def test_pixel_hash_survives_metadata_resave_file_hash_does_not(tmp_path):
    img = scene()
    plain, tagged = tmp_path / "plain.png", tmp_path / "tagged.png"
    img.save(plain)
    info = PngInfo()
    info.add_text("parameters", "a prompt\nSteps: 20")
    img.save(tagged, pnginfo=info)
    a, b = hash_image(str(plain)), hash_image(str(tagged))
    assert a["pixel_sha256"] == b["pixel_sha256"]
    assert a["file_sha256"] != b["file_sha256"]
    assert a["has_meta"] is False and b["has_meta"] is True
    assert b["parameters"].startswith("a prompt")


def test_pixel_hash_changes_with_one_pixel(tmp_path):
    img = scene()
    other = img.copy()
    other.putpixel((5, 5), (0, 0, 0))
    assert pixel_sha256(img) != pixel_sha256(other)


def test_dhash_survives_4x_resize():
    small = scene((300, 400))
    big = small.resize((1200, 1600), Image.LANCZOS)
    assert ham(dhash64(small), dhash64(big)) <= 2


def test_dhash_far_apart_for_different_images():
    assert ham(dhash64(scene(seed=1)), dhash64(scene(seed=2))) > 16


def test_unusual_images_hash_and_rotation_applied(tmp_path):
    Image.new("RGBA", (100, 80), (10, 20, 30, 0)).save(tmp_path / "a.png")
    Image.new("P", (100, 80), 5).save(tmp_path / "p.png")
    Image.new("I;16", (100, 80), 4000).save(tmp_path / "d.png")
    for name in ("a.png", "p.png", "d.png"):
        r = hash_image(str(tmp_path / name))
        assert r["error"] is None and r["pixel_sha256"], name
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (400, 200), (200, 0, 0)).save(tmp_path / "r.jpg", exif=exif.tobytes())
    r = hash_image(str(tmp_path / "r.jpg"))
    assert (r["width"], r["height"]) == (200, 400)


def test_jpeg_usercomment_counts_as_metadata(tmp_path):
    exif = Image.Exif()
    exif.get_ifd(0x8769)[37510] = b"ASCII\x00\x00\x00a prompt, Steps: 20"
    scene().save(tmp_path / "c.jpg", exif=exif.tobytes())
    scene().save(tmp_path / "n.jpg")
    assert hash_image(str(tmp_path / "c.jpg"))["has_meta"] is True
    assert hash_image(str(tmp_path / "n.jpg"))["has_meta"] is False


def test_thumbnail_is_jpeg_256(tmp_path):
    scene((1000, 500)).save(tmp_path / "w.png")
    thumb = hash_image(str(tmp_path / "w.png"))["thumb"]
    t = Image.open(io.BytesIO(thumb))
    assert t.format == "JPEG" and t.size == (256, 128)


# ---------------------------------------------------------------- scanning

def make_lib(root, n=4):
    root.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        scene(seed=i).save(root / f"img{i}.png")


def test_scan_skips_excluded_folders(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib / "keep", 1)
    for skipped in ("cropped__1024x1024", "upscaled__4096px_x", "civitai_ready", "_duplicates_trash"):
        make_lib(lib / skipped, 1)
    idx = ImageIndex(tmp_path / "idx.db")
    stats = idx.scan([str(lib)], workers=1)
    paths = [r.path for r in idx.rows([str(lib)])]
    assert stats.found == 1 and len(paths) == 1 and "keep" in paths[0]
    idx.close()


def test_rescan_reads_only_changed_files(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib)
    idx = ImageIndex(tmp_path / "idx.db")
    s1 = idx.scan([str(lib)], workers=1)
    assert (s1.hashed, s1.cached) == (4, 0)
    s2 = idx.scan([str(lib)], workers=1)
    assert (s2.hashed, s2.cached) == (0, 4)
    time.sleep(0.05)
    scene(seed=99).save(lib / "img0.png")
    s3 = idx.scan([str(lib)], workers=1)
    assert (s3.hashed, s3.cached) == (1, 3)
    idx.close()


def test_removed_files_dropped_on_rescan(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib)
    idx = ImageIndex(tmp_path / "idx.db")
    idx.scan([str(lib)], workers=1)
    (lib / "img3.png").unlink()
    stats = idx.scan([str(lib)], workers=1)
    assert stats.removed == 1 and len(idx.rows([str(lib)])) == 3
    idx.close()


def test_unreadable_file_recorded_but_not_returned(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib, 2)
    (lib / "bad.png").write_bytes(b"not an image")
    idx = ImageIndex(tmp_path / "idx.db")
    stats = idx.scan([str(lib)], workers=1)
    assert stats.errors == 1
    assert all(not r.path.endswith("bad.png") for r in idx.rows([str(lib)]))
    idx.close()


def test_missing_folder_reported(tmp_path):
    idx = ImageIndex(tmp_path / "idx.db")
    stats = idx.scan([str(tmp_path / "nope")], workers=1)
    assert stats.missing_folders == (str((tmp_path / "nope").resolve()),)
    idx.close()


def test_nested_folders_index_each_file_once(tmp_path):
    a = tmp_path / "a"
    make_lib(a, 1)
    make_lib(a / "b", 2)
    idx = ImageIndex(tmp_path / "idx.db")
    stats = idx.scan([str(a), str(a / "b")], workers=1)
    rows = idx.rows([str(a), str(a / "b")])
    assert stats.found == 3 and len(rows) == 3
    assert {r.root for r in rows} == {str(a.resolve())}
    idx.close()


def test_scan_runs_in_a_real_process_pool(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib)
    idx = ImageIndex(tmp_path / "idx.db")
    idx.scan([str(lib)], workers=2)
    rows = idx.rows([str(lib)])
    assert len(rows) == 4 and all(r.pixel_sha256 for r in rows)
    idx.close()


def test_cancel_keeps_rows_and_next_scan_finishes(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib, 6)
    idx = ImageIndex(tmp_path / "idx.db")
    seen = []
    stats = idx.scan([str(lib)], progress=lambda d, t, n: seen.append(d),
                     cancel=lambda: bool(seen), workers=1)
    assert stats.cancelled
    stats2 = idx.scan([str(lib)], workers=1)
    assert not stats2.cancelled and len(idx.rows([str(lib)])) == 6
    idx.close()


def test_dhash_roundtrips_through_sqlite_unsigned(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib, 3)
    idx = ImageIndex(tmp_path / "idx.db")
    idx.scan([str(lib)], workers=1)
    for r in idx.rows([str(lib)]):
        assert 0 <= r.dhash < 2 ** 64
        assert r.dhash == dhash64(Image.open(r.path))
    idx.close()


def test_thumbnail_lookup(tmp_path):
    lib = tmp_path / "lib"
    make_lib(lib, 1)
    idx = ImageIndex(tmp_path / "idx.db")
    idx.scan([str(lib)], workers=1)
    path = idx.rows([str(lib)])[0].path
    assert Image.open(io.BytesIO(idx.thumbnail(path))).format == "JPEG"
    idx.close()


def test_not_duplicate_pairs_roundtrip(tmp_path):
    idx = ImageIndex(tmp_path / "idx.db")
    idx.mark_not_duplicates("b", "a")
    assert idx.not_duplicate_pairs() == {("a", "b")}
    idx.close()


def test_corrupt_index_raises_and_rebuild_moves_it_aside(tmp_path):
    db = tmp_path / "idx.db"
    db.write_bytes(b"this is not sqlite" * 100)
    with pytest.raises(IndexCorrupt):
        ImageIndex(db)
    rebuild_index(db)
    assert list(tmp_path.glob("image_index.broken-*.db"))
    ImageIndex(db).close()
