import { clockOf, textFor, type Lang, type PlanDocument } from "@/lib/plan";

/** The reminder messages, one per distinct text, with the first time each one applies. */
export function Nudges({ plan, lang }: { plan: PlanDocument; lang: Lang }) {
  const events = new Map(plan.days.flatMap((d) => d.events).map((e) => [e.id, e]));
  const seen = new Set<string>();
  const items = plan.nudges.filter((n) => {
    const t = textFor(n.text, lang);
    if (seen.has(t)) return false;
    seen.add(t);
    return true;
  });
  return (
    <section aria-labelledby="nudges-heading" className="flex flex-col gap-3">
      <h2 id="nudges-heading" className="text-xl font-semibold">
        Reminders
      </h2>
      <ul className="flex flex-col gap-2" lang={lang === "tl" ? "tl" : "en"}>
        {items.map((n) => {
          const e = events.get(n.event_id);
          return (
            <li key={n.event_id} className="rounded-lg border border-[var(--border)] p-3">
              {e ? (
                <p className="text-sm text-[var(--muted)]">
                  {textFor(e.title, lang)}, from {clockOf(e.start_local)}
                </p>
              ) : null}
              <p>{textFor(n.text, lang)}</p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
