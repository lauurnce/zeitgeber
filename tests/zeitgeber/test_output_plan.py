"""Plan document: schema validation, events, recommendations and explanations."""

import json
from datetime import UTC, datetime, timedelta
from functools import cache

import pytest
from fixture_plans import planned
from golden import ROOT, check_golden
from pydantic import ValidationError

from zeitgeber.output import plan_document
from zeitgeber.output.plan import SCHEMA_VERSION, PlanDocument, json_schema, render_timeline

FIXTURES = ["permanent_nights", "rotating", "day_worker"]
GENERATED = datetime(2026, 11, 6, tzinfo=UTC)


@cache
def document(name: str) -> PlanDocument:
    return plan_document(planned(name), GENERATED)


def test_committed_schema_matches_the_model() -> None:
    text = json.dumps(json_schema(), indent=2, sort_keys=True) + "\n"
    check_golden(ROOT / "docs" / "schema" / f"plan-{SCHEMA_VERSION}.json", text)


@pytest.mark.parametrize("name", FIXTURES)
def test_document_round_trips_through_json(name: str) -> None:
    doc = document(name)
    again = PlanDocument.model_validate_json(doc.model_dump_json())
    assert again == doc
    assert doc.schema_version == "1.0" and doc.timezone == "Asia/Manila"


def test_schema_rejects_unknown_fields_and_versions() -> None:
    data = document("permanent_nights").model_dump(mode="json")
    with pytest.raises(ValidationError):
        PlanDocument.model_validate({**data, "extra": 1})
    with pytest.raises(ValidationError):
        PlanDocument.model_validate({**data, "schema_version": "2.0"})


@pytest.mark.parametrize("name", FIXTURES)
def test_events_are_ordered_unique_local_and_inside_the_plan(name: str) -> None:
    doc = document(name)
    events = doc.events()
    assert len({e.id for e in events}) == len(events)
    assert [e.start_utc for e in events] == sorted(e.start_utc for e in events)
    first = doc.start_date
    for day in doc.days:
        assert all(e.start_local.date() == day.date for e in day.events)
    for e in events:
        assert e.start_local.utcoffset() == timedelta(hours=8)
        assert e.start_local == e.start_utc and e.end_utc > e.start_utc
        assert first <= e.start_local.date() < first + timedelta(days=doc.days_count)
        assert not e.recommended or e.rule_ids, f"{e.id} is recommended without a rule"


@pytest.mark.parametrize("name", FIXTURES)
def test_no_recommended_sleep_or_nap_overlaps_a_shift(name: str) -> None:
    events = document(name).events()
    shifts = [e for e in events if e.kind == "shift"]
    for e in events:
        if e.kind in ("sleep", "rest_sleep", "nap"):
            assert not any(e.start_utc < s.end_utc and s.start_utc < e.end_utc for s in shifts)


@pytest.mark.parametrize("name", FIXTURES)
def test_explanations_and_nudges_follow_the_plan(name: str) -> None:
    result, doc = planned(name), document(name)
    assert [e.intervention for e in doc.explanations] == [
        e.intervention for e in result.explanations
    ]
    assert doc.score.plan.total_h == pytest.approx(result.plan.score.total_h, abs=1e-3)
    ids = {e.id for e in doc.events()}
    assert doc.nudges and all(n.event_id in ids for n in doc.nudges)
    assert all(n.source == {"en": "template", "tl": "template"} for n in doc.nudges)


def test_night_worker_plan_lists_each_change() -> None:
    doc = document("permanent_nights")
    names = [r.intervention for r in doc.recommendations]
    assert names == ["sunglasses", "sleep", "rest_day", "light_brake", "caffeine"]
    caffeine = [e for e in doc.events() if e.kind == "caffeine"]
    assert caffeine and all(e.rule_ids == ["C1", "C3"] for e in caffeine)


def test_day_worker_is_told_to_keep_the_schedule() -> None:
    doc = document("day_worker")
    assert [r.intervention for r in doc.recommendations] == ["keep", "caffeine"]
    assert doc.explanations == []


@pytest.mark.parametrize("name", FIXTURES)
def test_timeline_golden_text(name: str) -> None:
    doc = document(name)
    parts = [render_timeline(doc, "en"), render_timeline(doc, "tl"), "Nudges"]
    seen: set[str] = set()
    for n in doc.nudges:
        line = f"- {n.template}\n  en: {n.text.en}\n  tl: {n.text.tl}"
        if line not in seen:
            seen.add(line)
            parts.append(line)
    check_golden(ROOT / "tests" / "golden" / f"{name}.txt", "\n".join(parts) + "\n")
