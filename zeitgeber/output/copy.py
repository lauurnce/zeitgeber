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
