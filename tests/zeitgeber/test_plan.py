"""Planner: hard constraints, caffeine cutoff, ablations, determinism and improvement."""

from dataclasses import replace
from datetime import timedelta

import numpy as np
import pytest
from fixture_schedules import load_fixture

from zeitgeber.plan import (
    CAFFEINE_CUTOFF_H,
    CAFFEINE_CUTOFF_SLOW_H,
    PARAM_ORDER,
    Evaluator,
    InfeasibleError,
    Interventions,
    InterventionSpace,
    PlanResult,
    SearchConfig,
    apply,
    search,
)

FIXTURES = ["permanent_nights", "rotating", "day_worker"]
CONFIG = SearchConfig(cross_check=None)
_results: dict[str, PlanResult] = {}


def planned(name: str) -> PlanResult:
    if name not in _results:
        _results[name] = search(load_fixture(name), CONFIG)
    return _results[name]


def random_candidates(name: str, n: int = 60) -> list[Interventions]:
    space = InterventionSpace(load_fixture(name))
    rng = np.random.default_rng(7)
    out = []
    for _ in range(n):
        c = Interventions()
        for p in PARAM_ORDER:
            values = space.values(p)
            c = replace(c, **values[int(rng.integers(len(values)))])  # type: ignore[arg-type]
        out.append(c)
    return out


@pytest.mark.parametrize("name", FIXTURES)
def test_plan_never_puts_sleep_or_naps_in_a_shift_or_commute(name: str) -> None:
    schedule = load_fixture(name)
    plans = [apply(schedule, planned(name).plan.interventions)]
    for c in random_candidates(name):
        try:
            plans.append(apply(schedule, c))
        except InfeasibleError:
            continue
    assert len(plans) > 10
    for p in plans:
        intervals = p.schedule.materialize()
        busy = [iv for iv in intervals if iv.kind in ("shift", "commute_to_work", "commute_home")]
        rest = [iv for iv in intervals if iv.kind in ("sleep", "rest_sleep")]
        rest += [b for b in p.blocks if b.kind == "nap"]
        for r in rest:
            clash = [b.label for b in busy if b.overlaps(r)]
            assert not clash, f"{r.label} overlaps {clash} in {p.interventions}"


@pytest.mark.parametrize("name", FIXTURES)
def test_light_seek_blocks_sit_inside_shifts(name: str) -> None:
    schedule = load_fixture(name)
    p = apply(schedule, Interventions(light_seek_start_h=1.0, light_seek_len_h=1.0))
    shifts = [iv for iv in p.schedule.materialize(schedule.anchor_date - timedelta(days=1), 16)]
    for b in p.blocks:
        assert any(s.kind == "shift" and s.start <= b.start and b.end <= s.end for s in shifts)


@pytest.mark.parametrize("slow", [False, True])
@pytest.mark.parametrize("name", FIXTURES)
def test_caffeine_is_never_inside_the_cutoff(name: str, slow: bool) -> None:
    schedule = load_fixture(name)
    cutoff_h = CAFFEINE_CUTOFF_SLOW_H if slow else CAFFEINE_CUTOFF_H
    p = apply(schedule, planned(name).plan.interventions, slow_caffeine=slow)
    assert p.caffeine
    for w in p.caffeine:
        assert w.cutoff == w.next_sleep_start - timedelta(hours=cutoff_h)  # C1, C2
        if w.allowed is None:
            assert w.cutoff <= w.shift.start
            continue
        start, end = w.allowed
        assert start == w.shift.start
        assert end <= w.cutoff, "caffeine allowed after the cutoff"
        assert end <= w.shift.start + (w.shift.end - w.shift.start) / 2  # C3: first half


def test_dark_lenses_are_never_offered_to_drivers() -> None:
    schedule = load_fixture("permanent_nights")
    driver = schedule.model_copy(
        update={"commute_home": schedule.commute_home.model_copy(update={"mode": "motorcycle"})}
    )
    assert {v["sunglasses"] for v in InterventionSpace(driver).values("sunglasses")} == {
        "none",
        "cat3",
    }
    with pytest.raises(InfeasibleError, match="R7"):
        apply(driver, Interventions(sunglasses="dark"))


@pytest.mark.parametrize("name", FIXTURES)
def test_ablations_are_consistent(name: str) -> None:
    result = planned(name)
    fresh = Evaluator(load_fixture(name), CONFIG)
    assert [e.intervention for e in result.explanations] == result.plan.interventions.active()
    for e in result.explanations:
        assert e.score_with_h == result.plan.score.total_h
        alone = fresh.evaluate([result.plan.interventions.without(e.intervention)])[0]
        if alone is None:
            assert e.score_without_h is None
            continue
        assert e.score_without_h == pytest.approx(alone.score.total_h, abs=1e-9)
        assert e.delta_score_h == pytest.approx(alone.score.total_h - result.plan.score.total_h)
        if result.converged:  # dropping one change is a coordinate move the search tried
            assert e.objective_without_h is not None
            assert e.objective_without_h >= result.plan.objective_h - 1e-9


def test_same_input_and_seed_give_the_same_plan() -> None:
    first = planned("permanent_nights")
    again = search(load_fixture("permanent_nights"), CONFIG)
    assert again.plan.interventions == first.plan.interventions
    assert again.plan.score.total_h == first.plan.score.total_h
    assert again.plan.cbt_min == first.plan.cbt_min
    assert [e.delta_score_h for e in again.explanations] == [
        e.delta_score_h for e in first.explanations
    ]


@pytest.mark.parametrize(
    "name",
    [
        "permanent_nights",
        pytest.param(
            "rotating",
            marks=pytest.mark.xfail(
                strict=True,
                reason="two nights a week leave the modelled clock day-oriented; every plan "
                "with 7 h after nights (R3) scores 4.49 h or more against 4.48 h now",
            ),
        ),
        pytest.param(
            "day_worker",
            marks=pytest.mark.xfail(
                strict=True, reason="control fixture: no change in the space improves the score"
            ),
        ),
    ],
)
def test_plan_beats_the_current_schedule(name: str) -> None:
    result = planned(name)
    assert result.plan.score.total_h < result.baseline.score.total_h


def test_night_worker_plan_improves_score_by_more_than_half() -> None:
    result = planned("permanent_nights")
    assert result.plan.score.total_h < 0.5 * result.baseline.score.total_h
    assert result.plan.objective_h < result.baseline.objective_h


def test_day_worker_plan_asks_for_nothing() -> None:
    result = planned("day_worker")
    assert result.plan.interventions == Interventions()
    assert result.explanations == ()


def test_rotating_plan_clears_short_sleep_at_small_cost() -> None:
    result = planned("rotating")
    assert "R3" in result.baseline.penalties
    assert "R3" not in result.plan.penalties
    assert result.plan.objective_h < result.baseline.objective_h
    assert result.plan.score.total_h - result.baseline.score.total_h < 0.05
