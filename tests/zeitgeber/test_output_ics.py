"""Calendar export: parse the file back with icalendar and compare it with the plan."""

from datetime import UTC, datetime, timedelta

import icalendar
import pytest
from fixture_plans import planned

from zeitgeber.output import plan_document
from zeitgeber.output.ics import FIXED_KINDS, escape, fold, render_ics

FIXTURES = ["permanent_nights", "rotating", "day_worker"]
GENERATED = datetime(2026, 11, 6, tzinfo=UTC)


def calendar(name: str, **kwargs: object) -> tuple[str, list[icalendar.Component]]:
    doc = plan_document(planned(name), GENERATED)
    text = render_ics(doc, **kwargs)  # type: ignore[arg-type]
    cal = icalendar.Calendar.from_ical(text)
    return text, list(cal.walk("VEVENT"))


@pytest.mark.parametrize("name", FIXTURES)
@pytest.mark.parametrize("lang", ["en", "tl"])
def test_round_trip_matches_every_event(name: str, lang: str) -> None:
    doc = plan_document(planned(name), GENERATED)
    text = render_ics(doc, lang)  # type: ignore[arg-type]
    cal = icalendar.Calendar.from_ical(text)
    events = list(cal.walk("VEVENT"))
    planned_events = doc.events()
    assert len(events) == len(planned_events)
    nudges = {n.event_id: n.text.get(lang) for n in doc.nudges}  # type: ignore[arg-type]
    for vevent, e in zip(events, planned_events, strict=True):
        start, end = vevent.get("DTSTART").dt, vevent.get("DTEND").dt
        assert start == e.start_utc and end == e.end_utc
        assert str(start.tzinfo) == "Asia/Manila" and start.utcoffset() == timedelta(hours=8)
        assert str(vevent.get("SUMMARY")) == e.title.get(lang)  # type: ignore[arg-type]
        assert str(vevent.get("DESCRIPTION")) == nudges.get(e.id, e.title.get(lang))  # type: ignore[arg-type]
        alarms = list(vevent.walk("VALARM"))
        if e.reminder is None:
            assert alarms == []
        else:
            (alarm,) = alarms
            assert alarm.get("TRIGGER").dt == -timedelta(minutes=e.reminder.minutes_before)
            related = alarm.get("TRIGGER").params.get("RELATED", "START")
            assert related == e.reminder.related.upper()
    uids = [str(v.get("UID")) for v in events]
    assert len(set(uids)) == len(uids)


def test_file_follows_rfc_5545_line_rules() -> None:
    text, _ = calendar("permanent_nights", lang="tl")
    assert text.endswith("\r\n") and "\n" not in text.replace("\r\n", "")
    lines = text.split("\r\n")[:-1]
    assert all(len(line.encode()) <= 75 for line in lines)
    assert lines[:2] == ["BEGIN:VCALENDAR", "VERSION:2.0"] and lines[-1] == "END:VCALENDAR"
    for needed in ("PRODID:", "BEGIN:VTIMEZONE", "TZID:Asia/Manila", "TZOFFSETTO:+0800"):
        assert any(line.startswith(needed) for line in lines), needed
    assert "DTSTAMP:20261106T000000Z" in text


def test_same_plan_gives_the_same_file() -> None:
    assert calendar("permanent_nights")[0] == calendar("permanent_nights")[0]


def test_fixed_events_and_alarms_can_be_left_out() -> None:
    _, events = calendar("permanent_nights", include_fixed=False, alarms=False)
    assert events
    assert not any(str(v.get("CATEGORIES").cats[0]).lower() in FIXED_KINDS for v in events)
    assert all(list(v.walk("VALARM")) == [] for v in events)


def test_escape_and_fold() -> None:
    assert escape("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"
    long = "DESCRIPTION:" + "Tulog ñ " * 30
    parts = fold(long)
    assert all(len(p.encode()) <= 75 for p in parts)
    assert "".join(p[1:] if i else p for i, p in enumerate(parts)) == long
