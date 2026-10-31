import { Section } from "./ui";

export function Limitations() {
  return (
    <Section id="limits" eyebrow="Limitations" title="What Zeitgeber is not">
      <div className="grid gap-8 md:grid-cols-2">
        <div className="flex flex-col gap-4 text-lg leading-relaxed">
          <p>
            Zeitgeber is a wellness planning tool, not medical advice. Its times come from a model
            of an average adult body clock and from estimated light levels, not from measurements of
            you. Your body may differ, so adjust a time if it does not suit you.
          </p>
          <p>
            Never look at the sun, and do not wear very dark lenses if you drive or ride a
            motorcycle.
          </p>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
          <h3 className="text-lg font-semibold">Talk to a doctor if</h3>
          <ul className="mt-3 flex list-disc flex-col gap-2 pl-5">
            <li>
              you often cannot sleep, or cannot stay awake when you need to, for weeks at a time
            </li>
            <li>you nod off while driving or at work</li>
            <li>someone notices loud snoring or pauses in your breathing during sleep</li>
            <li>you are pregnant</li>
            <li>you have a health condition or take medicine that affects sleep</li>
          </ul>
        </div>
      </div>
    </Section>
  );
}
