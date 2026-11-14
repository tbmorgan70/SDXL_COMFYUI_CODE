import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from PIL import Image  # noqa: E402

from sorters.manual_sorter import ManualSorter  # noqa: E402


def _imgs(folder, names):
    for n in names:
        Image.new("RGB", (8, 8)).save(folder / n)


def test_execute_defaults_to_folders_inside_source(tmp_path):
    _imgs(tmp_path, ["a.png"])
    s = ManualSorter(None, tmp_path, ["Keep"])
    s.assign(tmp_path / "a.png", "Keep")
    s.execute()
    assert (tmp_path / "Keep" / "a.png").exists()


def test_execute_into_chosen_output_folder(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out" / "deep"
    src.mkdir()
    _imgs(src, ["a.png", "b.png"])
    s = ManualSorter(None, src, ["Keep"])
    s.assign(src / "a.png", "Keep")
    s.assign(src / "b.png", "Trash")
    s.execute(dest_root=out)
    assert (out / "Keep" / "a.png").exists() and (out / "Trash" / "b.png").exists()
    assert not (src / "Keep").exists()
