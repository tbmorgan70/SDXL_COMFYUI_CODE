"""
Duplicate Finder — group indexed images into duplicate sets and pick a keeper.

Certain   identical pixels (identical bytes included): safe to handle in bulk.
Probable  look-alikes by 64-bit difference hash, shapes matching within 3%:
          shown for a quick human check, closest first.

Each set keeps one image — the most pixels, then the copy that carries its
generation metadata, then the bigger file, then the older one — and the
rest are "extras". No UI here; the review window lives in duplicates_window.py.
"""

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

import numpy as np

from core.image_index import TRASH_DIR, ImageRow

STRICTNESS = {"Strict": 4, "Normal": 6, "Loose": 10}
ASPECT_TOLERANCE = 0.03
PRETICK_DISTANCE = 2
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
        # Only near-identical rows start ticked. A 2x/4x size gap is NOT a reason
        # on its own: on the user's library every scaled pair at distance 3+
        # was a different picture; real upscales sat at 0-2.
        pretick = all(d <= PRETICK_DISTANCE for d in dist.values())
        probable.append(DupSet("probable", keeper, extras, max(dist.values()), pretick))
    probable.sort(key=lambda s: (s.distance, -s.reclaim_bytes))
    return certain, probable


# ----------------------------------------------------------------------
# Trash, restore, empty
#
# Extras move into <scanned folder>/_duplicates_trash/<relative path>, so the
# move is a rename on the same drive. Every move is one JSON line in that
# trash's _trash_log.jsonl; Restore and Empty work only from those lines.
# ----------------------------------------------------------------------

LOG_NAME = "_trash_log.jsonl"
SIDECAR_EXTS = (".txt", ".json")


@dataclass
class TrashResult:
    moved: List[str] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)    # (path, reason)
    bytes: int = 0


def _free_path(target: Path, tag: str = "") -> Path:
    """target, or <stem><tag>, <stem><tag>_2 … when taken (tag '' → _2, _3 …)."""
    if tag:
        candidate = target.with_name(f"{target.stem}{tag}{target.suffix}")
        n = 2
        while candidate.exists():
            candidate = target.with_name(f"{target.stem}{tag}_{n}{target.suffix}")
            n += 1
        return candidate
    candidate, n = target, 2
    while candidate.exists():
        candidate = target.with_name(f"{target.stem}_{n}{target.suffix}")
        n += 1
    return candidate


def _sidecars(path: Path) -> List[Path]:
    return [path.with_suffix(ext) for ext in SIDECAR_EXTS if path.with_suffix(ext).exists()]


def _trash_dirs(folders: List[str]) -> List[Path]:
    return [Path(f).resolve() / TRASH_DIR for f in folders]


def _read_log(trash: Path) -> List[dict]:
    log = trash / LOG_NAME
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_log(trash: Path, entries: List[dict]) -> None:
    log = trash / LOG_NAME
    if entries:
        log.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries),
                       encoding="utf-8")
    elif log.exists():
        log.unlink()


def _prune_empty_dirs(trash: Path) -> None:
    if not trash.is_dir():
        return
    for dirpath, _dirs, _files in sorted(os.walk(trash), key=lambda t: -len(t[0])):
        try:
            os.rmdir(dirpath)       # only succeeds when empty
        except OSError:
            pass


def trash_sets(sets: List[DupSet], progress: Optional[Callable[[int, int, str], None]] = None
               ) -> TrashResult:
    result = TrashResult()
    total = sum(len(s.extras) for s in sets)
    done = 0
    for s in sets:
        if not os.path.exists(s.keeper.path):
            result.skipped.extend((e.path, "keeper missing") for e in s.extras)
            done += len(s.extras)
            continue
        for extra in s.extras:
            done += 1
            src = Path(extra.path)
            try:
                st = src.stat()
            except OSError:
                result.skipped.append((extra.path, "changed since scan"))
                continue
            if st.st_size != extra.size or st.st_mtime != extra.mtime:
                result.skipped.append((extra.path, "changed since scan"))
                continue
            root = Path(extra.root)
            trash = root / TRASH_DIR
            try:
                dest = _free_path(trash / src.relative_to(root))
                dest.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dest)
            except OSError as e:
                result.skipped.append((extra.path, f"locked: {e}"))
                continue
            moved_sidecars = []
            for side in _sidecars(src):
                side_dest = dest.with_suffix(side.suffix)
                try:
                    os.replace(side, side_dest)
                    moved_sidecars.append([str(side), str(side_dest)])
                except OSError:
                    pass
            with open(trash / LOG_NAME, "a", encoding="utf-8") as log:
                log.write(json.dumps({
                    "original": str(src), "trashed": str(dest), "sidecars": moved_sidecars,
                    "keeper": s.keeper.path, "kind": s.kind,
                    "time": datetime.now().isoformat(timespec="seconds")},
                    ensure_ascii=False) + "\n")
            result.moved.append(extra.path)
            result.bytes += extra.size
            if progress:
                progress(done, total, src.name)
    return result


def restore_all(folders: List[str]) -> TrashResult:
    result = TrashResult()
    for trash in _trash_dirs(folders):
        remaining = []
        for entry in _read_log(trash):
            trashed = Path(entry["trashed"])
            if not trashed.exists():
                continue                    # removed by hand; nothing to restore
            original = Path(entry["original"])
            target = original if not original.exists() else _free_path(original, "_restored")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                size = trashed.stat().st_size
                os.replace(trashed, target)
            except OSError as e:
                result.skipped.append((str(trashed), f"locked: {e}"))
                remaining.append(entry)
                continue
            for orig_side, trashed_side in entry.get("sidecars", []):
                side_target = target.with_suffix(Path(orig_side).suffix)
                if side_target.exists():
                    side_target = _free_path(side_target, "_restored")
                try:
                    os.replace(trashed_side, side_target)
                except OSError:
                    pass
            result.moved.append(str(target))
            result.bytes += size
        _write_log(trash, remaining)
        _prune_empty_dirs(trash)
    return result


def empty_trash(folders: List[str]) -> TrashResult:
    result = TrashResult()
    for trash in _trash_dirs(folders):
        remaining = []
        for entry in _read_log(trash):
            files = [entry["trashed"]] + [t for _o, t in entry.get("sidecars", [])]
            failed = False
            for f in files:
                p = Path(f)
                if not p.exists():
                    continue
                try:
                    size = p.stat().st_size
                    p.unlink()
                    result.bytes += size
                except OSError as e:
                    result.skipped.append((f, f"locked: {e}"))
                    failed = True
            if failed:
                remaining.append(entry)
            else:
                result.moved.append(entry["trashed"])
        _write_log(trash, remaining)
        _prune_empty_dirs(trash)
    return result


def trash_summary(folders: List[str]) -> Tuple[int, int]:
    files = size = 0
    for trash in _trash_dirs(folders):
        for entry in _read_log(trash):
            trashed = Path(entry["trashed"])
            if not trashed.exists():
                continue
            files += 1
            size += trashed.stat().st_size
            size += sum(Path(t).stat().st_size for _o, t in entry.get("sidecars", [])
                        if Path(t).exists())
    return files, size
