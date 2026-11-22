import os
import subprocess
import sys
from pathlib import Path

SORTER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter"))
# Child processes print emoji; a Windows pipe defaults to cp1252
UTF8_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run_app(script: str, tmp_path: Path) -> str:
    """Run `script` against a fresh SorterGUI in its own process."""
    prelude = f"""
import gui
from pathlib import Path
gui.DUP_SETTINGS_PATH = Path(r"{tmp_path / 'settings.json'}")
gui.DUP_INDEX_PATH = Path(r"{tmp_path / 'idx.db'}")
"""
    done = subprocess.run([sys.executable, "-c", prelude + script], cwd=SORTER,
                          capture_output=True, text=True, encoding="utf-8", timeout=120,
                          env=UTF8_ENV)
    assert "OK" in done.stdout, done.stderr[-3000:]
    return done.stdout


def test_scrub_checkbox_defaults_on_and_mirrors_into_plain_bool(tmp_path):
    run_app("""
app = gui.SorterGUI(); app.withdraw()
assert app.civitai_scrub_var.get() is True and app.civitai_scrub is True
assert "Scrub prompts" in app.civitai_scrub_check.cget("text")
app.civitai_scrub_check.toggle()   # what a click does: flips the var, fires the command
assert app.civitai_scrub_var.get() is False and app.civitai_scrub is False
app.civitai_scrub_check.toggle()
assert app.civitai_scrub is True
app.destroy(); print("OK")
""", tmp_path)


def test_edit_rules_opens_notepad_on_user_file(tmp_path):
    run_app("""
calls = []
gui.subprocess.Popen = lambda args, **k: calls.append(args)
app = gui.SorterGUI(); app.withdraw()
app._edit_scrub_rules()
assert calls and calls[0][0] == "notepad", calls
assert calls[0][1].endswith("scrub_rules.txt") and Path(calls[0][1]).is_file()
app.destroy(); print("OK")
""", tmp_path)


def test_window_header_shows_current_version(tmp_path):
    run_app("""
from version import VERSION
app = gui.SorterGUI(); app.withdraw()
assert f"Sorter {VERSION} " in app.title_label.cget("text"), app.title_label.cget("text")
app.destroy(); print("OK")
""", tmp_path)


def test_scrub_log_lines():
    run = {"scrub": {"enabled": True, "prompts_changed": 2, "changes": 3, "flagged_images": 1,
                     "report_path": "x", "rule_errors": ["line 4: bad regex"]}}
    # Exercise the static helper without building the whole GUI
    done = subprocess.run(
        [sys.executable, "-c",
         "import gui; print(gui.SorterGUI._scrub_log_lines(" + repr(run) + "))"],
        cwd=SORTER, capture_output=True, text=True, encoding="utf-8", timeout=120, env=UTF8_ENV)
    assert "line 4: bad regex" in done.stdout
    assert "Scrubbed 2 prompts (3 changes)" in done.stdout and "1 images flagged" in done.stdout
    off = subprocess.run(
        [sys.executable, "-c",
         "import gui; print(gui.SorterGUI._scrub_log_lines({'scrub': {'enabled': False}}))"],
        cwd=SORTER, capture_output=True, text=True, encoding="utf-8", timeout=120, env=UTF8_ENV)
    assert off.stdout.strip() == "[]"
