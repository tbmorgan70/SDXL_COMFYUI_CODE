"""Sorter's other modes must never walk into _duplicates_trash: Flatten would pull
the duplicates back out, Filename cleanup would rename them (breaking Restore),
Civitai Prep would rewrite them in place."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from PIL import Image  # noqa: E402

from core.image_index import TRASH_DIR  # noqa: E402


class Log:
    def __getattr__(self, name):
        return lambda *a, **k: None


@pytest.fixture
def lib(tmp_path):
    folder = tmp_path / "lib"
    (folder / "sub").mkdir(parents=True)
    (folder / TRASH_DIR / "sub").mkdir(parents=True)
    Image.new("RGB", (32, 32), (200, 0, 0)).save(folder / "a.png")
    Image.new("RGB", (32, 32), (0, 200, 0)).save(folder / "sub" / "c.png")
    Image.new("RGB", (32, 32), (0, 0, 200)).save(folder / TRASH_DIR / "sub" / "b.png")
    return folder


def names(paths):
    # unique: Generate Metadata's *.png and *.PNG globs both match on Windows
    return sorted({Path(p).name for p in paths})


def test_checkpoint_sorter(lib):
    from sorters.checkpoint_sorter import CheckpointSorter
    found = CheckpointSorter(Log())._find_png_files(str(lib), True)
    assert names(p for p, _rel in found) == ["a.png", "c.png"]


def test_metadata_generator(lib):
    from sorters.metadata_generator import MetadataGenerator
    found = MetadataGenerator(Log())._find_png_files(str(lib), True)
    assert names(p for p, _rel in found) == ["a.png", "c.png"]


def test_flattener(lib, tmp_path):
    from sorters.image_flattener import ImageFlattener
    target = tmp_path / "flat"
    ImageFlattener(Log()).flatten_images(str(lib), target_dir=str(target), move_files=False,
                                         remove_empty_dirs=False)
    assert names(target.iterdir()) == ["a.png", "c.png"]
    assert (lib / TRASH_DIR / "sub" / "b.png").exists()


def test_filename_cleanup(lib):
    from sorters.filename_cleanup import FilenameCleanup
    tool = FilenameCleanup(Log())
    tool.cleanup_directory(str(lib), remove_metadata_files=False, rename_files=True,
                           filename_prefix="x", dry_run=True)
    assert tool.stats["total_files"] == 2


def test_civitai_prep_listing(lib):
    from sorters.civitai_prep import list_pngs
    assert names(list_pngs(lib, recursive=True)) == ["a.png", "c.png"]


def test_upscaler_listing(lib):
    from sorters.upscaler import list_images
    assert names(list_images(lib, recursive=True, exclude=lib / "upscaled")) == ["a.png", "c.png"]
