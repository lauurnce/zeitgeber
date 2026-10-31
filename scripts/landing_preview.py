"""Write the data behind the landing page's live preview (web/src/content/preview.json).

    uv run python scripts/landing_preview.py

For the permanent-nights fixture worker (seed 0): the body-clock low on each of the 14 days
with the current schedule and with the plan, and the events of one work day (the second
Tuesday) before and after. Clock times are local hours, 0 to 24.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from zeitgeber.plan import SearchConfig, search
from zeitgeber.schedule import Schedule

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "schedules" / "permanent_nights.json"
TARGET = ROOT / "web" / "src" / "content" / "preview.json"
DAY_INDEX = 8  # second Tuesday


def hours(t: datetime) -> float:
    return round(t.hour + t.minute / 60 + t.second / 3600, 3)


def main() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data.pop("description")
    schedule = Schedule.model_validate(data)
    result = search(schedule, SearchConfig(cross_check=None))
    tz = schedule.location.tz

    def lows(times: tuple[datetime, ...]) -> list[float | None]:
        out: list[float | None] = []
        for k in range(schedule.plan_days):
            day = schedule.anchor_date + timedelta(days=k)
            hit = [t.astimezone(tz) for t in times if t.astimezone(tz).date() == day]
            out.append(hours(hit[0]) if hit else None)
        return out

    def day_events(evaluation_schedule: Schedule, blocks: tuple = ()) -> list[dict[str, object]]:
        day = schedule.anchor_date + timedelta(days=DAY_INDEX)
        start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=1)
        out = []
        for iv in [*evaluation_schedule.materialize(), *blocks]:
            s, e = max(iv.start.astimezone(tz), start), min(iv.end.astimezone(tz), end)
            if s < e:
                out.append(
                    {
                        "kind": iv.kind,
                        "start": hours(s),
                        "end": 24.0 if e == end else hours(e),
                    }
                )
        return sorted(out, key=lambda x: (x["start"], x["end"]))

    plan = result.plan.plan
    sunglasses = [
        {"kind": "sunglasses", "start": e["start"], "end": e["end"]}
        for e in day_events(plan.schedule)
        if e["kind"] == "commute_home"
    ]
    preview = {
        "worker": "Permanent nights, 10 PM to 7 AM, Monday to Friday (fixture permanent_nights)",
        "score_now_h": round(result.baseline.score.total_h, 2),
        "score_plan_h": round(result.plan.score.total_h, 2),
        "low_now": lows(result.baseline.cbt_min),
        "low_plan": lows(result.plan.cbt_min),
        "day_now": day_events(result.baseline.plan.schedule),
        "day_plan": day_events(plan.schedule, plan.blocks) + sunglasses,
    }
    TARGET.write_text(json.dumps(preview, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
