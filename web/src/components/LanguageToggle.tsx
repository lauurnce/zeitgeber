"use client";

import type { Lang } from "@/lib/plan";

const OPTIONS: [Lang, string][] = [
  ["en", "English"],
  ["tl", "Taglish"],
];

/** Two radio buttons: arrow keys move between them, as with any radio group. */
export function LanguageToggle({ lang, onChange }: { lang: Lang; onChange: (l: Lang) => void }) {
  return (
    <fieldset className="flex items-center gap-2">
      <legend className="sr-only">Language of the plan text</legend>
      {OPTIONS.map(([value, label]) => (
        <label
          key={value}
          className="cursor-pointer rounded-md border border-[var(--border)] px-3 py-1.5 text-sm has-[:checked]:bg-[var(--accent)] has-[:checked]:text-[var(--on-accent)] has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-[var(--focus)]"
        >
          <input
            type="radio"
            name="plan-language"
            value={value}
            checked={lang === value}
            onChange={() => onChange(value)}
            className="sr-only"
          />
          {label}
        </label>
      ))}
    </fieldset>
  );
}
