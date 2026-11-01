"""API settings from environment variables. None of them is a secret.

- ``ZEITGEBER_CORS_ORIGINS``: comma-separated origins allowed to call the API from a browser.
- ``ZEITGEBER_RATE_LIMIT``: requests per minute per client on the compute routes (default 20).
- ``ZEITGEBER_MAX_BODY_BYTES``: largest accepted request body (default 131072, room for a
  plan document of about 47 KB sent to ``/v1/calendar``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_ORIGINS = ("https://zeitgeber-five.vercel.app", "http://localhost:3000")


class ApiSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cors_origins: tuple[str, ...] = DEFAULT_ORIGINS
    rate_limit_per_min: int = Field(20, ge=1, le=10_000)
    max_body_bytes: int = Field(131_072, ge=1_024, le=4_000_000)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ApiSettings:
        env = os.environ if env is None else env
        values: dict[str, object] = {}
        if env.get("ZEITGEBER_CORS_ORIGINS"):
            origins = (o.strip().rstrip("/") for o in env["ZEITGEBER_CORS_ORIGINS"].split(","))
            values["cors_origins"] = tuple(o for o in origins if o)
        if env.get("ZEITGEBER_RATE_LIMIT"):
            values["rate_limit_per_min"] = env["ZEITGEBER_RATE_LIMIT"]
        if env.get("ZEITGEBER_MAX_BODY_BYTES"):
            values["max_body_bytes"] = env["ZEITGEBER_MAX_BODY_BYTES"]
        return cls.model_validate(values)
