"""Intervention space, constraints, seeded search and explanations.

Interventions come from the rules in docs/SCIENCE.md 5.4 (R1 to R7) and 6.3 (C1 to C4, N1 to
N3); the search design is docs/ARCHITECTURE.md 4. A candidate plan is applied by building a
new :class:`Schedule` (so the schedule's own validation rejects any sleep that overlaps a shift
or a commute) plus planner light blocks (bright light in the shift, the pre-shift nap and the
outdoor light brake) that the light builder lays over the profile.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, fields, replace
from datetime import datetime, time, timedelta
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import ValidationError

from zeitgeber.grid import REQUEST_STEP_H
from zeitgeber.light import LightInterventions, build_light_profile
from zeitgeber.schedule import (
    Interval,
    RestDayPolicy,
    Schedule,
    SleepWindow,
    SleepWindows,
)
from zeitgeber.score import LAMBDA, ScoreBreakdown, score
from zeitgeber.sim import ModelName, Warmup, equilibrate, get_model, integrate

Sunglasses = Literal["none", "cat3", "dark"]
RestChoice = Literal["current", "01:00", "02:00", "03:00", "04:00"]

# Rule parameters. Values marked design are Zeitgeber's choices (docs/SCIENCE.md 5.4, 6.3).
SLEEP_OFFSETS_H = (0.0, 0.5, 1.0, 1.5)  # R3: start within 1.5 h of getting home
SLEEP_LENGTHS_H = (7.0, 8.0, 9.0)  # R3: at least 7 h
REST_SLEEP_H = 8.0  # R4: late rest-day window, 8 h
LATE_REST_STARTS = ("01:00", "02:00", "03:00", "04:00")  # R4, default 03:00
LIGHT_SEEK_LENGTHS_H = (0.5, 1.0)  # R1
LIGHT_SEEK_MARGIN_H = 2.0  # R1: end at least 2 h before CBTmin
BRAKE_AFTER_WAKE_H = 0.5  # R5: 15 min outdoors within 2 h of waking (placed 30 min after, design)
BRAKE_MIN = 15
NAP_LENGTHS_MIN = (30, 60, 90)  # N1
NAP_MARGIN_MIN = 30  # N1: ends 30 min before leaving home
CAFFEINE_CUTOFF_H = 6.0  # C1
CAFFEINE_CUTOFF_SLOW_H = 8.0  # C2
MIN_WORKDAY_SLEEP_H = 7.0  # R3


@dataclass(frozen=True)
class Interventions:
    """One candidate plan. Every default means "as the worker does now"."""

    sunglasses: Sunglasses = "none"  # R2 on the commute home; dark only for non-drivers (R7)
    sleep_start_offset_h: float | None = None  # R3, after-night-shift sleep, from getting home
    sleep_len_h: float | None = None  # R3
    rest_day: RestChoice = "current"  # R4 late window
    light_brake: bool = False  # R5
    light_seek_start_h: float | None = None  # R1, hours after shift start
    light_seek_len_h: float = 1.0
    nap_len_min: int = 0  # N1, before night shifts

    def active(self) -> list[str]:
        """Names of the parameters that differ from "as now" (light seeking counts once)."""
        out = []
        for f in fields(self):
            if f.name == "light_seek_len_h":
                continue
            if getattr(self, f.name) != f.default:
                out.append(f.name)
        return out

    @property
    def burden(self) -> float:
        """Number of changes asked of the worker; dark lenses count 2 (ARCHITECTURE 4.3)."""
        return len(self.active()) + (1 if self.sunglasses == "dark" else 0)

    def without(self, name: str) -> Interventions:
        """This plan with one parameter back to "as now" (used by the ablations)."""
        defaults = {f.name: f.default for f in fields(self)}
        changes = {name: defaults[name]}
        if name == "light_seek_start_h":
            changes["light_seek_len_h"] = defaults["light_seek_len_h"]
        return replace(self, **changes)  # type: ignore[arg-type]


PARAM_ORDER = (
    "sunglasses",
    "sleep_start_offset_h",
    "sleep_len_h",
    "rest_day",
    "light_brake",
    "light_seek",
    "nap_len_min",
)
RULES = {
    "sunglasses": ("R2", "R7"),
    "sleep_start_offset_h": ("R3",),
    "sleep_len_h": ("R3",),
    "rest_day": ("R4",),
    "light_brake": ("R5",),
    "light_seek_start_h": ("R1",),
    "nap_len_min": ("N1", "N3"),
}


def _each(name: str, values: Sequence[object]) -> list[dict[str, object]]:
    return [{name: v} for v in values]


def _hours(td: timedelta) -> float:
    return td.total_seconds() / 3600.0


def _clock(t: time, hours: float) -> time:
    minutes = (t.hour * 60 + t.minute + round(hours * 60)) % (24 * 60)
    return time(minutes // 60, minutes % 60)


class InterventionSpace:
    """The values each parameter may take for one schedule (docs/ARCHITECTURE.md 4.1)."""

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule
        self.night_weekdays = sorted(s.weekday for s in schedule.shifts if s.crosses_midnight)
        night = [s for s in schedule.shifts if s.crosses_midnight]
        self.has_nights = bool(night)
        shortest = min(s.duration_min for s in schedule.shifts) / 60.0
        self.shift_len_h = shortest

    def values(self, name: str) -> list[dict[str, object]]:
        """Each allowed setting of one parameter, as field updates, "as now" first."""
        if name == "sunglasses":
            lenses: list[Sunglasses] = ["none", "cat3"]
            if not self.schedule.commute_home.drives:
                lenses.append("dark")  # R7
            return _each(name, lenses)
        if name == "sleep_start_offset_h":
            if not self.has_nights:
                return [{name: None}]
            return _each(name, [None, *SLEEP_OFFSETS_H])
        if name == "sleep_len_h":
            if not self.has_nights:
                return [{name: None}]
            return _each(name, [None, *SLEEP_LENGTHS_H])
        if name == "rest_day":
            if not self.schedule.rest_weekdays:
                return [{name: "current"}]
            # D1 and R4: a late rest-day window, never a full switch to night hours. Keeping
            # nights stays possible only as "current" for someone who already does it.
            return _each(name, ["current", *LATE_REST_STARTS])
        if name == "light_brake":
            return _each(name, [False, True] if self.has_nights else [False])
        if name == "light_seek":
            out: list[dict[str, object]] = [{"light_seek_start_h": None, "light_seek_len_h": 1.0}]
            last = int(self.shift_len_h - LIGHT_SEEK_MARGIN_H)
            for start in range(0, last + 1):
                for length in LIGHT_SEEK_LENGTHS_H:
                    out.append({"light_seek_start_h": float(start), "light_seek_len_h": length})
            return out
        if name == "nap_len_min":
            if not self.has_nights:
                return [{name: 0}]
            return _each(name, [0, *NAP_LENGTHS_MIN])
        raise ValueError(f"unknown intervention parameter {name!r}")


class InfeasibleError(ValueError):
    """A candidate breaks a hard constraint (docs/ARCHITECTURE.md 4.2)."""


@dataclass(frozen=True)
class CaffeineWindow:
    """When caffeine fits for one shift: first half of the shift and before the cutoff."""

    shift: Interval
    next_sleep_start: datetime
    cutoff: datetime  # next main sleep start minus 6 h (C1) or 8 h (C2)
    allowed: tuple[datetime, datetime] | None  # None when the cutoff falls before the shift


@dataclass(frozen=True)
class AppliedPlan:
    interventions: Interventions
    schedule: Schedule
    blocks: tuple[Interval, ...]  # nap, light_seek and light_brake blocks, UTC
    caffeine: tuple[CaffeineWindow, ...]


def _sleep_windows(base: Schedule, c: Interventions) -> SleepWindows:
    sleep = base.sleep
    if c.sleep_start_offset_h is None and c.sleep_len_h is None:
        return sleep
    home = timedelta(minutes=base.commute_home.duration_min)
    by_weekday = dict(sleep.after_shift_by_weekday)
    first: SleepWindow | None = None
    for shift in sorted(base.shifts, key=lambda s: s.weekday):
        if not shift.crosses_midnight:
            continue
        habit = sleep.for_shift(shift.weekday)
        arrive = _clock(shift.end, _hours(home))
        habit_offset = (
            _hours(
                datetime.combine(datetime.min, habit.start) - datetime.combine(datetime.min, arrive)
            )
            % 24.0
        )
        offset = habit_offset if c.sleep_start_offset_h is None else c.sleep_start_offset_h
        length = habit.duration_min / 60.0 if c.sleep_len_h is None else c.sleep_len_h
        start = _clock(arrive, offset)
        window = SleepWindow(start=start, end=_clock(start, length))
        by_weekday[shift.weekday] = window
        first = first or window
    if first is None:
        return sleep
    return sleep.model_copy(update={"after_shift": first, "after_shift_by_weekday": by_weekday})


def _rest(
    base: Schedule, c: Interventions, sleep: SleepWindows
) -> tuple[SleepWindows, RestDayPolicy]:
    if c.rest_day == "current":
        return sleep, base.rest_days
    start = time.fromisoformat(c.rest_day)
    window = SleepWindow(start=start, end=_clock(start, REST_SLEEP_H))
    return sleep.model_copy(update={"rest_day": window}), RestDayPolicy(mode="flip_to_days")


def apply(base: Schedule, c: Interventions, slow_caffeine: bool = False) -> AppliedPlan:
    """Turn a candidate into a schedule and light blocks, or raise :class:`InfeasibleError`."""
    if c.sunglasses == "dark" and base.commute_home.drives:
        raise InfeasibleError("dark lenses are not offered to someone who drives home (R7)")
    sleep, rest = _rest(base, c, _sleep_windows(base, c))
    try:
        schedule = Schedule.model_validate(
            {**base.model_dump(), "sleep": sleep.model_dump(), "rest_days": rest.model_dump()}
        )
    except ValidationError as err:
        raise InfeasibleError(str(err.errors()[0]["msg"])) from err

    day_before = schedule.anchor_date - timedelta(days=1)
    intervals = schedule.materialize(day_before, schedule.plan_days + 2)
    shifts = [iv for iv in intervals if iv.kind == "shift"]
    to_work = [iv for iv in intervals if iv.kind == "commute_to_work"]
    sleeps = [iv for iv in intervals if iv.kind in ("sleep", "rest_sleep")]
    night = {s.weekday for s in schedule.shifts if s.crosses_midnight}
    tz = schedule.location.tz
    blocks: list[Interval] = []
    for sh in shifts:
        is_night = sh.start.astimezone(tz).weekday() in night
        if c.light_seek_start_h is not None:
            s = sh.start + timedelta(hours=c.light_seek_start_h)
            blocks.append(
                Interval(s, s + timedelta(hours=c.light_seek_len_h), "light_seek", "bright light")
            )
        if c.nap_len_min and is_night:
            leave = next((iv.start for iv in to_work if iv.end == sh.start), sh.start)
            end = leave - timedelta(minutes=NAP_MARGIN_MIN)
            blocks.append(Interval(end - timedelta(minutes=c.nap_len_min), end, "nap", "nap"))
    if c.light_brake:
        for sl in sleeps:
            if sl.kind == "sleep" and any(
                sh.end <= sl.start < sh.end + timedelta(hours=4)
                for sh in shifts
                if sh.start.astimezone(tz).weekday() in night
            ):
                s = sl.end + timedelta(hours=BRAKE_AFTER_WAKE_H)
                blocks.append(
                    Interval(s, s + timedelta(minutes=BRAKE_MIN), "light_brake", "outdoors")
                )
    occupied = [iv for iv in intervals if iv.kind != "shift"] + shifts
    for b in blocks:
        if b.kind == "light_seek":
            continue
        clash = next((iv for iv in occupied if iv.overlaps(b)), None)
        if clash is not None:
            raise InfeasibleError(f"the {b.label} block overlaps {clash.label}")

    cutoff_h = CAFFEINE_CUTOFF_SLOW_H if slow_caffeine else CAFFEINE_CUTOFF_H
    caffeine = []
    for sh in shifts:
        nxt = min((sl.start for sl in sleeps if sl.start >= sh.end), default=None)
        if nxt is None:
            continue
        cutoff = nxt - timedelta(hours=cutoff_h)
        half = sh.start + (sh.end - sh.start) / 2  # C3: first half of the shift
        end = min(half, cutoff)
        caffeine.append(
            CaffeineWindow(sh, nxt, cutoff, (sh.start, end) if end > sh.start else None)
        )
    return AppliedPlan(c, schedule, tuple(blocks), tuple(caffeine))


# Objective (docs/ARCHITECTURE.md 4.3): J = S + soft penalties + burden_h * burden.
PENALTY_LIGHT_SEEK_H = 0.5  # R1: a light block ending less than 2 h before CBTmin (design)
PENALTY_SHORT_SLEEP_H = 1.0  # R3: an after-night-shift sleep shorter than 7 h (design)


@dataclass(frozen=True)
class SearchConfig:
    seed: int = 0
    passes: int = 4
    restarts: int = 4
    step_h: float = REQUEST_STEP_H
    lam: float = LAMBDA
    burden_h: float = 0.05
    model: ModelName = "forger99"
    cross_check: ModelName | None = "hannay19"
    slow_caffeine: bool = False  # C2


@dataclass(frozen=True)
class Evaluation:
    plan: AppliedPlan
    score: ScoreBreakdown
    penalty_h: float
    penalties: tuple[str, ...]  # rule ids with a soft violation
    objective_h: float
    cbt_min: tuple[datetime, ...]  # UTC

    @property
    def interventions(self) -> Interventions:
        return self.plan.interventions


class Evaluator:
    """Simulates and scores candidates, all from one warm-up on the worker's current schedule."""

    def __init__(self, schedule: Schedule, config: SearchConfig | None = None) -> None:
        self.schedule = schedule
        self.config = config = config or SearchConfig()
        self.model = get_model(config.model)
        base = build_light_profile(schedule, step_h=config.step_h)
        self.grid = base.grid
        self.warmup: Warmup = equilibrate(self.model, base.grid, base.lux)
        self._cache: dict[Interventions, Evaluation | None] = {}
        self.simulations = 0

    def evaluate(self, candidates: Sequence[Interventions]) -> list[Evaluation | None]:
        """Evaluations in input order; None for a candidate that breaks a hard constraint."""
        todo: list[AppliedPlan] = []
        for c in dict.fromkeys(candidates):
            if c in self._cache:
                continue
            try:
                todo.append(apply(self.schedule, c, self.config.slow_caffeine))
            except InfeasibleError:
                self._cache[c] = None
        if todo:
            lux = np.stack([self._lux(a) for a in todo], axis=1)
            traj = integrate(self.model, self.grid, lux, self.warmup.state)
            self.simulations += len(todo)
            for a, hours in zip(todo, traj.cbt_min_hours(), strict=True):
                cbt = tuple(self.grid.start + timedelta(hours=float(h)) for h in hours)
                self._cache[a.interventions] = self._score(a, cbt)
        return [self._cache[c] for c in candidates]

    def _lux(self, a: AppliedPlan) -> NDArray[np.float64]:
        profile = build_light_profile(
            a.schedule,
            step_h=self.config.step_h,
            interventions=LightInterventions(sunglasses=a.interventions.sunglasses),
            extras=a.blocks,
        )
        return profile.lux

    def _score(self, a: AppliedPlan, cbt: tuple[datetime, ...]) -> Evaluation:
        begin, end = self.grid.start, self.grid.end
        intervals = a.schedule.materialize()
        # Only sleeps wholly inside the window are scored; the edges are clipped.
        sleeps = [iv for iv in intervals if iv.start > begin and iv.end < end]
        shifts = [iv for iv in intervals if iv.kind == "shift"]
        result = score(cbt, sleeps, shifts, a.schedule.location.tz, self.config.lam)
        penalty, rules = 0.0, []
        seeks = [b for b in a.blocks if b.kind == "light_seek" and begin <= b.start < end]
        if seeks:
            margin = timedelta(hours=LIGHT_SEEK_MARGIN_H)
            late = sum(any(b.start <= c < b.end + margin for c in cbt) for b in seeks)
            if late:
                penalty += PENALTY_LIGHT_SEEK_H * late / len(seeks)
                rules.append("R1")
        night = {s.weekday for s in a.schedule.shifts if s.crosses_midnight}
        short = any(
            a.schedule.sleep.for_shift(w).duration_min < MIN_WORKDAY_SLEEP_H * 60 for w in night
        )
        if short:
            penalty += PENALTY_SHORT_SLEEP_H
            rules.append("R3")
        objective = result.total_h + penalty + self.config.burden_h * a.interventions.burden
        return Evaluation(a, result, penalty, tuple(rules), objective, cbt)


def _better(a: Evaluation, b: Evaluation) -> bool:
    """Strictly better objective; ties go to the smaller burden."""
    if not math.isclose(a.objective_h, b.objective_h, abs_tol=1e-9):
        return a.objective_h < b.objective_h
    return a.interventions.burden < b.interventions.burden


def _descend(
    ev: Evaluator, space: InterventionSpace, starts: Sequence[Interventions], passes: int
) -> list[tuple[Evaluation, bool]]:
    """Coordinate descent from each start, run in lockstep so that each parameter step of
    every descent shares one batched simulation. Each descent follows exactly the path it
    would follow alone: per pass, parameters in :data:`PARAM_ORDER`, keeping the best option.
    """
    firsts = ev.evaluate(starts)
    if any(f is None for f in firsts):
        raise InfeasibleError("a starting point breaks a hard constraint")
    best = [f for f in firsts if f is not None]
    done = [False] * len(best)
    for _ in range(passes):
        active = [k for k, d in enumerate(done) if not d]
        if not active:
            break
        changed = dict.fromkeys(active, False)
        for name in PARAM_ORDER:
            options = {
                k: [replace(best[k].interventions, **v) for v in space.values(name)]  # type: ignore[arg-type]
                for k in active
            }
            results = iter(ev.evaluate([c for k in active for c in options[k]]))
            for k in active:
                for _option in options[k]:
                    e = next(results)
                    if e is not None and _better(e, best[k]):
                        best[k], changed[k] = e, True
        for k in active:
            done[k] = not changed[k]
    return list(zip(best, done, strict=True))


def _random_start(space: InterventionSpace, rng: np.random.Generator) -> Interventions:
    c = Interventions()
    for name in PARAM_ORDER:
        values = space.values(name)
        c = replace(c, **values[int(rng.integers(len(values)))])  # type: ignore[arg-type]
    return c


@dataclass(frozen=True)
class Explanation:
    """What one recommended change is worth: the plan scored with and without it."""

    intervention: str
    rule_ids: tuple[str, ...]
    score_with_h: float
    score_without_h: float | None  # None when removing it alone breaks a hard constraint
    objective_without_h: float | None
    delta_cbt_day7_h: float | None  # CBTmin without minus with, hours (positive: later)
    delta_cbt_day14_h: float | None

    @property
    def delta_score_h(self) -> float | None:
        """Score without minus score with; positive means the change lowers misalignment."""
        if self.score_without_h is None:
            return None
        return self.score_without_h - self.score_with_h


@dataclass(frozen=True)
class PlanResult:
    schedule: Schedule
    config: SearchConfig
    baseline: Evaluation
    plan: Evaluation
    explanations: tuple[Explanation, ...]
    converged: bool
    simulations: int
    cross_check: dict[str, ScoreBreakdown] | None  # "baseline" and "plan" under the second model


def _cbt_on_day(ev: Evaluation, schedule: Schedule, day_index: int) -> datetime | None:
    tz = schedule.location.tz
    day = schedule.anchor_date + timedelta(days=day_index)
    return next((c for c in ev.cbt_min if c.astimezone(tz).date() == day), None)


def explain(ev: Evaluator, plan: Evaluation) -> tuple[Explanation, ...]:
    """Ablation: revert each active change on its own and re-simulate (ARCHITECTURE 4.5)."""
    names = plan.interventions.active()
    ablated = ev.evaluate([plan.interventions.without(n) for n in names])
    out = []
    for name, other in zip(names, ablated, strict=True):
        deltas: list[float | None] = []
        for day in (6, 13):
            a = _cbt_on_day(plan, ev.schedule, day)
            b = None if other is None else _cbt_on_day(other, ev.schedule, day)
            deltas.append(None if a is None or b is None else _hours(b - a))
        out.append(
            Explanation(
                intervention=name,
                rule_ids=RULES[name],
                score_with_h=plan.score.total_h,
                score_without_h=None if other is None else other.score.total_h,
                objective_without_h=None if other is None else other.objective_h,
                delta_cbt_day7_h=deltas[0],
                delta_cbt_day14_h=deltas[1],
            )
        )
    return tuple(out)


def search(schedule: Schedule, config: SearchConfig | None = None) -> PlanResult:
    """Seeded coordinate descent from "as now" plus random restarts (ARCHITECTURE 4.4).

    The same schedule and seed always give the same plan. Ties in the objective go to the
    smaller burden, then to the earlier start.
    """
    config = config or SearchConfig()
    ev = Evaluator(schedule, config)
    space = InterventionSpace(schedule)
    baseline = ev.evaluate([Interventions()])[0]
    if baseline is None:
        raise InfeasibleError("the current schedule itself breaks a hard constraint")
    rng = np.random.default_rng(config.seed)
    starts = [Interventions()]
    for _ in range(config.restarts):
        for _attempt in range(50):
            c = _random_start(space, rng)
            if ev.evaluate([c])[0] is not None:
                starts.append(c)
                break
    best, converged = baseline, True
    for found, done in _descend(ev, space, starts, config.passes):
        if _better(found, best):
            best, converged = found, done
    cross: dict[str, ScoreBreakdown] | None = None
    if config.cross_check is not None:
        other = Evaluator(schedule, replace(config, model=config.cross_check))
        pair = other.evaluate([baseline.interventions, best.interventions])
        cross = {k: e.score for k, e in zip(("baseline", "plan"), pair, strict=True) if e}
    return PlanResult(
        schedule=schedule,
        config=config,
        baseline=baseline,
        plan=best,
        explanations=explain(ev, best),
        converged=converged,
        simulations=ev.simulations,
        cross_check=cross,
    )
