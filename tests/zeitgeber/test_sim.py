"""Simulator adapter: parity with the package, input checks and markers (docs/SCIENCE.md 1, 2)."""

import warnings
from datetime import UTC, date, datetime, timedelta
from typing import Any

import numpy as np
import pytest
from circadian.models import Forger99, Hannay19, Jewett99
from fixture_schedules import load_fixture

from zeitgeber.grid import TimeGrid
from zeitgeber.light import LightProfile, build_light_profile
from zeitgeber.sim import (
    CONVENTIONS,
    MAX_LUX,
    MODEL_NAMES,
    ClockModel,
    ModelName,
    equilibrate,
    integrate,
    simulate,
)

PACKAGE = {"forger99": Forger99, "jewett99": Jewett99, "hannay19": Hannay19}
GRID = TimeGrid(datetime(2026, 1, 1, tzinfo=UTC), 0.1, 240 * 4)
DAY_LUX = np.where((GRID.hours() % 24) >= 8, 150.0, 0.0)  # 16 h light, 8 h dark


def package_run(name: ModelName) -> tuple[Any, Any]:
    model = PACKAGE[name]()
    time = np.append(GRID.hours(), GRID.n * GRID.step_h)
    # The package applies light[i] over the step that ends at time[i]; ours over the step
    # that starts at hours[i]. Shifting by one sample makes the two schemes identical.
    traj = model.integrate(time, input=np.append(0.0, DAY_LUX))
    return model, traj


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_states_match_package_integrate(name: ModelName) -> None:
    _, traj = package_run(name)
    ours = integrate(name, GRID, DAY_LUX)
    np.testing.assert_allclose(ours.states[:, :, 0], traj.states, rtol=0, atol=1e-12)


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_cbtmin_matches_package_within_one_step(name: ModelName) -> None:
    model, traj = package_run(name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        theirs = model.cbt(traj)
    ours = integrate(name, GRID, DAY_LUX).cbt_min_hours()[0]
    assert ours.shape == theirs.shape
    np.testing.assert_allclose(ours, theirs, atol=GRID.step_h)


def test_batch_equals_separate_runs() -> None:
    other = np.where((GRID.hours() % 24) >= 6, 500.0, 1.0)
    both = integrate("forger99", GRID, np.stack([DAY_LUX, other], axis=1))
    for col, lux in enumerate((DAY_LUX, other)):
        alone = integrate("forger99", GRID, lux)
        np.testing.assert_array_equal(both.states[:, :, col], alone.states[:, :, 0])


def test_lux_above_cap_is_capped() -> None:
    bright = integrate("forger99", GRID, DAY_LUX * 1000)
    capped = integrate("forger99", GRID, np.minimum(DAY_LUX * 1000, MAX_LUX))
    np.testing.assert_array_equal(bright.states, capped.states)


@pytest.mark.parametrize(
    ("lux", "message"),
    [(-1.0, "negative"), (np.nan, "NaN")],
)
def test_bad_lux_is_rejected(lux: float, message: str) -> None:
    bad = DAY_LUX.copy()
    bad[10] = lux
    with pytest.raises(ValueError, match=message):
        integrate("forger99", GRID, bad)


def test_lux_length_must_match_grid() -> None:
    with pytest.raises(ValueError, match="shape"):
        integrate("forger99", GRID, DAY_LUX[:-1])


def test_unknown_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown model 'kronauer'"):
        ClockModel("kronauer")  # type: ignore[arg-type]


def test_marker_conventions_match_science_table() -> None:
    assert CONVENTIONS["forger99"].cbt_offset_h == 0.0
    assert CONVENTIONS["jewett99"].cbt_offset_h == 0.8
    assert CONVENTIONS["hannay19"].cbt_offset_h == 0.0
    assert {c.dlmo_before_cbt_h for c in CONVENTIONS.values()} == {7.0}
    assert all("SCIENCE.md 1." in c.source and "and 1.6" in c.source for c in CONVENTIONS.values())


def test_warmup_needs_whole_days() -> None:
    half = TimeGrid(GRID.start, 0.1, 120)
    with pytest.raises(ValueError, match="whole days"):
        equilibrate("forger99", half, np.full(120, 100.0))


def test_warmup_converges_on_a_regular_day() -> None:
    day = TimeGrid(GRID.start, 0.1, 240)
    warm = equilibrate("forger99", day, DAY_LUX[:240])
    assert warm.converged
    assert warm.last_change_h < 0.05


def test_baseline_must_share_clock_time() -> None:
    schedule = load_fixture("day_worker")
    profile = build_light_profile(schedule, days=7)
    shifted = TimeGrid(profile.grid.start + timedelta(hours=3), 0.1, profile.grid.n)
    baseline = LightProfile(shifted, profile.lux, profile.labels)
    with pytest.raises(ValueError, match="same clock time"):
        simulate(profile, baseline=baseline)


def test_daily_markers_one_row_per_local_day() -> None:
    schedule = load_fixture("day_worker")
    run = simulate(build_light_profile(schedule, days=7))
    rows = run.daily(schedule.location.tz)
    assert [r.day for r in rows] == [date(2026, 11, 16) + timedelta(days=k) for k in range(7)]
    for r in rows:
        assert r.cbt_min is not None and r.dlmo is not None
        assert r.cbt_min - r.dlmo == timedelta(hours=7)
        assert r.cbt_min.date() == r.day
