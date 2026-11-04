"""Fixture schedules validate against the Schedule model."""

import pytest
from fixture_schedules import NAMES, load_fixture


@pytest.mark.parametrize("name", NAMES)
def test_fixture_is_a_valid_schedule(name: str) -> None:
    schedule = load_fixture(name)
    kinds = {iv.kind for iv in schedule.materialize()}
    assert {"shift", "commute_to_work", "commute_home", "sleep", "rest_sleep"} <= kinds
