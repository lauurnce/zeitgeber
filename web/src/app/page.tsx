import { site } from "@/lib/site";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <h1 className="text-4xl font-semibold">{site.name}</h1>
      <p className="text-lg">{site.tagline}</p>
      <p className="text-sm opacity-70">The planner is being built.</p>
      <p className="text-sm opacity-70">{site.notice}</p>
    </main>
  );
}
