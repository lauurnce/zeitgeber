"""Circadian simulation: package adapters, batched integration, warm-up and phase markers.

This is the only module that imports the Arcascope ``circadian`` package (pinned 1.0.3,
docs/SCIENCE.md 2). The equations stay in the package: each adapter calls the package model's
``derv``, and :func:`integrate` runs the same fixed-step fourth-order Runge-Kutta scheme as the
package's ``step_rk4`` over a whole batch of light profiles at once (docs/ARCHITECTURE.md 2.4).

Conventions (docs/SCIENCE.md 1.6):

- Forger99: CBTmin is the minimum of ``x``.
- Jewett99: CBTmin is the minimum of ``x`` plus 0.8 h.
- Hannay19: CBTmin is the time the collective phase ``psi`` passes pi.
- DLMO is CBTmin minus 7 h for every model, so it carries no information of its own.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, tzinfo
from typing import Any, Literal, get_args

import numpy as np
from circadian.models import Forger99, Hannay19, Jewett99
from numpy.typing import NDArray

from zeitgeber.grid import TimeGrid
from zeitgeber.light import LightProfile

ModelName = Literal["forger99", "jewett99", "hannay19"]
MODEL_NAMES: tuple[ModelName, ...] = get_args(ModelName)
DEFAULT_MODEL: ModelName = "forger99"  # docs/SCIENCE.md 1.9, decision D12
CROSS_CHECK_MODEL: ModelName = "hannay19"

MAX_LUX = 10_000.0  # model input cap (docs/SCIENCE.md 1.7)
MIN_HANNAY_R = 0.05  # guard on the 1/R term (docs/SCIENCE.md 1.7)
MIN_MARKER_SPACING_H = 13.0  # same as the package's _min_marker_distance_in_hours


class SimulationError(RuntimeError):
    """The model left its valid range (docs/SCIENCE.md 1.7)."""


@dataclass(frozen=True)
class MarkerConvention:
    """How a model's state maps to CBTmin and DLMO, with the source of each number."""

    cbt_rule: str
    cbt_offset_h: float
    dlmo_before_cbt_h: float
    source: str


CONVENTIONS: dict[ModelName, MarkerConvention] = {
    "forger99": MarkerConvention(
        cbt_rule="minimum of x",
        cbt_offset_h=0.0,
        dlmo_before_cbt_h=7.0,
        source="docs/SCIENCE.md 1.3 and 1.6; Forger 1999 [1.1]; DLMO offset Crowley 2003 [5.3]",
    ),
    "jewett99": MarkerConvention(
        cbt_rule="minimum of x plus 0.8 h",
        cbt_offset_h=0.8,
        dlmo_before_cbt_h=7.0,
        source="docs/SCIENCE.md 1.4 and 1.6; Jewett 1999 [1.2]; DLMO offset Crowley 2003 [5.3]",
    ),
    "hannay19": MarkerConvention(
        cbt_rule="collective phase psi passes pi",
        cbt_offset_h=0.0,
        dlmo_before_cbt_h=7.0,
        source="docs/SCIENCE.md 1.5 and 1.6; Hannay 2019 [1.3]; DLMO offset Crowley 2003 [5.3]",
    ),
}


class ClockModel:
    """One pacemaker model from the package, with Zeitgeber's marker conventions."""

    def __init__(self, name: ModelName) -> None:
        if name not in MODEL_NAMES:
            raise ValueError(f"unknown model {name!r}; choose one of {', '.join(MODEL_NAMES)}")
        self.name: ModelName = name
        self.convention = CONVENTIONS[name]
        self._model: Any = {"forger99": Forger99, "jewett99": Jewett99, "hannay19": Hannay19}[
            name
        ]()
        self.n_states: int = int(self._model._num_states)

    def __repr__(self) -> str:
        return f"ClockModel({self.name!r})"

    def default_state(self) -> NDArray[np.float64]:
        """The package's default state: midnight on a 16 h light, 8 h dark day (SCIENCE 2.6)."""
        return np.array(self._model._default_initial_condition, dtype=np.float64)

    def derivative(
        self, state: NDArray[np.float64], lux: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Right-hand side from the package. ``state`` is (n_states, batch), ``lux`` is (batch,)."""
        return np.asarray(self._model.derv(0.0, state, lux), dtype=np.float64)

    def phase(self, states: NDArray[np.float64]) -> NDArray[np.float64]:
        """The model's own phase in radians, same formulas as the package's ``phase``.

        ``states`` is (n, n_states, batch); the result is (n, batch) in (-pi, pi]. CBTmin sits
        near pi for every model (exactly pi for Hannay19, at the minimum of x for the others).
        """
        if self.name == "hannay19":
            return np.asarray(np.angle(np.exp(1j * states[:, 1])), dtype=np.float64)
        return np.asarray(np.angle(states[:, 0] - 1j * states[:, 1]), dtype=np.float64)

    def amplitude(self, states: NDArray[np.float64]) -> NDArray[np.float64]:
        if self.name == "hannay19":
            return np.asarray(states[:, 0], dtype=np.float64)
        return np.asarray(np.hypot(states[:, 0], states[:, 1]), dtype=np.float64)

    def _trough_signal(self, states: NDArray[np.float64]) -> NDArray[np.float64]:
        """A signal whose minima are the native CBTmin, as in the package's ``cbt``."""
        if self.name == "hannay19":
            return np.asarray(np.cos(states[:, 1]), dtype=np.float64)
        return np.asarray(states[:, 0], dtype=np.float64)

    def cbt_min_hours(
        self, hours: NDArray[np.float64], states: NDArray[np.float64]
    ) -> list[NDArray[np.float64]]:
        """CBTmin times (hours on the ``hours`` axis) for each batch column, offset applied."""
        signal = self._trough_signal(states)
        step = float(hours[1] - hours[0])
        return [
            _troughs(hours, signal[:, b], step) + self.convention.cbt_offset_h
            for b in range(signal.shape[1])
        ]


def _troughs(
    hours: NDArray[np.float64], y: NDArray[np.float64], step: float
) -> NDArray[np.float64]:
    """Interior local minima of ``y`` at least 13 h apart, refined by a parabola through 3 points.

    Matches the package's ``find_peaks(-y, distance=...)``: the deepest minimum wins when two
    fall within the spacing. Minima on the first or last sample are not markers.
    """
    inner = np.flatnonzero((y[1:-1] < y[:-2]) & (y[1:-1] <= y[2:])) + 1
    if inner.size == 0:
        return np.empty(0, dtype=np.float64)
    spacing = math.ceil(MIN_MARKER_SPACING_H / step)
    kept: list[int] = []
    for i in inner[np.argsort(y[inner], kind="stable")]:
        if all(abs(int(i) - k) >= spacing for k in kept):
            kept.append(int(i))
    idx = np.array(sorted(kept))
    left, mid, right = y[idx - 1], y[idx], y[idx + 1]
    curve = left - 2.0 * mid + right
    shift = np.where(curve > 0, 0.5 * (left - right) / np.where(curve > 0, curve, 1.0), 0.0)
    return np.asarray(hours[idx] + np.clip(shift, -0.5, 0.5) * step, dtype=np.float64)


def get_model(model: ModelName | ClockModel) -> ClockModel:
    return model if isinstance(model, ClockModel) else ClockModel(model)


@dataclass(frozen=True)
class Trajectory:
    """Model states on a grid. Row ``i`` is the state at ``grid.at(i)``; row ``n`` is the state at
    ``grid.end``, so a trajectory can be continued from its last row."""

    model: ClockModel
    grid: TimeGrid
    states: NDArray[np.float64]  # (n + 1, n_states, batch)

    @property
    def hours(self) -> NDArray[np.float64]:
        return np.arange(self.grid.n + 1, dtype=np.float64) * self.grid.step_h

    @property
    def final(self) -> NDArray[np.float64]:
        return np.asarray(self.states[-1], dtype=np.float64)

    def phase(self) -> NDArray[np.float64]:
        return self.model.phase(self.states)

    def amplitude(self) -> NDArray[np.float64]:
        return self.model.amplitude(self.states)

    def cbt_min_hours(self) -> list[NDArray[np.float64]]:
        return self.model.cbt_min_hours(self.hours, self.states)


def _as_batch_lux(lux: NDArray[np.float64], n: int) -> NDArray[np.float64]:
    arr = np.asarray(lux, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim != 2 or arr.shape[0] != n:
        raise ValueError(f"lux must have shape (n,) or (n, batch) with n={n}, got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("lux contains NaN or infinite values")
    if np.any(arr < 0):
        raise ValueError("lux cannot be negative")
    return np.minimum(arr, MAX_LUX)


def _as_batch_state(state: NDArray[np.float64], n_states: int, batch: int) -> NDArray[np.float64]:
    arr = np.asarray(state, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.shape[0] != n_states or arr.ndim != 2:
        raise ValueError(f"state must have {n_states} rows, got shape {arr.shape}")
    if arr.shape[1] == 1 and batch > 1:
        arr = np.repeat(arr, batch, axis=1)
    if arr.shape[1] != batch:
        raise ValueError(f"state has {arr.shape[1]} columns but lux has {batch}")
    return arr


def integrate(
    model: ModelName | ClockModel,
    grid: TimeGrid,
    lux: NDArray[np.float64],
    state0: NDArray[np.float64] | None = None,
) -> Trajectory:
    """Fixed-step RK4 over the grid, light held constant within each sample (SCIENCE 2.4).

    ``lux`` is (n,) or (n, batch); values above 10,000 lux are capped (SCIENCE 1.7). ``state0`` is
    (n_states,) or (n_states, batch) and defaults to the package's default state.
    """
    m = get_model(model)
    light = _as_batch_lux(lux, grid.n)
    batch = light.shape[1]
    state = _as_batch_state(m.default_state() if state0 is None else state0, m.n_states, batch)
    dt = grid.step_h
    out = np.empty((grid.n + 1, m.n_states, batch), dtype=np.float64)
    out[0] = state
    for i in range(grid.n):
        li = light[i]
        k1 = m.derivative(state, li)
        k2 = m.derivative(state + k1 * dt / 2.0, li)
        k3 = m.derivative(state + k2 * dt / 2.0, li)
        k4 = m.derivative(state + k3 * dt, li)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        out[i + 1] = state
    if not np.all(np.isfinite(out)):
        raise SimulationError(f"{m.name} produced non-finite states")
    if m.name == "hannay19" and float(out[:, 0].min()) < MIN_HANNAY_R:
        raise SimulationError(
            f"hannay19 amplitude R fell below {MIN_HANNAY_R}; its phase is undefined there"
        )
    return Trajectory(m, grid, out)


DAY_H = 24.0
WARMUP_TOL_H = 0.05  # every CBTmin moves less than this between the last two loops (SCIENCE 2.6)
WARMUP_MAX_LOOPS = 40


@dataclass(frozen=True)
class Warmup:
    """Result of looping a baseline light profile until the clock repeats itself."""

    state: NDArray[np.float64]  # (n_states, batch), the state at the end of the last loop
    loops: int
    converged: bool
    last_change_h: float  # largest CBTmin change between the last two loops
    baseline_days: float


def _whole_days(grid: TimeGrid) -> float:
    days = grid.n * grid.step_h / DAY_H
    if not math.isclose(days, round(days), abs_tol=1e-9) or round(days) < 1:
        raise ValueError(
            f"a warm-up baseline must cover whole days so it can repeat, got {days:.3f} days"
        )
    return float(round(days))


def _marker_change(a: list[NDArray[np.float64]], b: list[NDArray[np.float64]]) -> float:
    worst = 0.0
    for x, y in zip(a, b, strict=True):
        if x.shape != y.shape:
            return math.inf
        if x.size:
            worst = max(worst, float(np.abs(x - y).max()))
    return worst


def equilibrate(
    model: ModelName | ClockModel,
    grid: TimeGrid,
    lux: NDArray[np.float64],
    state0: NDArray[np.float64] | None = None,
    tol_h: float = WARMUP_TOL_H,
    max_loops: int = WARMUP_MAX_LOOPS,
) -> Warmup:
    """Repeat a whole-day light profile until every CBTmin in it moves less than ``tol_h``.

    This is the explicit warm-up: the clock starts from the package's default state (a
    16 h light, 8 h dark day) and is entrained to the baseline before anything is reported.
    The package's own ``equilibrate`` checks only the last DLMO; this checks all markers
    (docs/ARCHITECTURE.md 2.4). A run that does not converge is returned with
    ``converged=False`` so the caller can flag it.
    """
    m = get_model(model)
    days = _whole_days(grid)
    state = state0
    previous: list[NDArray[np.float64]] | None = None
    change = math.inf
    for loop in range(1, max_loops + 1):
        traj = integrate(m, grid, lux, state)
        markers = traj.cbt_min_hours()
        state = traj.final
        if previous is not None:
            change = _marker_change(previous, markers)
            if change < tol_h:
                return Warmup(state, loop, True, change, days)
        previous = markers
    assert state is not None
    return Warmup(state, max_loops, False, change, days)


@dataclass(frozen=True)
class DailyMarkers:
    """Phase markers that fall on one local calendar day."""

    day: date
    cbt_min: datetime | None  # local time
    dlmo: datetime | None  # local time, CBTmin minus the model's DLMO offset


@dataclass(frozen=True)
class Simulation:
    """One model run on one light profile after warm-up on a baseline."""

    model: ClockModel
    trajectory: Trajectory
    warmup: Warmup
    cbt_min: tuple[datetime, ...]  # UTC
    dlmo: tuple[datetime, ...]  # UTC

    @property
    def grid(self) -> TimeGrid:
        return self.trajectory.grid

    def phase(self) -> NDArray[np.float64]:
        """Phase in radians at every grid time plus the end, shape (n + 1,)."""
        return np.asarray(self.trajectory.phase()[:, 0], dtype=np.float64)

    def times(self) -> list[datetime]:
        """UTC time of every row of :meth:`phase`."""
        return [self.grid.at(i) for i in range(self.grid.n + 1)]

    def daily(self, tz: tzinfo) -> list[DailyMarkers]:
        """CBTmin and DLMO per local day of the profile, first CBTmin of the day if two."""
        first = self.grid.start.astimezone(tz).date()
        last = (self.grid.end - timedelta(microseconds=1)).astimezone(tz).date()
        lag = timedelta(hours=self.model.convention.dlmo_before_cbt_h)
        by_day: dict[date, datetime] = {}
        for t in self.cbt_min:
            local = t.astimezone(tz)
            by_day.setdefault(local.date(), local)
        out: list[DailyMarkers] = []
        for k in range((last - first).days + 1):
            d = first + timedelta(days=k)
            c = by_day.get(d)
            out.append(DailyMarkers(d, c, None if c is None else c - lag))
        return out


def simulate(
    profile: LightProfile,
    model: ModelName | ClockModel = DEFAULT_MODEL,
    baseline: LightProfile | None = None,
    tol_h: float = WARMUP_TOL_H,
    max_loops: int = WARMUP_MAX_LOOPS,
) -> Simulation:
    """Warm up on ``baseline`` (default: the profile itself), then run ``profile`` once.

    The baseline is the light the worker lives under now, repeated until the clock is
    entrained to it. It must cover whole days, use the same step and line up with the
    profile's clock time, so that looping it hands over to the profile at the right hour.
    """
    m = get_model(model)
    if profile.lux.ndim != 1:
        raise ValueError("simulate takes one light profile; use integrate for a batch")
    base = baseline or profile
    if not math.isclose(base.grid.step_h, profile.grid.step_h):
        raise ValueError(
            f"baseline step {base.grid.step_h} h differs from profile step {profile.grid.step_h} h"
        )
    gap_h = (profile.grid.start - base.grid.start).total_seconds() / 3600.0
    if not math.isclose(gap_h % DAY_H, 0.0, abs_tol=1e-6) and not math.isclose(
        gap_h % DAY_H, DAY_H, abs_tol=1e-6
    ):
        raise ValueError("baseline and profile must start at the same clock time of day")
    warm = equilibrate(m, base.grid, base.lux, tol_h=tol_h, max_loops=max_loops)
    traj = integrate(m, profile.grid, profile.lux, warm.state)
    hours = traj.cbt_min_hours()[0]
    cbt = tuple(profile.grid.start + timedelta(hours=float(h)) for h in hours)
    lag = timedelta(hours=m.convention.dlmo_before_cbt_h)
    return Simulation(m, traj, warm, cbt, tuple(t - lag for t in cbt))


def compare_models(
    profile: LightProfile,
    baseline: LightProfile | None = None,
    models: Sequence[ModelName] = MODEL_NAMES,
) -> dict[ModelName, Simulation]:
    """Run the same profile and warm-up through several models (docs/SCIENCE.md 1.9)."""
    return {name: simulate(profile, name, baseline) for name in models}
