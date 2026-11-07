"""Intervention space, constraints, seeded search and explanations.

Interventions come from the rules in docs/SCIENCE.md 5.4 (R1 to R7) and 6.3 (C1 to C4, N1 to
N3); the search design is docs/ARCHITECTURE.md 4. A candidate plan is applied by building a
new :class:`Schedule` (so the schedule's own validation rejects any sleep that overlaps a shift
or a commute) plus planner light blocks (bright light in the shift, the pre-shift nap and the
outdoor light brake) that the light builder lays over the profile.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields, replace
from datetime import datetime, time, timedelta
from typing import Literal

from pydantic import ValidationError

from zeitgeber.schedule import (
    Interval,
    RestDayPolicy,
    Schedule,
    SleepWindow,
    SleepWindows,
)

Sunglasses = Literal["none", "cat3", "dark"]
RestChoice = Literal["current", "keep_nights", "01:00", "02:00", "03:00", "04:00"]

# Rule parameters. Values marked design are Zeitgeber's choices (docs/SCIENCE.md 5.4, 6.3).
SLEEP_OFFSETS_H = (0.0, 0.5, 1.0, 1.5)  # R3: start within 1.5 h of getting home
SLEEP_LENGTHS_H = (7.0, 8.0, 9.0)  # R3: at least 7 h
REST_SLEEP_H = 8.0  # R4: late rest-day window, 8 h
LIGHT_SEEK_LENGTHS_H = (0.5, 1.0)  # R1
LIGHT_SEEK_MARGIN_H = 2.0  # R1: end at least 2 h before CBTmin
BRAKE_AFTER_WAKE_H = 0.5  # R5: 15 min outdoors within 2 h of waking (placed 30 min after, design)
BRAKE_MIN = 15
NAP_LENGTHS_MIN = (30, 60, 90)  # N1
NAP_MARGIN_MIN = 30  # N1: ends 30 min before leaving home
CAFFEINE_CUTOFF_H = 6.0  # C1
CAFFEINE_CUTOFF_SLOW_H = 8.0  # C2
MIN_WORKDAY_SLEEP_H = 7.0  # R3


@dataclass(frozen=True)
class Interventions:
    """One candidate plan. Every default means "as the worker does now"."""

    sunglasses: Sunglasses = "none"  # R2 on the commute home; dark only for non-drivers (R7)
    sleep_start_offset_h: float | None = None  # R3, after-night-shift sleep, from getting home
    sleep_len_h: float | None = None  # R3
    rest_day: RestChoice = "current"  # R4 late window, or keep night hours
    light_brake: bool = False  # R5
    light_seek_start_h: float | None = None  # R1, hours after shift start
    light_seek_len_h: float = 1.0
    nap_len_min: int = 0  # N1, before night shifts

    def active(self) -> list[str]:
        """Names of the parameters that differ from "as now" (light seeking counts once)."""
        out = []
        for f in fields(self):
            if f.name == "light_seek_len_h":
                continue
            if getattr(self, f.name) != f.default:
                out.append(f.name)
        return out

    @property
    def burden(self) -> float:
        """Number of changes asked of the worker; dark lenses count 2 (ARCHITECTURE 4.3)."""
        return len(self.active()) + (1 if self.sunglasses == "dark" else 0)

    def without(self, name: str) -> Interventions:
        """This plan with one parameter back to "as now" (used by the ablations)."""
        defaults = {f.name: f.default for f in fields(self)}
        changes = {name: defaults[name]}
        if name == "light_seek_start_h":
            changes["light_seek_len_h"] = defaults["light_seek_len_h"]
        return replace(self, **changes)  # type: ignore[arg-type]


PARAM_ORDER = (
    "sunglasses",
    "sleep_start_offset_h",
    "sleep_len_h",
    "rest_day",
    "light_brake",
    "light_seek",
    "nap_len_min",
)
RULES = {
    "sunglasses": ("R2", "R7"),
    "sleep_start_offset_h": ("R3",),
    "sleep_len_h": ("R3",),
    "rest_day": ("R4",),
    "light_brake": ("R5",),
    "light_seek_start_h": ("R1",),
    "nap_len_min": ("N1", "N3"),
}


def _each(name: str, values: Sequence[object]) -> list[dict[str, object]]:
    return [{name: v} for v in values]


def _hours(td: timedelta) -> float:
    return td.total_seconds() / 3600.0


def _clock(t: time, hours: float) -> time:
    minutes = (t.hour * 60 + t.minute + round(hours * 60)) % (24 * 60)
    return time(minutes // 60, minutes % 60)


class InterventionSpace:
    """The values each parameter may take for one schedule (docs/ARCHITECTURE.md 4.1)."""

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule
        self.night_weekdays = sorted(s.weekday for s in schedule.shifts if s.crosses_midnight)
        night = [s for s in schedule.shifts if s.crosses_midnight]
        self.has_nights = bool(night)
        shortest = min(s.duration_min for s in schedule.shifts) / 60.0
        self.shift_len_h = shortest

    def values(self, name: str) -> list[dict[str, object]]:
        """Each allowed setting of one parameter, as field updates, "as now" first."""
        if name == "sunglasses":
            lenses: list[Sunglasses] = ["none", "cat3"]
            if not self.schedule.commute_home.drives:
                lenses.append("dark")  # R7
            return _each(name, lenses)
        if name == "sleep_start_offset_h":
            if not self.has_nights:
                return [{name: None}]
            return _each(name, [None, *SLEEP_OFFSETS_H])
        if name == "sleep_len_h":
            if not self.has_nights:
                return [{name: None}]
            return _each(name, [None, *SLEEP_LENGTHS_H])
        if name == "rest_day":
            if not self.schedule.rest_weekdays:
                return [{name: "current"}]
            return [
                {name: v} for v in ("current", "keep_nights", "01:00", "02:00", "03:00", "04:00")
            ]
        if name == "light_brake":
            return _each(name, [False, True] if self.has_nights else [False])
        if name == "light_seek":
            out: list[dict[str, object]] = [{"light_seek_start_h": None, "light_seek_len_h": 1.0}]
            last = int(self.shift_len_h - LIGHT_SEEK_MARGIN_H)
            for start in range(0, last + 1):
                for length in LIGHT_SEEK_LENGTHS_H:
                    out.append({"light_seek_start_h": float(start), "light_seek_len_h": length})
            return out
        if name == "nap_len_min":
            if not self.has_nights:
                return [{name: 0}]
            return _each(name, [0, *NAP_LENGTHS_MIN])
        raise ValueError(f"unknown intervention parameter {name!r}")


class InfeasibleError(ValueError):
    """A candidate breaks a hard constraint (docs/ARCHITECTURE.md 4.2)."""


@dataclass(frozen=True)
class CaffeineWindow:
    """When caffeine fits for one shift: first half of the shift and before the cutoff."""

    shift: Interval
    next_sleep_start: datetime
    cutoff: datetime  # next main sleep start minus 6 h (C1) or 8 h (C2)
    allowed: tuple[datetime, datetime] | None  # None when the cutoff falls before the shift


@dataclass(frozen=True)
class AppliedPlan:
    interventions: Interventions
    schedule: Schedule
    blocks: tuple[Interval, ...]  # nap, light_seek and light_brake blocks, UTC
    caffeine: tuple[CaffeineWindow, ...]


def _sleep_windows(base: Schedule, c: Interventions) -> SleepWindows:
    sleep = base.sleep
    if c.sleep_start_offset_h is None and c.sleep_len_h is None:
        return sleep
    home = timedelta(minutes=base.commute_home.duration_min)
    by_weekday = dict(sleep.after_shift_by_weekday)
    first: SleepWindow | None = None
    for shift in sorted(base.shifts, key=lambda s: s.weekday):
        if not shift.crosses_midnight:
            continue
        habit = sleep.for_shift(shift.weekday)
        arrive = _clock(shift.end, _hours(home))
        habit_offset = (
            _hours(
                datetime.combine(datetime.min, habit.start) - datetime.combine(datetime.min, arrive)
            )
            % 24.0
        )
        offset = habit_offset if c.sleep_start_offset_h is None else c.sleep_start_offset_h
        length = habit.duration_min / 60.0 if c.sleep_len_h is None else c.sleep_len_h
        start = _clock(arrive, offset)
        window = SleepWindow(start=start, end=_clock(start, length))
        by_weekday[shift.weekday] = window
        first = first or window
    if first is None:
        return sleep
    return sleep.model_copy(update={"after_shift": first, "after_shift_by_weekday": by_weekday})


def _rest(
    base: Schedule, c: Interventions, sleep: SleepWindows
) -> tuple[SleepWindows, RestDayPolicy]:
    if c.rest_day == "current":
        return sleep, base.rest_days
    if c.rest_day == "keep_nights":
        return sleep, RestDayPolicy(mode="keep_nights")
    start = time.fromisoformat(c.rest_day)
    window = SleepWindow(start=start, end=_clock(start, REST_SLEEP_H))
    return sleep.model_copy(update={"rest_day": window}), RestDayPolicy(mode="flip_to_days")


def apply(base: Schedule, c: Interventions, slow_caffeine: bool = False) -> AppliedPlan:
    """Turn a candidate into a schedule and light blocks, or raise :class:`InfeasibleError`."""
    if c.sunglasses == "dark" and base.commute_home.drives:
        raise InfeasibleError("dark lenses are not offered to someone who drives home (R7)")
    sleep, rest = _rest(base, c, _sleep_windows(base, c))
    try:
        schedule = Schedule.model_validate(
            {**base.model_dump(), "sleep": sleep.model_dump(), "rest_days": rest.model_dump()}
        )
    except ValidationError as err:
        raise InfeasibleError(str(err.errors()[0]["msg"])) from err

    day_before = schedule.anchor_date - timedelta(days=1)
    intervals = schedule.materialize(day_before, schedule.plan_days + 2)
    shifts = [iv for iv in intervals if iv.kind == "shift"]
    to_work = [iv for iv in intervals if iv.kind == "commute_to_work"]
    sleeps = [iv for iv in intervals if iv.kind in ("sleep", "rest_sleep")]
    night = {s.weekday for s in schedule.shifts if s.crosses_midnight}
    tz = schedule.location.tz
    blocks: list[Interval] = []
    for sh in shifts:
        is_night = sh.start.astimezone(tz).weekday() in night
        if c.light_seek_start_h is not None:
            s = sh.start + timedelta(hours=c.light_seek_start_h)
            blocks.append(
                Interval(s, s + timedelta(hours=c.light_seek_len_h), "light_seek", "bright light")
            )
        if c.nap_len_min and is_night:
            leave = next((iv.start for iv in to_work if iv.end == sh.start), sh.start)
            end = leave - timedelta(minutes=NAP_MARGIN_MIN)
            blocks.append(Interval(end - timedelta(minutes=c.nap_len_min), end, "nap", "nap"))
    if c.light_brake:
        for sl in sleeps:
            if sl.kind == "sleep" and any(
                sh.end <= sl.start < sh.end + timedelta(hours=4)
                for sh in shifts
                if sh.start.astimezone(tz).weekday() in night
            ):
                s = sl.end + timedelta(hours=BRAKE_AFTER_WAKE_H)
                blocks.append(
                    Interval(s, s + timedelta(minutes=BRAKE_MIN), "light_brake", "outdoors")
                )
    occupied = [iv for iv in intervals if iv.kind != "shift"] + shifts
    for b in blocks:
        if b.kind == "light_seek":
            continue
        clash = next((iv for iv in occupied if iv.overlaps(b)), None)
        if clash is not None:
            raise InfeasibleError(f"the {b.label} block overlaps {clash.label}")

    cutoff_h = CAFFEINE_CUTOFF_SLOW_H if slow_caffeine else CAFFEINE_CUTOFF_H
    caffeine = []
    for sh in shifts:
        nxt = min((sl.start for sl in sleeps if sl.start >= sh.end), default=None)
        if nxt is None:
            continue
        cutoff = nxt - timedelta(hours=cutoff_h)
        half = sh.start + (sh.end - sh.start) / 2  # C3: first half of the shift
        end = min(half, cutoff)
        caffeine.append(
            CaffeineWindow(sh, nxt, cutoff, (sh.start, end) if end > sh.start else None)
        )
    return AppliedPlan(c, schedule, tuple(blocks), tuple(caffeine))
