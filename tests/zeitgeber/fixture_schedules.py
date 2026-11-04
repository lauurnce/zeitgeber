"""Loader for the fixture schedules in tests/fixtures/schedules."""

import json
from pathlib import Path

from zeitgeber.schedule import Schedule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "schedules"
NAMES = ["permanent_nights", "rotating", "day_worker"]


def load_fixture(name: str) -> Schedule:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return Schedule.model_validate(data)
