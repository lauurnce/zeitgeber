import Link from "next/link";

import { site } from "@/lib/site";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <h1 className="text-4xl font-semibold">{site.name}</h1>
      <p className="text-lg">{site.tagline}</p>
      <p>
        <Link
          href="/plan"
          className="inline-block rounded-md bg-[var(--accent)] px-4 py-3 font-semibold text-[var(--on-accent)] hover:bg-[var(--accent-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
        >
          Make your plan
        </Link>
      </p>
      <p className="text-sm text-[var(--muted)]">{site.notice}</p>
    </main>
  );
}
