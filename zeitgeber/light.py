"""Solar times and the lux profile builder.

Every lux value comes from docs/SCIENCE.md 3.5 and is a named field of ``LuxConstants`` so tests
can scale it. Sun times use the NOAA method as implemented by astral 3.2 (docs/SCIENCE.md 9).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

import numpy as np
from astral import Observer
from astral.sun import sun
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from zeitgeber.grid import REQUEST_STEP_H, TimeGrid
from zeitgeber.schedule import Interval, Location, Schedule


class LuxConstants(BaseModel):
    """Photopic lux at the eye for each light environment (docs/SCIENCE.md 3.5)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outdoor_sun: float = Field(10_000.0, description="outdoors, sun up, open")
    shade_or_vehicle: float = Field(1_000.0, description="outdoors in shade or inside a vehicle")
    office: float = Field(500.0, description="call-center floor or office")
    home: float = Field(100.0, description="home, awake, lights on")
    home_dim_phone: float = Field(30.0, description="home, lights low, phone in hand")
    sleep: float = Field(1.0, description="sleep in a dark room")
    night_street: float = Field(10.0, description="outdoors or in transit after dark")
    light_seek: float = Field(1_000.0, description="light-seeking window in the shift (rule R1)")
    sunglasses: dict[str, float] = Field(
        default_factory=lambda: {"none": 1.0, "cat3": 0.15, "dark": 0.02},
        description="transmission factor while the sun is up",
    )
    max_lux: float = Field(10_000.0, description="model input cap (docs/SCIENCE.md 1.7)")


@dataclass(frozen=True)
class SolarTimes:
    """Sun events for one local date, as UTC instants."""

    dawn: datetime
    sunrise: datetime
    noon: datetime
    sunset: datetime
    dusk: datetime


@lru_cache(maxsize=4096)
def solar_times(location: Location, day: date) -> SolarTimes:
    """Civil dawn, sunrise, solar noon, sunset and civil dusk for a local date."""
    events = sun(Observer(location.latitude, location.longitude), date=day, tzinfo=location.tz)
    return SolarTimes(
        **{k: events[k].astimezone(UTC) for k in ("dawn", "sunrise", "noon", "sunset", "dusk")}
    )


def sun_up(location: Location, grid: TimeGrid) -> NDArray[np.bool_]:
    """True for samples between sunrise and sunset. Civil twilight counts as dark."""
    tz = location.tz
    first = grid.start.astimezone(tz).date() - timedelta(days=1)
    last = grid.end.astimezone(tz).date() + timedelta(days=1)
    out = np.zeros(grid.n, dtype=bool)
    day = first
    while day <= last:
        times = solar_times(location, day)
        out |= grid.mask(times.sunrise, times.sunset)
        day += timedelta(days=1)
    return out


# Environment codes stored with every sample, used by the timeline and the explanations.
HOME, OFFICE, COMMUTE_OUTDOOR, COMMUTE_TRANSIT, SLEEP, PRE_SLEEP_DIM = range(6)
LIGHT_SEEK, NAP, LIGHT_BRAKE = range(6, 9)
LABELS = {
    HOME: "home",
    OFFICE: "office",
    COMMUTE_OUTDOOR: "commute, outdoors",
    COMMUTE_TRANSIT: "commute, in transit",
    SLEEP: "sleep",
    PRE_SLEEP_DIM: "phone in bed",
    LIGHT_SEEK: "bright light in the shift",
    NAP: "pre-shift nap",
    LIGHT_BRAKE: "outdoor light brake",
}


class LightInterventions(BaseModel):
    """Interventions that change the light profile. More arrive with the planner (Z9)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sunglasses: str = Field("none", pattern="^(none|cat3|dark)$")


@dataclass(frozen=True)
class LightProfile:
    """Lux at the eye and the environment code for every sample of ``grid``."""

    grid: TimeGrid
    lux: NDArray[np.float64]
    labels: NDArray[np.int8]


def build_light_profile(
    schedule: Schedule,
    start: date | None = None,
    days: int | None = None,
    step_h: float = REQUEST_STEP_H,
    interventions: LightInterventions | None = None,
    constants: LuxConstants | None = None,
    extras: Sequence[Interval] = (),
) -> LightProfile:
    """Lux over ``days`` local days from ``start`` (defaults: the schedule's plan window).

    Awake time at home is indoor light; shifts are office light; sleep is dark; the minutes of
    phone use before each sleep are dim. Commutes put the outdoor share half at the start and half
    at the end (walking to and from transport) and the rest in transit. Outdoors means
    ``outdoor_sun`` and transit means ``shade_or_vehicle`` while the sun is up, and
    ``night_street`` for both after sunset. Sunglasses scale the commute home while the sun is up
    (rule R2, docs/SCIENCE.md 5.4).

    ``extras`` are planner blocks laid over the result: a ``light_seek`` block raises office light
    to at least ``light_seek`` (R1) and only inside a shift; a ``nap`` block is dark (N3); a
    ``light_brake`` block is outdoors in the sun (R5) and has no effect after sunset.
    """
    k = constants or LuxConstants()
    chosen = interventions or LightInterventions()
    grid = TimeGrid.covering(*schedule.window_utc(start, days), step_h=step_h)
    daylight = sun_up(schedule.location, grid)
    lux = np.full(grid.n, k.home, dtype=np.float64)
    labels = np.full(grid.n, HOME, dtype=np.int8)
    intervals = schedule.materialize(start, days)
    dim = timedelta(minutes=schedule.sleep.phone_in_bed_min)

    for iv in intervals:
        if iv.kind in ("sleep", "rest_sleep") and dim:
            m = grid.mask(iv.start - dim, iv.start) & (labels == HOME)
            lux[m], labels[m] = k.home_dim_phone, PRE_SLEEP_DIM
    for iv in intervals:
        m = grid.mask(iv.start, iv.end)
        if iv.kind == "shift":
            lux[m], labels[m] = k.office, OFFICE
        elif iv.kind in ("sleep", "rest_sleep"):
            lux[m], labels[m] = k.sleep, SLEEP
        else:
            commute = (
                schedule.commute_home if iv.kind == "commute_home" else schedule.commute_to_work
            )
            first = timedelta(minutes=commute.outdoor_min // 2)
            last = timedelta(minutes=commute.outdoor_min - commute.outdoor_min // 2)
            outdoor = grid.mask(iv.start, iv.start + first) | grid.mask(iv.end - last, iv.end)
            outdoor &= m
            transit = m & ~outdoor
            lux[outdoor] = np.where(daylight[outdoor], k.outdoor_sun, k.night_street)
            lux[transit] = np.where(daylight[transit], k.shade_or_vehicle, k.night_street)
            labels[outdoor], labels[transit] = COMMUTE_OUTDOOR, COMMUTE_TRANSIT
            if iv.kind == "commute_home":
                shaded = m & daylight
                lux[shaded] *= k.sunglasses[chosen.sunglasses]
    for iv in extras:
        m = grid.mask(iv.start, iv.end)
        if iv.kind == "light_seek":
            m &= labels == OFFICE
            lux[m], labels[m] = np.maximum(lux[m], k.light_seek), LIGHT_SEEK
        elif iv.kind == "nap":
            lux[m], labels[m] = k.sleep, NAP
        elif iv.kind == "light_brake":
            m &= daylight
            lux[m], labels[m] = k.outdoor_sun, LIGHT_BRAKE
        else:
            raise ValueError(f"extras take nap, light_seek or light_brake blocks, not {iv.kind}")
    np.minimum(lux, k.max_lux, out=lux)
    return LightProfile(grid, lux, labels)
