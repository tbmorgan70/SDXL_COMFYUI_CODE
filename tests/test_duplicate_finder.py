import os
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from core.image_index import ImageRow  # noqa: E402
from sorters.duplicate_finder import find_sets, keeper_key  # noqa: E402


def row(path, w=832, h=1216, pixel=None, dhash=0, size=1000, meta=False, mtime=0.0):
    return ImageRow(path=path, root="R", size=size, mtime=mtime, width=w, height=h,
                    file_sha256=f"f-{path}", pixel_sha256=pixel or f"p-{path}", dhash=dhash,
                    has_meta=meta, parameters=None)


# ---------------------------------------------------------------- certain

def test_certain_groups_same_pixels_keeper_has_meta():
    a = row("a", pixel="P", size=17_000_000)               # post upscale, no metadata
    b = row("b", pixel="P", size=36_000_000, meta=True)    # Image Saver final
    certain, probable = find_sets([a, b])
    assert len(certain) == 1 and certain[0].keeper.path == "b" and certain[0].extras == [a]
    assert certain[0].kind == "certain" and certain[0].pretick and certain[0].distance == 0
    assert certain[0].reclaim_bytes == 17_000_000
    assert probable == []


@pytest.mark.parametrize("better,worse", [
    (dict(w=3328, h=4864), dict(w=832, h=1216, meta=True, size=10**9)),   # pixels first
    (dict(meta=True), dict(size=10**9)),                                  # then metadata
    (dict(size=2000), dict(size=1000)),                                   # then size
    (dict(mtime=1.0), dict(mtime=2.0)),                                   # then older
])
def test_keeper_order(better, worse):
    assert keeper_key(row("x", **better)) < keeper_key(row("y", **worse))


def test_keeper_order_falls_back_to_path():
    assert keeper_key(row("a")) < keeper_key(row("b"))


# ---------------------------------------------------------------- probable

def test_probable_4x_upscale_matched_and_preticked():
    big = row("final", w=3328, h=4864, dhash=0b1011, meta=True)
    small = row("post_sampler", w=832, h=1216, dhash=0b1111)          # distance 1
    _, probable = find_sets([big, small])
    assert len(probable) == 1
    s = probable[0]
    assert s.kind == "probable" and s.keeper.path == "final" and s.extras == [small]
    assert s.distance == 1 and s.pretick


def test_scaled_pair_beyond_distance_2_is_not_preticked():
    # On the user's library, every 2x/4x pair at distance 3-6 was a different
    # picture (neighbouring img2img outputs); real upscales sat at 0-2.
    big = row("big", w=3328, h=4864, dhash=0)
    small = row("small", w=832, h=1216, dhash=0b11111)                 # 4x, distance 5
    _, probable = find_sets([big, small], "Normal")
    assert len(probable) == 1 and not probable[0].pretick
    near = row("near", w=832, h=1216, dhash=0b11)                       # 4x, distance 2
    _, probable = find_sets([big, near], "Normal")
    assert probable[0].pretick


@pytest.mark.parametrize("strictness,expected", [("Strict", 0), ("Normal", 1), ("Loose", 1)])
def test_strictness(strictness, expected):
    a, b = row("a", dhash=0), row("b", dhash=0b11111)                  # distance 5
    _, probable = find_sets([a, b], strictness)
    assert len(probable) == expected


def test_aspect_mismatch_never_matches():
    a, b = row("a", w=1024, h=1024, dhash=7), row("b", w=832, h=1216, dhash=7)
    assert find_sets([a, b]) == ([], [])


def test_no_chains():
    a = row("A", w=3328, h=4864, dhash=0)             # best
    b = row("B", w=1664, h=2432, dhash=0x0F)          # A-B 4
    c = row("C", w=832, h=1216, dhash=0xFF)           # B-C 4, A-C 8
    _, probable = find_sets([a, b, c], "Normal")
    assert len(probable) == 1
    assert probable[0].keeper.path == "A" and [r.path for r in probable[0].extras] == ["B"]


def test_certain_extras_not_in_probable():
    x = row("X", w=3328, h=4864, pixel="P", size=5000, dhash=0)
    x2 = row("X2", w=3328, h=4864, pixel="P", size=4000, dhash=0)
    y = row("Y", w=832, h=1216, dhash=1)
    certain, probable = find_sets([x, x2, y])
    assert certain[0].keeper.path == "X" and [r.path for r in certain[0].extras] == ["X2"]
    assert len(probable) == 1 and probable[0].keeper.path == "X"
    assert [r.path for r in probable[0].extras] == ["Y"]


def test_not_duplicates_excluded():
    a, b = row("a", pixel="pa", dhash=0), row("b", pixel="pb", dhash=1)
    assert find_sets([a, b], not_dupes={("pa", "pb")}) == ([], [])


def test_probable_sorted_closest_first():
    far_a, far_b = row("fa", dhash=0), row("fb", dhash=0b111)                  # distance 3
    near_a = row("na", dhash=0xFF00_0000_0000_0000)
    near_b = row("nb", dhash=0xFF00_0000_0000_0001)                           # distance 1
    _, probable = find_sets([far_a, far_b, near_a, near_b])
    assert [s.distance for s in probable] == [1, 3]


def test_twenty_thousand_rows_under_ten_seconds():
    rng = np.random.default_rng(0)
    hashes = rng.integers(0, 2**63, 20_000, dtype=np.int64).astype(np.uint64) * 2 + 1
    rows = [row(f"r{i}", dhash=int(h)) for i, h in enumerate(hashes)]
    t0 = time.perf_counter()
    find_sets(rows, "Loose")
    assert time.perf_counter() - t0 < 10


# ================================================================ trash / restore / empty

import json  # noqa: E402
from pathlib import Path  # noqa: E402

from PIL import Image  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

from core.image_index import TRASH_DIR, ImageIndex  # noqa: E402
from sorters.duplicate_finder import (  # noqa: E402
    LOG_NAME, empty_trash, restore_all, trash_sets, trash_summary, with_keeper)


def picture(seed=0, size=(120, 160)):
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8))


def save(img, path, meta=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    info = None
    if meta:
        info = PngInfo()
        info.add_text("parameters", "prompt\nSteps: 20")
    img.save(path, pnginfo=info)
    return path


def library(tmp_path, orig_name="orig.png", copy_name="copy.png"):
    """lib/sub/orig.png (with metadata, the keeper) + lib/sub/copy.png (+ copy.txt)."""
    lib = tmp_path / "lib"
    img = picture()
    orig = save(img, lib / "sub" / orig_name, meta=True)
    copy = save(img, lib / "sub" / copy_name)
    copy.with_suffix(".txt").write_text("caption", encoding="utf-8")
    index = ImageIndex(tmp_path / "idx.db")
    index.scan([str(lib)], workers=1)
    return lib, orig, copy, index


def certain_sets(index, lib):
    certain, _ = find_sets(index.rows([str(lib)]))
    return certain


def test_trash_moves_extra_with_sidecars_and_logs(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    result = trash_sets(certain_sets(index, lib))
    trash = lib / TRASH_DIR
    assert result.moved == [str(copy.resolve())] and result.skipped == []
    assert (trash / "sub" / "copy.png").exists() and (trash / "sub" / "copy.txt").exists()
    assert orig.exists() and not copy.exists() and not copy.with_suffix(".txt").exists()
    entry = json.loads((trash / LOG_NAME).read_text(encoding="utf-8").strip())
    assert entry["kind"] == "certain" and entry["original"] == str(copy.resolve())
    assert entry["keeper"] == str(orig.resolve()) and len(entry["sidecars"]) == 1
    index.close()


def test_trash_skips_changed_since_scan(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    st = copy.stat()
    os.utime(copy, (st.st_atime, st.st_mtime + 10))
    result = trash_sets(certain_sets(index, lib))
    assert result.moved == [] and result.skipped == [(str(copy.resolve()), "changed since scan")]
    assert copy.exists()
    index.close()


def test_trash_skips_set_when_keeper_missing(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    sets = certain_sets(index, lib)
    orig.unlink()
    result = trash_sets(sets)
    assert result.skipped == [(str(copy.resolve()), "keeper missing")] and copy.exists()
    index.close()


def test_trash_name_clash_gets_suffix(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))
    save(picture(), copy)
    index.scan([str(lib)], workers=1)
    result = trash_sets(certain_sets(index, lib))
    assert len(result.moved) == 1
    assert (lib / TRASH_DIR / "sub" / "copy_2.png").exists()
    index.close()


def test_unicode_names_trash_and_restore(tmp_path):
    lib, orig, copy, index = library(tmp_path, "Feelin' Lucky ✨.png", "Feelin' Lucky ✨ copy.png")
    trash_sets(certain_sets(index, lib))
    log = (lib / TRASH_DIR / LOG_NAME).read_text(encoding="utf-8")
    assert "Feelin' Lucky ✨ copy.png" in log
    result = restore_all([str(lib)])
    assert copy.exists() and len(result.moved) == 1
    index.close()


def test_restore_all_handles_taken_spot(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))
    save(picture(seed=5), copy)                     # something new now lives there
    restore_all([str(lib)])
    assert (lib / "sub" / "copy_restored.png").exists()
    assert np.array_equal(np.asarray(Image.open(copy)), np.asarray(picture(seed=5)))
    assert trash_summary([str(lib)]) == (0, 0)
    index.close()


def test_empty_deletes_only_logged_files(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    size = copy.stat().st_size + copy.with_suffix(".txt").stat().st_size
    trash_sets(certain_sets(index, lib))
    stray = save(picture(seed=9), lib / TRASH_DIR / "stray.png")
    result = empty_trash([str(lib)])
    assert result.bytes == size and not (lib / TRASH_DIR / "sub" / "copy.png").exists()
    assert stray.exists() and orig.exists()
    assert trash_summary([str(lib)]) == (0, 0)
    index.close()


def test_trash_summary_counts(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    size = copy.stat().st_size + copy.with_suffix(".txt").stat().st_size
    trash_sets(certain_sets(index, lib))
    assert trash_summary([str(lib)]) == (1, size)
    index.close()


def test_rescan_after_trash_and_restore(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))
    index.scan([str(lib)], workers=1)
    paths = {r.path for r in index.rows([str(lib)])}
    assert str(copy.resolve()) not in paths and str(orig.resolve()) in paths
    restore_all([str(lib)])
    index.scan([str(lib)], workers=1)
    assert str(copy.resolve()) in {r.path for r in index.rows([str(lib)])}
    index.close()


def test_with_keeper_swaps_roles():
    s = find_sets([row("big", w=3328, h=4864, dhash=0), row("small", dhash=1)])[1][0]
    swapped = with_keeper(s, s.extras[0])
    assert swapped.keeper.path == "small" and [r.path for r in swapped.extras] == ["big"]


# ================================================================ review fixes

import threading  # noqa: E402

from sorters.duplicate_finder import (  # noqa: E402
    DupSet, extras_by_folder, in_reject, is_posted)


def junction(link: Path, target: Path):
    import _winapi
    _winapi.CreateJunction(str(target), str(link))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junctions")
def test_junction_alias_is_not_a_duplicate_of_itself(tmp_path):
    lib = tmp_path / "lib"
    save(picture(), lib / "real" / "only_copy.png")
    junction(lib / "alias", lib / "real")
    index = ImageIndex(tmp_path / "idx.db")
    stats = index.scan([str(lib)], workers=1)
    assert stats.found == 1
    assert find_sets(index.rows([str(lib)])) == ([], [])
    index.close()


def test_trash_refuses_extra_that_is_the_keepers_file(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    rows = {Path(r.path).name: r for r in index.rows([str(lib)])}
    keeper = rows["orig.png"]
    alias = ImageRow(**{**keeper.__dict__, "path": str(lib / "sub" / "." / "orig.png")})
    result = trash_sets([DupSet("certain", keeper, [alias], 0, True)])
    assert result.moved == [] and result.skipped == [(alias.path, "same file as keeper")]
    assert orig.exists()
    index.close()


def test_sidecar_stays_when_another_image_shares_its_stem(tmp_path):
    lib = tmp_path / "lib"
    img = picture()
    save(img, lib / "x.png", meta=True)                          # keeper
    img.save(lib / "x.webp", lossless=True)                      # extra, same pixels
    (lib / "x.txt").write_text("keeper's caption", encoding="utf-8")
    index = ImageIndex(tmp_path / "idx.db")
    index.scan([str(lib)], workers=1)
    certain = certain_sets(index, lib)
    assert certain[0].keeper.path.endswith("x.png")
    trash_sets(certain)
    assert (lib / "x.txt").exists() and not (lib / "x.webp").exists()
    index.close()


def test_trashed_sidecar_never_overwrites_a_file_in_the_trash(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))                          # -> copy.png, copy.txt
    stray = lib / TRASH_DIR / "sub" / "copy_2.txt"
    stray.write_text("someone else's", encoding="utf-8")
    save(picture(), copy)
    copy.with_suffix(".txt").write_text("caption 2", encoding="utf-8")
    index.scan([str(lib)], workers=1)
    trash_sets(certain_sets(index, lib))
    assert stray.read_text(encoding="utf-8") == "someone else's"
    assert (lib / TRASH_DIR / "sub" / "copy_3.png").exists()
    assert (lib / TRASH_DIR / "sub" / "copy_3.txt").read_text(encoding="utf-8") == "caption 2"
    index.close()


def test_torn_or_bom_log_lines_are_kept_and_ignored(tmp_path):
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))
    log = lib / TRASH_DIR / LOG_NAME
    text = log.read_text(encoding="utf-8")
    log.write_bytes(b"\xef\xbb\xbf" + (text + '{"original": "torn').encode("utf-8"))
    assert trash_summary([str(lib)])[0] == 1
    restore_all([str(lib)])
    assert copy.exists()
    assert log.read_text(encoding="utf-8-sig").strip() == '{"original": "torn'
    index.close()


def test_log_rewrites_wait_for_the_log_lock(tmp_path):
    from sorters import duplicate_finder as df
    lib, orig, copy, index = library(tmp_path)
    trash_sets(certain_sets(index, lib))
    done = threading.Event()
    with df.LOG_LOCK:
        t = threading.Thread(target=lambda: (restore_all([str(lib)]), done.set()))
        t.start()
        assert not done.wait(0.3)                                 # blocked on the lock
    assert done.wait(5) and copy.exists()
    index.close()


# ---------------------------------------------------------------- keeper: REJECT / posted

@pytest.mark.parametrize("path,expected", [
    (r"D:\out\CROP\REJECT\a.png", True),
    (r"D:\out\rejects\a.png", True),
    (r"D:\out\Rejected Batch\a.png", True),
    (r"D:\out\posted\a.png", False),
])
def test_in_reject(path, expected):
    assert in_reject(path) is expected


@pytest.mark.parametrize("path,expected", [
    (r"D:\out\Posted Projects\Feeling Lucky\batch3_posted\a.png", True),
    (r"D:\out\new_batch13_POSTED\a.png", True),
    (r"D:\out\Posted Projects\New Vintage Girls_Posted\unposted\a.png", False),
    (r"D:\out\unposted\a.png", False),
    (r"D:\out\2026-10-07\a.png", False),
])
def test_is_posted_nearest_folder_decides(path, expected):
    assert is_posted(path) is expected


def test_never_keep_from_reject_even_at_higher_resolution():
    rej = row(r"D:\o\REJECT\a.png", w=3328, h=4864, dhash=0, meta=True)
    ok = row(r"D:\o\keep\a.png", w=832, h=1216, dhash=0)
    _, probable = find_sets([rej, ok])
    assert probable[0].keeper.path == ok.path


def test_all_copies_in_reject_still_keeps_one():
    a = row(r"D:\o\REJECT\a.png", pixel="P", size=2)
    b = row(r"D:\o\REJECT\b.png", pixel="P", size=1)
    certain, _ = find_sets([a, b])
    assert certain[0].keeper.path == a.path


def test_posted_copy_kept_at_equal_resolution():
    big_unposted = row(r"D:\o\placeholder\a.png", pixel="P", size=5000, meta=True)
    posted = row(r"D:\o\batch3_posted\a.png", pixel="P", size=1000)
    certain, _ = find_sets([big_unposted, posted])
    assert certain[0].keeper.path == posted.path


def test_resolution_beats_posted():
    posted_small = row(r"D:\o\batch_posted\a.png", w=832, h=1216, dhash=0)
    big = row(r"D:\o\output\a.png", w=3328, h=4864, dhash=0)
    _, probable = find_sets([posted_small, big])
    assert probable[0].keeper.path == big.path


def test_extras_by_folder_counts_where_extras_come_from():
    sets = [DupSet("certain", row(r"D:\k\1.png"), [row(r"D:\a\1.png"), row(r"D:\b\1.png")], 0, True),
            DupSet("certain", row(r"D:\k\2.png"), [row(r"D:\a\2.png")], 0, True)]
    assert extras_by_folder(sets) == [(r"D:\a", 2), (r"D:\b", 1)]
