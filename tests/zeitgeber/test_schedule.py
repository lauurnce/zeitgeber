"""Schedule validation and materialization."""

import re
from datetime import UTC, date, time, timedelta
from itertools import pairwise

import pytest
from fixture_schedules import NAMES, load_fixture
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from zeitgeber.schedule import (
    Commute,
    RestDayPolicy,
    Schedule,
    Shift,
    SleepWindow,
    SleepWindows,
)

MONDAY = date(2026, 11, 16)


def nights(**overrides: object) -> Schedule:
    fields: dict[str, object] = {
        "anchor_date": MONDAY,
        "shifts": [Shift(weekday=d, start=time(22), end=time(7)) for d in range(5)],
        "commute_to_work": Commute(duration_min=90, outdoor_share=0.3),
        "commute_home": Commute(duration_min=90, outdoor_share=0.44),
        "sleep": SleepWindows(
            after_shift=SleepWindow(start=time(9), end=time(15)),
            rest_day=SleepWindow(start=time(23), end=time(7)),
        ),
    }
    fields.update(overrides)
    return Schedule.model_validate(fields)


def test_two_shifts_on_one_weekday_are_rejected() -> None:
    shifts = [
        Shift(weekday=0, start=time(22), end=time(7)),
        Shift(weekday=0, start=time(9), end=time(17)),
    ]
    with pytest.raises(ValidationError, match="two shifts start on Monday"):
        nights(shifts=shifts)


def test_overlapping_shifts_are_rejected() -> None:
    shifts = [
        Shift(weekday=0, start=time(22), end=time(7)),
        Shift(weekday=1, start=time(6), end=time(15)),
    ]
    with pytest.raises(ValidationError, match=r"Monday shift .* overlaps .*Tuesday shift"):
        nights(shifts=shifts)


def test_sleep_during_a_shift_is_rejected() -> None:
    sleep = SleepWindows(
        after_shift=SleepWindow(start=time(12), end=time(23)),
        rest_day=SleepWindow(start=time(23), end=time(7)),
    )
    with pytest.raises(ValidationError, match=r"sleep after the Monday shift .* overlaps"):
        nights(sleep=sleep)


def test_sleep_before_getting_home_is_rejected() -> None:
    sleep = SleepWindows(
        after_shift=SleepWindow(start=time(8), end=time(15)),
        rest_day=SleepWindow(start=time(23), end=time(7)),
    )
    with pytest.raises(
        ValidationError,
        match=re.escape("starts at Tuesday 08:00, before you get home at Tuesday 08:30"),
    ):
        nights(sleep=sleep)


def test_split_policy_needs_a_second_window() -> None:
    with pytest.raises(ValidationError, match=re.escape("needs sleep.rest_day_second")):
        nights(rest_days=RestDayPolicy(mode="split"))


def test_rest_day_policies_change_weekend_sleep() -> None:
    tz = nights().location.tz

    def weekend_sleeps(schedule: Schedule) -> list[str]:
        return [
            f"{iv.start.astimezone(tz):%a %H:%M}"
            for iv in schedule.materialize(days=7)
            if iv.kind == "rest_sleep"
        ]

    assert weekend_sleeps(nights()) == ["Mon 00:00", "Sat 23:00", "Sun 23:00"]
    assert weekend_sleeps(nights(rest_days=RestDayPolicy(mode="keep_nights"))) == ["Sun 09:00"]
    split = nights(
        rest_days=RestDayPolicy(mode="split"),
        sleep=SleepWindows(
            after_shift=SleepWindow(start=time(9), end=time(15)),
            rest_day=SleepWindow(start=time(2), end=time(7)),
            rest_day_second=SleepWindow(start=time(14), end=time(17)),
        ),
    )
    # Saturday 02:00 falls inside the Friday shift and 14:00 inside the after-shift sleep.
    assert weekend_sleeps(split) == ["Sun 02:00", "Sun 14:00"]


def test_materialize_uses_utc_and_clips_to_the_window() -> None:
    schedule = nights()
    begin, end = schedule.window_utc()
    intervals = schedule.materialize()
    assert begin == schedule.window_utc()[0] and end - begin == timedelta(days=14)
    assert all(iv.start.tzinfo is UTC and iv.end.tzinfo is UTC for iv in intervals)
    assert intervals[0].start >= begin and intervals[-1].end <= end


@given(name=st.sampled_from(NAMES), offset=st.integers(0, 6), days=st.integers(1, 21))
def test_materialized_intervals_never_overlap(name: str, offset: int, days: int) -> None:
    schedule = load_fixture(name)
    start = schedule.anchor_date + timedelta(days=offset)
    begin, end = schedule.window_utc(start, days)
    intervals = schedule.materialize(start, days)
    for a, b in pairwise(intervals):
        assert a.end <= b.start
    assert all(begin <= iv.start < iv.end <= end for iv in intervals)
