"""Runtime settings, read from environment variables.

Optional nudge rewording is off unless ``ZEITGEBER_LLM_WORDING`` is set to a true value. The
provider and model are settings so that the rest of the code never names a vendor; provider
adapters live in :mod:`zeitgeber.output.providers`.

- ``ZEITGEBER_LLM_WORDING``: ``1``, ``true`` or ``yes`` turns rewording on (default off).
- ``ZEITGEBER_LLM_PROVIDER``: ``anthropic`` (the only provider in v0.1).
- ``ZEITGEBER_LLM_MODEL``: model id for the provider (default ``claude-opus-5-5``).
- ``ZEITGEBER_LLM_TIMEOUT_S``: per-call timeout in seconds (default 10).

The provider's own credentials come from its usual variables (``ANTHROPIC_API_KEY``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Provider = Literal["anthropic"]
TRUE = {"1", "true", "yes", "on"}


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    llm_wording: bool = False
    llm_provider: Provider = "anthropic"
    llm_model: str = "claude-opus-5-5"
    llm_timeout_s: float = Field(10.0, gt=0, le=60)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        values: dict[str, object] = {
            "llm_wording": env.get("ZEITGEBER_LLM_WORDING", "").strip().lower() in TRUE
        }
        for field, name in (
            ("llm_provider", "ZEITGEBER_LLM_PROVIDER"),
            ("llm_model", "ZEITGEBER_LLM_MODEL"),
            ("llm_timeout_s", "ZEITGEBER_LLM_TIMEOUT_S"),
        ):
            if env.get(name):
                values[field] = env[name].strip()
        return cls.model_validate(values)
