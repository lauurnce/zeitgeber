"""Misalignment score (docs/SCIENCE.md 7.3 and 7.4)."""

from datetime import UTC, datetime, timedelta

import pytest

from zeitgeber.schedule import Interval
from zeitgeber.score import main_sleeps, score, wrap_hours

T0 = datetime(2026, 11, 16, tzinfo=UTC)


def at(h: float) -> datetime:
    return T0 + timedelta(hours=h)


def sleep(a: float, b: float, kind: str = "sleep") -> Interval:
    return Interval(at(a), at(b), kind, "sleep")  # type: ignore[arg-type]


def shift(a: float, b: float) -> Interval:
    return Interval(at(a), at(b), "shift", "shift")


@pytest.mark.parametrize(
    ("raw", "wrapped"), [(0, 0), (13, -11), (-13, 11), (12, 12), (-12, 12), (25, 1)]
)
def test_wrap_hours(raw: float, wrapped: float) -> None:
    assert wrap_hours(raw) == wrapped


def test_cbtmin_two_hours_before_wake_scores_zero() -> None:
    result = score([at(5)], [sleep(-1, 7)], [shift(9, 18)], UTC)
    day = result.days[0]
    assert result.total_h == 0
    assert (day.delta_h, day.target_h, day.phase_angle_h) == (2, 2, 0)
    assert day.work_in_low_h == 0
    assert day.sleep_in_night_frac == 1
    assert day.category == "complete"


def test_cbtmin_inside_the_shift_counts_work_in_the_low() -> None:
    # Night shift 22:00 to 07:00, day sleep 09:00 to 15:00, clock still at 04:00.
    result = score([at(4)], [sleep(9, 15)], [shift(-2, 7)], UTC)
    day = result.days[0]
    assert day.category == "not"
    assert day.work_in_low_h == 4
    assert day.delta_h == -8
    assert day.phase_angle_h == 9  # |-8 - (3 - 2)|
    assert result.total_h == 9 + 0.5 * 4
    assert result.work_in_low_h == 4
    assert result.phase_angle_h == 9


def test_categories_follow_crowley() -> None:
    cases = {8: "not", 10: "partial", 13: "complete", 16: "past"}
    for c, expected in cases.items():
        assert score([at(c)], [sleep(9, 15)], [], UTC).days[0].category == expected


def test_no_marker_within_12_h_scores_12_and_is_flagged() -> None:
    result = score([at(40)], [sleep(9, 15)], [], UTC)
    assert result.total_h == 12
    assert result.flagged_days == 1
    assert result.modal_category == "no_marker"


def test_social_jetlag_compares_work_and_rest_mid_sleep() -> None:
    sleeps = [sleep(9, 15), sleep(33, 39), sleep(47, 55, "rest_sleep")]  # mids 12:00 and 03:00
    result = score([at(13), at(37), at(50)], sleeps, [], UTC)
    assert result.social_jetlag_h == pytest.approx(9)


def test_short_episodes_are_not_scored_days() -> None:
    assert main_sleeps([sleep(9, 15), sleep(18, 20, "rest_sleep")]) == [sleep(9, 15)]
    with pytest.raises(ValueError, match="no main sleep"):
        score([at(5)], [sleep(18, 20)], [], UTC)


def test_components_average_to_the_total() -> None:
    sleeps = [sleep(9, 15), sleep(33, 39)]
    result = score([at(4), at(36)], sleeps, [shift(-2, 7), shift(22, 31)], UTC)
    expected = sum(d.phase_angle_h + 0.5 * d.work_in_low_h for d in result.days) / 2
    assert result.total_h == pytest.approx(expected)
    assert result.total_h == pytest.approx(result.phase_angle_h + 0.5 * result.work_in_low_h)
