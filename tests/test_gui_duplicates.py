import json
import os
import subprocess
import sys
from pathlib import Path

SORTER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter"))


def run_app(script: str, tmp_path: Path) -> str:
    """Run `script` against a fresh SorterGUI in its own process (one Tk root
    per process), with the settings file and index pointed into tmp_path."""
    prelude = f"""
import gui
from pathlib import Path
gui.DUP_SETTINGS_PATH = Path(r"{tmp_path / 'settings.json'}")
gui.DUP_INDEX_PATH = Path(r"{tmp_path / 'idx.db'}")
"""
    done = subprocess.run([sys.executable, "-c", prelude + script], cwd=SORTER,
                          capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert "OK" in done.stdout, done.stderr[-3000:]
    return done.stdout


def test_dup_mode_switches_form_and_remembers_folders(tmp_path):
    folder = tmp_path / "pics"
    folder.mkdir()
    run_app(f"""
gui.filedialog.askdirectory = lambda **k: r"{folder}"
app = gui.SorterGUI(); app.withdraw()
assert "Find Duplicates" in app.mode_menu.cget("values")
app.mode_var.set("Find Duplicates"); app._switch_mode(); app.update()
assert app.dup_frame.winfo_manager() == "pack"
app._dup_add_folder()
app.dup_strictness_var.set("Strict"); app._dup_save_settings()
app.destroy(); print("OK")
""", tmp_path)
    saved = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert saved == {"folders": [str(folder.resolve())], "strictness": "Strict"}
    run_app(f"""
app = gui.SorterGUI(); app.withdraw()
assert app.dup_folders == [r"{folder.resolve()}"], app.dup_folders
assert app.dup_strictness_var.get() == "Strict"
app.destroy(); print("OK")
""", tmp_path)


def test_importing_gui_does_not_load_torch():
    # Scan workers re-import the launching script (gui.py) on Windows; torch
    # there would cost ~500 MB and ~2 s per worker
    done = subprocess.run(
        [sys.executable, "-c", "import sys, gui; print('torch' in sys.modules, "
                               "'ultralytics' in sys.modules)"],
        cwd=SORTER, capture_output=True, text=True, timeout=120)
    assert done.stdout.strip().splitlines()[-1] == "False False", done.stderr[-2000:]


def test_scan_workers_capped():
    sys.path.insert(0, SORTER)
    from core.image_index import MAX_WORKERS, default_workers
    assert MAX_WORKERS == 8
    assert default_workers() == max(1, min(MAX_WORKERS, (os.cpu_count() or 2) - 1))


def test_trash_panel_reports_counts(tmp_path):
    folder = tmp_path / "pics"
    trash = folder / "_duplicates_trash"
    trash.mkdir(parents=True)
    lines = []
    for name in ("a.png", "b.png"):
        (trash / name).write_bytes(b"x" * 1000)
        lines.append(json.dumps({"original": str(folder / name), "trashed": str(trash / name),
                                 "sidecars": [], "keeper": "", "kind": "certain", "time": ""}))
    (trash / "_trash_log.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "settings.json").write_text(
        json.dumps({"folders": [str(folder.resolve())], "strictness": "Normal"}), encoding="utf-8")
    run_app("""
app = gui.SorterGUI(); app.withdraw(); app.update()
text = app.dup_trash_label.cget("text")
assert text.startswith("🗑 Duplicates trash: 2 files"), text
app.destroy(); print("OK")
""", tmp_path)
