"""Planner results for the fixture schedules, searched once per test session."""

from fixture_schedules import load_fixture

from zeitgeber.plan import PlanResult, SearchConfig, search

CONFIG = SearchConfig(cross_check=None)
_results: dict[str, PlanResult] = {}


def planned(name: str) -> PlanResult:
    if name not in _results:
        _results[name] = search(load_fixture(name), CONFIG)
    return _results[name]
