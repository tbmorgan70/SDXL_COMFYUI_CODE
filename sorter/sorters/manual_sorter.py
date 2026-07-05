"""
Manual Sorter — backend for the visual triage tool.

Scans a folder for images, tracks per-image bucket assignments,
and executes the final move into named bucket subfolders.
The UI lives in gui.py (TriageWindow); this module is UI-free.
"""

import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

TRASH_BUCKET = "Trash"


class ManualSorter:
    """Holds triage state: image list, bucket names, assignments."""

    def __init__(self, logger, source_dir, bucket_names):
        """
        Parameters
        ----------
        logger       : SortLogger or None
        source_dir   : folder containing images to triage
        bucket_names : list of up to 4 names; "Trash" is always appended
                       if not present as the last bucket.
        """
        self.logger = logger
        self.source_dir = Path(source_dir)

        names = [n.strip() for n in bucket_names if n and n.strip()]
        # Trash is always the last bucket
        names = [n for n in names if n.lower() != TRASH_BUCKET.lower()]
        self.buckets = (names + [TRASH_BUCKET])[:5] if len(names) >= 4 else names + [TRASH_BUCKET]

        self.images = sorted(
            (f for f in self.source_dir.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS),
            key=lambda p: p.name.lower()
        )
        # path -> bucket name (or absent = unassigned)
        self.assignments = {}

    def _log(self, msg):
        if self.logger:
            self.logger.log_info(msg)
        else:
            print(msg)

    # ------------------------------------------------------------------

    def assign(self, image_path, bucket_name):
        """Assign an image to a bucket; bucket_name=None clears it."""
        image_path = Path(image_path)
        if bucket_name is None:
            self.assignments.pop(image_path, None)
        elif bucket_name in self.buckets:
            self.assignments[image_path] = bucket_name

    def get_assignment(self, image_path):
        return self.assignments.get(Path(image_path))

    def counts(self):
        """Per-bucket assignment counts plus 'unassigned'."""
        result = {b: 0 for b in self.buckets}
        for bucket in self.assignments.values():
            if bucket in result:
                result[bucket] += 1
        result['unassigned'] = len(self.images) - sum(result[b] for b in self.buckets)
        return result

    # ------------------------------------------------------------------

    def execute(self, progress_callback=None):
        """Move assigned images into bucket subfolders under source_dir.

        Unassigned images are left in place. Returns stats dict.
        """
        stats = {b: 0 for b in self.buckets}
        errors = []
        items = list(self.assignments.items())
        total = len(items)

        self._log(f"Manual sort: moving {total} images into {len(self.buckets)} buckets")

        for i, (src, bucket) in enumerate(items):
            if progress_callback:
                progress_callback(i, total, src.name)
            try:
                dest_dir = self.source_dir / bucket
                dest_dir.mkdir(exist_ok=True)
                dest = dest_dir / src.name
                # Avoid clobbering existing files with the same name
                if dest.exists():
                    stem, suffix = src.stem, src.suffix
                    n = 1
                    while dest.exists():
                        dest = dest_dir / f"{stem}_{n}{suffix}"
                        n += 1
                shutil.move(str(src), str(dest))
                stats[bucket] += 1
            except Exception as e:
                errors.append(f"{src.name}: {e}")
                self._log(f"  ✗ Failed to move {src.name}: {e}")

        if progress_callback:
            progress_callback(total, total, "")

        self._log(f"Manual sort complete: {stats}")
        return {"moved": stats, "errors": errors, "total": total}
