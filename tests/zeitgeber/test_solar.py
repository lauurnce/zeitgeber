"""Sun times for Manila against a published table.

Reference: U.S. Naval Observatory, Astronomical Applications Department, "Sun and Moon Data for
One Day", queried for 14.5995 N, 120.9842 E, UTC+8 on 2026-11-09.
https://aa.usno.navy.mil/api/rstt/oneday?date=2026-03-21&coords=14.5995,120.9842&tz=8
Tolerance 2 minutes (docs/SCIENCE.md 9.3); USNO publishes whole minutes.
"""

from datetime import date, datetime, time, timedelta

import pytest

from zeitgeber.light import solar_times
from zeitgeber.schedule import Location

USNO_MANILA = [
    (date(2026, 3, 21), time(6, 0), time(18, 7), time(5, 38), time(18, 28)),
    (date(2026, 12, 21), time(6, 16), time(17, 32), time(5, 53), time(17, 55)),
]


@pytest.mark.parametrize(("day", "rise", "set_", "dawn", "dusk"), USNO_MANILA)
def test_manila_sun_times_match_usno(
    day: date, rise: time, set_: time, dawn: time, dusk: time
) -> None:
    location = Location()
    times = solar_times(location, day)
    for computed, published in (
        (times.sunrise, rise),
        (times.sunset, set_),
        (times.dawn, dawn),
        (times.dusk, dusk),
    ):
        expected = datetime.combine(day, published, tzinfo=location.tz)
        assert abs(computed - expected) <= timedelta(minutes=2)
