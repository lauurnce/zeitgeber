"""Schedule input models and validation.

Models follow docs/ARCHITECTURE.md 2.1 with the changes recorded in docs/DECISIONS.md D27. All
wall-clock times are local to ``Location.timezone``. ``Schedule.materialize`` is the only place
where they become timezone-aware UTC intervals, so shifts that cross midnight are handled once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MINUTES_PER_DAY = 24 * 60

CommuteMode = Literal["walk", "jeepney_bus", "train", "car_driver", "car_passenger", "motorcycle"]
RestDayMode = Literal["keep_nights", "flip_to_days", "split"]


def minutes_of(t: time) -> int:
    """Minutes after local midnight."""
    return t.hour * 60 + t.minute


def span_minutes(start: time, end: time) -> int:
    """Length of a wall-clock window; an end at or before the start means it crosses midnight."""
    length = (minutes_of(end) - minutes_of(start)) % MINUTES_PER_DAY
    return length or MINUTES_PER_DAY


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Location(_Model):
    """Where the worker lives. Defaults to Manila (docs/SCIENCE.md 9.4)."""

    name: str = "Manila"
    latitude: float = Field(14.5995, ge=-72.0, le=72.0)
    longitude: float = Field(120.9842, ge=-180.0, le=180.0)
    timezone: str = "Asia/Manila"

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"unknown time zone {value!r}; use an IANA name such as 'Asia/Manila'"
            ) from exc
        return value

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


class Shift(_Model):
    """One shift that starts on ``weekday`` (0 = Monday) at local ``start``."""

    weekday: int = Field(ge=0, le=6)
    start: time
    end: time

    @model_validator(mode="after")
    def _sensible_length(self) -> Shift:
        hours = self.duration_min / 60
        if not 4 <= hours <= 14:
            raise ValueError(
                f"the {WEEKDAY_NAMES[self.weekday]} shift {self.start:%H:%M} to {self.end:%H:%M} "
                f"lasts {hours:.1f} h; shifts must last 4 to 14 h"
            )
        return self

    @property
    def duration_min(self) -> int:
        return span_minutes(self.start, self.end)

    @property
    def crosses_midnight(self) -> bool:
        return minutes_of(self.start) + self.duration_min > MINUTES_PER_DAY


class Commute(_Model):
    """A one-way commute. ``outdoor_share`` is the fraction of it spent outdoors."""

    duration_min: int = Field(ge=0, le=300)
    outdoor_share: float = Field(0.0, ge=0.0, le=1.0)
    mode: CommuteMode = "jeepney_bus"

    @property
    def outdoor_min(self) -> int:
        return round(self.duration_min * self.outdoor_share)

    @property
    def drives(self) -> bool:
        """True when the worker drives or rides; dark lenses are not offered (rule R7)."""
        return self.mode in ("car_driver", "motorcycle")


class SleepWindow(_Model):
    """A local sleep window; an end at or before the start means it ends the next day."""

    start: time
    end: time

    @model_validator(mode="after")
    def _sensible_length(self) -> SleepWindow:
        hours = self.duration_min / 60
        if not 3 <= hours <= 12:
            raise ValueError(
                f"sleep window {self.start:%H:%M} to {self.end:%H:%M} lasts {hours:.1f} h; "
                "sleep windows must last 3 to 12 h"
            )
        return self

    @property
    def duration_min(self) -> int:
        return span_minutes(self.start, self.end)


class SleepWindows(_Model):
    """Current sleep habits.

    ``after_shift`` is the main sleep that follows each shift; ``after_shift_by_weekday`` overrides
    it for shifts starting on given weekdays, which rotating schedules need. ``rest_day`` is the
    sleep on rest days; ``rest_day_second`` is the second episode when the rest-day policy is
    ``split``. ``phone_in_bed_min`` is dim screen time before each sleep (docs/SCIENCE.md 3.5).
    """

    after_shift: SleepWindow
    after_shift_by_weekday: dict[int, SleepWindow] = Field(default_factory=dict)
    rest_day: SleepWindow
    rest_day_second: SleepWindow | None = None
    phone_in_bed_min: int = Field(0, ge=0, le=180)

    @field_validator("after_shift_by_weekday")
    @classmethod
    def _weekday_keys(cls, value: dict[int, SleepWindow]) -> dict[int, SleepWindow]:
        bad = sorted(k for k in value if not 0 <= k <= 6)
        if bad:
            raise ValueError(f"after_shift_by_weekday keys must be weekdays 0 to 6, got {bad}")
        return value

    def for_shift(self, weekday: int) -> SleepWindow:
        return self.after_shift_by_weekday.get(weekday, self.after_shift)


class RestDayPolicy(_Model):
    """How the worker sleeps on days without a shift.

    ``keep_nights``: the after-shift sleep times are kept on rest days. ``flip_to_days``: the
    ``rest_day`` window is used. ``split``: the ``rest_day`` window plus ``rest_day_second``.
    """

    mode: RestDayMode = "flip_to_days"


NOON = time(12)

IntervalKind = Literal["shift", "commute_to_work", "commute_home", "sleep", "rest_sleep"]


@dataclass(frozen=True)
class Interval:
    """An absolute, timezone-aware UTC interval ``[start, end)`` with a readable label."""

    start: datetime
    end: datetime
    kind: IntervalKind
    label: str

    def overlaps(self, other: Interval) -> bool:
        return self.start < other.end and other.start < self.end


def _local(d: date, t: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(d, t, tzinfo=tz)


def _hm(dt: datetime, tz: ZoneInfo) -> str:
    local = dt.astimezone(tz)
    return f"{WEEKDAY_NAMES[local.weekday()]} {local:%H:%M}"


class Schedule(_Model):
    """A weekly repeating work and sleep pattern, planned from ``anchor_date`` for ``plan_days``."""

    anchor_date: date
    plan_days: int = Field(14, ge=1, le=28)
    location: Location = Field(default_factory=Location)
    shifts: list[Shift] = Field(min_length=1)
    commute_to_work: Commute
    commute_home: Commute
    sleep: SleepWindows
    rest_days: RestDayPolicy = Field(default_factory=RestDayPolicy)

    @model_validator(mode="after")
    def _consistent(self) -> Schedule:
        seen: dict[int, Shift] = {}
        for shift in self.shifts:
            if shift.weekday in seen:
                raise ValueError(
                    f"two shifts start on {WEEKDAY_NAMES[shift.weekday]}; "
                    "v0.1 allows one shift per weekday"
                )
            seen[shift.weekday] = shift
        if self.rest_days.mode == "split" and self.sleep.rest_day_second is None:
            raise ValueError("rest-day policy 'split' needs sleep.rest_day_second")
        problems = self._conflicts()
        if problems:
            raise ValueError("schedule conflicts: " + "; ".join(problems[:3]))
        return self

    @property
    def rest_weekdays(self) -> list[int]:
        worked = {s.weekday for s in self.shifts}
        return [d for d in range(7) if d not in worked]

    def window_utc(
        self, start: date | None = None, days: int | None = None
    ) -> tuple[datetime, datetime]:
        """UTC bounds of the local days ``[start, start + days)``."""
        first = start or self.anchor_date
        tz = self.location.tz
        begin = _local(first, time(0), tz)
        end = _local(first + timedelta(days=days or self.plan_days), time(0), tz)
        return begin.astimezone(UTC), end.astimezone(UTC)

    def materialize(self, start: date | None = None, days: int | None = None) -> list[Interval]:
        """Shifts, commutes and sleeps as UTC intervals, clipped to the requested local days."""
        first = start or self.anchor_date
        span = days or self.plan_days
        begin, end = self.window_utc(first, span)
        clipped: list[Interval] = []
        built, _ = self._build(first - timedelta(days=1), span + 2)
        for iv in built:
            s, e = max(iv.start, begin), min(iv.end, end)
            if s < e:
                clipped.append(Interval(s, e, iv.kind, iv.label))
        return clipped

    def _build(self, first: date, days: int) -> tuple[list[Interval], list[str]]:
        """Intervals for ``days`` local days from ``first``, and any conflicts found."""
        tz = self.location.tz
        by_day = {s.weekday: s for s in self.shifts}
        work: list[Interval] = []
        problems: list[str] = []
        for offset in range(days):
            d = first + timedelta(days=offset)
            shift = by_day.get(d.weekday())
            if shift is None:
                continue
            name = f"{WEEKDAY_NAMES[shift.weekday]} shift"
            s = _local(d, shift.start, tz)
            e = s + timedelta(minutes=shift.duration_min)
            work.append(
                Interval(
                    s.astimezone(UTC),
                    e.astimezone(UTC),
                    "shift",
                    f"{name} ({shift.start:%H:%M} to {shift.end:%H:%M})",
                )
            )
            to_work = timedelta(minutes=self.commute_to_work.duration_min)
            home = timedelta(minutes=self.commute_home.duration_min)
            if to_work:
                work.append(
                    Interval(
                        (s - to_work).astimezone(UTC),
                        s.astimezone(UTC),
                        "commute_to_work",
                        f"commute to the {name}",
                    )
                )
            if home:
                work.append(
                    Interval(
                        e.astimezone(UTC),
                        (e + home).astimezone(UTC),
                        "commute_home",
                        f"commute home from the {name}",
                    )
                )
            window = self.sleep.for_shift(shift.weekday)
            local_end = e.astimezone(tz)
            sleep_start = _local(local_end.date(), window.start, tz)
            if sleep_start < local_end:
                sleep_start += timedelta(days=1)
            arrive = local_end + home
            if sleep_start < arrive:
                problems.append(
                    f"the sleep after the {name} starts at {_hm(sleep_start, tz)}, "
                    f"before you get home at {_hm(arrive, tz)}"
                )
            elif sleep_start - arrive > timedelta(hours=12):
                problems.append(
                    f"the sleep after the {name} would start "
                    f"{(sleep_start - arrive) / timedelta(hours=1):.0f} h after you get "
                    "home; check the after-shift sleep window"
                )
            sleep_end = sleep_start + timedelta(minutes=window.duration_min)
            work.append(
                Interval(
                    sleep_start.astimezone(UTC),
                    sleep_end.astimezone(UTC),
                    "sleep",
                    f"sleep after the {name} ({window.start:%H:%M} to {window.end:%H:%M})",
                )
            )
        work.sort(key=lambda iv: (iv.start, iv.end))
        for i, a in enumerate(work):
            for b in work[i + 1 :]:
                if b.start >= a.end:
                    break
                problems.append(f"{a.label} overlaps {b.label} on {_hm(max(a.start, b.start), tz)}")
        intervals = list(work)
        rest = self._rest_windows()
        for offset in range(days):
            d = first + timedelta(days=offset)
            if d.weekday() in by_day:
                continue
            for window in rest:
                # A window that starts before noon is the sleep of the night after the rest day.
                night = d + timedelta(days=1) if window.start < NOON else d
                s = _local(night, window.start, tz)
                e = s + timedelta(minutes=window.duration_min)
                candidate = Interval(
                    s.astimezone(UTC),
                    e.astimezone(UTC),
                    "rest_sleep",
                    f"rest-day sleep ({window.start:%H:%M} to {window.end:%H:%M})",
                )
                if not any(candidate.overlaps(iv) for iv in intervals):
                    intervals.append(candidate)
        intervals.sort(key=lambda iv: (iv.start, iv.end))
        return intervals, list(dict.fromkeys(problems))

    def _rest_windows(self) -> list[SleepWindow]:
        if self.rest_days.mode == "keep_nights":
            return [self.sleep.after_shift]
        windows = [self.sleep.rest_day]
        if self.rest_days.mode == "split" and self.sleep.rest_day_second is not None:
            windows.append(self.sleep.rest_day_second)
        return windows

    def _conflicts(self) -> list[str]:
        """Conflicts over two weeks, which covers every pair of weekdays in the pattern."""
        _, problems = self._build(self.anchor_date, 14)
        return problems
