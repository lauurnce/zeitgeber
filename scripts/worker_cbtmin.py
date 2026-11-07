"""Daily CBTmin for a fixture worker over the 14-day plan window, for every model.

    uv run python scripts/worker_cbtmin.py [fixture] [--from-day-worker]

By default the clock is warmed up on the worker's own schedule, so the table shows where the
model says this schedule leaves the clock. With ``--from-day-worker`` the warm-up uses the
day worker fixture instead, which shows the first two weeks after switching to this schedule.
Prints a Markdown table in Manila local time with the sleep window that holds each CBTmin.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

from zeitgeber.light import build_light_profile
from zeitgeber.schedule import Schedule
from zeitgeber.sim import MODEL_NAMES, compare_models

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "schedules"


def load(name: str) -> Schedule:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return Schedule.model_validate(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="permanent_nights")
    parser.add_argument("--from-day-worker", action="store_true")
    args = parser.parse_args()

    schedule = load(args.fixture)
    profile = build_light_profile(schedule)
    baseline = build_light_profile(load("day_worker")) if args.from_day_worker else None
    runs = compare_models(profile, baseline)
    tz = schedule.location.tz
    day_before = schedule.anchor_date - timedelta(days=1)
    window = schedule.materialize(day_before, schedule.plan_days + 1)
    sleeps = [iv for iv in window if iv.kind in ("sleep", "rest_sleep")]

    print("| Day | " + " | ".join(MODEL_NAMES) + " | Forger99 CBTmin in sleep? |")
    print("|---" * (len(MODEL_NAMES) + 2) + "|")
    daily = {name: run.daily(tz) for name, run in runs.items()}
    for i, row in enumerate(daily["forger99"]):
        cells = []
        for name in MODEL_NAMES:
            c = daily[name][i].cbt_min
            cells.append(c.strftime("%H:%M") if c else "none")
        c = row.cbt_min
        where = "no CBTmin"
        if c is not None:
            hit = [iv for iv in sleeps if iv.start <= c < iv.end]
            where = "no"
            if hit:
                s, e = hit[0].start.astimezone(tz), hit[0].end.astimezone(tz)
                half = "second" if c >= s + (e - s) / 2 else "first"
                where = f"{half} half of {s:%H:%M} to {e:%H:%M}"
        print(f"| {row.day:%a %d %b} | " + " | ".join(cells) + f" | {where} |")
    for name, run in runs.items():
        w = run.warmup
        print(
            f"\n{name}: warm-up {w.loops} loops of {w.baseline_days:g} d, converged {w.converged}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
