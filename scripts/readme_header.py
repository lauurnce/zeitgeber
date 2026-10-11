"""Draw the animated README header from real model output.

    uv run python scripts/readme_header.py

Writes docs/figures/header-dark.svg and docs/figures/header-light.svg. Every line and dot is
computed here: the permanent-nights fixture worker (seed 0) is planned with the Forger99 model,
then the header shows (1) light at the eye over two days now and with the plan, (2) the
predicted body-clock low on each of the 14 days now and with the plan, and (3) the 24-hour
clock stepping through those days. The animation is SVG (SMIL), which GitHub plays in an
image; nothing runs scripts.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from zeitgeber.light import LightInterventions, build_light_profile
from zeitgeber.plan import SearchConfig, search
from zeitgeber.schedule import Schedule

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "schedules" / "permanent_nights.json"
OUT = ROOT / "docs" / "figures"

W, H = 1280, 500
FRAMES = 15  # frame 0: now; frames 1 to 14: plan days
FRAME_S = 1.1
LEAD_S = 0.8
HOLD_S = 2.2
CYCLE_S = LEAD_S + FRAMES * FRAME_S + HOLD_S
DAY_SHOWN = 8  # second Tuesday, for the light trace and the outer ring

THEMES = {
    "dark": {
        "bg": "#0b1026",
        "panel": "#121938",
        "fg": "#eef0fa",
        "muted": "#aab0cf",
        "faint": "#2a3260",
        "grid": "#222a55",
        "now": "#9aa0bd",
        "plan": "#f2b25c",
        "work": "#ef8a4f",
        "commute": "#7c83a6",
        "sleep": "#9b8cff",
        "step": "#4fd1a5",
        "night": "#5aa2ff",
    },
    "light": {
        "bg": "#f7f5ef",
        "panel": "#ffffff",
        "fg": "#121633",
        "muted": "#4a4f6b",
        "faint": "#e6e2d6",
        "grid": "#e9e6dc",
        "now": "#6f7287",
        "plan": "#b8650a",
        "work": "#c4501f",
        "commute": "#8b8ea3",
        "sleep": "#5b49d0",
        "step": "#0d7a54",
        "night": "#1f63c4",
    },
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SERIF = "Georgia, 'Times New Roman', serif"


def clock(h: float) -> str:
    total = round((h % 24) * 60) % 1440
    hh, mm = divmod(total, 60)
    suffix = "AM" if hh < 12 else "PM"
    h12 = hh % 12 or 12
    return f"{h12} {suffix}" if mm == 0 else f"{h12}:{mm:02d} {suffix}"


def hours(t: datetime) -> float:
    return t.hour + t.minute / 60 + t.second / 3600


def frame_start(k: int) -> float:
    return LEAD_S + k * FRAME_S


def visible(frames: set[int]) -> str:
    """SMIL opacity animation: shown exactly during the given frames, looping."""
    times = [0.0] + [frame_start(k) / CYCLE_S for k in range(FRAMES)] + [1.0]
    states = [0 in frames] + [k in frames for k in range(FRAMES)]
    # before frame 0 starts, show frame 0's state
    values = ";".join("1" if s else "0" for s in states)
    keys = ";".join(f"{t:.4f}" for t in times[:-1])
    return (
        f'<animate attributeName="opacity" values="{values}" keyTimes="{keys}" '
        f'dur="{CYCLE_S:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
    )


def data() -> dict[str, object]:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw.pop("description")
    schedule = Schedule.model_validate(raw)
    result = search(schedule, SearchConfig(cross_check=None))
    tz = schedule.location.tz

    def lows(times: tuple[datetime, ...]) -> list[float]:
        out = []
        for k in range(schedule.plan_days):
            day = schedule.anchor_date + timedelta(days=k)
            hit = [t.astimezone(tz) for t in times if t.astimezone(tz).date() == day]
            out.append(hours(hit[0]) if hit else float("nan"))
        return out

    start = schedule.anchor_date + timedelta(days=DAY_SHOWN)
    now = build_light_profile(result.baseline.plan.schedule, start, 2)
    applied = result.plan.plan
    plan = build_light_profile(
        applied.schedule,
        start,
        2,
        interventions=LightInterventions(sunglasses=applied.interventions.sunglasses),
        extras=applied.blocks,
    )

    def ring(sched: Schedule, blocks: tuple = ()) -> list[tuple[str, float, float]]:
        day0 = datetime.combine(start, datetime.min.time(), tzinfo=tz)
        day1 = day0 + timedelta(days=1)
        out = []
        for iv in [*sched.materialize(), *blocks]:
            s, e = max(iv.start.astimezone(tz), day0), min(iv.end.astimezone(tz), day1)
            if s < e:
                out.append((iv.kind, hours(s), 24.0 if e == day1 else hours(e)))
        return out

    plan_ring = ring(applied.schedule, applied.blocks)
    if applied.interventions.sunglasses != "none":
        plan_ring += [("sunglasses", s, e) for k, s, e in plan_ring if k == "commute_home"]
    shifts = [
        (
            hours(iv.start.astimezone(tz)) + 24 * (iv.start.astimezone(tz).date() - start).days,
            hours(iv.end.astimezone(tz)) + 24 * (iv.end.astimezone(tz).date() - start).days,
        )
        for iv in applied.schedule.materialize(start, 2)
        if iv.kind == "shift"
    ]
    return {
        "low_now": lows(result.baseline.cbt_min),
        "low_plan": lows(result.plan.cbt_min),
        "lux_now": now.lux,
        "lux_plan": plan.lux,
        "step_h": now.grid.step_h,
        "ring_now": ring(result.baseline.plan.schedule),
        "ring_plan": plan_ring,
        "shifts": shifts,
        "score_now": result.baseline.score.total_h,
        "score_plan": result.plan.score.total_h,
    }


def arc(start: float, end: float, r0: float, r1: float, cx: float, cy: float) -> str:
    span = (end - start) % 24 or 24
    span = min(span, 23.999)
    stop = start + span
    large = 1 if span > 12 else 0

    def p(h: float, r: float) -> str:
        a = h / 24 * 2 * math.pi - math.pi / 2
        return f"{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}"

    return (
        f"M{p(start, r1)} A{r1} {r1} 0 {large} 1 {p(stop, r1)} "
        f"L{p(stop, r0)} A{r0} {r0} 0 {large} 0 {p(start, r0)} Z"
    )


def svg(d: dict, t: dict[str, str]) -> str:
    out: list[str] = []
    add = out.append
    add(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">'
    )
    add('<title id="t">Zeitgeber: how a plan is made</title>')
    low_now = d["low_now"][DAY_SHOWN]
    lp = [x for x in d["low_plan"] if not math.isnan(x)]
    add(
        f'<desc id="d">Simulated for an example worker on nights, 10 PM to 7 AM. Light at the eye '
        f"falls on the commute home with sunglasses. The predicted body-clock low moves from "
        f"{clock(low_now)} to between {clock(min(lp))} and {clock(max(lp))}, inside day sleep. "
        f"Misalignment score {d['score_now']:.1f} h now, "
        f"{d['score_plan']:.1f} h with the plan.</desc>"
    )
    add(f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>')
    # title row
    add(
        f'<text x="40" y="52" font-family="{SERIF}" font-size="30" font-weight="600" '
        f'fill="{t["fg"]}">Zeitgeber</text>'
    )
    add(
        f'<text x="196" y="52" font-family="{SANS}" font-size="15" fill="{t["muted"]}">'
        f"How a plan is made, simulated for one worker on nights, 10 PM to 7 AM, Manila</text>"
    )
    add(
        f'<text x="{W - 40}" y="52" text-anchor="end" font-family="{MONO}" font-size="15" '
        f'fill="{t["muted"]}">score <tspan fill="{t["now"]}">{d["score_now"]:.1f} h</tspan> now '
        f'<tspan fill="{t["fg"]}">&#8594;</tspan> <tspan fill="{t["plan"]}">'
        f"{d['score_plan']:.1f} h</tspan> with the plan</text>"
    )

    def panel(x: float, w: float, n: str, title: str, sub: str) -> None:
        add(f'<rect x="{x}" y="80" width="{w}" height="374" rx="12" fill="{t["panel"]}"/>')
        add(
            f'<text x="{x + 20}" y="110" font-family="{MONO}" font-size="13" '
            f'fill="{t["plan"]}">{n}</text>'
        )
        add(
            f'<text x="{x + 42}" y="110" font-family="{SANS}" font-size="16" font-weight="600" '
            f'fill="{t["fg"]}">{title}</text>'
        )
        add(
            f'<text x="{x + 20}" y="132" font-family="{SANS}" font-size="13" '
            f'fill="{t["muted"]}">{sub}</text>'
        )

    # Panel 1: light at the eye, two days, log scale
    px, pw = 40, 400
    panel(px, pw, "1", "Light at the eye", "Tue and Wed, log scale. The plan dims the ride home.")
    gx0, gx1, gy0, gy1 = px + 56, px + pw - 20, 156, 392
    span_h = 48.0

    def lx(h: float) -> float:
        return gx0 + (gx1 - gx0) * h / span_h

    def ly(lux: float) -> float:
        v = math.log10(max(lux, 1.0)) / 4.0
        return gy1 - (gy1 - gy0) * v

    for s, e in d["shifts"]:
        s, e = max(s, 0), min(e, span_h)
        if s < e:
            add(
                f'<rect x="{lx(s):.1f}" y="{gy0}" width="{lx(e) - lx(s):.1f}" '
                f'height="{gy1 - gy0}" fill="{t["work"]}" opacity="0.10"/>'
            )
            add(
                f'<text x="{(lx(s) + lx(e)) / 2:.1f}" y="{gy0 + 14}" text-anchor="middle" '
                f'font-family="{SANS}" font-size="11" fill="{t["work"]}">shift</text>'
            )
    for k, label in enumerate(["1", "10", "100", "1k", "10k"]):
        y = ly(10**k)
        add(f'<line x1="{gx0}" y1="{y:.1f}" x2="{gx1}" y2="{y:.1f}" stroke="{t["grid"]}"/>')
        add(
            f'<text x="{gx0 - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" fill="{t["muted"]}">{label}</text>'
        )
    for h, label in [(0, "Tue"), (12, "noon"), (24, "Wed"), (36, "noon"), (48, "")]:
        add(
            f'<text x="{lx(h):.1f}" y="{gy1 + 18}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="11" fill="{t["muted"]}">{label}</text>'
        )

    def trace(lux: np.ndarray, color: str, width: float, dash: str = "") -> None:
        step = d["step_h"]
        pts = " ".join(f"{lx(i * step):.1f},{ly(v):.1f}" for i, v in enumerate(lux))
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        add(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linejoin="round"{extra}/>'
        )

    trace(d["lux_now"], t["now"], 1.4, "4 3")
    trace(d["lux_plan"], t["plan"], 1.8)
    add(
        f'<line x1="{gx0}" y1="{gy0}" x2="{gx0}" y2="{gy1}" stroke="{t["fg"]}" '
        f'stroke-width="1" opacity="0.5">'
        f'<animate attributeName="x1" values="{gx0};{gx1}" dur="{CYCLE_S:.2f}s" '
        f'repeatCount="indefinite"/><animate attributeName="x2" values="{gx0};{gx1}" '
        f'dur="{CYCLE_S:.2f}s" repeatCount="indefinite"/></line>'
    )
    add(
        f'<g font-family="{SANS}" font-size="12"><line x1="{px + 20}" y1="424" x2="{px + 44}" '
        f'y2="424" stroke="{t["now"]}" stroke-dasharray="4 3" stroke-width="1.6"/>'
        f'<text x="{px + 50}" y="428" fill="{t["muted"]}">now</text>'
        f'<line x1="{px + 96}" y1="424" x2="{px + 120}" y2="424" stroke="{t["plan"]}" '
        f'stroke-width="2"/><text x="{px + 126}" y="428" fill="{t["muted"]}">'
        f"with the plan</text></g>"
    )

    # Panel 2: body-clock low per day
    qx, qw = 460, 400
    panel(qx, qw, "2", "Body-clock low, 14 days", "Predicted time of the daily low (CBTmin)")
    bx0, bx1, by0, by1 = qx + 70, qx + qw - 24, 160, 396
    y_top, y_bot = 8.0, 17.0  # clock hours shown, earlier at the top

    def bx(day: int) -> float:
        return bx0 + (bx1 - bx0) * day / 13

    def by(h: float) -> float:
        return by0 + (by1 - by0) * (h - y_top) / (y_bot - y_top)

    add(
        f'<rect x="{bx0 - 10}" y="{by(9):.1f}" width="{bx1 - bx0 + 20}" '
        f'height="{by(15) - by(9):.1f}" fill="{t["sleep"]}" opacity="0.10"/>'
    )
    add(
        f'<rect x="{bx0 - 10}" y="{by(15):.1f}" width="{bx1 - bx0 + 20}" '
        f'height="{by(16) - by(15):.1f}" fill="{t["sleep"]}" opacity="0.05"/>'
    )
    add(
        f'<text x="{bx1 + 6}" y="{by(9) + 14:.1f}" text-anchor="end" font-family="{SANS}" '
        f'font-size="11" fill="{t["sleep"]}">day sleep now</text>'
    )
    add(
        f'<text x="{bx1 + 6}" y="{by(16) - 4:.1f}" text-anchor="end" font-family="{SANS}" '
        f'font-size="11" fill="{t["sleep"]}">with the plan, sleep runs to 4 PM</text>'
    )
    for h in range(9, 18, 2):
        add(
            f'<line x1="{bx0 - 10}" y1="{by(h):.1f}" x2="{bx1 + 10}" y2="{by(h):.1f}" '
            f'stroke="{t["grid"]}"/>'
        )
        add(
            f'<text x="{bx0 - 16}" y="{by(h) + 4:.1f}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" fill="{t["muted"]}">{clock(h)}</text>'
        )
    for k in (0, 6, 13):
        add(
            f'<text x="{bx(k):.1f}" y="{by1 + 20}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="11" fill="{t["muted"]}">day {k + 1}</text>'
        )
    now_pts = " ".join(f"{bx(k):.1f},{by(h):.1f}" for k, h in enumerate(d["low_now"]))
    add(
        f'<polyline points="{now_pts}" fill="none" stroke="{t["now"]}" stroke-width="1.4" '
        f'stroke-dasharray="4 3"/>'
    )
    for k, h in enumerate(d["low_now"]):
        add(f'<circle cx="{bx(k):.1f}" cy="{by(h):.1f}" r="3" fill="{t["now"]}"/>')
    for k, h in enumerate(d["low_plan"]):
        if math.isnan(h):
            continue
        if k:
            h0 = d["low_plan"][k - 1]
            add(
                f'<line x1="{bx(k - 1):.1f}" y1="{by(h0):.1f}" x2="{bx(k):.1f}" y2="{by(h):.1f}" '
                f'stroke="{t["plan"]}" stroke-width="1.8">{visible(set(range(k + 1, FRAMES)))}'
                f"</line>"
            )
        add(
            f'<circle cx="{bx(k):.1f}" cy="{by(h):.1f}" r="4" fill="{t["plan"]}">'
            f"{visible(set(range(k + 1, FRAMES)))}</circle>"
        )
    add(
        f'<g font-family="{SANS}" font-size="12"><line x1="{qx + 20}" y1="424" x2="{qx + 44}" '
        f'y2="424" stroke="{t["now"]}" stroke-dasharray="4 3" stroke-width="1.6"/>'
        f'<text x="{qx + 50}" y="428" fill="{t["muted"]}">now</text>'
        f'<circle cx="{qx + 108}" cy="424" r="4" fill="{t["plan"]}"/>'
        f'<text x="{qx + 118}" y="428" fill="{t["muted"]}">with the plan, day by day</text></g>'
    )

    # Panel 3: the 24-hour clock
    rx, rw = 880, 360
    panel(rx, rw, "3", "Body clock, one day", "Inner: biological night. Outer: the day")
    cx, cy = rx + rw / 2, 284
    colors = {
        "shift": t["work"],
        "commute_to_work": t["commute"],
        "commute_home": t["commute"],
        "sleep": t["sleep"],
        "rest_sleep": t["sleep"],
    }
    add(f'<circle cx="{cx}" cy="{cy}" r="89" fill="none" stroke="{t["faint"]}" stroke-width="26"/>')
    for name, items, frames in (
        ("now", d["ring_now"], {0}),
        ("plan", d["ring_plan"], set(range(1, FRAMES))),
    ):
        add(f'<g id="ring-{name}">{visible(frames)}')
        for kind, s, e in items:
            if kind in colors:
                add(
                    f'<path d="{arc(s, e, 76, 102, cx, cy)}" fill="{colors[kind]}" '
                    f'stroke="{t["panel"]}" stroke-width="2"/>'
                )
            else:
                add(
                    f'<path d="{arc(s, max(e, s + 0.3), 106, 114, cx, cy)}" fill="{t["step"]}" '
                    f'stroke="{t["panel"]}" stroke-width="1.5"/>'
                )
        add("</g>")
    for h, label in [(0, "12 AM"), (6, "6 AM"), (12, "12 PM"), (18, "6 PM")]:
        a = h / 24 * 2 * math.pi - math.pi / 2
        add(
            f'<text x="{cx + 130 * math.cos(a):.1f}" y="{cy + 130 * math.sin(a) + 4:.1f}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="10" '
            f'fill="{t["muted"]}">{label}</text>'
        )
    angles = [d["low_now"][DAY_SHOWN] * 15] + [
        (h if not math.isnan(h) else d["low_now"][DAY_SHOWN]) * 15 for h in d["low_plan"]
    ]
    values, keys = [f"{angles[0]:.1f} {cx} {cy}"], ["0"]
    for k in range(FRAMES):
        t0 = frame_start(k) / CYCLE_S
        t1 = min((frame_start(k) + 0.45) / CYCLE_S, 1.0)
        prev = angles[k - 1] if k else angles[0]
        values += [f"{prev:.1f} {cx} {cy}", f"{angles[k]:.1f} {cx} {cy}"]
        keys += [f"{t0:.4f}", f"{t1:.4f}"]
    values.append(f"{angles[-1]:.1f} {cx} {cy}")
    keys.append("1")
    add(
        f'<g><animateTransform attributeName="transform" type="rotate" '
        f'values="{";".join(values)}" keyTimes="{";".join(keys)}" dur="{CYCLE_S:.2f}s" '
        f'repeatCount="indefinite"/>'
        f'<path d="{arc(-6, 2, 44, 66, cx, cy)}" fill="{t["night"]}" opacity="0.9"/>'
        f'<line x1="{cx}" y1="{cy - 30}" x2="{cx}" y2="{cy - 116}" stroke="{t["fg"]}" '
        f'stroke-width="2.5"/><circle cx="{cx}" cy="{cy - 30}" r="4.5" fill="{t["fg"]}"/></g>'
    )
    for k in range(FRAMES):
        label = "Now" if k == 0 else f"Plan day {k}"
        low = angles[k] / 15
        add(
            f'<text x="{cx}" y="440" text-anchor="middle" font-family="{MONO}" font-size="13" '
            f'fill="{t["fg"]}" opacity="0">{label} · lowest {clock(low)}{visible({k})}</text>'
        )

    # arrows between panels
    for x in (440, 860):
        add(
            f'<path d="M{x + 4} 260 L{x + 16} 260 M{x + 11} 255 L{x + 16} 260 L{x + 11} 265" '
            f'stroke="{t["muted"]}" stroke-width="1.5" fill="none"/>'
        )
    add(
        f'<text x="40" y="484" font-family="{SANS}" font-size="12" fill="{t["muted"]}">'
        f"Computed with the Forger99 model (circadian 1.0.3) for the example worker in "
        f"tests/fixtures. Not decoration: regenerate with scripts/readme_header.py.</text>"
    )
    add("</svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    d = data()
    for name, theme in THEMES.items():
        path = OUT / f"header-{name}.svg"
        path.write_text(svg(d, theme), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
