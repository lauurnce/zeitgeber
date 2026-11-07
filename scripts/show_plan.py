"""Search a plan for a fixture worker and print it as Markdown.

    uv run python scripts/show_plan.py [fixture] [--seed N]

Prints the recommended changes with clock times, the score before and after with each
component, the ablation table, and CBTmin per day before and after (Manila time).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, tzinfo
from pathlib import Path

from zeitgeber.plan import PlanResult, SearchConfig, search
from zeitgeber.schedule import Schedule

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "schedules"
NAMES = {
    "sunglasses": "sunglasses on the commute home",
    "sleep_start_offset_h": "day sleep start",
    "sleep_len_h": "day sleep length",
    "rest_day": "rest-day sleep window",
    "light_brake": "light brake after waking",
    "light_seek_start_h": "bright light in the shift",
    "nap_len_min": "pre-shift nap",
}
BLOCKS = (
    ("light_brake", "Light brake: 15 min outdoors"),
    ("nap", "Nap"),
    ("light_seek", "Bright light (1,000 lux or more)"),
)


def load(name: str) -> Schedule:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return Schedule.model_validate(data)


def clock(t: datetime, tz: tzinfo) -> str:
    return t.astimezone(tz).strftime("%H:%M")


def signed(h: float | None) -> str:
    return "n/a" if h is None else f"{h:+.2f} h"


def first_on(times: tuple[datetime, ...], day: date, tz: tzinfo) -> str:
    hit = [t for t in times if t.astimezone(tz).date() == day]
    return clock(hit[0], tz) if hit else "none"


def describe(r: PlanResult) -> list[str]:
    c = r.plan.interventions
    s = r.plan.plan.schedule
    tz = s.location.tz
    lines = []
    if c.sunglasses != "none":
        lens = {"cat3": "category 3 (15% transmission)", "dark": "very dark (2%)"}[c.sunglasses]
        lines.append(f"- Sunglasses, {lens}, on the commute home while the sun is up (R2).")
    if c.sleep_start_offset_h is not None or c.sleep_len_h is not None:
        w = s.sleep.after_shift
        span = f"{w.start:%H:%M} to {w.end:%H:%M}"
        lines.append(f"- Day sleep after each night shift {span} in a dark room (R3).")
    if c.rest_day != "current":
        w = s.sleep.rest_day
        lines.append(f"- Rest-day sleep {w.start:%H:%M} to {w.end:%H:%M} (R4).")
    for kind, text in BLOCKS:
        blocks = [b for b in r.plan.plan.blocks if b.kind == kind]
        if blocks:
            b = blocks[-1]
            lines.append(f"- {text} {clock(b.start, tz)} to {clock(b.end, tz)} on workdays.")
    w = next(x for x in r.plan.plan.caffeine if x.allowed)
    assert w.allowed is not None
    a, z = w.allowed
    cutoff = clock(w.cutoff, tz)
    lines.append(f"- Caffeine only {clock(a, tz)} to {clock(z, tz)}; none after {cutoff} (C1, C3).")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="permanent_nights")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    schedule = load(args.fixture)
    r = search(schedule, SearchConfig(seed=args.seed))
    b, p = r.baseline.score, r.plan.score
    tz = schedule.location.tz

    print(f"## Plan for {args.fixture} (seed {args.seed})\n")
    print("\n".join(describe(r)))
    print("\n| Score component | Now | Plan |\n|---|---|---|")
    for label, attr in (
        ("S, total (h)", "total_h"),
        ("Phase angle M, mean (h)", "phase_angle_h"),
        ("Work in the circadian low P, mean (h)", "work_in_low_h"),
        ("Sleep inside the biological night (share)", "sleep_in_night_frac"),
        ("Social-jetlag analogue (h)", "social_jetlag_h"),
    ):
        print(f"| {label} | {getattr(b, attr):.2f} | {getattr(p, attr):.2f} |")
    print(f"| Most common category | {b.modal_category} | {p.modal_category} |")
    now, plan = (", ".join(e.penalties) or "none" for e in (r.baseline, r.plan))
    print(f"| Soft-rule penalties | {now} | {plan} |")
    if r.cross_check:
        cb, cp = r.cross_check["baseline"], r.cross_check["plan"]
        print(f"| S under Hannay19 (cross-check) | {cb.total_h:.2f} | {cp.total_h:.2f} |")

    print("\n| Change | Rules | S with | S without | Cut in S | CBTmin moves, day 7 | day 14 |")
    print("|---|---|---|---|---|---|---|")
    for e in r.explanations:
        without = "infeasible" if e.score_without_h is None else f"{e.score_without_h:.2f}"
        cut = "n/a" if e.delta_score_h is None else f"{e.delta_score_h:.2f} h"
        print(
            f"| {NAMES[e.intervention]} | {', '.join(e.rule_ids)} | {e.score_with_h:.2f} "
            f"| {without} | {cut} | {signed(e.delta_cbt_day7_h)} | {signed(e.delta_cbt_day14_h)} |"
        )

    print("\n| Day | CBTmin now | CBTmin with plan |\n|---|---|---|")
    for k in range(schedule.plan_days):
        day = schedule.anchor_date + timedelta(days=k)
        now_c, plan_c = first_on(r.baseline.cbt_min, day, tz), first_on(r.plan.cbt_min, day, tz)
        print(f"| {day:%a %d %b} | {now_c} | {plan_c} |")
    print(f"\n{r.simulations} simulations, converged {r.converged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
