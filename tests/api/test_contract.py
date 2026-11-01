"""Contract tests: every response matches the schema the API publishes in its OpenAPI."""

from datetime import date

import icalendar
import pytest
from fastapi.testclient import TestClient
from helpers import response_schema, schedule, validate

from api.main import app
from zeitgeber.output.plan import PlanDocument

client = TestClient(app)


def test_openapi_lists_the_routes_and_states_the_privacy_rules() -> None:
    spec = app.openapi()
    assert set(spec["paths"]) == {
        "/v1/health",
        "/v1/plan",
        "/v1/plan.ics",
        "/v1/calendar",
        "/v1/simulate",
    }
    text = spec["info"]["description"]
    for promise in ("Stateless by design", "Nothing is stored", "never logged"):
        assert promise in text
    for path in ("/v1/plan", "/v1/plan.ics", "/v1/calendar", "/v1/simulate"):
        responses = spec["paths"][path]["post"]["responses"]
        assert {"200", "413", "422", "429"} <= set(responses)


def test_health_matches_its_schema() -> None:
    response = client.get("/v1/health")
    validate(app, "Health", response.json())


@pytest.mark.parametrize("name", ["permanent_nights", "day_worker"])
def test_plan_matches_its_schema(name: str) -> None:
    body = {"schedule": schedule(name), "options": {"cross_check": False}}
    response = client.post("/v1/plan", json=body)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/json"
    validate(app, "PlanDocument", response.json())
    doc = PlanDocument.model_validate(response.json())
    assert doc.start_date == date(2026, 11, 16) and len(doc.days) == 14
    assert doc.score.cross_check_plan is None


def test_plan_is_deterministic_for_a_seed() -> None:
    body = {"schedule": schedule(), "options": {"seed": 3, "cross_check": False}}
    a, b = (client.post("/v1/plan", json=body).json() for _ in range(2))
    a.pop("generated_at"), b.pop("generated_at")
    assert a == b


def test_calendar_route_returns_a_parseable_file() -> None:
    body = {"schedule": schedule(), "options": {"cross_check": False}}
    response = client.post("/v1/plan.ics?lang=tl", json=body)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert "attachment" in response.headers["content-disposition"]
    assert "text/calendar" in response_schema(app, "/v1/plan.ics", "post", "200")["content"]
    cal = icalendar.Calendar.from_ical(response.text)
    assert len(list(cal.walk("VEVENT"))) > 50


def test_simulate_matches_its_schema() -> None:
    response = client.post("/v1/simulate", json={"schedule": schedule(), "model": "hannay19"})
    assert response.status_code == 200, response.text
    body = response.json()
    validate(app, "SimulateResponse", body)
    assert body["model"] == "hannay19" and len(body["days"]) == 14
    assert body["warmup_converged"] is True
    assert sum(d["cbt_min_local"] is not None for d in body["days"]) >= 13


def test_error_bodies_match_the_problem_schema() -> None:
    response = client.post("/v1/plan", json={"schedule": {}})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    validate(app, "Problem", response.json())


def test_calendar_renders_a_returned_plan_without_a_new_search() -> None:
    body = {"schedule": schedule(), "options": {"cross_check": False}}
    plan = client.post("/v1/plan", json=body).json()
    response = client.post("/v1/calendar", json={"plan": plan, "lang": "tl"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    events = list(icalendar.Calendar.from_ical(response.text).walk("VEVENT"))
    assert len(events) == sum(len(d["events"]) for d in plan["days"])
    assert any("ang huling kape mo" in str(e.get("DESCRIPTION")) for e in events)
    broken = client.post("/v1/calendar", json={"plan": {**plan, "schema_version": "9"}})
    assert broken.status_code == 422
