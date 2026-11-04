"""Fixture schedules validate against the Schedule model."""

import json
from pathlib import Path

import pytest

from zeitgeber.schedule import Schedule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "schedules"
NAMES = ["permanent_nights", "rotating", "day_worker"]


def load_fixture(name: str) -> Schedule:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return Schedule.model_validate(data)


@pytest.mark.parametrize("name", NAMES)
def test_fixture_is_a_valid_schedule(name: str) -> None:
    schedule = load_fixture(name)
    kinds = {iv.kind for iv in schedule.materialize()}
    assert {"shift", "commute_to_work", "commute_home", "sleep", "rest_sleep"} <= kinds
