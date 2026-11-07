"""Simulator against published behavior (docs/SCIENCE.md 4.3, features F1, F2 and F9)."""

from datetime import timedelta

import numpy as np
import pytest
from fixture_schedules import load_fixture

from zeitgeber.grid import TEST_STEP_H
from zeitgeber.light import build_light_profile
from zeitgeber.prc import KHALSA_PULSE, phase_response_curve
from zeitgeber.sim import MODEL_NAMES, ModelName, simulate

pytestmark = pytest.mark.science

# F9: CBTmin a few hours before waking (Smith and Eastman 2012 [3.3]; Dijk and Czeisler 1995
# [4.4]); design tolerance 1 to 4 h before lights on or wake (docs/SCIENCE.md 4.3).
F9_BEFORE_WAKE_H = (1.0, 4.0)
# F2: zero crossing of the 6.7 h pulse curve at CBTmin (Khalsa 2003 [4.1]); design tolerance.
F2_TOLERANCE_H = 1.5


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_f9_cbtmin_before_lights_on_on_a_16_8_day(name: ModelName) -> None:
    curve = phase_response_curve(name, KHALSA_PULSE, n_phases=4)
    before_lights_on = 24.0 - curve.entrained_cbt_h
    lo, hi = F9_BEFORE_WAKE_H
    assert lo <= before_lights_on <= hi


def test_entrained_day_worker_has_stable_early_morning_cbtmin() -> None:
    schedule = load_fixture("day_worker")
    run = simulate(build_light_profile(schedule))
    assert run.warmup.converged
    sleeps = [iv for iv in schedule.materialize() if iv.kind in ("sleep", "rest_sleep")]
    lo, hi = F9_BEFORE_WAKE_H
    assert len(run.cbt_min) == schedule.plan_days
    for cbt in run.cbt_min:
        inside = [iv for iv in sleeps if iv.start <= cbt < iv.end]
        assert inside, f"CBTmin {cbt} falls outside every sleep window"
        if inside[0].kind == "sleep":  # workday nights end at the 07:00 alarm
            assert lo <= (inside[0].end - cbt) / timedelta(hours=1) <= hi
    clock = np.array(
        [(c.astimezone(schedule.location.tz).hour * 60 + c.minute) for c in run.cbt_min]
    )
    assert clock.max() - clock.min() < 60, "daily CBTmin should vary by less than 1 h"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_f1_evening_light_delays_and_morning_light_advances(name: ModelName) -> None:
    curve = phase_response_curve(name, KHALSA_PULSE)
    evening = (curve.phase_h <= -2.0) & (curve.phase_h >= -8.0)
    morning = (curve.phase_h >= 2.0) & (curve.phase_h <= 8.0)
    assert evening.any() and morning.any()
    assert np.all(curve.shift_h[evening] < 0), "light 2 to 8 h before CBTmin must delay"
    assert np.all(curve.shift_h[morning] > 0), "light 2 to 8 h after CBTmin must advance"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_f2_prc_crossover_near_cbtmin(name: ModelName) -> None:
    curve = phase_response_curve(name, KHALSA_PULSE)
    assert abs(curve.crossover_h()) <= F2_TOLERANCE_H


def test_simulation_is_deterministic() -> None:
    profile = build_light_profile(load_fixture("permanent_nights"))
    a = simulate(profile, "forger99")
    b = simulate(profile, "forger99")
    np.testing.assert_array_equal(a.trajectory.states, b.trajectory.states)
    assert a.cbt_min == b.cbt_min


def test_one_minute_step_moves_cbtmin_by_less_than_0_1_h() -> None:
    schedule = load_fixture("permanent_nights")
    coarse = simulate(build_light_profile(schedule), "forger99")
    fine = simulate(build_light_profile(schedule, step_h=TEST_STEP_H), "forger99")
    assert len(coarse.cbt_min) == len(fine.cbt_min)
    worst = max(
        abs((a - b).total_seconds()) for a, b in zip(coarse.cbt_min, fine.cbt_min, strict=True)
    )
    assert worst / 3600 < 0.1  # docs/SCIENCE.md 1.7


@pytest.mark.parametrize("fixture", ["permanent_nights", "rotating", "day_worker"])
def test_warmup_converges_on_every_fixture(fixture: str) -> None:
    run = simulate(build_light_profile(load_fixture(fixture)), "forger99")
    assert run.warmup.converged, f"warm-up still moving {run.warmup.last_change_h:.3f} h"
