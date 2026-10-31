import type { ReactNode } from "react";

export const linkClass =
  "underline decoration-[var(--accent)] decoration-2 underline-offset-4 hover:text-[var(--accent)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]";

export function Section({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section
      aria-labelledby={`${id}-title`}
      className="mx-auto w-full max-w-5xl px-4 py-16 sm:py-20"
    >
      <p className="font-mono text-sm tracking-wide text-[var(--accent)] uppercase">{eyebrow}</p>
      <h2 id={`${id}-title`} className="mt-2 font-serif text-3xl font-semibold sm:text-4xl">
        {title}
      </h2>
      <div className="mt-6">{children}</div>
    </section>
  );
}

export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} className={linkClass} rel="noopener noreferrer">
      {children}
    </a>
  );
}
