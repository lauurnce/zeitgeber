"use client";

import { useSyncExternalStore } from "react";

import { applyTheme, readTheme, type Theme } from "@/lib/theme";

const listeners = new Set<() => void>();
const subscribe = (fn: () => void) => {
  listeners.add(fn);
  return () => listeners.delete(fn);
};

/** A switch between the night (dark) and dawn (light) themes. */
export function ThemeToggle() {
  const theme = useSyncExternalStore<Theme>(subscribe, readTheme, () => "dark");
  const next: Theme = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      onClick={() => {
        applyTheme(next);
        listeners.forEach((fn) => fn());
      }}
      aria-pressed={theme === "light"}
      className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
    >
      Light theme
    </button>
  );
}
