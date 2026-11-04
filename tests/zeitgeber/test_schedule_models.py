"""Validation of the schedule value models."""

import re
from datetime import time

import pytest
from pydantic import ValidationError

from zeitgeber.schedule import Commute, Location, Shift, SleepWindow, SleepWindows


def test_location_defaults_to_manila() -> None:
    loc = Location()
    assert (loc.name, loc.timezone) == ("Manila", "Asia/Manila")
    assert loc.latitude == pytest.approx(14.5995)


def test_location_rejects_unknown_timezone() -> None:
    with pytest.raises(ValidationError, match="unknown time zone"):
        Location(timezone="Asia/Atlantis")


def test_location_rejects_polar_latitude() -> None:
    with pytest.raises(ValidationError):
        Location(latitude=80.0)


def test_night_shift_crosses_midnight() -> None:
    shift = Shift(weekday=0, start=time(22), end=time(7))
    assert shift.duration_min == 540
    assert shift.crosses_midnight


def test_shift_length_error_names_the_day() -> None:
    with pytest.raises(
        ValidationError, match=re.escape("Tuesday shift 09:00 to 10:00 lasts 1.0 h")
    ):
        Shift(weekday=1, start=time(9), end=time(10))


def test_commute_outdoor_minutes_and_driving() -> None:
    commute = Commute(duration_min=90, outdoor_share=40 / 90, mode="car_driver")
    assert commute.outdoor_min == 40
    assert commute.drives


def test_commute_share_is_a_fraction() -> None:
    with pytest.raises(ValidationError):
        Commute(duration_min=60, outdoor_share=1.5)


def test_sleep_window_length_is_checked() -> None:
    with pytest.raises(ValidationError, match="sleep windows must last 3 to 12 h"):
        SleepWindow(start=time(9), end=time(10))


def test_sleep_windows_override_by_weekday() -> None:
    default = SleepWindow(start=time(9), end=time(15))
    monday = SleepWindow(start=time(21, 30), end=time(5))
    windows = SleepWindows(
        after_shift=default,
        after_shift_by_weekday={0: monday},
        rest_day=SleepWindow(start=time(23), end=time(7)),
    )
    assert windows.for_shift(0) == monday
    assert windows.for_shift(3) == default


def test_sleep_windows_reject_bad_weekday_key() -> None:
    window = SleepWindow(start=time(9), end=time(15))
    with pytest.raises(ValidationError, match="weekdays 0 to 6"):
        SleepWindows(after_shift=window, after_shift_by_weekday={7: window}, rest_day=window)
