# Duplicate Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A "Find Duplicates" mode in Sorter that indexes chosen folders, groups byte/pixel-identical (Certain) and look-alike (Probable) images, keeps the highest-resolution copy, and moves extras to a restorable `_duplicates_trash`.

**Architecture:** `sorter/core/image_index.py` is a SQLite index filled by a process-pool scanner (hashes, size, metadata flag, thumbnail). `sorter/sorters/duplicate_finder.py` is UI-free grouping plus trash/restore/empty. `sorter/duplicates_window.py` is the review window; `sorter/gui.py` adds the mode form.

**Tech Stack:** Python 3.11.9, sqlite3, Pillow, numpy, concurrent.futures, customtkinter/Tk, pytest.

**Spec:** `docs/superpowers/specs/2026-10-24-duplicate-finder-design.md`

## Global Constraints

- Run Python as `python` (3.11.9), never `py -3`. Work and commit in the worktree `.claude/worktrees/duplicate-finder`; do not push.
- No new dependencies (sqlite3, numpy, Pillow, customtkinter are already available).
- Tests live in `tests/` and start with `sys.path.insert(0, <repo>/sorter)`; imports are `core.image_index`, `sorters.duplicate_finder`, `duplicates_window`, `gui`.
- Tk objects only on the main thread; workers hand PIL images/results over a `queue.Queue` drained by an `after()` poller.
- File types `.png .jpg .jpeg .webp`. Skipped folder names: prefix `cropped__` or `upscaled__`, exact `civitai_ready`, exact `_duplicates_trash`.
- Strictness → Hamming distance: Strict 4, Normal 6 (default), Loose 10. Aspect ratios must agree within 3%.
- Pre-tick: every extra within distance 2 of the keeper, or keeper-to-extra linear scale within 1% of 2, 3 or 4 (and within the strictness distance).
- Keeper order: most pixels → has generation metadata → larger file → older mtime → path.
- Probable page size 15; Certain spot-check up to 30 sets. Thumbnails 256 px long edge, JPEG q80.
- Trash: `<scanned folder>\_duplicates_trash\<relative path>`; log `_trash_log.jsonl` in that trash folder; sidecars `.txt`/`.json` with the same stem; trash clash `_2`, `_3`…; restore clash `_restored`, `_restored_2`….
- Nothing is ever deleted except by Empty, and Empty deletes only files listed in a trash log.
- Version Sorter 3.7.0 / repo 3.8.0. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Nested folders in the list** (e.g. `D:\a` and `D:\a\b`): every file indexed once, under the outermost listed folder; never matched against itself (Task 1 test).
2. **Non-ASCII names** (`Feelin' Lucky ✨.png`): scanning, trashing, the JSONL log and restore all work (Task 3 test).
3. **Unusual images** (16-bit PNG, RGBA, palette, EXIF-rotated JPEG): hashing never crashes; width/height are after EXIF rotation (Task 1 test).
4. **Big libraries**: `find_sets` on 20,000 rows finishes in under 10 s (Task 2 test).
5. **Trash then re-scan**: trashed files drop out of the index (their folder is skipped), and restored files come back (Task 3 test).

---

### Task 1: Image index and scanner

**Files:**
- Create: `sorter/core/image_index.py`
- Modify: `.gitignore` (add `sorter/image_index.db`, `sorter/image_index.db-*`, `sorter/duplicate_finder_settings.json`)
- Test: `tests/test_image_index.py`

**Interfaces:**
- Produces:
  - `IMAGE_EXTS`, `TRASH_DIR = "_duplicates_trash"`, `THUMB_EDGE = 256`, `DEFAULT_DB = <sorter>/image_index.db`
  - `is_excluded_dir(name: str) -> bool`
  - `@dataclass(frozen=True) class ImageRow: path: str; root: str; size: int; mtime: float; width: int; height: int; file_sha256: str; pixel_sha256: str; dhash: int; has_meta: bool; parameters: str | None` (`dhash` is the unsigned 64-bit value)
    - `pixels` property = `width * height`
  - `@dataclass(frozen=True) class ScanStats: found: int; hashed: int; cached: int; errors: int; removed: int; missing_folders: tuple[str, ...]; cancelled: bool`
  - `pixel_sha256(img: Image.Image) -> str` — SHA-256 over `f"{w}x{h}|"` + `img.convert("RGB").tobytes()`, after EXIF transpose
  - `dhash64(img: Image.Image) -> int` — grayscale, resize to 9×8 with LANCZOS, bit = `px[x] > px[x+1]` row-major, first bit most significant
  - `hash_image(path: str) -> dict` — module-level process-pool worker. Keys: `path, size, mtime, width, height, file_sha256, pixel_sha256, dhash, has_meta, parameters, thumb, error`. On failure, `error` holds the reason and the hashes are `None`.
    - `has_meta` = PNG text `prompt`, `workflow` or `parameters` present, or EXIF UserComment (37510) non-empty
    - `thumb` = JPEG q80 bytes, long edge 256
  - `class ImageIndex` (opens SQLite with `check_same_thread=False` and guards every DB call with one `threading.Lock`):
    - `__init__(self, db_path: Path = DEFAULT_DB)`
    - `scan(self, folders: list[str], progress=None, cancel=None, workers: int | None = None) -> ScanStats` — `progress(done, total, name)`, `cancel() -> bool`; `workers` defaults to `max(1, os.cpu_count() - 1)`
    - `rows(self, folders: list[str]) -> list[ImageRow]` (error rows excluded)
    - `thumbnail(self, path: str) -> bytes | None`
    - `drop(self, paths) -> None`
    - `mark_not_duplicates(self, pixel_a: str, pixel_b: str) -> None`
    - `not_duplicate_pairs(self) -> set[tuple[str, str]]` (each pair ordered `a < b`)
    - `close(self) -> None`
  - `class IndexCorrupt(Exception)` — raised by `ImageIndex.__init__` when the file isn't a usable SQLite database
  - `rebuild_index(db_path: Path = DEFAULT_DB) -> Path` — renames the broken file aside to `image_index.broken-<YYYYmmdd-HHMMSS>.db` and returns the new path
- Behaviour:
  - Folders are resolved to absolute paths. A file under several listed folders gets the outermost as `root`.
  - Unchanged files (same path, size and mtime) are counted as `cached` and never re-read.
  - Rows under the scanned folders whose file is gone, or now sits inside a skipped folder, are deleted and counted as `removed`.
  - Missing listed folders go into `missing_folders`.
  - SQLite stores `dhash` as a signed 64-bit integer; convert on the way in and out.

- [ ] **Step 1: Write the failing tests** in `tests/test_image_index.py`. Helpers: `noise(path, size, seed, mode="RGB", **save_kw)` writes a seeded random-noise image and returns its path; `ham(a, b)` returns `bin(a ^ b).count("1")`.

```python
def test_pixel_hash_survives_metadata_resave_file_hash_does_not(tmp_path):
    # same pixels saved with and without a `parameters` text chunk
    # -> equal pixel_sha256, different file_sha256; has_meta True only for the chunked one

def test_pixel_hash_changes_with_one_pixel(tmp_path): ...

def test_dhash_survives_4x_resize(tmp_path):
    # 300x400 smooth gradient + shapes, and its 4x LANCZOS upscale -> ham(...) <= 2

def test_dhash_far_apart_for_different_images(tmp_path):
    # noise seed 1 vs seed 2 at the same size -> ham(...) > 16

def test_unusual_images_hash_and_rotation_applied(tmp_path):
    # RGBA, P, I;16 PNGs hash without error; a JPEG of 400x200 with EXIF Orientation 6
    # is recorded as width 200, height 400

def test_jpeg_usercomment_counts_as_metadata(tmp_path): ...

def test_thumbnail_is_jpeg_256(tmp_path):
    # 1000x500 image -> thumbnail decodes as JPEG with size (256, 128)

def test_scan_skips_excluded_folders(tmp_path):
    # files in cropped__1024x1024, upscaled__4096px_x, civitai_ready, _duplicates_trash are
    # not indexed; a sibling normal folder is

def test_rescan_reads_only_changed_files(tmp_path):
    # 4 images; first scan hashed=4; second scan cached=4, hashed=0;
    # rewrite one -> hashed=1, cached=3

def test_removed_files_dropped_on_rescan(tmp_path): ...    # stats.removed == 1, rows() shrinks

def test_unreadable_file_recorded_but_not_returned(tmp_path):
    # garbage bytes in bad.png -> stats.errors == 1, bad.png not in rows()

def test_missing_folder_reported(tmp_path): ...

def test_nested_folders_index_each_file_once(tmp_path):          # Review Focus 1
    # scan([a, a/b]) -> each file exactly one row, root == str(a)

def test_scan_runs_in_a_real_process_pool(tmp_path):
    # workers=2 over 4 images -> 4 rows with pixel hashes

def test_cancel_keeps_rows_and_next_scan_finishes(tmp_path):
    # cancel() returns True after the first progress callback -> stats.cancelled;
    # next scan without cancel indexes everything

def test_not_duplicate_pairs_roundtrip(tmp_path):
    # mark_not_duplicates("b", "a") -> {("a", "b")}

def test_corrupt_index_raises_and_rebuild_moves_it_aside(tmp_path):
    # garbage bytes in idx.db -> ImageIndex(idx.db) raises IndexCorrupt;
    # rebuild_index(idx.db) leaves an image_index.broken-*.db next to it and ImageIndex(idx.db) opens
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_image_index.py -q -p no:warnings`
Expected: collection error, `ModuleNotFoundError: No module named 'core.image_index'`

- [ ] **Step 3: Implement `sorter/core/image_index.py`** per the Interfaces block.
  - Walk folders with `os.walk`, pruning skipped names from `dirnames` in place.
  - Submit changed files to `ProcessPoolExecutor(max_workers=workers)`, collect results with `as_completed`, and write to SQLite in batches of 200.
  - Check `cancel()` between results; on cancel, shut the pool down with `cancel_futures=True`.
  - Read the file bytes once and use them for both `file_sha256` and decoding (`Image.open(io.BytesIO(data))`).

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_image_index.py -q -p no:warnings`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sorter/core/image_index.py tests/test_image_index.py .gitignore
git commit -m "Image index: SQLite + process-pool scanner with hashes and thumbnails"
```

---

### Task 2: Grouping into Certain and Probable sets

**Files:**
- Create: `sorter/sorters/duplicate_finder.py`
- Test: `tests/test_duplicate_finder.py`

**Interfaces:**
- Consumes: `ImageRow` (Task 1).
- Produces:
  - `STRICTNESS = {"Strict": 4, "Normal": 6, "Loose": 10}`, `ASPECT_TOLERANCE = 0.03`, `PRETICK_DISTANCE = 2`, `SCALE_STEPS = (2, 3, 4)`, `SCALE_TOLERANCE = 0.01`
  - `@dataclass class DupSet: kind: str; keeper: ImageRow; extras: list[ImageRow]; distance: int; pretick: bool`
    - `reclaim_bytes` property = sum of the extras' sizes
  - `keeper_key(row: ImageRow) -> tuple` — sorts best first: `(-row.pixels, not row.has_meta, -row.size, row.mtime, row.path)`
  - `with_keeper(s: DupSet, row: ImageRow) -> DupSet` — `row` becomes keeper, the old keeper joins the extras; `distance` and `pretick` are unchanged
  - `find_sets(rows: list[ImageRow], strictness: str = "Normal", not_dupes: set[tuple[str, str]] = frozenset()) -> tuple[list[DupSet], list[DupSet]]` — returns `(certain, probable)`
- Rules:
  - **Certain:** rows grouped by `pixel_sha256` with ≥ 2 members (byte-identical files are pixel-identical); keeper = min by `keeper_key`; `distance=0`, `pretick=True`; sorted by `reclaim_bytes` descending.
  - **Probable candidates:** the keeper of each certain set plus every row not in a certain set.
  - **Neighbours:** Hamming ≤ strictness distance, aspect ratios within 3%, and the pixel-hash pair (ordered) not in `not_dupes`.
  - **Set building:** visit candidates in `keeper_key` order. Each unassigned row claims its unassigned neighbours; if it claimed any, that's a set. `distance` = the largest keeper↔extra distance.
  - **pretick:** every extra is within distance 2, or has an integer scale 2/3/4 within 1% (keeper width ÷ extra width).
  - **Sorting:** probable sets by `(distance, -reclaim_bytes)`.
- Hamming for all pairs: numpy, `dh = np.array(..., dtype=np.uint64)`, rows in chunks of 256, `x = dh[i:i+256, None] ^ dh[None, :]`, popcount via `np.unpackbits(x.view(np.uint8), axis=-1).sum(-1)` (or a 256-entry lookup table on the bytes). Only pairs `j > i` are kept.

- [ ] **Step 1: Write the failing tests** in `tests/test_duplicate_finder.py`. Helper `row(path, w=832, h=1216, pixel=None, dhash=0, size=1000, meta=False, mtime=0.0)` builds an `ImageRow`. `pixel` defaults to a unique value derived from the path, and `root` is `"R"`.

```python
def test_certain_groups_same_pixels_keeper_has_meta():
    a = row("a", pixel="P", size=17_000_000)               # post upscale, no metadata
    b = row("b", pixel="P", size=36_000_000, meta=True)    # Image Saver final
    certain, probable = find_sets([a, b])
    assert len(certain) == 1 and certain[0].keeper.path == "b" and certain[0].extras == [a]
    assert probable == []

@pytest.mark.parametrize("better,worse", [
    (dict(w=3328, h=4864), dict(w=832, h=1216, meta=True, size=10**9)),   # pixels first
    (dict(meta=True), dict(size=10**9)),                                  # then metadata
    (dict(size=2000), dict(size=1000)),                                   # then size
    (dict(mtime=1.0), dict(mtime=2.0)),                                   # then older
])
def test_keeper_order(better, worse):
    assert keeper_key(row("x", **better)) < keeper_key(row("y", **worse))

def test_probable_4x_upscale_matched_and_preticked():
    big = row("final", w=3328, h=4864, dhash=0b1011, meta=True)
    small = row("post_sampler", w=832, h=1216, dhash=0b1111)          # distance 1
    _, probable = find_sets([big, small])
    assert probable[0].keeper.path == "final" and probable[0].pretick

def test_integer_scale_pretick_at_distance_5():
    # distance 5 at Normal: 4x pair pre-ticked, same-size pair not

@pytest.mark.parametrize("strict,expect", [("Strict", 0), ("Normal", 1), ("Loose", 1)])
def test_strictness(strict, expect):
    # two same-size rows at distance 5

def test_aspect_mismatch_never_matches():
    # 1024x1024 vs 832x1216 at distance 0 -> no probable sets

def test_no_chains():
    # A best (most pixels), A-B distance 4, B-C distance 4, A-C distance 8, Normal
    # -> one set {A: [B]}; C not in it

def test_certain_extras_not_in_probable(): ...
def test_not_duplicates_excluded(): ...
def test_probable_sorted_closest_first(): ...

def test_twenty_thousand_rows_under_ten_seconds():           # Review Focus 4
    # random 64-bit dhashes, 20_000 rows; time.perf_counter() around find_sets < 10
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_duplicate_finder.py -q -p no:warnings`
Expected: collection error, `ModuleNotFoundError: No module named 'sorters.duplicate_finder'`

- [ ] **Step 3: Implement** the Interfaces block in `sorter/sorters/duplicate_finder.py`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_duplicate_finder.py -q -p no:warnings`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sorter/sorters/duplicate_finder.py tests/test_duplicate_finder.py
git commit -m "Duplicate finder: Certain/Probable sets, keeper order, pre-ticks"
```

---

### Task 3: Trash, restore, empty

**Files:**
- Modify: `sorter/sorters/duplicate_finder.py`
- Test: `tests/test_duplicate_finder.py` (append)

**Interfaces:**
- Consumes: `DupSet`, `ImageRow`, `TRASH_DIR`, `ImageIndex` (tests only).
- Produces:
  - `LOG_NAME = "_trash_log.jsonl"`, `SIDECAR_EXTS = (".txt", ".json")`
  - `@dataclass class TrashResult: moved: list[str]; skipped: list[tuple[str, str]]; bytes: int` (`skipped` holds `(path, reason)`)
  - `trash_sets(sets: list[DupSet], progress=None) -> TrashResult`
  - `restore_all(folders: list[str]) -> TrashResult`
  - `empty_trash(folders: list[str]) -> TrashResult`
  - `trash_summary(folders: list[str]) -> tuple[int, int]` — `(files, bytes)` from the logs
- Behaviour:
  - Skip reasons, verbatim:
    - `"changed since scan"`: the extra's size or mtime differs from its row
    - `"keeper missing"`: the keeper file is gone; applies to the whole set
    - `"locked: <error>"`: an `OSError` on move
  - **Trash destination:** `Path(row.root) / TRASH_DIR / Path(row.path).relative_to(row.root)`. Parents are created, and a clash gets `_2`, `_3`….
  - **Sidecars:** same stem, same folder, `.txt` or `.json`.
  - **Log line** (JSON, UTF-8): `{"original", "trashed", "sidecars": [[orig, trashed], …], "keeper", "kind", "time"}`.
  - **Restore:** puts files back, or `<stem>_restored<ext>` (`_restored_2`…) if the spot is taken; restored lines leave the log.
  - **Empty:** deletes only the logged `trashed` files that still exist, clears those log lines, and removes empty folders inside `_duplicates_trash`.

- [ ] **Step 1: Write the failing tests** (append). They use real files: index `tmp_path` with `ImageIndex(tmp_path / "idx.db")` and build sets with `find_sets(index.rows([str(tmp_path)]))`.

```python
def test_trash_moves_extra_with_sidecars_and_logs(tmp_path):
    # original + metadata-less copy with copy.txt -> trash_sets(certain) moves copy.png and copy.txt
    # under tmp_path/_duplicates_trash/<sub>/, keeper untouched, one JSON log line with kind "certain"

def test_trash_skips_changed_since_scan(tmp_path): ...  # touch the extra after scanning
def test_trash_skips_set_when_keeper_missing(tmp_path): ...
def test_trash_name_clash_gets_suffix(tmp_path): ...      # second trashing of the same relative path -> _2

def test_unicode_names_trash_and_restore(tmp_path):        # Review Focus 2
    # "Feelin' Lucky ✨.png" copies -> trash, log readable as UTF-8, restore_all brings it back

def test_restore_all_handles_taken_spot(tmp_path):
    # trash, recreate a file at the original path, restore -> "<stem>_restored.png"

def test_empty_deletes_only_logged_files(tmp_path):
    # an unlogged stray file placed in _duplicates_trash survives empty_trash; bytes freed reported

def test_trash_summary_counts(tmp_path): ...

def test_rescan_after_trash_and_restore(tmp_path):         # Review Focus 5
    # trash -> index.scan -> trashed path no longer in rows(); restore_all -> scan -> back in rows()

def test_with_keeper_swaps_roles():
    # with_keeper(s, s.extras[0]) -> keeper is that row, old keeper in extras
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_duplicate_finder.py -q -p no:warnings`
Expected: the new tests fail with `ImportError: cannot import name 'trash_sets'`

- [ ] **Step 3: Implement** the Task 3 functions in `duplicate_finder.py` (moves with `os.replace`; the log is opened in append mode with `encoding="utf-8"`).

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_duplicate_finder.py tests/test_image_index.py -q -p no:warnings`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sorter/sorters/duplicate_finder.py tests/test_duplicate_finder.py
git commit -m "Duplicate finder: restorable trash with log, restore and empty"
```

---

### Task 4: Results window

**Files:**
- Create: `sorter/duplicates_window.py`
- Test: `tests/test_duplicates_window.py`

**Interfaces:**
- Consumes: `ImageIndex.thumbnail`, `ImageIndex.mark_not_duplicates`, `ImageIndex.drop` (Task 1); `DupSet`, `with_keeper`, `trash_sets` (Tasks 2–3).
- Produces: `class DuplicatesWindow(ctk.CTkToplevel)` with:

```python
PAGE_SIZE = 15
SPOT_CHECK = 30
def __init__(self, parent, index: ImageIndex, certain: list[DupSet], probable: list[DupSet],
             log_fn: Callable[[str], None])
summary_text: str            # the summary line
page: int
probable: list[DupSet]       # mutable: keeper swaps, removals
ticked: dict[int, bool]      # index into probable -> ticked (seeded from pretick)
def show_tab(self, name: str) -> None              # "Certain" | "Probable"
def set_keeper(self, set_index: int, row: ImageRow) -> None
def mark_not_duplicates(self, set_index: int) -> None
def change_page(self, delta: int) -> None
def trash_certain(self, confirm: bool = True) -> None
def trash_ticked_page(self, confirm: bool = True) -> None
def busy(self) -> bool                             # a trash batch is running
```

- Behaviour:
  - **Summary text, exact form:** `Certain: {n} sets · {x} extra files · {gb:.1f} GB | Probable: {n} sets · {x} extra files · {gb:.1f} GB`
  - **Probable rows:** a thumbnail per image with the caption `"{w}×{h} · {mb:.1f} MB · {folder name}"`. The keeper gets a 3 px `#4CAF50` border. The tick box starts from `pretick`. Buttons: "Not duplicates".
  - **Clicks:** clicking a thumbnail calls `set_keeper`; double-clicking calls `os.startfile(path)`.
  - **Page keys:** PgUp/PgDn call `change_page(∓1)`.
  - **Trashing:** runs `trash_sets` on a worker thread. When done (on the main thread), it removes the handled sets, calls `index.drop(moved)`, logs `"🗑 Trashed {n} files ({gb:.2f} GB)"` plus any skips, re-renders and recomputes the summary.
  - **After a probable batch:** the page stays put if any sets remain at that index, otherwise steps back.
  - **Thumbnails:** blobs are decoded on a worker thread and `CTkImage` objects created in an `after()` poller.

- [ ] **Step 1: Write the failing tests** in `tests/test_duplicates_window.py`.
  - Fixtures:
    - a module `root = ctk.CTk()`, withdrawn
    - `pump(cond)` as in `tests/test_triage_crop.py`
    - `lib(tmp_path)`: writes 20 near-duplicate pairs (a 4× upscale of each base image) and 3 exact copies, scans them into `ImageIndex(tmp_path/"idx.db")`, runs `find_sets`, and returns `(index, certain, probable)`
  - The `win` fixture destroys the window and calls `gc.collect()` on teardown.

```python
def test_summary_line(lib, win): ...                     # matches the exact format with the lib's counts
def test_first_page_has_15_rows_preticked(lib, win): ...  # 4x pairs are pre-ticked
def test_set_keeper_swaps(lib, win): ...                  # keeper of probable[0] becomes the clicked row
def test_trash_ticked_page_moves_and_advances(lib, win, tmp_path):
    # untick row 0; trash_ticked_page(confirm=False); pump until not busy()
    # -> 14 extras in _duplicates_trash, row 0's extra still in place, len(win.probable) == 6
def test_not_duplicates_hides_and_persists(lib, win): ...  # pair in index.not_duplicate_pairs()
def test_trash_certain(lib, win, tmp_path): ...           # 3 copies' extras moved
def test_page_keys(lib, win): ...                          # PgDn -> page 1, PgUp -> page 0
def test_double_click_opens_file(lib, win, monkeypatch): ... # os.startfile called with the path
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_duplicates_window.py -q -p no:warnings`
Expected: collection error, `ModuleNotFoundError: No module named 'duplicates_window'`

- [ ] **Step 3: Implement** `sorter/duplicates_window.py` per the Interfaces block.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m pytest tests/test_duplicates_window.py -q -p no:warnings`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sorter/duplicates_window.py tests/test_duplicates_window.py
git commit -m "Duplicates window: Certain spot-check, Probable pre-ticked pages"
```

---

### Task 5: Find Duplicates mode, settings, version 3.7.0, real-data check

**Files:**
- Modify: `sorter/gui.py` — imports, mode list, frame creation and build calls, `_switch_mode`, `run_operation`, window title, plus the new `_build_dup_form` / `find_duplicates` methods
- Modify: `sorter/version.py`, `sorter/CHANGELOG.md`, `VERSION.md`, `README.md`, `sorter/README.md`
- Test: `tests/test_gui_duplicates.py`

**Interfaces:**
- Consumes: `ImageIndex`, `find_sets`, `STRICTNESS`, `restore_all`, `empty_trash`, `trash_summary`, `DuplicatesWindow`.
- Produces:
  - In `SorterGUI`:
    - mode `"Find Duplicates"`, placed after `"Manual Crop"`
    - `self.dup_frame`, `self.dup_folders: list[str]`, `self.dup_strictness_var`, `self.dup_trash_label`
    - `_build_dup_form`, `find_duplicates`, `_dup_add_folder`, `_dup_remove_folder`, `_dup_refresh_trash`, `_dup_restore_all`, `_dup_empty_trash`
  - Settings: `sorter/duplicate_finder_settings.json` = `{"folders": [...], "strictness": "Normal"}`, read at start and written on every change.
- Behaviour:
  - `find_duplicates` opens a `ProgressWindow(self, "Finding Duplicates")`. A background `Thread` calls `index.scan(...)` with progress → `("progress", (done, total, name))` and `cancel=lambda: progress_window.cancelled`, then `rows` → `find_sets`.
  - It logs `"🔍 Indexed {found} images ({hashed} read, {cached} from cache, {errors} unreadable)"` and enqueues `("complete", True)`.
  - The `DuplicatesWindow` is opened with `self.after(0, …)` on the main thread, sharing the same `ImageIndex`.
  - The trash panel label reads `"🗑 Duplicates trash: {files} files · {gb:.1f} GB"`, refreshed after scans, trashing, restore and empty.
  - Empty asks `messagebox.askyesno` and states files and GB.
  - If opening the index raises `IndexCorrupt`, ask `"The duplicate index is damaged. Move it aside and build a new one?"`; on yes, `rebuild_index()` and continue the scan.
  - Version: `VERSION = "3.7.0"` with today's `BUILD_DATE` and a FEATURES entry `"Find Duplicates (Certain/Probable, highest-resolution keeper, restorable trash)",  # NEW in v3.7.0!`, plus the window title, a CHANGELOG section, a VERSION.md repo 3.8.0 section and a README mode line.

- [ ] **Step 1: Write the failing tests** in `tests/test_gui_duplicates.py`. The app runs in a subprocess (one Tk root per process), as in `tests/test_triage_crop.py::test_manual_crop_mode_switches_form`.

```python
def test_dup_mode_switches_form_and_remembers_folders(tmp_path):
    # subprocess: SorterGUI(), point the settings file at tmp_path, _dup_add_folder via the folder
    # list API (patch filedialog), switch to "Find Duplicates" -> dup_frame packed; new SorterGUI
    # in a second subprocess reads the same folders back

def test_trash_panel_reports_counts(tmp_path):
    # pre-made _duplicates_trash with a 2-line log -> label text "🗑 Duplicates trash: 2 files · …"
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/test_gui_duplicates.py -q -p no:warnings`
Expected: FAIL — `"Find Duplicates"` is not in the mode list / `AttributeError: dup_frame`

- [ ] **Step 3: Implement** the Interfaces block in `gui.py`, plus the version and docs updates.

- [ ] **Step 4: Run the whole new suite and confirm it passes**

Run: `python -m pytest tests/test_image_index.py tests/test_duplicate_finder.py tests/test_duplicates_window.py tests/test_gui_duplicates.py tests/test_crop_tool.py tests/test_crop_editor.py tests/test_triage_crop.py -q -p no:warnings`
Expected: all PASS

- [ ] **Step 5: Real-data dry run** (no moves).
  - Scan `D:\ComfyUI_windows_portable\ComfyUI\output`, `D:\sdxl_images_collection` and `F:\Generated_Images\CivitAi Archive`, skipping any that don't exist, into an index in the session scratchpad.
  - Then call `find_sets(..., "Normal")` and print the time taken, the counts, the GB per kind, and the 5 largest probable sets with their paths.
  - Expected: it completes; the totals are the same order of magnitude as the Livebound snapshot (~37 GB reclaimable), allowing for the user's reorganisation since.

- [ ] **Step 6: Screenshot check.** Open `DuplicatesWindow` on a copy of ~40 real images from that run, capture the window with `PIL.ImageGrab`, and view it.
  - Expected: thumbnails, captions, green keeper ring and pre-ticks are all visible, and the summary line is correct.

- [ ] **Step 7: Launch check.** Run `python sorter/gui.py` for about 8 s. Expected: the title shows 3.7.0, the mode menu lists "Find Duplicates", and there is no traceback.

- [ ] **Step 8: Commit**

```bash
git add sorter/gui.py sorter/version.py sorter/CHANGELOG.md VERSION.md README.md sorter/README.md tests/test_gui_duplicates.py
git commit -m "Sorter 3.7: Find Duplicates mode"
```
