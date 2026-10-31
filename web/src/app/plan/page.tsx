import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { Planner } from "@/components/Planner";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Make your plan",
  description: "Make a 14-day body-clock plan for your shift schedule.",
  alternates: { canonical: "/plan" },
};

export default function PlanPage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-col gap-2">
        <p>
          <Link
            href="/"
            className="text-sm underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-[var(--focus)]"
          >
            {site.name}
          </Link>
        </p>
        <h1 className="text-3xl font-semibold">Make your plan</h1>
        <p className="max-w-prose text-[var(--muted)]">
          Enter your shifts, commute and sleep. The planner simulates your body clock for 14 days
          and suggests changes to light, sleep and caffeine.
        </p>
        <p className="max-w-prose text-sm">{site.notice}</p>
      </header>
      {/* The default start date depends on today, so the form renders per visit. */}
      <Suspense fallback={<p>Loading the planner...</p>}>
        <Planner />
      </Suspense>
    </main>
  );
}
