"""Fixture schedules parse and carry the fields the Schedule model will require.

Full validation against the Schedule model arrives with zeitgeber.schedule.
"""

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "schedules"
REQUIRED = {
    "anchor_date",
    "plan_days",
    "location",
    "shifts",
    "commute_to_work",
    "commute_home",
    "sleep",
    "rest_days",
}


@pytest.mark.parametrize("name", ["permanent_nights", "rotating", "day_worker"])
def test_fixture_has_required_fields(name: str) -> None:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    assert data.keys() >= REQUIRED
    weekdays = [shift["weekday"] for shift in data["shifts"]]
    assert len(weekdays) == len(set(weekdays))
    assert not set(weekdays) & set(data["rest_days"]["weekdays"])
    for commute in (data["commute_to_work"], data["commute_home"]):
        assert 0 <= commute["outdoor_min"] <= commute["duration_min"]
