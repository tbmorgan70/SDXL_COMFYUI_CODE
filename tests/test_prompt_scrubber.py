import os
import sys
from pathlib import Path

SORTER = Path(__file__).resolve().parent.parent / "sorter"
sys.path.insert(0, str(SORTER))

from core.prompt_scrubber import (  # noqa: E402
    DEFAULT_RULES_NAME, USER_RULES_NAME, PromptScrubber, ensure_user_rules, parse_rules,
)


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


def test_remove_records_change():
    s = PromptScrubber(*parse_rules("Audrey Hepburn => (remove)"))
    assert s.scrub("portrait, audrey hepburn").changes == [("audrey hepburn", "")]


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
    s = PromptScrubber(*parse_rules(
        "late teens => 20s\nin her late teens, or early 20s => in her early 20s"))
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
    assert p == tmp_path / USER_RULES_NAME
    assert p.read_text(encoding="utf-8") == "kid => (flag)\n"
    p.write_text("mine\n", encoding="utf-8")
    assert ensure_user_rules(tmp_path).read_text(encoding="utf-8") == "mine\n"  # never overwritten


def test_ensure_user_rules_nothing_there(tmp_path):
    assert ensure_user_rules(tmp_path) is None


def test_shipped_default_rules_parse_cleanly():
    rules, errors = parse_rules((SORTER / DEFAULT_RULES_NAME).read_text(encoding="utf-8-sig"))
    assert errors == [] and len(rules) >= 10


def test_shipped_default_rules_on_florence_caption():
    rules, errors = parse_rules((SORTER / DEFAULT_RULES_NAME).read_text(encoding="utf-8-sig"))
    r = PromptScrubber(rules).scrub(
        "The image shows a woman in her late teens, or early 20s, resembling Audrey Hepburn, "
        "a teen girl walking past a canteen")
    assert r.text == ("The image shows a woman in her early 20s, resembling, "
                      "a young woman walking past a canteen")
    assert r.flags == []
