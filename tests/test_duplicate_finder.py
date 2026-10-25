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


def test_integer_scale_pretick_at_distance_5():
    big = row("big", w=3328, h=4864, dhash=0)
    small = row("small", w=832, h=1216, dhash=0b11111)                 # 4x, distance 5
    _, probable = find_sets([big, small], "Normal")
    assert probable[0].pretick
    a, b = row("a", dhash=0), row("b", dhash=0b11111)                  # same size, distance 5
    _, probable = find_sets([a, b], "Normal")
    assert not probable[0].pretick


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
