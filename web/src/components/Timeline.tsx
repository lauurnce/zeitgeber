"use client";

import {
  clock,
  clockOf,
  groupOf,
  segmentsOn,
  textFor,
  type Lang,
  type PlanDocument,
} from "@/lib/plan";

const FILL = {
  work: "var(--series-work)",
  commute: "var(--series-commute)",
  sleep: "var(--series-sleep)",
  plan: "var(--series-plan)",
} as const;

interface Props {
  plan: PlanDocument;
  lang: Lang;
  selected: number;
  onSelect: (index: number) => void;
}

/** Fourteen rows, one per day: a 24-hour bar for sighted readers and a list for everyone. */
export function Timeline({ plan, lang, selected, onSelect }: Props) {
  return (
    <section aria-labelledby="timeline-heading" className="flex flex-col gap-3">
      <h2 id="timeline-heading" className="text-xl font-semibold">
        Your 14 days
      </h2>
      <p className="text-sm text-[var(--muted)]">
        Each bar runs from midnight to midnight. Choose a day to show it on the clock. Items marked
        new are changes the plan asks for.
      </p>
      <div aria-hidden className="ml-[6.5rem] grid grid-cols-4 text-xs text-[var(--muted)]">
        {[0, 6, 12, 18].map((h) => (
          <span key={h}>{clock(h)}</span>
        ))}
      </div>
      <ol className="flex flex-col gap-1">
        {plan.days.map((day, i) => {
          const segments = segmentsOn(plan, day.date);
          const label = textFor(day.label, lang);
          return (
            <li key={day.date} className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  aria-pressed={selected === i}
                  onClick={() => onSelect(i)}
                  className="w-24 shrink-0 rounded-md px-2 py-1 text-left text-sm hover:bg-[var(--hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] aria-pressed:bg-[var(--accent)] aria-pressed:text-[var(--on-accent)]"
                >
                  {label}
                </button>
                <svg
                  aria-hidden
                  viewBox="0 0 240 14"
                  preserveAspectRatio="none"
                  className="h-4 w-full rounded-sm bg-[var(--hover)]"
                >
                  {segments
                    .filter((s) => groupOf(s.event.kind) !== "plan")
                    .map((s) => (
                      <rect
                        key={`${s.event.id}-${s.start}`}
                        x={s.start * 10}
                        y={0}
                        width={(s.end - s.start) * 10}
                        height={10}
                        fill={FILL[groupOf(s.event.kind)]}
                        stroke="var(--surface)"
                        strokeWidth={0.5}
                      />
                    ))}
                  {segments
                    .filter((s) => groupOf(s.event.kind) === "plan")
                    .map((s) => (
                      <rect
                        key={`${s.event.id}-${s.start}`}
                        x={s.start * 10}
                        y={11}
                        width={Math.max((s.end - s.start) * 10, 2.5)}
                        height={3}
                        fill={FILL.plan}
                      />
                    ))}
                </svg>
              </div>
              <details className="ml-[6.5rem] text-sm">
                <summary className="cursor-pointer text-[var(--muted)] focus-visible:outline-2 focus-visible:outline-[var(--focus)]">
                  {label}: list of times
                </summary>
                <ul className="mt-1 flex flex-col gap-0.5">
                  {day.events.map((e) => (
                    <li key={e.id}>
                      {clockOf(e.start_local)} to {clockOf(e.end_local)}: {textFor(e.title, lang)}
                      {e.recommended ? " (new)" : ""}
                    </li>
                  ))}
                  {day.cbt_min_local ? (
                    <li>Body clock lowest around {clockOf(day.cbt_min_local)}</li>
                  ) : null}
                </ul>
              </details>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
