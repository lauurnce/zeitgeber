"""Optional rewording of nudges, held to the plan by a grounding check.

A :class:`Rewriter` receives one filled template at a time, never the schedule. Its output is
used only when :class:`GroundingCheck` finds no time or number that the template did not
already contain, no term from the medical blocklist, and no large growth in length. Anything
else, including an error from the provider, falls back to the template text.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Protocol

from zeitgeber.output.copy import Lang

# Medical terms that must never appear in a nudge (CLAUDE.md wellness framing), with common
# English forms and Tagalog equivalents. Matched case-insensitively at word starts.
BANNED_TERMS: tuple[str, ...] = (
    r"melatonin\w*",
    r"dos(?:e|es|age|ages|ing)",
    r"disorders?",
    r"treat(?:s|ed|ing|ment|ments)?",
    r"cur(?:e|es|ed|ing)",
    r"diagnos\w*",
    r"medications?",
    r"medicines?",
    r"prescri\w*",
    r"pills?",
    r"supplements?",
    r"insomnia",
    r"sedatives?",
    r"gamot\w*",
    r"gamutin",
    r"ginagamot",
    r"lunas\w*",
    r"malunasan",
    r"reseta",
    r"nireseta\w*",
    r"pampatulog",
    r"tableta\w*",
    r"diyagnos\w*",
    r"sakit",
)

# Number words in English, Tagalog and the Spanish-derived numbers used in Taglish times.
NUMBER_WORDS: dict[str, float] = {
    **dict.fromkeys(("zero", "wala"), 0.0),
    **{
        w: float(i)
        for i, words in enumerate(
            [
                (),
                ("one", "isa", "uno"),
                ("two", "dalawa", "dos"),
                ("three", "tatlo", "tres"),
                ("four", "apat", "kwatro", "kuwatro"),
                ("five", "lima", "singko"),
                ("six", "anim", "sais"),
                ("seven", "pito", "siyete"),
                ("eight", "walo", "otso"),
                ("nine", "siyam", "nuwebe"),
                ("ten", "sampu", "diyes", "dyes"),
                ("eleven", "onse"),
                ("twelve", "dose"),
            ]
        )
        for w in words
    },
    **{w: float(n) for w, n in (("fifteen", 15), ("twenty", 20), ("thirty", 30), ("sixty", 60))},
    **dict.fromkeys(("half", "kalahati"), 0.5),
}

_TIME_12 = re.compile(
    r"(?<![\d:.])(\d{1,2})(?::([0-5]\d))?\s*([ap])\.?\s?m\b\.?", flags=re.IGNORECASE
)
_TIME_24 = re.compile(r"(?<![\d:.])([01]?\d|2[0-3]):([0-5]\d)(?![\d:])")
_NAMED_TIMES = {"noon": "12:00", "tanghali": "12:00", "midnight": "00:00", "hatinggabi": "00:00"}
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_WORD = re.compile(r"[a-z]+", flags=re.IGNORECASE)


def _num(value: float) -> str:
    return f"n:{value:g}"


def tokens(text: str) -> set[str]:
    """Every time ("t:HH:MM") and number ("n:value") in ``text``, in a canonical form."""
    found: set[str] = set()
    rest = text
    for m in _TIME_12.finditer(text):
        hour, minute = int(m.group(1)) % 12, int(m.group(2) or 0)
        hour += 12 if m.group(3).lower() == "p" else 0
        found.add(f"t:{hour:02d}:{minute:02d}")
    rest = _TIME_12.sub(" ", rest)
    for m in _TIME_24.finditer(rest):
        found.add(f"t:{int(m.group(1)):02d}:{m.group(2)}")
    rest = _TIME_24.sub(" ", rest)
    for m in _NUMBER.finditer(rest):
        found.add(_num(float(m.group(0).replace(",", "."))))
    for m in _WORD.finditer(rest):
        word = m.group(0).lower()
        if word in _NAMED_TIMES:
            found.add(f"t:{_NAMED_TIMES[word]}")
        elif word in NUMBER_WORDS:
            found.add(_num(NUMBER_WORDS[word]))
        elif word.endswith("ng") and word[:-2] in NUMBER_WORDS:
            found.add(_num(NUMBER_WORDS[word[:-2]]))  # Tagalog linker: "dalawang", "isang"
    return found


@dataclass(frozen=True)
class GroundingCheck:
    """Rejects text with a new time or number, a banned term, or too much added length."""

    banned_terms: tuple[str, ...] = BANNED_TERMS
    max_growth: float = 1.6  # output length at most 1.6 times the template, plus 40 characters

    def banned_in(self, text: str) -> list[str]:
        return [
            m.group(0)
            for term in self.banned_terms
            for m in re.finditer(rf"\b{term}\b", text, flags=re.IGNORECASE)
        ]

    def problems(self, text: str, template: str) -> list[str]:
        """Reasons to reject ``text`` as a rewording of ``template``; empty when it passes."""
        if not text.strip():
            return ["empty"]
        out = []
        new = sorted(tokens(text) - tokens(template))
        if new:
            out.append("not in the plan: " + ", ".join(new))
        banned = self.banned_in(text)
        if banned:
            out.append("blocked term: " + ", ".join(sorted({b.lower() for b in banned})))
        if len(text) > self.max_growth * len(template) + 40:
            out.append("too long")
        return out

    def passes(self, text: str, template: str) -> bool:
        return not self.problems(text, template)


class Rewriter(Protocol):
    """A wording provider. It sees one filled template and the language, nothing else."""

    def rewrite(self, text: str, lang: Lang) -> str: ...


@dataclass(frozen=True)
class Worded:
    text: str
    source: Literal["template", "rewritten", "fallback"]
    reason: str | None = None  # why a rewording was rejected


def finalize(template: str, lang: Lang, rewriter: Rewriter | None, check: GroundingCheck) -> Worded:
    """The rewording when it passes the check, otherwise the template."""
    if rewriter is None:
        return Worded(template, "template")
    try:
        candidate = rewriter.rewrite(template, lang).strip()
    except Exception as err:  # any provider failure falls back to the template
        return Worded(template, "fallback", f"provider error: {type(err).__name__}")
    problems = check.problems(candidate, template)
    if problems:
        return Worded(template, "fallback", "; ".join(problems))
    return Worded(candidate, "rewritten")


def finalize_all(
    items: Iterable[tuple[str, Lang]],
    rewriter: Rewriter | None,
    check: GroundingCheck | None = None,
    workers: int = 8,
) -> dict[tuple[str, Lang], Worded]:
    """Finalize each distinct (template, language) pair once, in parallel when rewording."""
    check = check or GroundingCheck()
    unique = list(dict.fromkeys(items))
    if rewriter is None or len(unique) <= 1:
        return {k: finalize(k[0], k[1], rewriter, check) for k in unique}
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        done = pool.map(lambda k: finalize(k[0], k[1], rewriter, check), unique)
        return dict(zip(unique, done, strict=True))
