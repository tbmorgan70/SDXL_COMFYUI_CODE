"""
Duplicate Finder — group indexed images into duplicate sets and pick a keeper.

Certain   identical pixels (identical bytes included): safe to handle in bulk.
Probable  look-alikes by 64-bit difference hash, shapes matching within 3%:
          shown for a quick human check, closest first.

Each set keeps one image — the most pixels, then the copy that carries its
generation metadata, then the bigger file, then the older one — and the
rest are "extras". No UI here; the review window lives in duplicates_window.py.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

import numpy as np

from core.image_index import ImageRow

STRICTNESS = {"Strict": 4, "Normal": 6, "Loose": 10}
ASPECT_TOLERANCE = 0.03
PRETICK_DISTANCE = 2
SCALE_STEPS = (2, 3, 4)
SCALE_TOLERANCE = 0.01
_BLOCK = 512

_M1 = np.uint64(0x5555555555555555)
_M2 = np.uint64(0x3333333333333333)
_M4 = np.uint64(0x0F0F0F0F0F0F0F0F)
_H01 = np.uint64(0x0101010101010101)


@dataclass
class DupSet:
    kind: str                 # "certain" | "probable"
    keeper: ImageRow
    extras: List[ImageRow]
    distance: int             # largest keeper↔extra hash distance (0 for certain)
    pretick: bool

    @property
    def reclaim_bytes(self) -> int:
        return sum(r.size for r in self.extras)


def keeper_key(row: ImageRow) -> tuple:
    """Sorts best first."""
    return (-row.pixels, not row.has_meta, -row.size, row.mtime, row.path)


def with_keeper(s: DupSet, row: ImageRow) -> DupSet:
    members = [s.keeper] + s.extras
    return DupSet(s.kind, row, [r for r in members if r.path != row.path], s.distance, s.pretick)


def _popcount(x: np.ndarray) -> np.ndarray:
    x = x - ((x >> np.uint64(1)) & _M1)
    x = (x & _M2) + ((x >> np.uint64(2)) & _M2)
    x = (x + (x >> np.uint64(4))) & _M4
    return (x * _H01) >> np.uint64(56)


def _close_pairs(hashes: List[int], limit: int) -> Iterable[Tuple[int, int, int]]:
    """Every (i, j, distance) with i < j and Hamming distance <= limit."""
    dh = np.array(hashes, dtype=np.uint64)
    n = len(dh)
    for start in range(0, n, _BLOCK):
        block = dh[start:start + _BLOCK]
        rest = dh[start:]
        dist = _popcount(block[:, None] ^ rest[None, :])
        ii, jj = np.nonzero(dist <= limit)
        for a, b in zip(ii.tolist(), jj.tolist()):
            i, j = start + a, start + b
            if j > i:
                yield i, j, int(dist[a, b])


def _aspect_ok(a: ImageRow, b: ImageRow) -> bool:
    ra, rb = a.width / max(a.height, 1), b.width / max(b.height, 1)
    return abs(ra / rb - 1) <= ASPECT_TOLERANCE


def _scale_step(keeper: ImageRow, extra: ImageRow) -> bool:
    scale = keeper.width / max(extra.width, 1)
    return any(abs(scale / k - 1) <= SCALE_TOLERANCE for k in SCALE_STEPS)


def find_sets(rows: List[ImageRow], strictness: str = "Normal",
              not_dupes: Set[Tuple[str, str]] = frozenset()) -> Tuple[List[DupSet], List[DupSet]]:
    limit = STRICTNESS[strictness]

    # Certain: same pixels
    by_pixel: Dict[str, List[ImageRow]] = defaultdict(list)
    for r in rows:
        by_pixel[r.pixel_sha256].append(r)
    certain: List[DupSet] = []
    reps: List[ImageRow] = []
    for members in by_pixel.values():
        members = sorted(members, key=keeper_key)
        reps.append(members[0])
        if len(members) > 1:
            certain.append(DupSet("certain", members[0], members[1:], 0, True))
    certain.sort(key=lambda s: -s.reclaim_bytes)

    # Probable: look-alikes among one representative per picture
    neighbours: Dict[int, Dict[int, int]] = defaultdict(dict)
    for i, j, d in _close_pairs([r.dhash for r in reps], limit):
        a, b = reps[i], reps[j]
        if not _aspect_ok(a, b):
            continue
        if tuple(sorted((a.pixel_sha256, b.pixel_sha256))) in not_dupes:
            continue
        neighbours[i][j] = d
        neighbours[j][i] = d

    probable: List[DupSet] = []
    assigned: Set[int] = set()
    for i in sorted(neighbours, key=lambda k: keeper_key(reps[k])):
        if i in assigned:
            continue
        assigned.add(i)
        claimed = [(j, d) for j, d in neighbours[i].items() if j not in assigned]
        if not claimed:
            continue
        assigned.update(j for j, _ in claimed)
        keeper = reps[i]
        dist = dict(claimed)
        extras = sorted((reps[j] for j in dist), key=keeper_key)
        pretick = all(dist[j] <= PRETICK_DISTANCE or _scale_step(keeper, reps[j]) for j in dist)
        probable.append(DupSet("probable", keeper, extras, max(dist.values()), pretick))
    probable.sort(key=lambda s: (s.distance, -s.reclaim_bytes))
    return certain, probable
