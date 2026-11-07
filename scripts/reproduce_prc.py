"""Reproduce the human phase response curve to bright light with each model.

    MPLBACKEND=Agg uv run python scripts/reproduce_prc.py

Runs the Khalsa et al. 2003 protocol (6.7 h at 9,985 lux) and the St Hilaire et al. 2012
protocol (1 h at about 8,000 lux) through Forger99, Hannay19 and Jewett99 (zeitgeber/prc.py),
prints the features of docs/SCIENCE.md 4.3 as a Markdown table, and writes docs/figures/prc.png
with the published key features drawn on the same axes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from zeitgeber.prc import HILAIRE_PULSE, KHALSA_PULSE, PhaseResponse, phase_response_curve
from zeitgeber.sim import ModelName

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures" / "prc.png"
MODELS: tuple[tuple[ModelName, str, str], ...] = (
    ("forger99", "Forger99 (default)", "#2a78d6"),
    ("hannay19", "Hannay19 (cross-check)", "#eb6834"),
    ("jewett99", "Jewett99", "#1baf7a"),
)
# Published peak-to-trough amplitude and design tolerance (docs/SCIENCE.md 4.3, F3 and F4).
PUBLISHED = {6.7: (5.02, 1.5, "Khalsa 2003"), 1.0: (2.20, 1.0, "St Hilaire 2012")}
CROSSOVER_TOL_H = 1.5  # F2
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def panel(ax: plt.Axes, curves: list[PhaseResponse], hours: float) -> None:
    value, tol, source = PUBLISHED[hours]
    ax.axvspan(-CROSSOVER_TOL_H, CROSSOVER_TOL_H, color="#f0efec", lw=0, zorder=0)
    ax.text(
        0,
        0.97,
        "published crossover\nat CBTmin, ±1.5 h",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8,
        color=MUTED,
    )
    ax.axhline(0, color=MUTED, lw=0.8, zorder=1)
    for curve, (_, label, color) in zip(curves, MODELS, strict=True):
        ax.plot(curve.phase_h, curve.shift_h, color=color, lw=2, label=label, zorder=3)
    lines = [f"{source}: peak to trough {value:.2f} h (±{tol:g} h tolerance)"]
    lines += [
        f"{label.split()[0]}: {c.peak_to_trough_h:.2f} h, crossover {c.crossover_h():+.2f} h"
        for c, (_, label, _) in zip(curves, MODELS, strict=True)
    ]
    ax.text(
        0.0,
        -0.2,
        "\n".join(lines),
        transform=ax.transAxes,
        fontsize=8,
        color=INK,
        va="top",
        linespacing=1.4,
    )
    p = curves[0].pulse
    ax.set_title(f"{p.hours:g} h pulse at {p.lux:,.0f} lux", fontsize=10, color=INK, loc="left")
    ax.set_xlim(-12, 12)
    ax.set_xticks(range(-12, 13, 3))
    ax.set_xlabel("pulse center relative to CBTmin (h)", fontsize=9, color=MUTED)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)


def main() -> int:
    results = {
        pulse.hours: [phase_response_curve(name, pulse) for name, _, _ in MODELS]
        for pulse in (KHALSA_PULSE, HILAIRE_PULSE)
    }
    print(
        "| Model | Pulse | Peak to trough (h) | Max advance (h) | Max delay (h) | Crossover (h) |"
    )
    print("|---|---|---|---|---|---|")
    for hours, curves in results.items():
        for c in curves:
            print(
                f"| {c.model} | {hours:g} h | {c.peak_to_trough_h:.2f} | {c.shift_h.max():.2f} "
                f"| {-c.shift_h.min():.2f} | {c.crossover_h():+.2f} |"
            )

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), dpi=150, sharey=True)
    for ax, (hours, curves) in zip(axes, results.items(), strict=True):
        panel(ax, curves, hours)
    axes[0].set_ylabel("phase shift (h), advance positive", fontsize=9, color=MUTED)
    axes[0].set_ylim(-3.2, 3.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.95),
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    fig.suptitle(
        "Simulated phase response to bright light, Khalsa protocol",
        x=0.01,
        ha="left",
        fontsize=11,
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
