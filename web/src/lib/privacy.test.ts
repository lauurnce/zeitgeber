// The privacy line says the schedule is not stored. Keep it true in the browser: no storage
// APIs, cookies, analytics or third-party scripts anywhere in the web source.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sources(path);
    return /\.(ts|tsx)$/.test(name) && !/\.test\.tsx?$/.test(name) ? [path] : [];
  });
}

describe("privacy", () => {
  const files = sources(join(__dirname, ".."));

  it("never stores or tracks the schedule in the browser", () => {
    const banned =
      /\blocalStorage\b|\bsessionStorage\b|\bindexedDB\b|document\.cookie|sendBeacon|gtag\(|google-analytics|@vercel\/analytics|serviceWorker/;
    for (const file of files) {
      expect(banned.test(readFileSync(file, "utf-8")), file).toBe(false);
    }
  });

  it("sends the schedule only to the planner API, without credentials", () => {
    const api = readFileSync(join(__dirname, "api.ts"), "utf-8");
    expect(api).toContain('credentials: "omit"');
    const fetchers = files.filter((f) => /\bfetch\(/.test(readFileSync(f, "utf-8")));
    expect(fetchers.map((f) => f.replace(/.*src\//, ""))).toEqual(["lib/api.ts"]);
  });
});
