"""Schedule input models and validation.

Models follow docs/ARCHITECTURE.md 2.1 with the changes recorded in docs/DECISIONS.md D27. All
wall-clock times are local to ``Location.timezone``. ``Schedule.materialize`` is the only place
where they become timezone-aware UTC intervals, so shifts that cross midnight are handled once.
"""

from __future__ import annotations

from datetime import time
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
