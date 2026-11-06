"""Calendar export (RFC 5545) with reminders, in the schedule's local time.

One VEVENT per plan event that asks something of the worker (sleep, nap, light, sunglasses,
caffeine), plus shifts and commutes unless ``include_fixed`` is False. Times carry
``TZID=Asia/Manila`` with a matching VTIMEZONE so Google Calendar and Apple Calendar show them
in Manila time. Zones whose UTC offset changes during the plan fall back to UTC times. Each
reminder is a VALARM of type DISPLAY. UIDs are stable for a given plan, so importing the same
plan twice updates the events instead of duplicating them.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from zeitgeber.output.copy import Lang, text
from zeitgeber.output.plan import PlanDocument, PlanEvent

PRODID = "-//Zeitgeber//Plan 1.0//EN"
FIXED_KINDS = ("shift", "commute_to_work", "commute_home")
_LIMIT = 75  # octets per line before folding (RFC 5545 3.1)


def escape(value: str) -> str:
    """Escape a TEXT value (RFC 5545 3.3.11)."""
    return value.replace("\\", "\\\\").replace(";", r"\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line: str) -> list[str]:
    """Split a content line into lines of at most 75 octets, never inside a UTF-8 character."""
    out: list[str] = []
    current, size, limit = "", 0, _LIMIT
    for ch in line:
        n = len(ch.encode())
        if size + n > limit:
            out.append(current)
            current, size, limit = " ", 1, _LIMIT
        current += ch
        size += n
    out.append(current)
    return out


def _duration(minutes: int) -> str:
    return "PT0S" if minutes == 0 else f"-PT{minutes}M"


def _utc(t: datetime) -> str:
    return t.strftime("%Y%m%dT%H%M%SZ")


def _local(t: datetime) -> str:
    return t.strftime("%Y%m%dT%H%M%S")


def _fixed_offset(doc: PlanDocument) -> timedelta | None:
    offsets = {e.start_local.utcoffset() for e in doc.events()}
    offsets |= {e.end_local.utcoffset() for e in doc.events()}
    if len(offsets) == 1:
        (offset,) = offsets
        return offset
    return None


def _offset(td: timedelta) -> str:
    minutes = int(td.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    return f"{sign}{abs(minutes) // 60:02d}{abs(minutes) % 60:02d}"


def _vtimezone(tzid: str, offset: timedelta) -> list[str]:
    off = _offset(offset)
    return [
        "BEGIN:VTIMEZONE",
        f"TZID:{tzid}",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        f"TZOFFSETFROM:{off}",
        f"TZOFFSETTO:{off}",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]


def _vevent(
    doc: PlanDocument, e: PlanEvent, lang: Lang, description: str, tzid: str | None, alarms: bool
) -> list[str]:
    if tzid is None:
        start, end = f"DTSTART:{_utc(e.start_utc)}", f"DTEND:{_utc(e.end_utc)}"
    else:
        start = f"DTSTART;TZID={tzid}:{_local(e.start_local)}"
        end = f"DTEND;TZID={tzid}:{_local(e.end_local)}"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{e.id}-{doc.plan_id}@zeitgeber",
        f"DTSTAMP:{_utc(doc.generated_at)}",
        start,
        end,
        f"SUMMARY:{escape(e.title.get(lang))}",
        f"DESCRIPTION:{escape(description)}",
        f"CATEGORIES:{e.kind.upper()}",
        "TRANSP:TRANSPARENT" if e.kind not in FIXED_KINDS else "TRANSP:OPAQUE",
    ]
    if alarms and e.reminder is not None:
        related = ";RELATED=END" if e.reminder.related == "end" else ""
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER{related}:{_duration(e.reminder.minutes_before)}",
            f"DESCRIPTION:{escape(description)}",
            "END:VALARM",
        ]
    return [*lines, "END:VEVENT"]


def render_ics(
    doc: PlanDocument, lang: Lang = "en", alarms: bool = True, include_fixed: bool = True
) -> str:
    """The plan as an iCalendar file (CRLF line endings, folded lines)."""
    offset = _fixed_offset(doc)
    tzid = doc.timezone if offset is not None else None
    nudges = {n.event_id: n.text.get(lang) for n in doc.nudges}
    calname = text("ics.calendar_name", lang)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(calname)}",
        f"X-WR-CALDESC:{escape(' '.join(d.get(lang) for d in doc.disclaimers))}",
    ]
    if tzid is not None and offset is not None:
        lines.append(f"X-WR-TIMEZONE:{tzid}")
        lines += _vtimezone(tzid, offset)
    for e in doc.events():
        if e.kind in FIXED_KINDS and not include_fixed:
            continue
        description = nudges.get(e.id, e.title.get(lang))
        lines += _vevent(doc, e, lang, description, tzid, alarms)
    lines.append("END:VCALENDAR")
    return "".join(f"{part}\r\n" for line in lines for part in fold(line))
