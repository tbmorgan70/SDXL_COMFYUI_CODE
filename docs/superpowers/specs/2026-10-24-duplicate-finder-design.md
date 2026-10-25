# Duplicate Finder — Design

**Date:** 2026-10-24
**Target release:** Sorter 3.7.0 / repo 3.8.0
**Status:** Approved in conversation; awaiting spec review

## Goal

Find copies and look-alikes across the user's finished-image folders, keep the best copy of each,
and free disk space — safely, with everything restorable until the user empties the trash.

This is sub-project 1 of 2. Sub-project 2, the **Source Finder** (search the same index by prompt,
LoRA, checkpoint, size or face; collect picks into a LoRA training set or ComfyUI's input folder),
gets its own design later. This project builds the image index with that reuse in mind.

Context measured from Livebound's index of the user's library (2026-10-04 snapshot, 11,807 images,
207 GB): ~2,800 extra copies / ~37 GB reclaimable keeping the best copy; 15.6 GB of it byte-identical;
524 sets mix resolutions — typically a workflow's `post_sampler` (832×1216), `post upscale` (4×) and
the final Image Saver file (4×, with metadata).

## Decisions (from the user)

| Question | Decision |
|---|---|
| Which copy to keep | Highest resolution (tie-breaks below) |
| What the found images are also for | LoRA training sets, img2img / ControlNet inputs → Source Finder, sub-project 2 |
| Order | Duplicate Finder first, on an index the Source Finder reuses |
| Which folders | Picked each run (list remembered); re-scans only read changed files |
| Where extras go | A `_duplicates_trash` folder, restorable, emptied on request |
| Sorter's own output folders | Left out entirely |
| Certain sets | Handled in bulk after a spot-check |
| Probable sets | Bulk pages of pre-ticked rows |
| Index storage | SQLite + parallel scanner + thumbnail cache (approach A) |

## User-facing behaviour

### Find Duplicates mode (main menu)

- **Folders:** a list with Add / Remove; the last list is remembered between sessions.
- **Strictness** for look-alikes: Strict / Normal (default) / Loose.
- **Scan:** progress bar with counts (found / read / from cache), time remaining and Cancel.
  Unchanged files (same path, size and modified time) come from the index without being read.
- Always skipped: folders named `cropped__*`, `upscaled__*`, `civitai_ready`, `_duplicates_trash`.
- File types: `.png`, `.jpg`, `.jpeg`, `.webp`.
- **Duplicates trash panel** on the form: files and GB waiting in the trash of the listed folders,
  with **Restore all** and **Empty** (permanent; the confirmation states the file count and size).

### Results window (opens after a scan)

Summary line: `Certain: N sets · X extra files · Y GB | Probable: N sets · X extra files · Y GB`.

**Certain tab** — a spot-check gallery of up to 30 sets (keeper marked, extras beside it) and one
button: **Trash N extras (Y GB)**, with a confirmation.

**Probable tab** — pages of 15 sets, closest matches first, one row per set:

- thumbnails side by side, each captioned with resolution, file size and folder name;
- the keeper ringed green; extras marked for the trash;
- a tick box per row, pre-ticked for very close matches (rule below);
- click a thumbnail to make it the keeper;
- **Not duplicates** on a row: remembered, the set is never offered again;
- **Trash extras of ticked rows** handles the page and moves to the next; PgUp / PgDn change page;
- double-click a thumbnail to open it full-size in the default image viewer.

## Matching rules

- **Certain:** identical file bytes (SHA-256 of the file), or identical pixels with different
  metadata (SHA-256 over `"{W}x{H}|"` + the RGB bytes; alpha ignored).
- **Probable:** 64-bit difference hash (9×8 grayscale, horizontal gradients) within a Hamming
  distance of **4 (Strict) / 6 (Normal) / 10 (Loose)**, *and* aspect ratios within **3%** of each
  other (so different crops never match).
- Every image is compared with every other (numpy, chunked XOR + popcount) — no banding shortcuts,
  so nothing within the distance is missed.
- Probable matching runs on one representative per certain set (its keeper); a certain set's extras
  never appear in probable rows.
- **No chains:** sets are built around keepers. Images are visited in keeper order (below); each
  unassigned image starts a set containing every unassigned image within the distance *of it*.
  Leftovers start their own sets. A~B and B~C therefore never pulls A and C together through B.
- Pairs marked **Not duplicates** are stored by pixel hash (stable across moves) and excluded.

### Keeper order (best first)

1. most pixels;
2. has generation metadata (PNG `prompt`, `workflow` or `parameters` text, or EXIF UserComment);
3. larger file;
4. older modified time;
5. path (alphabetical), so the choice is deterministic.

### Pre-ticked probable rows

A row is pre-ticked when every extra in it is either within distance **2** of the keeper, or the same
picture at **2×, 3× or 4×** (keeper-to-extra linear scale within 1% of an integer 2–4) within the
Strictness distance. Other rows start unticked.

### Ordering

Probable sets: largest distance inside the set, ascending (closest first); ties by bytes reclaimed,
descending.

## Trash, restore, empty

- An extra moves to `<scanned folder>\_duplicates_trash\<its path relative to that folder>`, where
  *scanned folder* is the top-level folder from the list it was found under. This keeps the move on
  the same drive (an instant rename) and avoids drive roots that need administrator rights.
- Sidecars move with it: files with the same stem and extension `.txt` or `.json` in the same folder.
- A name clash inside the trash gets `_2`, `_3`, …
- Each move appends one JSON line to `<trash>\_trash_log.jsonl`:
  `{"original", "trashed", "sidecars": [[original, trashed], …], "keeper", "kind": "certain|probable", "time"}`.
- **Before moving:** the extra's size and modified time must match the index, and the keeper must
  still exist. Otherwise the set is skipped and listed as "changed since scan".
- Locked files (Windows sharing violations) are skipped and listed.
- **Restore all:** moves every logged file back; if the original location is taken, restores as
  `<stem>_restored.<ext>` (then `_restored_2` …). Restored entries leave the log.
- **Empty:** permanently deletes only files listed in the logs, removes their log lines and any
  now-empty folders inside the trash.
- The index drops rows for trashed files at the next scan (trash folders are skipped).

## Architecture

### `sorter/core/image_index.py` (new, no UI)

SQLite file `sorter/image_index.db` (git-ignored). Table `images`:

| column | type | notes |
|---|---|---|
| `path` | TEXT PRIMARY KEY | absolute |
| `root` | TEXT | top-level scanned folder it was found under |
| `size`, `mtime` | INTEGER, REAL | change detection |
| `width`, `height` | INTEGER | after EXIF orientation |
| `file_sha256`, `pixel_sha256` | TEXT | |
| `dhash` | INTEGER | 64-bit, stored signed |
| `has_meta` | INTEGER | 0/1 |
| `parameters` | TEXT | A1111 `parameters` text when present (for the Source Finder) |
| `thumb` | BLOB | 256 px long-edge JPEG q80 |
| `error` | TEXT | unreadable files are kept with the reason, never matched |

Table `not_duplicates(a TEXT, b TEXT, PRIMARY KEY(a, b))` — pixel hashes, `a < b`.

- `scan(folders, progress=None, cancel=None) -> ScanStats` walks the folders (skipping the excluded
  folder names), reuses unchanged rows, and hashes the rest in a `ProcessPoolExecutor`
  (workers = CPU count − 1, minimum 1). The worker function is module-level (Windows spawn) and
  returns plain data; only the scanning thread writes SQLite, in batches.
- `rows(folders) -> list[ImageRow]` for the listed folders, excluding rows with `error`.

### `sorter/sorters/duplicate_finder.py` (new, no UI)

- `keeper_key(row)`, `find_sets(rows, strictness, not_dupes) -> (certain: list[DupSet], probable: list[DupSet])`;
  `DupSet` holds the keeper, extras, max distance, bytes reclaimable and the pre-tick flag.
- `trash_set(dupset, keeper=None) -> TrashResult`, `restore_all(folders)`, `empty_trash(folders)`,
  `trash_summary(folders)`.

### `sorter/duplicates_window.py` (new)

The results window: Certain spot-check + bulk button; Probable pages. Thumbnails come from the
index blobs (decoded on a worker thread, Tk images created on the main thread). Trashing runs on a
worker thread with progress.

### `sorter/gui.py` (changed)

"Find Duplicates" mode: folder list (remembered in a small JSON settings file next to the index),
Strictness, Scan, trash panel. Scanning runs on a background thread that owns the process pool.

### Versioning

Sorter 3.7.0 / repo 3.8.0: `sorter/version.py`, `sorter/CHANGELOG.md`, `VERSION.md`, READMEs,
window title; `.gitignore` gains `sorter/image_index.db` and the settings file.

## Error handling

- Unreadable or truncated images: indexed with `error`, counted in the scan summary, never matched.
- A folder in the list that no longer exists: skipped with a warning.
- Cancel during a scan: rows already written are kept; the next scan resumes from them.
- Index file locked or corrupt: the scan reports it and offers to rebuild the index (rename the old
  file aside first).
- Trash move failures (permissions, locks, changed files): skipped and listed after the batch.

## Testing

1. **pytest — `tests/test_image_index.py`:** hashes stable across metadata-only re-saves (pixel
   hash) and changed by edits; dHash survives a 4× resize; incremental re-scan reads only changed
   files; excluded folders skipped; unreadable file recorded with `error`; worker runs in a real
   process pool.
2. **pytest — `tests/test_duplicate_finder.py`:** synthetic sets — byte copies, metadata-only
   copies, 4× upscales, near variations, different aspect, an A~B~C chain; keeper order (each
   tie-break); pre-tick rule; ordering; not-duplicates exclusion; trash → restore → empty round
   trips with sidecars, name clashes, changed-since-scan and missing keeper.
3. **Real folders, dry run:** scan the user's folders without moving anything; compare totals with
   the Livebound snapshot (allowing for the user's reorganisation since).
4. **GUI smoke + screenshot:** open the results window on synthetic sets; check thumbnails, keeper
   ring, pre-ticks, page buttons, and trash/restore through the UI.

## Out of scope

The Source Finder (sub-project 2); deleting outside the trash; video files; matching across
different crops/aspect ratios; duplicates inside archives.
