"""The plan document (versioned JSON schema) and the plain-text daily timeline.

:func:`build_document` turns a :class:`zeitgeber.plan.PlanResult` into a :class:`PlanDocument`:
the 14 days of events in the worker's timezone, the recommended changes, the ablation
explanations and the score before and after. Every text field carries English and Taglish
from the string catalog (copy.toml). Nudges are added by :mod:`zeitgeber.output.nudges`.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict

from zeitgeber.light import solar_times
from zeitgeber.output.copy import LANGS, Lang, clock, day_label, text
from zeitgeber.plan import BRAKE_MIN, MIN_WORKDAY_SLEEP_H, PlanResult
from zeitgeber.schedule import Interval, Schedule
from zeitgeber.score import ScoreBreakdown

SCHEMA_VERSION: Literal["1.0"] = "1.0"

EventKind = Literal[
    "shift",
    "commute_to_work",
    "commute_home",
    "sleep",
    "rest_sleep",
    "nap",
    "light_seek",
    "light_brake",
    "sunglasses",
    "caffeine",
]
NudgeSource = Literal["template", "rewritten", "fallback"]

# Reminder lead times in minutes (design; docs/DECISIONS.md D35). Kinds without one get none.
REMINDERS: dict[str, tuple[int, Literal["start", "end"]]] = {
    "sleep": (30, "start"),
    "rest_sleep": (30, "start"),
    "nap": (10, "start"),
    "light_seek": (0, "start"),
    "light_brake": (0, "start"),
    "sunglasses": (0, "start"),
    "caffeine": (30, "end"),  # before the last coffee
}
KIND_ORDER = {k: i for i, k in enumerate(EventKind.__args__)}  # type: ignore[attr-defined]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Text(_Model):
    en: str
    tl: str

    def get(self, lang: Lang) -> str:
        return self.en if lang == "en" else self.tl


class Reminder(_Model):
    minutes_before: int
    related: Literal["start", "end"] = "start"


class PlanEvent(_Model):
    id: str  # unique in the plan: local start and kind, "20261116-0900-sleep"
    kind: EventKind
    start_utc: datetime
    end_utc: datetime
    start_local: datetime  # with the UTC offset of the schedule timezone
    end_local: datetime
    title: Text
    rule_ids: list[str]  # docs/SCIENCE.md rules behind this event
    recommended: bool  # True when the plan adds or changes this event
    reminder: Reminder | None


class Nudge(_Model):
    event_id: str
    template: str  # catalog key
    text: Text
    source: dict[Lang, NudgeSource]


class PlanDay(_Model):
    date: date
    label: Text
    events: list[PlanEvent]
    cbt_min_local: datetime | None  # body-clock low (CBTmin) predicted on this date
    category: str | None  # Crowley category of the main sleep that starts on this date


class Recommendation(_Model):
    intervention: str
    rule_ids: list[str]
    text: Text


class Explanation(_Model):
    intervention: str
    rule_ids: list[str]
    score_with_h: float
    score_without_h: float | None
    delta_score_h: float | None  # positive: the change lowers misalignment
    delta_cbt_day7_h: float | None  # CBTmin without minus with; positive means later
    delta_cbt_day14_h: float | None
    text: Text


class ScoreSummary(_Model):
    total_h: float
    phase_angle_h: float
    work_in_low_h: float
    sleep_in_night_frac: float
    social_jetlag_h: float
    modal_category: str
    flagged_days: int
    lam: float


class Scores(_Model):
    model: str
    baseline: ScoreSummary
    plan: ScoreSummary
    cross_check_model: str | None
    cross_check_baseline: ScoreSummary | None
    cross_check_plan: ScoreSummary | None


class PlanDocument(_Model):
    schema_version: Literal["1.0"]
    plan_id: str
    generated_at: datetime
    timezone: str
    start_date: date
    days_count: int
    seed: int
    disclaimers: list[Text]
    recommendations: list[Recommendation]
    explanations: list[Explanation]
    score: Scores
    days: list[PlanDay]
    nudges: list[Nudge]

    def events(self) -> list[PlanEvent]:
        return [e for d in self.days for e in d.events]

    def event(self, event_id: str) -> PlanEvent:
        return next(e for e in self.events() if e.id == event_id)


def both(key: str, **values: object) -> Text:
    """A catalog string in both languages; a :class:`Text` value is filled per language."""

    def fill(lang: Lang) -> dict[str, object]:
        return {k: v.get(lang) if isinstance(v, Text) else v for k, v in values.items()}

    return Text(**{lang: text(key, lang, **fill(lang)) for lang in LANGS})


def _r(x: float | None, nd: int = 3) -> float | None:
    return None if x is None else round(x, nd)


def _summary(s: ScoreBreakdown) -> ScoreSummary:
    return ScoreSummary(
        total_h=round(s.total_h, 3),
        phase_angle_h=round(s.phase_angle_h, 3),
        work_in_low_h=round(s.work_in_low_h, 3),
        sleep_in_night_frac=round(s.sleep_in_night_frac, 3),
        social_jetlag_h=round(s.social_jetlag_h, 3),
        modal_category=s.modal_category,
        flagged_days=s.flagged_days,
        lam=s.lam,
    )


def _minute(t: datetime) -> datetime:
    return t.replace(second=0, microsecond=0) + timedelta(minutes=1 if t.second >= 30 else 0)


def _sun_up_during(schedule: Schedule, iv: Interval) -> bool:
    tz = schedule.location.tz
    day = iv.start.astimezone(tz).date()
    for d in (day - timedelta(days=1), day):
        sun = solar_times(schedule.location, d)
        if iv.start < sun.sunset and sun.sunrise < iv.end:
            return True
    return False


def _events(result: PlanResult) -> list[PlanEvent]:
    applied = result.plan.plan
    c = applied.interventions
    schedule = applied.schedule
    tz = schedule.location.tz
    begin, end = schedule.window_utc()
    sleep_changed = c.sleep_start_offset_h is not None or c.sleep_len_h is not None
    caffeine_rules = ["C1", "C2", "C3"] if result.config.slow_caffeine else ["C1", "C3"]

    found: list[tuple[str, datetime, datetime, list[str], bool]] = []
    first, span = schedule.anchor_date - timedelta(days=1), schedule.plan_days + 2
    current = {
        (iv.kind, iv.start, iv.end) for iv in result.baseline.plan.schedule.materialize(first, span)
    }
    for iv in schedule.materialize(first, span):
        if iv.kind in ("sleep", "rest_sleep"):
            # A sleep is a recommendation only when the plan moved or resized it.
            asked = sleep_changed if iv.kind == "sleep" else c.rest_day != "current"
            changed = asked and (iv.kind, iv.start, iv.end) not in current
            rule = "R3" if iv.kind == "sleep" else "R4"
            found.append((iv.kind, iv.start, iv.end, [rule] if changed else [], changed))
        else:
            found.append((iv.kind, iv.start, iv.end, [], False))
        if iv.kind == "commute_home" and c.sunglasses != "none" and _sun_up_during(schedule, iv):
            found.append(("sunglasses", iv.start, iv.end, ["R2", "R7"], True))
    rules = {"nap": ["N1", "N3"], "light_seek": ["R1"], "light_brake": ["R5"]}
    for b in applied.blocks:
        found.append((b.kind, b.start, b.end, rules[b.kind], True))
    for w in applied.caffeine:
        if w.allowed is not None:
            found.append(("caffeine", w.allowed[0], w.allowed[1], caffeine_rules, True))

    out: list[PlanEvent] = []
    seen: set[str] = set()
    for kind, s, e, rule_ids, recommended in sorted(found, key=lambda f: (f[1], KIND_ORDER[f[0]])):
        if not begin <= s < end:
            continue
        s_loc, e_loc = _minute(s.astimezone(tz)), _minute(e.astimezone(tz))
        event_id = f"{s_loc:%Y%m%d-%H%M}-{kind}"
        if event_id in seen:
            continue
        seen.add(event_id)
        lead = REMINDERS.get(kind)
        out.append(
            PlanEvent(
                id=event_id,
                kind=kind,  # type: ignore[arg-type]
                start_utc=_minute(s),
                end_utc=_minute(e),
                start_local=s_loc,
                end_local=e_loc,
                title=both(f"event.{kind}"),
                rule_ids=rule_ids,
                recommended=recommended,
                reminder=None
                if lead is None
                else Reminder(minutes_before=lead[0], related=lead[1]),
            )
        )
    return out


def _first(events: Sequence[PlanEvent], kind: str) -> PlanEvent | None:
    return next((e for e in events if e.kind == kind), None)


def _recommendations(result: PlanResult, events: Sequence[PlanEvent]) -> list[Recommendation]:
    c = result.plan.interventions
    sleep = result.plan.plan.schedule.sleep
    recs: list[Recommendation] = []

    def add(name: str, rule_ids: Sequence[str], key: str, **values: object) -> None:
        recs.append(
            Recommendation(intervention=name, rule_ids=list(rule_ids), text=both(key, **values))
        )

    if not c.active():
        add("keep", [], "rec.keep")
    if c.sunglasses != "none":
        add("sunglasses", ["R2", "R7"], f"rec.sunglasses.{c.sunglasses}")
    if c.sleep_start_offset_h is not None or c.sleep_len_h is not None:
        w = sleep.after_shift
        add("sleep", ["R3"], "rec.sleep", start=clock(w.start), end=clock(w.end))
    if c.rest_day != "current":
        w = sleep.rest_day
        add("rest_day", ["R4"], "rec.rest_day", start=clock(w.start), end=clock(w.end))
    for kind, key, rule_ids in (
        ("light_brake", "rec.light_brake", ["R5"]),
        ("light_seek", "rec.light_seek", ["R1"]),
        ("nap", "rec.nap", ["N1", "N3"]),
    ):
        e = _first(events, kind)
        if e is not None:
            values = {"start": clock(e.start_local), "end": clock(e.end_local)}
            add(kind, rule_ids, key, minutes=BRAKE_MIN, **values)
    windows = Counter(
        (clock(e.start_local), clock(e.end_local)) for e in events if e.kind == "caffeine"
    )
    if windows:
        (start, end), _ = windows.most_common(1)[0]
        caffeine = next(e for e in events if e.kind == "caffeine")
        add("caffeine", caffeine.rule_ids, "rec.caffeine", start=start, end=end)
    return recs


def _explanations(result: PlanResult) -> list[Explanation]:
    out = []
    for e in result.explanations:
        change = both(f"change.{e.intervention}")
        values = {"with": f"{e.score_with_h:.1f}", "without": f"{e.score_without_h or 0:.1f}"}
        if e.score_without_h is None:
            words = both("explain.needed", change=change)
        elif e.score_without_h < e.score_with_h:
            if e.intervention == "sleep_len_h":
                hours = f"{MIN_WORKDAY_SLEEP_H:g}"
                words = both("explain.sleep_floor", change=change, hours=hours, **values)
            else:
                words = both("explain.cost", change=change, **values)
        else:
            words = both("explain.score", change=change, **values)
        out.append(
            Explanation(
                intervention=e.intervention,
                rule_ids=list(e.rule_ids),
                score_with_h=round(e.score_with_h, 3),
                score_without_h=_r(e.score_without_h),
                delta_score_h=_r(e.delta_score_h),
                delta_cbt_day7_h=_r(e.delta_cbt_day7_h),
                delta_cbt_day14_h=_r(e.delta_cbt_day14_h),
                text=words,
            )
        )
    return out


def _days(result: PlanResult, events: Sequence[PlanEvent]) -> list[PlanDay]:
    schedule = result.plan.plan.schedule
    tz = schedule.location.tz
    days = []
    for k in range(schedule.plan_days):
        d = schedule.anchor_date + timedelta(days=k)
        cbt = next((c for c in result.plan.cbt_min if c.astimezone(tz).date() == d), None)
        category = next(
            (
                s.category
                for s in result.plan.score.days
                if s.sleep.start.astimezone(tz).date() == d
            ),
            None,
        )
        days.append(
            PlanDay(
                date=d,
                label=Text(**{lang: day_label(d, lang) for lang in LANGS}),
                events=[e for e in events if e.start_local.date() == d],
                cbt_min_local=None if cbt is None else _minute(cbt.astimezone(tz)),
                category=category,
            )
        )
    return days


def _plan_id(events: Sequence[PlanEvent], seed: int) -> str:
    key = "|".join(f"{e.id}/{e.end_utc:%Y%m%dT%H%M}" for e in events) + f"|{seed}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def build_document(result: PlanResult, generated_at: datetime) -> PlanDocument:
    """The plan as a versioned document, without nudges.

    :func:`zeitgeber.output.plan_document` builds the document and adds the nudges.
    """
    schedule = result.plan.plan.schedule
    events = _events(result)
    cross = result.cross_check or {}
    scores = Scores(
        model=result.config.model,
        baseline=_summary(result.baseline.score),
        plan=_summary(result.plan.score),
        cross_check_model=result.config.cross_check if cross else None,
        cross_check_baseline=_summary(cross["baseline"]) if "baseline" in cross else None,
        cross_check_plan=_summary(cross["plan"]) if "plan" in cross else None,
    )
    return PlanDocument(
        schema_version=SCHEMA_VERSION,
        plan_id=_plan_id(events, result.config.seed),
        generated_at=generated_at,
        timezone=schedule.location.timezone,
        start_date=schedule.anchor_date,
        days_count=schedule.plan_days,
        seed=result.config.seed,
        disclaimers=[both(f"disclaimer.{k}") for k in ("wellness", "doctor", "model")],
        recommendations=_recommendations(result, events),
        explanations=_explanations(result),
        score=scores,
        days=_days(result, events),
        nudges=[],
    )


def json_schema() -> dict[str, object]:
    """JSON Schema of :class:`PlanDocument` (committed as docs/schema/plan-1.0.json)."""
    return PlanDocument.model_json_schema()


def _tz_name(tz: str) -> str:
    return "Philippine" if tz == "Asia/Manila" else tz


def _round_quarter(t: datetime) -> datetime:
    minutes = round((t.hour * 60 + t.minute) / 15) * 15
    return t.replace(hour=0, minute=0) + timedelta(minutes=minutes)


def render_timeline(doc: PlanDocument, lang: Lang = "en") -> str:
    """The plan as plain text: changes, score, reasons, then one block per day."""
    lines = [
        text("timeline.title", lang, days=doc.days_count, date=day_label(doc.start_date, lang)),
        text("timeline.timezone", lang, tz=_tz_name(doc.timezone)),
        *(d.get(lang) for d in doc.disclaimers),
        "",
        text("timeline.changes", lang),
        *(f"- {r.text.get(lang)}" for r in doc.recommendations),
        "",
        text(
            "timeline.score",
            lang,
            before=f"{doc.score.baseline.total_h:.1f}",
            after=f"{doc.score.plan.total_h:.1f}",
        ),
    ]
    if doc.score.cross_check_baseline and doc.score.cross_check_plan:
        lines.append(
            text(
                "timeline.cross_check",
                lang,
                before=f"{doc.score.cross_check_baseline.total_h:.1f}",
                after=f"{doc.score.cross_check_plan.total_h:.1f}",
            )
        )
    if doc.explanations:
        lines += ["", text("timeline.why", lang)]
        lines += [f"- {e.text.get(lang)}" for e in doc.explanations]
    lines += ["", text("timeline.days", lang)]
    new = text("timeline.changed", lang)
    for day in doc.days:
        lines += ["", day.label.get(lang)]
        for e in day.events:
            span = f"{clock(e.start_local)} to {clock(e.end_local)}"
            if e.end_local.date() > e.start_local.date():
                span += f" ({text('timeline.next_day', lang)})"
            mark = f"  [{new}]" if e.recommended else ""
            lines.append(f"  {span:<30}{e.title.get(lang)}{mark}")
        if day.cbt_min_local is not None:
            low = clock(_round_quarter(day.cbt_min_local))
            lines.append(f"  {text('timeline.body_clock_low', lang, time=low)}")
    return "\n".join(lines) + "\n"
