"""Zeitgeber HTTP API (docs/ARCHITECTURE.md 2.8).

Stateless: a schedule is processed in memory for one request and dropped. Nothing is stored,
request bodies are never logged, and unexpected errors are logged by exception class only, so
no schedule detail reaches the logs.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import ApiSettings
from api.limits import BodySizeLimit, Message, RateLimiter, Receive, Scope, Send
from api.models import (
    CalendarRequest,
    DayMarkers,
    FieldError,
    Health,
    PlanRequest,
    Problem,
    SimulateRequest,
    SimulateResponse,
)
from zeitgeber import __version__
from zeitgeber.output import plan_document
from zeitgeber.output.copy import Lang
from zeitgeber.output.ics import render_ics
from zeitgeber.output.plan import SCHEMA_VERSION, PlanDocument
from zeitgeber.output.providers import rewriter_from_settings
from zeitgeber.plan import InfeasibleError, SearchConfig, search
from zeitgeber.schedule import Schedule
from zeitgeber.sim import CROSS_CHECK_MODEL, MODEL_NAMES, SimulationError, simulate

log = logging.getLogger("zeitgeber.api")
PROBLEM = "application/problem+json"
DOCS = "https://github.com/lauurnce/zeitgeber/blob/main/docs/API.md"

DESCRIPTION = """
Body-clock planner for night-shift workers. Wellness planning, not medical advice.

**Stateless by design.** Each schedule is processed in memory for one request and then
dropped. Nothing is stored: no database, no cache of schedules, no cookies. Request bodies and
query strings are never logged, and errors are logged by type only, without schedule details.
The optional nudge rewording receives template text only, never the schedule.

Times in requests are local wall-clock times in the schedule's timezone (default
Asia/Manila). Errors use RFC 9457 problem details.
"""


def problem(status: int, title: str, detail: str | None = None, **extra: Any) -> JSONResponse:
    slug = title.lower().replace(" ", "-")
    body = Problem(type=f"{DOCS}#{slug}", title=title, status=status, detail=detail, **extra)
    return JSONResponse(body.model_dump(exclude_none=True), status_code=status, media_type=PROBLEM)


async def _too_large(scope: Scope, receive: Receive, send: Send) -> None:
    await problem(413, "Request too large", "The request body is over the size limit.")(
        scope, receive, send
    )


class ScrubErrors:
    """Turns any unhandled exception into a plain 500 and logs only its class name."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        started = False

        async def tracking(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking)
        except Exception as exc:
            log.error("unhandled %s on %s", type(exc).__name__, scope.get("path", "?"))
            if not started and scope["type"] == "http":
                await problem(500, "Internal error", "Something went wrong on our side.")(
                    scope, receive, send
                )


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or ApiSettings.from_env()
    limiter = RateLimiter(settings.rate_limit_per_min)
    errors: dict[int | str, dict[str, Any]] = {
        status: {"model": Problem, "description": text, "content": {PROBLEM: {}}}
        for status, text in (
            (413, "Request body over the size limit"),
            (422, "The request is invalid or no plan fits the schedule"),
            (429, "Too many requests from this client; see Retry-After"),
        )
    }
    app = FastAPI(
        title="Zeitgeber API",
        version=__version__,
        description=DESCRIPTION,
        license_info={"name": "MIT", "identifier": "MIT"},
        docs_url="/docs",
        redoc_url=None,
    )

    def rate_limit(request: Request) -> None:
        peer = request.client.host if request.client else None
        wait = limiter.check(limiter.key(request.headers.get("x-forwarded-for"), peer))
        if wait is not None:
            raise HTTPException(429, headers={"Retry-After": str(max(1, round(wait)))})

    limited = [Depends(rate_limit)]

    @app.exception_handler(RequestValidationError)
    async def invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        found = [
            FieldError(
                location=[p for p in e["loc"] if p != "body"] or ["body"],
                message=str(e["msg"]).removeprefix("Value error, "),
                type=str(e["type"]),
            )
            for e in exc.errors()
        ]
        return problem(
            422, "Invalid request", f"{len(found)} problem(s) in the request.", errors=found
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        titles = {404: "Not found", 405: "Method not allowed", 429: "Too many requests"}
        response = problem(exc.status_code, titles.get(exc.status_code, "Error"), exc.detail)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.middleware("http")
    async def no_store(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/v1/health", tags=["service"])
    def health() -> Health:
        """Service status, core version, available models and plan schema version."""
        return Health(
            status="ok",
            version=__version__,
            models=list(MODEL_NAMES),
            schema_version=SCHEMA_VERSION,
        )

    def make_plan(body: PlanRequest) -> PlanDocument:
        o = body.options
        config = SearchConfig(
            seed=o.seed,
            cross_check=CROSS_CHECK_MODEL if o.cross_check else None,
            slow_caffeine=o.slow_caffeine,
        )
        try:
            result = search(body.schedule, config)
        except InfeasibleError as err:
            raise HTTPException(422, detail=f"No plan fits this schedule: {err}") from err
        rewriter = rewriter_from_settings() if o.wording else None
        return plan_document(result, datetime.now(UTC), rewriter=rewriter)

    @app.post("/v1/plan", tags=["plan"], dependencies=limited, responses=errors)
    def plan(body: PlanRequest) -> PlanDocument:
        """Search a 14-day plan for a weekly schedule.

        Returns the plan document (schema 1.0): days and events in local time, recommended
        changes with their rule ids, the misalignment score before and after, an ablation
        explanation per change, and nudges in English and Taglish.
        """
        return make_plan(body)

    @app.post(
        "/v1/plan.ics",
        tags=["plan"],
        dependencies=limited,
        responses={**errors, 200: {"content": {"text/calendar": {}}}},
        response_class=Response,
    )
    def plan_ics(
        body: PlanRequest, lang: Annotated[Literal["en", "tl"], Query()] = "en"
    ) -> Response:
        """The same plan as an iCalendar file with reminders, in the schedule's timezone."""
        language: Lang = lang
        return Response(
            render_ics(make_plan(body), language),
            media_type="text/calendar; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="zeitgeber-plan.ics"'},
        )

    @app.post(
        "/v1/calendar",
        tags=["plan"],
        dependencies=limited,
        responses={**errors, 200: {"content": {"text/calendar": {}}}},
        response_class=Response,
    )
    def calendar(body: CalendarRequest) -> Response:
        """Render a plan returned by POST /v1/plan as an iCalendar file, without a new search."""
        language: Lang = body.lang
        return Response(
            render_ics(body.plan, language),
            media_type="text/calendar; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="zeitgeber-plan.ics"'},
        )

    @app.post("/v1/simulate", tags=["debug"], dependencies=limited, responses=errors)
    def simulate_markers(body: SimulateRequest) -> SimulateResponse:
        """Phase markers for the schedule as it is now, for debugging.

        Warms the model up on the schedule's own light profile, then reports the predicted
        CBTmin and DLMO for each local day of the plan window.
        """
        from zeitgeber.light import build_light_profile

        schedule: Schedule = body.schedule
        try:
            run = simulate(build_light_profile(schedule), body.model)
        except SimulationError as err:
            raise HTTPException(422, detail=f"The model could not run: {err}") from err
        tz = schedule.location.tz
        return SimulateResponse(
            model=body.model,
            timezone=schedule.location.timezone,
            warmup_loops=run.warmup.loops,
            warmup_converged=run.warmup.converged,
            days=[
                DayMarkers(date=d.day, cbt_min_local=d.cbt_min, dlmo_local=d.dlmo)
                for d in run.daily(tz)
            ],
        )

    app.add_middleware(ScrubErrors)
    app.add_middleware(BodySizeLimit, max_bytes=settings.max_body_bytes, on_reject=_too_large)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        max_age=600,
    )
    return app


app = create_app()
