"""Lux profile builder (docs/SCIENCE.md 3.5, docs/ARCHITECTURE.md 2.3)."""

import re
from datetime import date, time
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
from zeitgeber.schedule import Schedule, Shift

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
    assert "times 0.15 (category 3) or 0.02 (very dark)" in table
    assert (K.sunglasses["cat3"], K.sunglasses["dark"]) == (0.15, 0.02)
