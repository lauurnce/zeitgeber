"use client";

import { useEffect, useState } from "react";

import { arcPath } from "@/components/ClockChart";
import preview from "@/content/preview.json";
import { clock } from "@/lib/plan";

import { Section } from "./ui";

type Kind =
  | "shift"
  | "commute_to_work"
  | "commute_home"
  | "sleep"
  | "light_brake"
  | "sunglasses"
  | "nap"
  | "light_seek";

const FILL: Record<string, string> = {
  shift: "var(--series-work)",
  commute_to_work: "var(--series-commute)",
  commute_home: "var(--series-commute)",
  sleep: "var(--series-sleep)",
};
const PLAN_STEPS = new Set(["light_brake", "sunglasses", "nap", "light_seek"]);

interface Item {
  kind: string;
  start: number;
  end: number;
}

// Frame 0 is the worker's current week; frames 1 to 14 are the 14 days of the plan.
const FRAMES = [
  { label: "Now", low: preview.low_now[8] ?? 14.85, day: preview.day_now as Item[] },
  ...preview.low_plan.map((low, i) => ({
    label: `Plan day ${i + 1}`,
    low: low ?? 13,
    day: preview.day_plan as Item[],
  })),
];

function Ring({ items, visible }: { items: Item[]; visible: boolean }) {
  return (
    <g style={{ opacity: visible ? 1 : 0, transition: "opacity 700ms ease" }}>
      {items
        .filter((s) => !PLAN_STEPS.has(s.kind))
        .map((s) => (
          <path
            key={`${s.kind}-${s.start}`}
            d={arcPath(s.start, s.end, 98, 130)}
            fill={FILL[s.kind as Kind]}
            stroke="var(--background)"
            strokeWidth={2}
          />
        ))}
      {items
        .filter((s) => PLAN_STEPS.has(s.kind))
        .map((s) => (
          <path
            key={`${s.kind}-${s.start}`}
            d={arcPath(s.start, Math.max(s.end, s.start + 0.3), 136, 150)}
            fill="var(--series-plan)"
            stroke="var(--background)"
            strokeWidth={2}
          />
        ))}
    </g>
  );
}

export function LivePreview() {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    // Start on its own unless the reader asked for less motion.
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (calm) return;
    const t = setTimeout(() => setPlaying(true), 800);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!playing) return;
    const last = frame === FRAMES.length - 1;
    const t = setTimeout(
      () => setFrame(last ? 0 : frame + 1),
      last ? 2600 : frame === 0 ? 2000 : 900,
    );
    return () => clearTimeout(t);
  }, [playing, frame]);

  const current = FRAMES[frame]!;
  const planLows = preview.low_plan.filter((x): x is number => x !== null);
  const earliest = Math.min(...planLows);
  const latest = Math.max(...planLows);

  return (
    <Section id="preview" eyebrow="Live preview" title="From a misaligned week to a planned one">
      <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,360px)_1fr]">
        <figure className="flex flex-col items-center gap-3">
          <svg
            viewBox="-170 -170 340 340"
            className="w-full max-w-[360px]"
            role="img"
            aria-label="Animated 24-hour body clock for an example night-shift worker"
          >
            <circle r={114} fill="none" stroke="var(--hover)" strokeWidth={34} />
            <Ring items={FRAMES[0]!.day} visible={frame === 0} />
            <Ring items={FRAMES[1]!.day} visible={frame > 0} />
            <g
              style={{
                transform: `rotate(${current.low * 15}deg)`,
                transformOrigin: "0px 0px",
                transition: "transform 800ms ease-in-out",
              }}
            >
              <path d={arcPath(-6, 2, 62, 88)} fill="var(--series-night)" />
              <line x1={0} y1={-54} x2={0} y2={-132} stroke="var(--foreground)" strokeWidth={2.5} />
              <circle cx={0} cy={-48} r={5} fill="var(--foreground)" />
            </g>
            {[
              [0, "12 AM"],
              [6, "6 AM"],
              [12, "12 PM"],
              [18, "6 PM"],
            ].map(([h, text]) => {
              const a = ((h as number) / 24) * 2 * Math.PI - Math.PI / 2;
              return (
                <text
                  key={text}
                  x={40 * Math.cos(a)}
                  y={40 * Math.sin(a)}
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
          <p className="font-mono text-sm" aria-hidden>
            {current.label} · body clock lowest {clock(current.low)}
          </p>
          <button
            type="button"
            onClick={() => setPlaying((p) => !p)}
            className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
          >
            {playing ? "Pause animation" : "Play animation"}
          </button>
        </figure>
        <div className="flex flex-col gap-4 text-lg leading-relaxed">
          <p>
            Inner ring: the biological night the model predicts, with a line at the body&apos;s
            lowest point. Outer ring: work, commute and sleep. The outermost marks are the
            plan&apos;s steps: sunglasses on the way home and a short time outdoors after waking.
          </p>
          <p>
            Now, this worker&apos;s low falls at{" "}
            <span className="font-mono">{clock(FRAMES[0]!.low)}</span>, at the very end of a day
            sleep from <span className="font-mono">9 AM</span> to{" "}
            <span className="font-mono">3 PM</span>. With the plan, it settles between{" "}
            <span className="font-mono">{clock(earliest)}</span> and{" "}
            <span className="font-mono">{clock(latest)}</span>, inside a day sleep that runs to{" "}
            <span className="font-mono">4 PM</span>. The misalignment score drops from{" "}
            <span className="font-mono">{preview.score_now_h.toFixed(1)} h</span> to{" "}
            <span className="font-mono">{preview.score_plan_h.toFixed(1)} h</span>.
          </p>
          <p className="text-sm text-[var(--muted)]">
            Simulated with the Forger99 model for an example worker on permanent nights, 10 PM to 7
            AM, Monday to Friday. Your plan will differ.
          </p>
        </div>
      </div>
    </Section>
  );
}
