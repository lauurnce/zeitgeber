"use client";

import { useId } from "react";

import {
  GROUP_LABELS,
  biologicalNight,
  clock,
  groupOf,
  segmentsOn,
  textFor,
  type Group,
  type Lang,
  type PlanDocument,
} from "@/lib/plan";

const SIZE = 340;
const RINGS = {
  night: [62, 88],
  main: [98, 130],
  plan: [136, 150],
} as const;

function point(hours: number, r: number): [number, number] {
  const a = (hours / 24) * 2 * Math.PI - Math.PI / 2;
  return [r * Math.cos(a), r * Math.sin(a)];
}

/** Ring segment from ``start`` to ``end`` hours (end may pass 24), between two radii. */
export function arcPath(start: number, end: number, inner: number, outer: number): string {
  let span = end - start;
  if (span <= 0) span += 24;
  if (span >= 24) span = 23.999;
  const stop = start + span;
  const large = span > 12 ? 1 : 0;
  const [x1, y1] = point(start, outer);
  const [x2, y2] = point(stop, outer);
  const [x3, y3] = point(stop, inner);
  const [x4, y4] = point(start, inner);
  const f = (n: number) => n.toFixed(2);
  return (
    `M${f(x1)} ${f(y1)} A${outer} ${outer} 0 ${large} 1 ${f(x2)} ${f(y2)} ` +
    `L${f(x3)} ${f(y3)} A${inner} ${inner} 0 ${large} 0 ${f(x4)} ${f(y4)} Z`
  );
}

const FILL: Record<Group | "night", string> = {
  work: "var(--series-work)",
  commute: "var(--series-commute)",
  sleep: "var(--series-sleep)",
  plan: "var(--series-plan)",
  night: "var(--series-night)",
};

interface Props {
  plan: PlanDocument;
  dayIndex: number;
  lang: Lang;
}

/** A 24-hour dial for one day: biological night inside, the day's events outside. */
export function ClockChart({ plan, dayIndex, lang }: Props) {
  const id = useId();
  const day = plan.days[dayIndex];
  if (!day) return null;
  const segments = segmentsOn(plan, day.date);
  const main = segments.filter((s) => groupOf(s.event.kind) !== "plan");
  const steps = segments.filter((s) => groupOf(s.event.kind) === "plan");
  const night = day.cbt_min_local ? biologicalNight(day.cbt_min_local) : null;
  const label = textFor(day.label, lang);

  const describe = (list: typeof segments) =>
    list.map((s) => `${textFor(s.event.title, lang)} ${clock(s.start)} to ${clock(s.end)}`);
  const summary = [
    night
      ? `Biological night ${clock(night.start)} to ${clock(night.end)}; body clock lowest at ${clock(night.low)}.`
      : "No body-clock low was found on this day.",
    `${describe(main).join("; ")}.`,
    steps.length ? `Plan steps: ${describe(steps).join("; ")}.` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <figure className="flex flex-col items-center gap-3" aria-labelledby={`${id}-caption`}>
      <svg
        viewBox={`${-SIZE / 2} ${-SIZE / 2} ${SIZE} ${SIZE}`}
        className="w-full max-w-[340px]"
        role="img"
        aria-labelledby={`${id}-title`}
        aria-describedby={`${id}-desc`}
      >
        <title id={`${id}-title`}>{`24-hour body clock for ${label}`}</title>
        <desc id={`${id}-desc`}>{summary}</desc>
        <circle r={RINGS.main[1]} fill="none" stroke="var(--hover)" strokeWidth={34} />
        {[0, 3, 6, 9, 12, 15, 18, 21].map((h) => {
          const [x1, y1] = point(h, RINGS.night[0] - 6);
          const [x2, y2] = point(h, RINGS.plan[1] + 4);
          return (
            <line
              key={h}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="var(--border)"
              strokeWidth={0.5}
            />
          );
        })}
        {night ? (
          <path
            d={arcPath(night.start, night.end, RINGS.night[0], RINGS.night[1])}
            fill={FILL.night}
            stroke="var(--surface)"
            strokeWidth={2}
          />
        ) : null}
        {main.map((s) => (
          <path
            key={`${s.event.id}-${s.start}`}
            d={arcPath(s.start, s.end, RINGS.main[0], RINGS.main[1])}
            fill={FILL[groupOf(s.event.kind)]}
            stroke="var(--surface)"
            strokeWidth={2}
          />
        ))}
        {steps.map((s) => (
          <path
            key={`${s.event.id}-${s.start}`}
            d={arcPath(s.start, Math.max(s.end, s.start + 0.25), RINGS.plan[0], RINGS.plan[1])}
            fill={FILL.plan}
            stroke="var(--surface)"
            strokeWidth={2}
          />
        ))}
        {night
          ? (() => {
              const [x1, y1] = point(night.low, RINGS.night[0] - 8);
              const [x2, y2] = point(night.low, RINGS.main[1] + 2);
              const [cx, cy] = point(night.low, RINGS.night[0] - 14);
              return (
                <g>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="var(--foreground)"
                    strokeWidth={2.5}
                  />
                  <circle cx={cx} cy={cy} r={5} fill="var(--foreground)" />
                </g>
              );
            })()
          : null}
        {[
          [0, "12 AM"],
          [6, "6 AM"],
          [12, "12 PM"],
          [18, "6 PM"],
        ].map(([h, text]) => {
          const [x, y] = point(h as number, 40);
          return (
            <text
              key={text}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={11}
              fill="var(--muted)"
            >
              {text}
            </text>
          );
        })}
      </svg>
      <figcaption id={`${id}-caption`} className="text-center text-sm">
        <span className="font-semibold">{label}.</span> {summary}
      </figcaption>
    </figure>
  );
}

export function ChartLegend() {
  const items: [string, string, string][] = [
    ...(["work", "commute", "sleep", "plan"] as Group[]).map(
      (g) => [GROUP_LABELS[g], FILL[g], "outer rings"] as [string, string, string],
    ),
    ["Biological night", FILL.night, "inner ring"],
  ];
  return (
    <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-sm" aria-label="Chart key">
      {items.map(([label, color]) => (
        <li key={label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="inline-block size-3 rounded-sm"
            style={{ background: color }}
          />
          {label}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="inline-block size-3 rounded-full bg-[var(--foreground)]" />
        Body clock lowest
      </li>
    </ul>
  );
}
