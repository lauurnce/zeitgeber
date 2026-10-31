import Link from "next/link";

import { ThemeToggle } from "@/components/ThemeToggle";
import { site } from "@/lib/site";

const button =
  "inline-flex items-center justify-center rounded-md px-5 py-3 font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]";

export function Hero() {
  return (
    <header className="bg-[radial-gradient(ellipse_at_bottom,var(--sky-glow),transparent_60%),linear-gradient(to_bottom,var(--sky-top),var(--background))]">
      <nav
        aria-label="Site"
        className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-4"
      >
        <span className="font-serif text-xl font-semibold">{site.name}</span>
        <ThemeToggle />
      </nav>
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 pt-12 pb-20 sm:pt-20 sm:pb-28">
        <h1 className="max-w-3xl font-serif text-4xl leading-tight font-semibold sm:text-6xl">
          Set your body clock, not just your alarm.
        </h1>
        <p className="max-w-2xl text-lg text-[var(--muted)] sm:text-xl">
          A free planner for night-shift workers. Enter your shifts and get 14 days of light, sleep
          and caffeine timing, worked out with published models of the human body clock.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/plan"
            className={`${button} bg-[var(--accent)] text-[var(--on-accent)] hover:bg-[var(--accent-hover)]`}
          >
            Make my plan
          </Link>
          <a
            href={site.github}
            rel="noopener noreferrer"
            className={`${button} border border-[var(--border)] hover:bg-[var(--hover)]`}
          >
            View on GitHub
          </a>
        </div>
        <p className="text-sm text-[var(--muted)]">
          Free and open source. Your schedule is used to make your plan and isn&apos;t stored.
        </p>
      </div>
    </header>
  );
}
