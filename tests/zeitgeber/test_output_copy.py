"""String catalog: both languages, matching placeholders, house voice."""

from datetime import date, time

import pytest
from golden import ROOT

from zeitgeber.output.copy import LANGS, clock, day_label, entries, review_markdown, text

ENTRIES = list(entries().values())


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e.key)
def test_each_string_has_both_languages_with_the_same_placeholders(entry) -> None:
    assert entry.en.strip() and entry.tl.strip() and entry.where.strip()
    found = entry.placeholders
    assert found["en"] == found["tl"]


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e.key)
def test_strings_follow_the_house_voice(entry) -> None:
    for lang in LANGS:
        s = entry.text(lang)
        assert s.isascii(), "no dashes, emoji or curly quotes"


def test_clock_matches_how_times_are_written() -> None:
    assert clock(time(2)) == "2 AM"
    assert clock(time(9, 30)) == "9:30 AM"
    assert clock(time(0)) == "12 AM"
    assert clock(time(12)) == "12 PM"
    assert clock(time(16, 45)) == "4:45 PM"


def test_labels_and_filled_templates() -> None:
    assert day_label(date(2026, 11, 16), "en") == "Mon 16 Nov"
    assert day_label(date(2026, 11, 22), "tl") == "Lin 22 Nov"
    assert text("nudge.caffeine", "tl", end="2 AM").startswith("2 AM ang huling kape mo.")


def test_copy_review_doc_matches_the_catalog() -> None:
    committed = (ROOT / "docs" / "COPY_REVIEW.md").read_text(encoding="utf-8")
    assert committed == review_markdown(), "run: uv run python scripts/copy_review.py"


def test_copy_review_lists_every_string() -> None:
    doc = review_markdown()
    assert all(f"`{key}`" in doc for key in entries())
