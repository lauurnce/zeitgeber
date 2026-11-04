"""Plot a 3-day lux profile for a fixture schedule.

    MPLBACKEND=Agg uv run python scripts/plot_light_profile.py

Writes docs/figures/z3_worker_light_3day.png for the permanent nights worker from Z3
(tests/fixtures/schedules/permanent_nights.json), Monday 16 to Thursday 19 November 2026.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from zeitgeber.light import LABELS, build_light_profile, sun_up
from zeitgeber.schedule import Schedule

ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    "home": "#8a8f98",
    "office": "#3d6fb6",
    "commute, outdoors": "#e0a100",
    "commute, in transit": "#c46b1a",
    "sleep": "#2f2f5f",
    "phone in bed": "#8a62b3",
}


def main(fixture: str = "permanent_nights", start: date = date(2026, 11, 16), days: int = 3) -> int:
    data = json.loads((ROOT / "tests/fixtures/schedules" / f"{fixture}.json").read_text())
    data.pop("description")
    schedule = Schedule.model_validate(data)
    profile = build_light_profile(schedule, start=start, days=days)
    tz = schedule.location.tz
    times = np.array(
        [profile.grid.at(i).astimezone(tz).replace(tzinfo=None) for i in range(profile.grid.n)]
    )
    daylight = sun_up(schedule.location, profile.grid)

    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=150)
    step = times[1] - times[0]
    ax.fill_between(
        times, 0.5, 2e4, where=~daylight, step="post", color="#e9ebf2", lw=0, label="sun down"
    )
    for code, name in LABELS.items():
        mask = profile.labels == code
        if mask.any():
            ax.bar(
                times[mask],
                profile.lux[mask],
                width=step,
                align="edge",
                color=COLORS[name],
                lw=0,
                label=name,
            )
    ax.set_yscale("log")
    ax.set_ylim(0.5, 2e4)
    ax.set_ylabel("lux at the eye (log scale)")
    ax.set_xlim(times[0], times[-1] + step)
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %H:%M"))
    ax.set_title(
        "Light profile, permanent nights worker "
        "(22:00 to 07:00, 90 min commute home, 40 min outdoors)",
        fontsize=10,
    )
    ax.legend(loc="upper left", fontsize=7, ncol=7, frameon=False, bbox_to_anchor=(0, -0.12))
    ax.grid(axis="y", which="major", alpha=0.3)
    fig.tight_layout()
    out = ROOT / "docs/figures/z3_worker_light_3day.png"
    fig.savefig(out)
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
