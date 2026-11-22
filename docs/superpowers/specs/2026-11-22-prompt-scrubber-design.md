# Prompt Scrubber — design (2026-11-22)

## Why
Florence2 captions sometimes put words into prompts that get images blocked on Civitai: "teen girl",
"in her late teens, or early 20s", celebrity names ("Audrey Hepburn"). Today the user edits the prompt on
Civitai and appeals each block. The goal is to clean these prompts before upload, using a word list the
user maintains and grows as Civitai flags new phrases.

## Goals
- Rewrite known phrases automatically during Civitai Prep (the Civitai Prep tab and the 🏷️ chain after a sort).
- Words with no safe rewrite are **flagged, not changed**, and listed so the user can check those images.
- The user edits the rules in Notepad from an **Edit rules** button.
- The log says what happened: how many prompts were changed, and how many images were flagged.

## Non-goals
- No rules editor inside the GUI (that belongs with the later Metadata viewer/editor tab, ROADMAP idea #4).
- No "check only" dry run yet (that's ROADMAP idea #1, next after this).
- No ComfyUI node (that's a separate, optional workflow change).
- No automatic detection of celebrity names. The list is what the user writes.

## Anti-goals
- Matching inside other words ("teen" must not hit "canteen" or "seventeen").
- Leaving broken text behind after a removal (", , " or double spaces).
- Overwriting the user's rules when they `git pull`.
- Silently stopping a prep run because of one bad rule.

## Approaches considered
- **A. Rules text file + Edit rules button (chosen by the user).** A small scrub module called from Civitai
  Prep just before it writes. About a day of work, easy to grow, easy to back up.
- B. A rules table in the GUI. Several times the work, and largely redone by the Metadata editor tab later.
- C. A ComfyUI string-replace node only. It cleans new images but not the existing back catalog.

## Decided with the user
- Auto-apply the rewrites + a flag list (not a per-image review).
- Rules live in a text file opened in Notepad.

## Design
**Rules file format** (one rule per line, `#` starts a comment):
```
teen girl                         => young woman
in her late teens, or early 20s   => in her early 20s
Audrey Hepburn                    => (remove)
child                             => (flag)
re:\bin (her|his|their) late teens\b  => in her early 20s
```
- Matching is case-insensitive and on whole words or phrases. Lines starting with `re:` are regex.
- Longer phrases are applied first, so the full "late teens, or early 20s" phrase wins over a shorter rule.
- `(remove)` deletes the match, then tidies the commas and spaces around it.
- `(flag)` changes nothing. The image is listed in the report with the word and a little surrounding text.

**Files**
- `sorter/scrub_rules.default.txt` — tracked starter rules, including the user's examples.
- `sorter/scrub_rules.txt` — the user's own copy. It's created from the default on first use and gitignored,
  so pulls never overwrite it.
- New module `sorter/core/prompt_scrubber.py`: loads the rules and scrubs a string, returning the new text,
  the replacements made and the flags found.

**Where it runs**
- `CivitaiPrep.process_folder` scrubs the positive prompt from `analyze_image` before `build_parameters`.
  The workflow JSON is not edited: Florence text only lives in `parameters`, and "Strip workflow JSON"
  already covers typed template text.
- Civitai Prep tab: a **Scrub prompts** checkbox (on by default) and an **Edit rules** button.
  The 🏷️ chain uses the same setting.
- CLI: `--no-scrub` and `--rules PATH`.

**Output**
- Log: `🧽 Scrubbed 37 prompts (52 changes); ⚠️ 4 images flagged — see scrub_report.txt`.
- `scrub_report.txt` in the output folder (`civitai_ready/`, or the source folder when in place). It has two
  sections: flagged images (file, word, surrounding text) and changes made (file, before → after).

## My calls (please check)
- **Positive prompt only.** Negatives are left alone, because they often list these words on purpose to keep
  the model away from them.
- **Flagged images are still written,** with the flagged word unchanged, and listed in the report and log.
  They aren't held back.
- A rule that fails to load (for example, a broken regex) is skipped, logged with its line number, and the
  run goes on.
- The starter list has the user's examples plus obvious variants ("teenage girl", "teenager(s)", "young teen"
  as flag, "schoolgirl"/"little girl"/"kid(s)"/"child(ren)" as flag). Names beyond Audrey Hepburn are left
  for the user to add.

## Left to the builder
- Exact tidy-up rules after removal; tests for each anti-goal.
- Version bump (new feature → Sorter 3.8.0), CHANGELOG, README and ROADMAP updates.
- Tests use synthetic PNGs with a `parameters` chunk, plus one real Florence-captioned image from ComfyUI output.
