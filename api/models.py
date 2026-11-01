"""Request and response bodies. The schedule model is :class:`zeitgeber.schedule.Schedule`."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from zeitgeber.output.plan import PlanDocument
from zeitgeber.schedule import Schedule
from zeitgeber.sim import ModelName


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanOptions(_Model):
    seed: int = Field(0, ge=0, le=2**31 - 1, description="Same schedule and seed, same plan.")
    cross_check: bool = Field(
        True, description="Also score the plan under Hannay19 (adds about 1 s)."
    )
    slow_caffeine: bool = Field(
        False, description="Use the 8 h caffeine cutoff instead of 6 h (SCIENCE rule C2)."
    )
    wording: bool = Field(
        False,
        description="Reword nudges with the configured language model, if the server has one. "
        "Rewordings that add a time, a number or a medical term are replaced by the template.",
    )


class PlanRequest(_Model):
    schedule: Schedule
    options: PlanOptions = Field(default_factory=PlanOptions)


class CalendarRequest(_Model):
    plan: PlanDocument = Field(description="A plan document returned by POST /v1/plan.")
    lang: Literal["en", "tl"] = "en"


class SimulateRequest(_Model):
    schedule: Schedule
    model: ModelName = "forger99"


class DayMarkers(_Model):
    date: date
    cbt_min_local: datetime | None
    dlmo_local: datetime | None


class SimulateResponse(_Model):
    model: ModelName
    timezone: str
    warmup_loops: int
    warmup_converged: bool
    days: list[DayMarkers]


class Health(_Model):
    status: Literal["ok"]
    version: str
    models: list[str]
    schema_version: str


class FieldError(_Model):
    location: list[str | int]
    message: str
    type: str


class Problem(_Model):
    """RFC 9457 problem details."""

    type: str
    title: str
    status: int
    detail: str | None = None
    errors: list[FieldError] | None = None
