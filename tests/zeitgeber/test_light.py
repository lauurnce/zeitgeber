"""Lux profile builder (docs/SCIENCE.md 3.5, docs/ARCHITECTURE.md 2.3)."""

import re
from datetime import date, datetime, time
from pathlib import Path

import numpy as np
import pytest
from fixture_schedules import load_fixture

from zeitgeber.light import (
    COMMUTE_OUTDOOR,
    PRE_SLEEP_DIM,
    LightInterventions,
    LuxConstants,
    build_light_profile,
)
from zeitgeber.schedule import Interval, Schedule, Shift

SCIENCE = Path(__file__).parents[2] / "docs" / "SCIENCE.md"
K = LuxConstants()


def commute_home_lux(
    schedule: Schedule, day: date, interventions: LightInterventions | None = None
) -> np.ndarray:
    profile = build_light_profile(schedule, start=day, days=1, interventions=interventions)
    home = [iv for iv in schedule.materialize(day, 1) if iv.kind == "commute_home"]
    assert home, "expected a commute home on this day"
    return profile.lux[profile.grid.mask(home[0].start, home[0].end)]


def test_morning_commute_after_sunrise_is_bright() -> None:
    lux = commute_home_lux(load_fixture("permanent_nights"), date(2026, 11, 17))
    assert lux.max() == K.outdoor_sun
    assert lux.min() == K.shade_or_vehicle


def test_same_commute_before_sunrise_is_dark() -> None:
    early = load_fixture("permanent_nights").model_copy(
        update={"shifts": [Shift(weekday=d, start=time(19), end=time(4)) for d in range(5)]}
    )
    early = Schedule.model_validate(early.model_dump())
    lux = commute_home_lux(early, date(2026, 11, 17))
    assert lux.max() == K.night_street


def test_sleep_windows_are_dark() -> None:
    schedule = load_fixture("permanent_nights")
    profile = build_light_profile(schedule)
    for iv in schedule.materialize():
        if iv.kind in ("sleep", "rest_sleep"):
            assert np.all(profile.lux[profile.grid.mask(iv.start, iv.end)] == K.sleep)


def test_phone_in_bed_is_dim_before_sleep() -> None:
    profile = build_light_profile(load_fixture("permanent_nights"))
    assert np.all(profile.lux[profile.labels == PRE_SLEEP_DIM] == K.home_dim_phone)
    assert np.any(profile.labels == PRE_SLEEP_DIM)


@pytest.mark.parametrize("lens", ["cat3", "dark"])
def test_sunglasses_cut_commute_home_by_the_cited_factor(lens: str) -> None:
    schedule, day = load_fixture("permanent_nights"), date(2026, 11, 17)
    bare = commute_home_lux(schedule, day)
    shaded = commute_home_lux(schedule, day, LightInterventions(sunglasses=lens))
    assert shaded == pytest.approx(bare * K.sunglasses[lens])
    other_bare = build_light_profile(schedule, start=day, days=1)
    other_shaded = build_light_profile(
        schedule, start=day, days=1, interventions=LightInterventions(sunglasses=lens)
    )
    changed = other_bare.lux != other_shaded.lux
    assert np.all(other_bare.labels[changed] >= COMMUTE_OUTDOOR)


def test_profiles_are_deterministic() -> None:
    schedule = load_fixture("rotating")
    a, b = build_light_profile(schedule), build_light_profile(schedule)
    assert np.array_equal(a.lux, b.lux) and np.array_equal(a.labels, b.labels)
    assert a.grid == b.grid and a.grid.n == 3360


def test_constants_match_science_table() -> None:
    text = SCIENCE.read_text(encoding="utf-8")
    table = text[text.index("### 3.5") : text.index("### 3.6")]

    def lux(row: str) -> float:
        line = next(line for line in table.splitlines() if line.startswith(f"| {row} |"))
        match = re.search(r"\| ([\d,]+) lux", line)
        assert match, f"no lux value in SCIENCE.md row {row!r}"
        return float(match.group(1).replace(",", ""))

    assert K.outdoor_sun == lux("Outdoors, sun up, open")
    assert K.shade_or_vehicle == lux("Outdoors, sun up, shade or inside a vehicle")
    assert K.office == lux("Call-center floor or office")
    assert K.home == lux("Home, awake, lights on")
    assert K.home_dim_phone == lux("Home, awake, lights low, phone in hand")
    assert K.sleep == lux("Sleep in a dark room")
    assert K.night_street == lux("Outdoors at night, street")
    assert K.light_seek == lux("Light-seeking window in the shift")
    assert "times 0.15 (category 3) or 0.02 (very dark)" in table
    assert (K.sunglasses["cat3"], K.sunglasses["dark"]) == (0.15, 0.02)


def test_planner_blocks_change_only_their_samples() -> None:
    schedule = load_fixture("permanent_nights")
    day = date(2026, 11, 17)
    tz = schedule.location.tz
    at = lambda h, m=0: datetime.combine(day, time(h, m), tzinfo=tz)  # noqa: E731
    blocks = [
        Interval(at(17), at(18), "nap", "nap"),
        Interval(at(23), at(23, 59), "light_seek", "light box"),
        Interval(at(16), at(16, 15), "light_brake", "walk outside"),
        Interval(at(21), at(21, 30), "light_brake", "after sunset"),
    ]
    plain = build_light_profile(schedule, start=day, days=1)
    with_blocks = build_light_profile(schedule, start=day, days=1, extras=blocks)
    g = plain.grid
    nap, seek = g.mask(at(17), at(18)), g.mask(at(23), at(23, 59))
    brake, dark = g.mask(at(16), at(16, 15)), g.mask(at(21), at(21, 30))
    assert np.all(with_blocks.lux[nap] == K.sleep)
    assert np.all(with_blocks.lux[seek] == K.light_seek)
    assert np.all(with_blocks.lux[brake] == K.outdoor_sun)
    np.testing.assert_array_equal(with_blocks.lux[dark], plain.lux[dark])  # sun down
    rest = ~(nap | seek | brake)
    np.testing.assert_array_equal(with_blocks.lux[rest], plain.lux[rest])


def test_light_seek_outside_a_shift_does_nothing() -> None:
    schedule = load_fixture("permanent_nights")
    day = date(2026, 11, 17)
    tz = schedule.location.tz
    block = Interval(
        datetime.combine(day, time(12), tzinfo=tz),
        datetime.combine(day, time(13), tzinfo=tz),
        "light_seek",
        "at home",
    )
    plain = build_light_profile(schedule, start=day, days=1)
    moved = build_light_profile(schedule, start=day, days=1, extras=[block])
    np.testing.assert_array_equal(plain.lux, moved.lux)
