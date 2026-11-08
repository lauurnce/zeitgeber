"""Latency of POST /v1/plan against the 6 s budget (docs/ARCHITECTURE.md 3.4 and 3.6).

Runs only with ZEITGEBER_PERF=1. With ZEITGEBER_API_URL set it measures the deployed API
(one warm-up request, then three timed ones); otherwise it measures the app in process.
The budget is not met yet (docs/DECISIONS.md D42), so the check is a strict expected failure:
it will report XPASS, and fail, once the plan route fits the budget.
"""

import json
import os
import statistics
import time
import urllib.request

import pytest
from fastapi.testclient import TestClient
from helpers import schedule

from api.main import app

BUDGET_S = 6.0
pytestmark = pytest.mark.perf


def timed_requests(n: int) -> list[float]:
    body = {"schedule": schedule("permanent_nights")}
    url = os.environ.get("ZEITGEBER_API_URL", "").rstrip("/")
    times = []
    if url:
        data = json.dumps(body).encode()
        for k in range(n + 1):
            request = urllib.request.Request(
                f"{url}/v1/plan", data=data, headers={"content-type": "application/json"}
            )
            start = time.perf_counter()
            with urllib.request.urlopen(request, timeout=60) as response:
                assert response.status == 200
                response.read()
            if k:  # the first request may include a cold start
                times.append(time.perf_counter() - start)
        return times
    client = TestClient(app)
    for _ in range(n):
        start = time.perf_counter()
        assert client.post("/v1/plan", json=body).status_code == 200
        times.append(time.perf_counter() - start)
    return times


@pytest.mark.xfail(
    strict=True,
    reason="D42: about 6.4 s in process on the dev Mac and 22 s on Vercel; budget 6 s",
)
def test_plan_fits_the_latency_budget() -> None:
    times = timed_requests(3)
    print(f"plan latency: median {statistics.median(times):.2f} s, max {max(times):.2f} s")
    assert max(times) < BUDGET_S
