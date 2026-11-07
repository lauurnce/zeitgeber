"""Phase response curve protocol for checking the models (docs/SCIENCE.md 4).

The protocol follows Khalsa et al. 2003 [4.1] as the circadian package encodes it in
``PhaseResponseCurveLight.light_khalsa`` (docs/SCIENCE.md 2.5): after entrainment, a constant
routine in dim light of length ``L``, 8 h of darkness, 16 h awake in dim light with the bright
pulse centered in the middle, 8 h of darkness, then dim light until the end. Varying ``L`` moves
the pulse across circadian phase. Each pulsed run has a control run with the same ``L`` and no
pulse; the phase shift is the difference between their final CBTmin times, so free-running drift
in dim light cancels.

Signs follow the published curves: advances are positive, delays negative. The phase of a pulse
is its center minus the control run's CBTmin nearest to it, in hours.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from numpy.typing import NDArray

from zeitgeber.grid import REQUEST_STEP_H, TimeGrid
from zeitgeber.sim import ClockModel, ModelName, equilibrate, get_model, integrate

# Entrainment before the protocol: 16 h light at 150 lux, 8 h dark (docs/SCIENCE.md 4.3).
ENTRAIN_LUX = 150.0
ENTRAIN_LIGHT_H = 16.0
# Protocol light levels as encoded in the package's light_khalsa (docs/SCIENCE.md 2.5).
DIM_LUX = 15.0
SLEEP_H = 8.0
WAKE_H = 16.0
POST_H = 60.0  # dim light after the second sleep; long enough for two clean CBTmin markers


@dataclass(frozen=True)
class Pulse:
    lux: float
    hours: float
    source: str


# 6.7 h at 9,985 lux: Khalsa 2003 [4.1] via the package's light_khalsa (docs/SCIENCE.md 2.5).
KHALSA_PULSE = Pulse(9_985.0, 6.7, "Khalsa 2003 [4.1]; package light_khalsa")
# 1 h at about 8,000 lux: St Hilaire 2012 [4.2]; 7,997 lux as in the package's light_hilaire.
HILAIRE_PULSE = Pulse(7_997.0, 1.0, "St Hilaire 2012 [4.2]; package light_hilaire")


@dataclass(frozen=True)
class PhaseResponse:
    model: ModelName
    pulse: Pulse
    phase_h: NDArray[np.float64]  # pulse center minus CBTmin, hours, sorted, in [-12, 12)
    shift_h: NDArray[np.float64]  # advance positive, hours
    entrained_cbt_h: float  # CBTmin on the entrainment day, hours after lights on

    @property
    def peak_to_trough_h(self) -> float:
        return float(self.shift_h.max() - self.shift_h.min())

    def crossover_h(self) -> float:
        """Phase where the curve crosses from delay to advance nearest CBTmin (phase 0)."""
        x, y = self.phase_h, self.shift_h
        found: list[float] = []
        for i in range(len(x) - 1):
            if y[i] < 0.0 <= y[i + 1]:
                found.append(float(x[i] - y[i] * (x[i + 1] - x[i]) / (y[i + 1] - y[i])))
        if not found:
            raise ValueError("the curve never crosses from delay to advance")
        return min(found, key=abs)


def _entrained_state(m: ClockModel, step_h: float) -> tuple[NDArray[np.float64], float]:
    """State at lights on after looping the 16:8 day, and that day's CBTmin (hours after on)."""
    grid = TimeGrid(datetime(2026, 1, 1, tzinfo=UTC), step_h, round(24.0 / step_h))
    lux = np.where(grid.hours() < ENTRAIN_LIGHT_H, ENTRAIN_LUX, 0.0)
    warm = equilibrate(m, grid, lux)
    day = integrate(m, grid, lux, warm.state)
    cbt = day.cbt_min_hours()[0]
    return warm.state, float(cbt[0]) if cbt.size else float("nan")


def _protocol_lux(
    grid: TimeGrid, lead_h: NDArray[np.float64], pulse: Pulse | None
) -> NDArray[np.float64]:
    """Lux for each lead length (one column each), starting at habitual lights on."""
    h = grid.hours()[:, None]
    lead = lead_h[None, :]
    lux = np.full((grid.n, lead_h.size), DIM_LUX)
    first_sleep = (h >= lead) & (h < lead + SLEEP_H)
    second_sleep = (h >= lead + SLEEP_H + WAKE_H) & (h < lead + 2 * SLEEP_H + WAKE_H)
    lux[first_sleep | second_sleep] = 0.0
    if pulse is not None:
        center = lead + SLEEP_H + WAKE_H / 2.0
        on = (h >= center - pulse.hours / 2.0 - 1e-9) & (h < center + pulse.hours / 2.0 - 1e-9)
        lux[on] = pulse.lux
    return lux


def phase_response_curve(
    model: ModelName | ClockModel,
    pulse: Pulse = KHALSA_PULSE,
    n_phases: int = 48,
    step_h: float = REQUEST_STEP_H,
) -> PhaseResponse:
    """Simulate the protocol at ``n_phases`` pulse timings spread over one cycle."""
    m = get_model(model)
    state0, entrained_cbt = _entrained_state(m, step_h)
    lead = np.round(np.arange(n_phases) * (24.0 / n_phases) / step_h) * step_h
    total = float(lead.max()) + 2 * SLEEP_H + WAKE_H + POST_H
    grid = TimeGrid(datetime(2026, 1, 1, 8, tzinfo=UTC), step_h, round(total / step_h))
    lux = np.concatenate([_protocol_lux(grid, lead, pulse), _protocol_lux(grid, lead, None)], 1)
    traj = integrate(m, grid, lux, state0)
    markers = traj.cbt_min_hours()
    centers = lead + SLEEP_H + WAKE_H / 2.0
    late = grid.n * step_h - 30.0
    phase = np.empty(n_phases)
    shift = np.empty(n_phases)
    for k in range(n_phases):
        pulsed, control = markers[k], markers[n_phases + k]
        nearest = control[np.argmin(np.abs(control - centers[k]))]
        phase[k] = (centers[k] - nearest + 12.0) % 24.0 - 12.0
        c_end = control[np.argmin(np.abs(control - late))]
        p_end = pulsed[np.argmin(np.abs(pulsed - c_end))]
        shift[k] = c_end - p_end
    order = np.argsort(phase)
    return PhaseResponse(m.name, pulse, phase[order], shift[order], entrained_cbt)
