"""Contract test for the health route."""

from fastapi.testclient import TestClient

from api.main import app
from zeitgeber import __version__


def test_health_reports_ok_and_version() -> None:
    response = TestClient(app).get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}
