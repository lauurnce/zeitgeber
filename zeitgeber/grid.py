"""Uniform time grid shared by the light builder and the simulator.

Sample ``i`` sits at ``start + i * step`` and stands for the interval ``[t_i, t_i + step)``; the
simulator holds light constant over it (docs/SCIENCE.md 2.4). Requests use a 0.1 h step and tests
also use 1/60 h (docs/ARCHITECTURE.md 3.4). Light arrays, trajectories and markers carry the grid
they were computed on so arrays from different grids cannot be mixed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
from numpy.typing import NDArray

REQUEST_STEP_H = 0.1
TEST_STEP_H = 1 / 60


@dataclass(frozen=True)
class TimeGrid:
    """``n`` samples from the UTC instant ``start``, ``step_h`` hours apart."""

    start: datetime
    step_h: float
    n: int

    def __post_init__(self) -> None:
        if self.start.utcoffset() != timedelta(0):
            raise ValueError("TimeGrid.start must be a timezone-aware UTC datetime")
        if self.step_h <= 0 or not math.isclose(self.step_s, round(self.step_s)):
            raise ValueError(
                f"step_h must be a positive whole number of seconds, got {self.step_h}"
            )
        if self.n < 1:
            raise ValueError(f"a grid needs at least one sample, got n={self.n}")

    @classmethod
    def covering(cls, begin: datetime, end: datetime, step_h: float = REQUEST_STEP_H) -> TimeGrid:
        """The grid from ``begin`` with as many samples as fit before ``end``."""
        n = int((end - begin) / timedelta(hours=step_h) + 1e-9)
        return cls(begin.astimezone(UTC), step_h, n)

    @property
    def step_s(self) -> float:
        return self.step_h * 3600.0

    @property
    def end(self) -> datetime:
        return self.at(self.n)

    def hours(self) -> NDArray[np.float64]:
        """Hours since ``start`` for every sample, the time axis the simulator integrates over."""
        return np.arange(self.n, dtype=np.float64) * self.step_h

    def at(self, i: int) -> datetime:
        return self.start + timedelta(seconds=round(i * self.step_s))

    def index(self, t: datetime) -> int:
        """Index of the sample whose interval contains ``t``."""
        return math.floor((t - self.start).total_seconds() / self.step_s + 1e-9)

    def mask(self, begin: datetime, end: datetime) -> NDArray[np.bool_]:
        """Samples whose time falls in ``[begin, end)``."""
        out = np.zeros(self.n, dtype=bool)
        lo = max(0, math.ceil((begin - self.start).total_seconds() / self.step_s - 1e-9))
        hi = min(self.n, math.ceil((end - self.start).total_seconds() / self.step_s - 1e-9))
        if lo < hi:
            out[lo:hi] = True
        return out
