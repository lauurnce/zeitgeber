"""Shared helpers for the API tests: fixture schedules and OpenAPI schema validation."""

import json
from functools import cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from jsonschema import Draft202012Validator

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "schedules"


def schedule(name: str = "permanent_nights") -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return data


@cache
def _openapi(app_id: int, app: FastAPI) -> dict[str, Any]:
    return app.openapi()


def validate(app: FastAPI, component: str, body: object) -> None:
    """Validate ``body`` against ``#/components/schemas/<component>`` of the app's OpenAPI."""
    document = dict(_openapi(id(app), app))
    root = {**document, "$ref": f"#/components/schemas/{component}"}
    Draft202012Validator(root).validate(body)


def response_schema(app: FastAPI, path: str, method: str, status: str) -> dict[str, Any]:
    op = _openapi(id(app), app)["paths"][path][method]
    return dict(op["responses"][status])
