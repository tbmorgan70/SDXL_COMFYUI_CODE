# Prompt Scrubber Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Civitai Prep rewrites known-bad phrases in the positive prompt using a user-editable rules file,
and lists images with words that have no safe rewrite.

**Architecture:** A self-contained `core/prompt_scrubber.py` parses `scrub_rules.txt` and scrubs a string.
`CivitaiPrep.process_folder` calls it on the positive prompt before `build_parameters` and writes
`scrub_report.txt`. The GUI adds a checkbox and an Edit rules button; the 🏷️ sort chain uses the same setting.

**Tech Stack:** Python 3.11 (`python`, never `py -3`), `re`, Pillow, customtkinter, pytest.

**Spec:** `docs/superpowers/specs/2026-11-22-prompt-scrubber-design.md`

## Global Constraints

- Positive prompt only; the negative prompt is never changed.
- Matching is case-insensitive and whole-word/phrase: `teen` must not match `canteen` or `seventeen`.
- Flagged images are still written, with the flagged word unchanged.
- A rule that fails to parse is skipped and logged with its line number; the run continues.
- `sorter/scrub_rules.default.txt` is tracked; `sorter/scrub_rules.txt` is gitignored and created from the default on first use.
- The workflow/prompt JSON chunks are not edited.
- Tests import from `sorter/` via `sys.path.insert(0, <repo>/sorter)` like `tests/test_civitai_sampler_name.py`.
- Work in this worktree; commit per task; do not push.

## Review Focus

1. **Notepad-saved rules file** (UTF-8 with BOM, CRLF line endings) — first rule must still parse. Test in Task 1.
2. **Punctuation at phrase edges** (`late teens, or early 20s,` followed by a comma; `(teen girl:1.2)` weights) — match and keep the surrounding syntax. Test in Task 1.
3. **A flag word inside a phrase that a rule already rewrote** (`teen` vs `teen girl => young woman`) — must not flag. Flags are checked after all rewrites. Test in Task 1.
4. **User rules file deleted, or default file missing too** — user file is recreated from default; if both are missing, prep runs unscrubbed with one warning. Test in Task 2.
5. **Positive prompt that isn't a string** (a linked `[node, slot]` list, or empty) — skipped, no crash. Test in Task 2.

---

### Task 1: Rules parser and scrubber

**Files:**
- Create: `sorter/core/prompt_scrubber.py`
- Create: `sorter/scrub_rules.default.txt`
- Modify: `.gitignore` (add `sorter/scrub_rules.txt` next to `sorter/civitai_hash_cache.json`)
- Test: `tests/test_prompt_scrubber.py`

**Interfaces:**
- Produces:
  - `DEFAULT_RULES_NAME = "scrub_rules.default.txt"`, `USER_RULES_NAME = "scrub_rules.txt"`
  - `@dataclass Rule(pattern: re.Pattern, action: str, replacement: str, source: str, line: int)`; `action` ∈ `"replace" | "remove" | "flag"`
  - `@dataclass ScrubResult(text: str, changes: list[tuple[str, str]], flags: list[tuple[str, str]])` — `changes` = (matched text, replacement or `""`); `flags` = (matched text, context)
  - `parse_rules(text: str) -> tuple[list[Rule], list[str]]` — rules, error messages (`"line 7: bad regex …"`)
  - `class PromptScrubber(rules: list[Rule], errors: list[str] = [])` with `.scrub(text: str) -> ScrubResult`, `.errors`, and `@classmethod from_file(path: str | Path) -> PromptScrubber` (reads `utf-8-sig`)
  - `ensure_user_rules(sorter_dir: str | Path) -> Path | None` — copies the default to the user name if the user file is missing; returns the user path, or `None` if neither exists

**Decisions the implementer can't infer:**
- Line format: `phrase => target`, split on the **first** `=>`, both sides stripped. Blank lines and lines starting with `#` are skipped. A line without `=>` is an error.
- Target `(remove)` → remove, `(flag)` → flag, anything else → replace with that text verbatim.
- Plain phrase → `re.escape`, with each run of whitespace becoming `\s+`, wrapped in `(?<!\w)…(?!\w)`, `re.IGNORECASE`. Lines starting with `re:` use the rest as the pattern, `re.IGNORECASE`.
- Order: regex rules first in file order, then plain rules longest-source first. Flag rules run after every replace/remove rule, against the rewritten text.
- Tidy only if at least one `remove` matched: `\s+,` → `,`; `(,\s*){2,}` → `, `; runs of spaces → one; strip leading/trailing `,` and spaces.
- Flag context: up to 30 characters each side of the match, newlines turned into spaces.

- [ ] **Step 1: Write the failing tests** in `tests/test_prompt_scrubber.py`

```python
def test_replace_phrase_case_insensitive():
    s = PromptScrubber(*parse_rules("teen girl => young woman"))
    assert s.scrub("A Teen Girl smiling").text == "A young woman smiling"

def test_whole_words_only():
    s = PromptScrubber(*parse_rules("teen => (flag)"))
    r = s.scrub("a canteen, seventeen candles")
    assert r.flags == [] and r.text == "a canteen, seventeen candles"

def test_phrase_with_punctuation_edges():
    s = PromptScrubber(*parse_rules("in her late teens, or early 20s => in her early 20s"))
    assert s.scrub("woman, in her late teens, or early 20s, red hair").text == \
        "woman, in her early 20s, red hair"

def test_weight_syntax_kept():
    s = PromptScrubber(*parse_rules("teen girl => young woman"))
    assert s.scrub("(teen girl:1.2), park").text == "(young woman:1.2), park"

def test_remove_tidies_commas():
    s = PromptScrubber(*parse_rules("Audrey Hepburn => (remove)"))
    assert s.scrub("portrait, Audrey Hepburn, film grain").text == "portrait, film grain"

def test_flag_leaves_text_and_reports_context():
    s = PromptScrubber(*parse_rules("child => (flag)"))
    r = s.scrub("a child's toy on a table")
    assert r.text == "a child's toy on a table"
    assert r.flags[0][0] == "child" and "toy" in r.flags[0][1]

def test_flags_checked_after_rewrites():
    s = PromptScrubber(*parse_rules("teen => (flag)\nteen girl => young woman"))
    r = s.scrub("teen girl at the beach")
    assert r.text == "young woman at the beach" and r.flags == []

def test_longest_plain_phrase_first():
    s = PromptScrubber(*parse_rules("late teens => 20s\nin her late teens, or early 20s => in her early 20s"))
    assert s.scrub("in her late teens, or early 20s").text == "in her early 20s"

def test_bad_lines_are_reported_and_skipped():
    rules, errors = parse_rules("# c\n\nre:([ => x\nno arrow here\nkid => (flag)")
    assert len(rules) == 1 and len(errors) == 2
    assert errors[0].startswith("line 3") and errors[1].startswith("line 4")

def test_notepad_bom_and_crlf(tmp_path):
    p = tmp_path / "r.txt"
    p.write_bytes("﻿teen girl => young woman\r\nkid => (flag)\r\n".encode("utf-8"))
    s = PromptScrubber.from_file(p)
    assert s.scrub("teen girl").text == "young woman" and not s.errors

def test_ensure_user_rules(tmp_path):
    (tmp_path / DEFAULT_RULES_NAME).write_text("kid => (flag)\n", encoding="utf-8")
    p = ensure_user_rules(tmp_path)
    assert p == tmp_path / USER_RULES_NAME and p.read_text(encoding="utf-8") == "kid => (flag)\n"
    p.write_text("mine\n", encoding="utf-8")
    assert ensure_user_rules(tmp_path).read_text(encoding="utf-8") == "mine\n"   # never overwritten

def test_ensure_user_rules_nothing_there(tmp_path):
    assert ensure_user_rules(tmp_path) is None

def test_shipped_default_rules_parse_cleanly():
    rules, errors = parse_rules((SORTER / DEFAULT_RULES_NAME).read_text(encoding="utf-8-sig"))
    assert errors == [] and len(rules) >= 10
```

- [ ] **Step 2: Run** `python -m pytest tests/test_prompt_scrubber.py -v` — expected: import error / FAIL.

- [ ] **Step 3: Implement `sorter/core/prompt_scrubber.py`** per the interfaces and decisions above.

- [ ] **Step 4: Create `sorter/scrub_rules.default.txt`** with exactly this content:

```
# Prompt Scrubber rules - used by Civitai Prep on the positive prompt.
# One rule per line:   phrase => replacement     phrase => (remove)     phrase => (flag)
# Matching ignores case and only hits whole words ("teen" never matches "canteen").
# (flag) changes nothing; the image is listed in scrub_report.txt for you to check.
# Lines starting with re: are regular expressions. They run first, in file order;
# plain phrases then run longest first. Flags are checked last.

re:in her late teens,? (or|to) (her )?early (20s|twenties) => in her early 20s
in her late teens => in her early 20s
teen girl => young woman
teenage girl => young woman
teenagers => young adults
teenager => young woman
Audrey Hepburn => (remove)

young teen => (flag)
teen => (flag)
teens => (flag)
schoolgirl => (flag)
little girl => (flag)
child => (flag)
children => (flag)
kid => (flag)
kids => (flag)
```

- [ ] **Step 5: Add `sorter/scrub_rules.txt` to `.gitignore`.**

- [ ] **Step 6: Run** `python -m pytest tests/test_prompt_scrubber.py -v` — expected: all PASS.

- [ ] **Step 7: Commit** — `git add sorter/core/prompt_scrubber.py sorter/scrub_rules.default.txt .gitignore tests/test_prompt_scrubber.py` then `git commit -m "Prompt Scrubber: rules parser and scrubber"`.

---

### Task 2: Scrub during Civitai Prep, report, CLI

**Files:**
- Modify: `sorter/sorters/civitai_prep.py` (`CivitaiPrep.__init__`, `process_folder`, `__main__` argparse)
- Test: `tests/test_civitai_prep_scrub.py`

**Interfaces:**
- Consumes: `PromptScrubber`, `ensure_user_rules`, `ScrubResult` from Task 1.
- Produces:
  - `CivitaiPrep(logger, models_dir, cache_path=None, api_lookup=True, rules_path: Optional[str] = None)`. `rules_path=None` → `ensure_user_rules(<sorter dir>)`.
  - `process_folder(..., scrub: bool = True, ...)`; the returned dict gains
    `'scrub': {'enabled': bool, 'prompts_changed': int, 'changes': int, 'flagged_images': int, 'report_path': Optional[str], 'rule_errors': list[str]}`.
  - CLI: `--no-scrub`, `--rules PATH`.

**Decisions:**
- Build the scrubber once, lazily, on the first `process_folder(scrub=True)`. Log each rule error (`⚠️ scrub rules line 7: …`). If no rules file can be found, log `⚠️ Prompt Scrubber off: no rules file found` once and set `enabled: False`.
- Scrub `analysis['prompts']['positive']` only when it's a non-empty `str`, right after `analyze_image` and before `build_parameters`.
- `scrub_report.txt` goes in `out_dir` and is overwritten each run. It's written only if there are changes or flags. Layout: a header line with counts; `== Flagged (check these) ==` with `relative/path.png | word | …context…`; `== Changed ==` with `relative/path.png | before → after` (paths relative to `source`).
- Log line after the run, only if `enabled`: `🧽 Scrubbed {prompts_changed} prompts ({changes} changes); ⚠️ {flagged_images} images flagged — see scrub_report.txt`. Drop the flagged clause when it's 0.

- [ ] **Step 1: Write the failing tests.** Build each fixture PNG with Pillow: 64×64, a `parameters` tEXt chunk (`"<prompt>\nNegative prompt: child, teen\nSteps: 20, Sampler: Euler, CFG scale: 7, Seed: 1, Size: 64x64"`), and a minimal `prompt` JSON chunk, so `has_metadata` is true. Construct with `CivitaiPrep(None, str(tmp_path / "models"), cache_path=str(tmp_path / "c.json"), api_lookup=False, rules_path=<tmp rules>)`. Read the written PNG back with `Image.open(p).info["parameters"]`.

```python
def test_positive_scrubbed_negative_untouched(tmp_path): ...
    # rules "teen girl => young woman\nchild => (flag)"; prompt "teen girl, park"
    # assert written params start with "young woman, park"
    # assert "Negative prompt: child, teen" still in params
    # assert report['scrub']['prompts_changed'] == 1 and report['scrub']['flagged_images'] == 0

def test_flagged_image_written_and_reported(tmp_path): ...
    # prompt "a child's kite"; assert stats['written'] == 1, flagged_images == 1,
    # civitai_ready/scrub_report.txt exists and contains the png name and "child"

def test_scrub_off(tmp_path): ...
    # process_folder(scrub=False) → prompt unchanged, report['scrub']['enabled'] is False, no scrub_report.txt

def test_no_rules_file_runs_unscrubbed(tmp_path): ...
    # rules_path=str(tmp_path / "missing.txt") → written == 1, enabled False, prompt unchanged

def test_nothing_to_report_writes_no_report(tmp_path): ...
    # clean prompt → no scrub_report.txt

def test_non_string_positive_is_skipped(tmp_path, monkeypatch): ...
    # monkeypatch analyze_image to return prompts={'positive': ['5', 0], 'negative': ''} → no exception, written == 1
```

The implementer fills each body following its comments.

- [ ] **Step 2: Run** `python -m pytest tests/test_civitai_prep_scrub.py -v` — expected: FAIL (unexpected `rules_path` / no `'scrub'` key).

- [ ] **Step 3: Implement** per the interfaces and decisions. In `__main__`, pass `rules_path=args.rules` and `scrub=not args.no_scrub`.

- [ ] **Step 4: Run** `python -m pytest tests/test_civitai_prep_scrub.py tests/test_prompt_scrubber.py tests/test_civitai_sampler_name.py -v` — expected: all PASS.

- [ ] **Step 5: Real-file check.** Copy 5–10 real Florence-captioned PNGs from ComfyUI output into a scratchpad folder, run `python sorter/sorters/civitai_prep.py <folder> --no-api`, and check that `civitai_ready/` prompts and `scrub_report.txt` look right. Originals are untouched.

- [ ] **Step 6: Commit** — `git commit -m "Civitai Prep: scrub positive prompts, scrub_report.txt, --no-scrub/--rules"`.

---

### Task 3: GUI, chain, docs and version

**Files:**
- Modify: `sorter/gui.py` — `_build_civitai_form` (~line 2068), `civitai_prep` (~2105), `_chain_civitai_prep` (~1859)
- Modify: `sorter/version.py`, `sorter/CHANGELOG.md`, `VERSION.md`, `ROADMAP.md`, `sorter/README.md`

**Interfaces:**
- Consumes: `CivitaiPrep.process_folder(scrub=...)`, `report['scrub']` from Task 2; `ensure_user_rules` from Task 1.

**Decisions:**
- `self.civitai_scrub_var = ctk.BooleanVar(value=True)`, a checkbox labelled `🧽 Scrub prompts` after "Strip workflow JSON". Next to it, a button `✏️ Edit rules` → `ensure_user_rules(<sorter dir>)` then `subprocess.Popen(["notepad", str(path)])`. If it returns `None`, show `messagebox.showerror` naming the missing default file.
- The confirm dialog gains the line `   Scrub prompts: Yes (scrub_rules.txt)` or `No`.
- Both `run_prep` and `_chain_civitai_prep` pass `scrub=self.civitai_scrub_var.get()` (read on the main thread before starting the worker) and enqueue the same `🧽` summary line as the Task 2 log, plus each rule error.
- The info label gains a second sentence: `🧽 Scrub prompts rewrites flagged words from scrub_rules.txt (positive prompt only).`
- Version: Sorter `3.8.0`, BUILD_DATE today, DESCRIPTION `"Advanced ComfyUI Image Organizer - Prompt Scrubber (3.8.0)"`, `"Prompt Scrubber for Civitai Prep"` appended to FEATURES. Repo version in VERSION.md → `3.9.0`, codename "Prompt Scrubber".
- CHANGELOG: `## [3.8.0] - <date> - Prompt Scrubber`, with an ✨ Added entry describing the rules file, auto-rewrite + flag list, report, checkbox and Edit rules, and CLI flags.
- ROADMAP: status line → `(v3.9, Sorter 3.8.0 — November 2026)` plus a `✅ Prompt Scrubber (3.8)` bullet. Mark idea #2 done. Add a Next Up item: `Try the Prompt Scrubber on a real upload batch and grow scrub_rules.txt`.
- sorter/README: a short Civitai Prep subsection on the scrubber and the rules format.

- [ ] **Step 1: Implement the GUI changes.**
- [ ] **Step 2: Smoke test.** Launch `python sorter/gui.py` and open Civitai Prep. Check that the checkbox and button show, and that Edit rules opens Notepad on `sorter/scrub_rules.txt` (created from the default). Run prep on the Task 2 scratchpad folder with the checkbox on; the 🧽 line should appear in the progress log. Close.
- [ ] **Step 3: Update the version and docs files** per the decisions.
- [ ] **Step 4: Run the full suite** `python -m pytest -q` — expected: only the known old failure (`tests/test_extract_primary_checkpoint.py` collect error, which imports the removed `sorter_v2`). Report anything else.
- [ ] **Step 5: Commit** — `git commit -m "Sorter 3.8.0: Prompt Scrubber in the GUI and 🏷️ chain, docs, version"`.
