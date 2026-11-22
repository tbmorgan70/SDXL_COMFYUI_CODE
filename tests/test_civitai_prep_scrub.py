import json
import os
import sys
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from sorters.civitai_prep import CivitaiPrep  # noqa: E402

NEGATIVE = "child, teen"


def make_png(folder: Path, name: str, positive: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add_text("parameters",
                  f"{positive}\nNegative prompt: {NEGATIVE}\n"
                  "Steps: 20, Sampler: Euler, CFG scale: 7, Seed: 1, Size: 64x64")
    info.add_text("prompt", json.dumps({"1": {"class_type": "Note", "inputs": {}}}))
    p = folder / name
    Image.new("RGB", (64, 64), "gray").save(p, pnginfo=info)
    return p


def make_prep(tmp_path: Path, rules: str = None, rules_path: str = None) -> CivitaiPrep:
    if rules is not None:
        rules_path = str(tmp_path / "rules.txt")
        Path(rules_path).write_text(rules, encoding="utf-8")
    (tmp_path / "models").mkdir(exist_ok=True)
    return CivitaiPrep(None, str(tmp_path / "models"), cache_path=str(tmp_path / "c.json"),
                       api_lookup=False, rules_path=rules_path)


def written_params(src: Path, name: str) -> str:
    with Image.open(src / "civitai_ready" / name) as im:
        return im.info["parameters"]


def test_positive_scrubbed_negative_untouched(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "teen girl, park")
    prep = make_prep(tmp_path, "teen girl => young woman\nchild => (flag)")
    report = prep.process_folder(str(src), enrich=False)
    params = written_params(src, "a.png")
    assert params.startswith("young woman, park")
    assert f"Negative prompt: {NEGATIVE}" in params
    assert report["scrub"]["enabled"] is True
    assert report["scrub"]["prompts_changed"] == 1
    assert report["scrub"]["changes"] == 1
    assert report["scrub"]["flagged_images"] == 0


def test_flagged_image_written_and_reported(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "kite.png", "a child's kite")
    prep = make_prep(tmp_path, "child => (flag)")
    report = prep.process_folder(str(src), enrich=False)
    assert report["stats"]["written"] == 1
    assert written_params(src, "kite.png").startswith("a child's kite")
    assert report["scrub"]["flagged_images"] == 1
    rp = src / "civitai_ready" / "scrub_report.txt"
    assert report["scrub"]["report_path"] == str(rp)
    text = rp.read_text(encoding="utf-8")
    assert "kite.png" in text and "child" in text


def test_scrub_off(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "teen girl, park")
    prep = make_prep(tmp_path, "teen girl => young woman")
    report = prep.process_folder(str(src), enrich=False, scrub=False)
    assert written_params(src, "a.png").startswith("teen girl, park")
    assert report["scrub"]["enabled"] is False
    assert not (src / "civitai_ready" / "scrub_report.txt").exists()


def test_no_rules_file_runs_unscrubbed(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "teen girl, park")
    prep = make_prep(tmp_path, rules_path=str(tmp_path / "missing.txt"))
    report = prep.process_folder(str(src), enrich=False)
    assert report["stats"]["written"] == 1
    assert report["scrub"]["enabled"] is False
    assert written_params(src, "a.png").startswith("teen girl, park")


def test_rule_errors_reported(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "park")
    prep = make_prep(tmp_path, "re:([ => x\nkid => (flag)")
    report = prep.process_folder(str(src), enrich=False)
    assert report["scrub"]["enabled"] is True
    assert len(report["scrub"]["rule_errors"]) == 1
    assert report["scrub"]["rule_errors"][0].startswith("line 1")


def test_nothing_to_report_writes_no_report(tmp_path):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "a woman in a park")
    prep = make_prep(tmp_path, "teen girl => young woman\nchild => (flag)")
    report = prep.process_folder(str(src), enrich=False)
    assert report["scrub"]["report_path"] is None
    assert not (src / "civitai_ready" / "scrub_report.txt").exists()


def test_non_string_positive_is_skipped(tmp_path, monkeypatch):
    src = tmp_path / "imgs"
    make_png(src, "a.png", "teen girl")
    prep = make_prep(tmp_path, "teen girl => young woman")
    real = prep.analyze_image

    def linked(*a, **k):
        r = real(*a, **k)
        r["prompts"] = {"positive": ["5", 0], "negative": ""}
        return r

    monkeypatch.setattr(prep, "analyze_image", linked)
    report = prep.process_folder(str(src), enrich=False)
    assert report["stats"]["written"] == 1
    assert report["scrub"]["prompts_changed"] == 0
