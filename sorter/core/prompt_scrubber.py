"""
Prompt Scrubber - rewrite or flag words in prompts before Civitai upload.

Rules live in a plain text file (sorter/scrub_rules.txt, one per line):

    teen girl        => young woman
    Audrey Hepburn   => (remove)
    child            => (flag)
    re:in her late teens,? or early 20s => in her early 20s

Matching ignores case and only hits whole words or phrases. Regex rules
run first in file order, then plain phrases longest first; flag rules are
checked last against the rewritten text, so a phrase a rule already
rewrote is never flagged.
"""

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union

DEFAULT_RULES_NAME = "scrub_rules.default.txt"
USER_RULES_NAME = "scrub_rules.txt"

_CONTEXT_CHARS = 30


@dataclass
class Rule:
    pattern: "re.Pattern"
    action: str          # 'replace' | 'remove' | 'flag'
    replacement: str
    source: str
    line: int


@dataclass
class ScrubResult:
    text: str
    changes: List[Tuple[str, str]] = field(default_factory=list)   # (matched, replacement or "")
    flags: List[Tuple[str, str]] = field(default_factory=list)     # (matched, context)


def _plain_pattern(phrase: str) -> "re.Pattern":
    parts = [re.escape(p) for p in phrase.split()]
    return re.compile(r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", re.IGNORECASE)


def parse_rules(text: str) -> Tuple[List[Rule], List[str]]:
    """Parse rules text. Returns (rules, error messages)."""
    rules: List[Rule] = []
    errors: List[str] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=>" not in line:
            errors.append(f"line {n}: no '=>' in {line!r}")
            continue
        source, target = (s.strip() for s in line.split("=>", 1))
        if not source:
            errors.append(f"line {n}: nothing before '=>'")
            continue
        low = target.lower()
        action = "remove" if low == "(remove)" else "flag" if low == "(flag)" else "replace"
        replacement = target if action == "replace" else ""
        if source.startswith("re:"):
            try:
                pattern = re.compile(source[3:].strip(), re.IGNORECASE)
            except re.error as e:
                errors.append(f"line {n}: bad regex {source[3:].strip()!r} ({e})")
                continue
        else:
            pattern = _plain_pattern(source)
        rules.append(Rule(pattern, action, replacement, source, n))
    return rules, errors


def _tidy(text: str) -> str:
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"(,\s*){2,}", ", ", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip(" ,")


class PromptScrubber:
    def __init__(self, rules: List[Rule], errors: Optional[List[str]] = None):
        self.errors = list(errors or [])
        rewrites = [r for r in rules if r.action != "flag"]
        regex = [r for r in rewrites if r.source.startswith("re:")]
        plain = sorted((r for r in rewrites if not r.source.startswith("re:")),
                       key=lambda r: len(r.source), reverse=True)
        self._rewrites = regex + plain
        self._flags = [r for r in rules if r.action == "flag"]

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "PromptScrubber":
        text = Path(path).read_text(encoding="utf-8-sig")
        return cls(*parse_rules(text))

    def scrub(self, text: str) -> ScrubResult:
        result = ScrubResult(text=text)
        removed = False
        for rule in self._rewrites:
            def sub(m, rule=rule):
                result.changes.append((m.group(0), rule.replacement))
                return rule.replacement
            new = rule.pattern.sub(sub, result.text)
            if rule.action == "remove" and new != result.text:
                removed = True
            result.text = new
        if removed:
            result.text = _tidy(result.text)
        for rule in self._flags:
            for m in rule.pattern.finditer(result.text):
                a = max(0, m.start() - _CONTEXT_CHARS)
                b = min(len(result.text), m.end() + _CONTEXT_CHARS)
                context = re.sub(r"\s*\n\s*", " ", result.text[a:b])
                result.flags.append((m.group(0), context))
        return result


def ensure_user_rules(sorter_dir: Union[str, Path]) -> Optional[Path]:
    """Return the user's rules file, copying the shipped default the first time.

    Never overwrites an existing user file. None if neither file exists.
    """
    sorter_dir = Path(sorter_dir)
    user = sorter_dir / USER_RULES_NAME
    if user.is_file():
        return user
    default = sorter_dir / DEFAULT_RULES_NAME
    if not default.is_file():
        return None
    shutil.copyfile(default, user)
    return user
