"""Solar times and the lux profile builder.

Every lux value comes from docs/SCIENCE.md 3.5 and is a named field of ``LuxConstants`` so tests
can scale it. Sun times use the NOAA method as implemented by astral 3.2 (docs/SCIENCE.md 9).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import numpy as np
from astral import Observer
from astral.sun import sun
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from zeitgeber.grid import TimeGrid
from zeitgeber.schedule import Location


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
