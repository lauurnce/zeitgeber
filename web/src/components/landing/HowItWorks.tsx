import { Section } from "./ui";

const STEPS = [
  {
    title: "Your schedule becomes a light profile",
    body: "Your shifts, commute and sleep turn into 14 days of estimated light, every six minutes, using sunrise and sunset for Manila.",
  },
  {
    title: "The model simulates your clock",
    body: "A published model of the human body clock (Forger, Jewett and Kronauer 1999) predicts when your body is at its lowest each day. A second model checks the result.",
  },
  {
    title: "The planner finds what to change",
    body: "It tries sunglasses, sleep times, outdoor breaks, naps and caffeine timing within published shift-work rules, and keeps the changes that line your clock up with your work. Each change shows what it is worth.",
  },
];

export function HowItWorks() {
  return (
    <Section id="how" eyebrow="How it works" title="Three steps, about half a minute">
      <ol className="grid gap-6 md:grid-cols-3">
        {STEPS.map((step, i) => (
          <li
            key={step.title}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5"
          >
            <p className="font-mono text-sm text-[var(--accent)]">Step {i + 1}</p>
            <h3 className="mt-2 text-lg font-semibold">{step.title}</h3>
            <p className="mt-2 text-[var(--muted)]">{step.body}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
