import { site } from "@/lib/site";

import { ExternalLink } from "./ui";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--border)]">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-10 text-sm sm:flex-row sm:items-center sm:justify-between">
        <p>
          Built by <ExternalLink href={site.authorUrl}>{site.author}</ExternalLink>.
        </p>
        <ul className="flex flex-wrap gap-x-5 gap-y-2">
          <li>
            <ExternalLink href={site.github}>GitHub repository</ExternalLink>
          </li>
          <li>
            <ExternalLink href={site.authorUrl}>lauurnce.is-a.dev</ExternalLink>
          </li>
          <li className="text-[var(--muted)]">MIT License. Not medical advice.</li>
        </ul>
      </div>
    </footer>
  );
}
