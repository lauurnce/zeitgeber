"""Error cases, limits, CORS and the privacy rules of the API."""

import asyncio
import logging
from collections.abc import MutableMapping
from typing import Any

import pytest
from fastapi.testclient import TestClient
from helpers import schedule, validate

import api.main
from api.config import ApiSettings
from api.limits import BodySizeLimit, RateLimiter
from api.main import create_app

client = TestClient(create_app(ApiSettings()))


def errors_of(response: Any) -> list[dict[str, Any]]:
    assert response.status_code == 422, response.text
    assert response.headers["content-type"] == "application/problem+json"
    return list(response.json()["errors"])


def test_invalid_json_is_a_problem_not_a_crash() -> None:
    response = client.post(
        "/v1/plan", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert errors_of(response)[0]["type"] == "json_invalid"


def test_missing_and_unknown_fields_name_their_location() -> None:
    body = {"schedule": {**schedule(), "favourite_colour": "blue"}}
    del body["schedule"]["commute_home"]
    found = {
        (tuple(e["location"]), e["type"]) for e in errors_of(client.post("/v1/plan", json=body))
    }
    assert (("schedule", "commute_home"), "missing") in found
    assert (("schedule", "favourite_colour"), "extra_forbidden") in found


def test_schedule_conflicts_come_back_in_plain_words() -> None:
    s = schedule()
    s["sleep"]["after_shift"] = {"start": "05:00", "end": "12:00"}  # before getting home
    (error,) = errors_of(client.post("/v1/plan", json={"schedule": s}))
    assert error["message"].startswith("schedule conflicts: the sleep after the Monday shift")
    assert "after you get home" in error["message"]


PATCHES: list[tuple[dict[str, Any], list[str]]] = [
    ({"location": {"timezone": "Mars/Olympus"}}, ["schedule", "location", "timezone"]),
    ({"plan_days": 60}, ["schedule", "plan_days"]),
    ({"shifts": []}, ["schedule", "shifts"]),
]


@pytest.mark.parametrize(("patch", "where"), PATCHES)
def test_out_of_range_values_are_rejected(patch: dict[str, Any], where: list[str]) -> None:
    errors = errors_of(client.post("/v1/plan", json={"schedule": {**schedule(), **patch}}))
    assert any(e["location"][: len(where)] == where for e in errors)


def test_bad_options_and_models_are_rejected() -> None:
    body: dict[str, Any] = {"schedule": schedule(), "options": {"seed": -1}}
    assert errors_of(client.post("/v1/plan", json=body))[0]["location"] == ["options", "seed"]
    body = {"schedule": schedule(), "model": "made_up"}
    assert errors_of(client.post("/v1/simulate", json=body))[0]["location"] == ["model"]
    response = client.post("/v1/plan.ics?lang=fr", json={"schedule": schedule()})
    assert errors_of(response)[0]["location"] == ["query", "lang"]


def test_unknown_routes_and_methods_are_problems() -> None:
    assert client.get("/v1/nothing").status_code == 404
    response = client.get("/v1/plan")
    assert response.status_code == 405
    assert response.headers["content-type"] == "application/problem+json"


def test_large_bodies_are_refused_with_413() -> None:
    small = TestClient(create_app(ApiSettings(max_body_bytes=2048)))
    body = {"schedule": {**schedule(), "padding": "x" * 4000}}
    response = small.post("/v1/plan", json=body)
    assert response.status_code == 413
    validate(small.app, "Problem", response.json())  # type: ignore[arg-type]


def test_streamed_bodies_are_cut_off_at_the_limit() -> None:
    sent: list[MutableMapping[str, Any]] = []
    rejected: list[bool] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        while (await receive()).get("more_body"):
            pass

    async def reject(scope: Any, receive: Any, send: Any) -> None:
        rejected.append(True)

    chunks = iter([b"x" * 600, b"x" * 600, b""])

    async def receive() -> dict[str, Any]:
        chunk = next(chunks)
        return {"type": "http.request", "body": chunk, "more_body": bool(chunk)}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    limit = BodySizeLimit(inner, max_bytes=1024, on_reject=reject)
    asyncio.run(limit({"type": "http", "headers": []}, receive, send))
    assert rejected == [True]


def test_rate_limit_answers_429_with_retry_after() -> None:
    limited = TestClient(create_app(ApiSettings(rate_limit_per_min=2)))
    codes = [limited.post("/v1/simulate", json={}).status_code for _ in range(3)]
    assert codes == [422, 422, 429]
    response = limited.post("/v1/simulate", json={})
    assert int(response.headers["retry-after"]) >= 1
    assert limited.get("/v1/health").status_code == 200  # health is not limited


def test_rate_limiter_window_and_client_keys() -> None:
    now = [0.0]
    limiter = RateLimiter(2, clock=lambda: now[0])
    a = limiter.key("203.0.113.9, 10.0.0.1", None)
    assert a == limiter.key("203.0.113.9", "10.0.0.2") != limiter.key("198.51.100.1", None)
    assert "203.0.113.9" not in a
    assert [limiter.check(a), limiter.check(a)] == [None, None]
    assert limiter.check(a) == pytest.approx(60.0)
    now[0] = 60.0
    assert limiter.check(a) is None


def test_cors_allows_only_the_web_origins() -> None:
    app = TestClient(create_app(ApiSettings(cors_origins=("https://zeitgeber.example",))))
    headers = {"access-control-request-method": "POST"}
    ok = app.options("/v1/plan", headers={**headers, "origin": "https://zeitgeber.example"})
    assert ok.headers["access-control-allow-origin"] == "https://zeitgeber.example"
    other = app.options("/v1/plan", headers={**headers, "origin": "https://elsewhere.example"})
    assert "access-control-allow-origin" not in other.headers


def test_settings_come_from_the_environment() -> None:
    env = {
        "ZEITGEBER_CORS_ORIGINS": "https://a.example/, https://b.example",
        "ZEITGEBER_RATE_LIMIT": "5",
        "ZEITGEBER_MAX_BODY_BYTES": "4096",
    }
    s = ApiSettings.from_env(env)
    assert s.cors_origins == ("https://a.example", "https://b.example")
    assert (s.rate_limit_per_min, s.max_body_bytes) == (5, 4096)


def test_unexpected_errors_are_scrubbed(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise ValueError("night shift 22:00 at Ortigas")

    monkeypatch.setattr(api.main, "search", broken)
    app = TestClient(create_app(ApiSettings()), raise_server_exceptions=False)
    with caplog.at_level(logging.DEBUG):
        response = app.post("/v1/plan", json={"schedule": schedule()})
    assert response.status_code == 500
    assert "22:00" not in response.text and "Ortigas" not in response.text
    assert "ValueError" in caplog.text
    assert "22:00" not in caplog.text and "Ortigas" not in caplog.text


def test_no_schedule_detail_is_logged_on_success(caplog: pytest.LogCaptureFixture) -> None:
    body = {"schedule": schedule(), "options": {"cross_check": False}}
    with caplog.at_level(logging.DEBUG):
        assert client.post("/v1/plan", json=body).status_code == 200
    for detail in ("22:00", "07:00", "anchor_date", "2026-11-16"):
        assert detail not in caplog.text
