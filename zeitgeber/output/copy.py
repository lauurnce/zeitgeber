"""The string catalog for plan outputs (copy.toml) and the clock-time format.

Every user-facing string lives in ``copy.toml`` with an English and a Taglish version, so the
wording can be reviewed in one place (docs/COPY_REVIEW.md) and changed without touching code.
"""

from __future__ import annotations

import string
import tomllib
from dataclasses import dataclass
from datetime import date, datetime, time
from functools import cache
from pathlib import Path
from typing import Literal

Lang = Literal["en", "tl"]
LANGS: tuple[Lang, ...] = ("en", "tl")
CATALOG = Path(__file__).with_name("copy.toml")


@dataclass(frozen=True)
class Entry:
    key: str
    where: str
    en: str
    tl: str

    def text(self, lang: Lang) -> str:
        return self.en if lang == "en" else self.tl

    @property
    def placeholders(self) -> dict[Lang, set[str]]:
        return {lang: fields_of(self.text(lang)) for lang in LANGS}


def fields_of(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


@cache
def _load() -> tuple[dict[str, Entry], dict[Lang, tuple[str, ...]]]:
    with CATALOG.open("rb") as f:
        raw = tomllib.load(f)
    entries = {
        key: Entry(key, str(v["where"]), str(v["en"]), str(v["tl"]))
        for key, v in raw["strings"].items()
    }
    weekdays: dict[Lang, tuple[str, ...]] = {lang: tuple(raw["weekdays"][lang]) for lang in LANGS}
    return entries, weekdays


def entries() -> dict[str, Entry]:
    return _load()[0]


def text(key: str, lang: Lang, **values: object) -> str:
    """The catalog string ``key`` in ``lang`` with its placeholders filled."""
    return entries()[key].text(lang).format(**values)


def clock(t: datetime | time) -> str:
    """12-hour clock as people write it in Manila: "2 AM", "9:30 AM", "12 PM"."""
    hour, minute = t.hour, t.minute
    suffix = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return f"{h12} {suffix}" if minute == 0 else f"{h12}:{minute:02d} {suffix}"


def day_label(d: date, lang: Lang) -> str:
    """Short date label, for example "Mon 16 Nov" or "Lun 16 Nov"."""
    return f"{_load()[1][lang][d.weekday()]} {d.day} {d:%b}"


SECTIONS = (
    ("disclaimer", "Disclaimers", "Top of the timeline, the plan JSON and the calendar."),
    ("rec", "Recommendations", 'The "What to change" list.'),
    ("nudge", "Nudges", "One per plan event; also the calendar reminder text."),
    ("event", "Event titles", "Timeline rows and calendar event names."),
    ("change", "Names of changes", "Used inside the explanations."),
    ("explain", "Explanations", 'The "Why" list.'),
    ("timeline", "Timeline", "Headings and labels in the daily text view."),
    ("ics", "Calendar", "Calendar export."),
)


def review_markdown() -> str:
    """docs/COPY_REVIEW.md: every catalog string side by side, grouped by where it appears."""
    from zeitgeber.output.wording import BANNED_TERMS, NUMBER_WORDS

    weekdays = _load()[1]
    out = [
        "# Copy review",
        "",
        "Every user-facing string in the plan outputs (timeline, plan JSON, calendar export and",
        "nudges), in English and Taglish. Generated from `zeitgeber/output/copy.toml` by",
        "`uv run python scripts/copy_review.py`; a test fails when this file and the catalog",
        "differ. To change wording, edit the catalog (or mark changes here and they are copied",
        "over), then regenerate.",
        "",
        "Status: all Taglish strings are drafts waiting for review by a native speaker.",
        "",
        "Words in braces are filled from the plan: `{start}` and `{end}` are clock times such",
        'as "2 AM" or "9:30 AM", `{minutes}` and `{hours}` are whole numbers, `{with}` and',
        "`{without}` are scores in hours with one decimal, `{change}` is a name from",
        '"Names of changes". Keep every placeholder in both languages.',
        "",
        "Filled-in examples for the three fixture workers: `tests/golden/*.txt`.",
        "",
        "Not covered here: the web site copy in `web/src/lib/site.ts` (English only for now).",
    ]
    all_entries = entries()
    for prefix, title, note in SECTIONS:
        out += [
            "",
            f"## {title}",
            "",
            note,
            "",
            "| Key | Where | English | Taglish |",
            "|---|---|---|---|",
        ]
        for key, e in all_entries.items():
            if key.split(".")[0] == prefix:
                where = e.where.replace("|", "/")
                out.append(f"| `{key}` | {where} | {e.en} | {e.tl} |")
    out += [
        "",
        "## Weekday labels",
        "",
        "| English | Taglish |",
        "|---|---|",
        *(f"| {en} | {tl} |" for en, tl in zip(weekdays["en"], weekdays["tl"], strict=True)),
        "",
        "## Grounding check word lists",
        "",
        "Rewordings from the optional language model are rejected when they contain one of these",
        "terms (matched at the start of a word, any case). Add Tagalog terms that should also be",
        "blocked.",
        "",
        ", ".join(f"`{t}`" for t in BANNED_TERMS),
        "",
        "Number words counted as numbers, so a rewording cannot add a quantity in words. The",
        'Tagalog linker form ("dalawang", "isang") is counted too.',
        "",
        ", ".join(f"`{w}`" for w in NUMBER_WORDS),
    ]
    return "\n".join(out) + "\n"
