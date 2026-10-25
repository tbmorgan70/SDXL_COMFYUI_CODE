"""Hashers for scan tests. Module-level so process-pool workers can import them
(they find this folder through the parent's sys.path)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from core.image_index import hash_image  # noqa: E402


def crashy_hash(path):
    """Kills its worker process on any file named *CRASH*."""
    if "CRASH" in os.path.basename(path):
        os._exit(3)
    return hash_image(path)


def flaky_hash(path):
    """Reports a transient read error for any file named *FLAKY*."""
    result = hash_image(path)
    if "FLAKY" in os.path.basename(path):
        result.update(error="OSError: transient", file_sha256=None, pixel_sha256=None,
                      dhash=None, thumb=None)
    return result
