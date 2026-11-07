"""Misalignment between the predicted clock and the work and sleep schedule (docs/SCIENCE.md 7.3).

Each main sleep episode is one scored day. For an episode from ``s`` to ``w`` with mid-sleep
``m`` and length ``L``, take the CBTmin ``c`` nearest to ``m``:

- phase angle: ``M = |wrap24(c - m) - (L/2 - 2)|``, zero when CBTmin sits 2 h before wake;
- work in the circadian low: ``P``, hours of shift inside ``[c - 2, c + 2]``;
- the score is ``S = mean(M + lam * P)`` with ``lam = 0.5``.

Reported beside ``S`` and not part of it: the share of each sleep inside the biological night,
taken as the 8 h ending 2 h after CBTmin (the window an ideal 8 h sleep would fill under the
7.3 target; design), the Crowley re-entrainment category, and the social-jetlag analogue.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from typing import Literal

from zeitgeber.schedule import Interval

LAMBDA = 0.5  # weight of work in the circadian low (SCIENCE 7.3, design)
TARGET_BEFORE_WAKE_H = 2.0  # CBTmin 2 h before wake (SCIENCE 7.3, design inside "a few hours")
LOW_HALF_WIDTH_H = 2.0  # half-width of the sleepiest window around CBTmin (SCIENCE 7.3)
NIGHT_BEFORE_CBT_H = 6.0  # biological night: CBTmin - 6 h to CBTmin + 2 h (design)
NIGHT_AFTER_CBT_H = 2.0
NO_MARKER_PENALTY_H = 12.0  # SCIENCE 7.4
MAIN_SLEEP_MIN_H = 4.0  # shorter episodes (split second halves, naps) are not scored days

Category = Literal["not", "partial", "complete", "past", "no_marker"]


def wrap_hours(delta_h: float) -> float:
    """Wrap hours into (-12, 12]."""
    out = (delta_h + 12.0) % 24.0 - 12.0
    return 12.0 if out == -12.0 else out


def _hours(td: timedelta) -> float:
    return td.total_seconds() / 3600.0


def _overlap_h(a0: datetime, a1: datetime, b0: datetime, b1: datetime) -> float:
    return max(0.0, _hours(min(a1, b1) - max(a0, b0)))


@dataclass(frozen=True)
class DayScore:
    sleep: Interval
    cbt_min: datetime | None
    delta_h: float  # wrap24(c - m)
    target_h: float  # L/2 - 2
    phase_angle_h: float  # M_d
    work_in_low_h: float  # P_d
    sleep_in_night_frac: float  # share of the sleep inside the biological night
    category: Category


@dataclass(frozen=True)
class ScoreBreakdown:
    total_h: float  # S
    phase_angle_h: float  # mean M_d
    work_in_low_h: float  # mean P_d
    sleep_in_night_frac: float  # mean share of sleep inside the biological night
    social_jetlag_h: float
    modal_category: Category
    days: tuple[DayScore, ...]
    lam: float = LAMBDA

    @property
    def flagged_days(self) -> int:
        return sum(d.category == "no_marker" for d in self.days)


def _category(c: datetime, sleep: Interval) -> Category:
    mid = sleep.start + (sleep.end - sleep.start) / 2
    if c < sleep.start:
        return "not"
    if c < mid:
        return "partial"
    if c < sleep.end:
        return "complete"
    return "past"


def score_day(sleep: Interval, cbt_min: Sequence[datetime], shifts: Sequence[Interval]) -> DayScore:
    length = _hours(sleep.end - sleep.start)
    mid = sleep.start + (sleep.end - sleep.start) / 2
    target = length / 2.0 - TARGET_BEFORE_WAKE_H
    c = min(cbt_min, key=lambda t: abs(t - mid), default=None)
    if c is None or abs(_hours(c - mid)) > 12.0:
        return DayScore(sleep, None, math.nan, target, NO_MARKER_PENALTY_H, 0.0, 0.0, "no_marker")
    delta = wrap_hours(_hours(c - mid))
    low0, low1 = c - timedelta(hours=LOW_HALF_WIDTH_H), c + timedelta(hours=LOW_HALF_WIDTH_H)
    work = sum(_overlap_h(w.start, w.end, low0, low1) for w in shifts)
    night = _overlap_h(
        sleep.start,
        sleep.end,
        c - timedelta(hours=NIGHT_BEFORE_CBT_H),
        c + timedelta(hours=NIGHT_AFTER_CBT_H),
    )
    return DayScore(
        sleep, c, delta, target, abs(delta - target), work, night / length, _category(c, sleep)
    )


def _circular_mean_clock_h(times: Sequence[datetime], tz: tzinfo) -> float:
    angles = [
        2 * math.pi * (t.astimezone(tz).hour + t.astimezone(tz).minute / 60) / 24 for t in times
    ]
    x = sum(math.cos(a) for a in angles)
    y = sum(math.sin(a) for a in angles)
    return (math.atan2(y, x) * 24 / (2 * math.pi)) % 24


def social_jetlag_h(sleeps: Sequence[Interval], tz: tzinfo) -> float:
    """|mean work-day mid-sleep - mean rest-day mid-sleep|, clock hours (adapted from [7.2])."""
    work = [s.start + (s.end - s.start) / 2 for s in sleeps if s.kind == "sleep"]
    rest = [s.start + (s.end - s.start) / 2 for s in sleeps if s.kind == "rest_sleep"]
    if not work or not rest:
        return 0.0
    return abs(wrap_hours(_circular_mean_clock_h(work, tz) - _circular_mean_clock_h(rest, tz)))


def main_sleeps(sleeps: Sequence[Interval]) -> list[Interval]:
    return [
        s
        for s in sleeps
        if s.kind in ("sleep", "rest_sleep") and _hours(s.end - s.start) >= MAIN_SLEEP_MIN_H
    ]


def score(
    cbt_min: Sequence[datetime],
    sleeps: Sequence[Interval],
    shifts: Sequence[Interval],
    tz: tzinfo,
    lam: float = LAMBDA,
) -> ScoreBreakdown:
    """Score every main sleep episode in ``sleeps`` against the CBTmin markers."""
    episodes = main_sleeps(sleeps)
    if not episodes:
        raise ValueError("no main sleep episode to score")
    days = tuple(score_day(s, cbt_min, shifts) for s in episodes)
    n = len(days)
    return ScoreBreakdown(
        total_h=sum(d.phase_angle_h + lam * d.work_in_low_h for d in days) / n,
        phase_angle_h=sum(d.phase_angle_h for d in days) / n,
        work_in_low_h=sum(d.work_in_low_h for d in days) / n,
        sleep_in_night_frac=sum(d.sleep_in_night_frac for d in days) / n,
        social_jetlag_h=social_jetlag_h(episodes, tz),
        modal_category=Counter(d.category for d in days).most_common(1)[0][0],
        days=days,
        lam=lam,
    )
