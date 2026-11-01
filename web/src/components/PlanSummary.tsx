import { textFor, type Lang, type PlanDocument } from "@/lib/plan";

const fmt = (h: number) => h.toFixed(1);

/** Score before and after, the recommended changes and why each one is there. */
export function PlanSummary({ plan, lang }: { plan: PlanDocument; lang: Lang }) {
  const { baseline, plan: after } = plan.score;
  const better = after.total_h < baseline.total_h - 0.05;
  return (
    <section aria-labelledby="summary-heading" className="flex flex-col gap-4">
      <h2 id="summary-heading" className="text-xl font-semibold">
        What to change
      </h2>
      <ul className="flex list-disc flex-col gap-1.5 pl-5">
        {plan.recommendations.map((r) => (
          <li key={r.intervention}>{textFor(r.text, lang)}</li>
        ))}
      </ul>
      <div className="rounded-lg border border-[var(--border)] p-4">
        <h3 className="font-semibold">Misalignment score</h3>
        <p className="text-sm text-[var(--muted)]">
          Hours between your body clock and your schedule, on average. Lower is better.
        </p>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-center">
          <div>
            <dt className="text-sm text-[var(--muted)]">Now</dt>
            <dd className="text-3xl font-semibold">{fmt(baseline.total_h)} h</dd>
          </div>
          <div>
            <dt className="text-sm text-[var(--muted)]">With the plan</dt>
            <dd className="text-3xl font-semibold">{fmt(after.total_h)} h</dd>
          </div>
        </dl>
        {!better ? (
          <p className="mt-2 text-sm">
            No plan we tried scores better than your current schedule by much. The changes listed
            keep the safety rules, such as enough sleep.
          </p>
        ) : null}
        {plan.score.cross_check_baseline && plan.score.cross_check_plan ? (
          <p className="mt-2 text-sm text-[var(--muted)]">
            A second body-clock model gives {fmt(plan.score.cross_check_baseline.total_h)} h now and{" "}
            {fmt(plan.score.cross_check_plan.total_h)} h with the plan.
          </p>
        ) : null}
      </div>
      {plan.explanations.length ? (
        <div>
          <h3 className="font-semibold">Why each change</h3>
          <ul className="mt-1 flex list-disc flex-col gap-1.5 pl-5">
            {plan.explanations.map((e) => (
              <li key={e.intervention}>{textFor(e.text, lang)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <ul className="text-sm text-[var(--muted)]">
        {plan.disclaimers.map((d) => (
          <li key={d.en}>{textFor(d, lang)}</li>
        ))}
      </ul>
    </section>
  );
}
