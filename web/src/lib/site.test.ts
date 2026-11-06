import { describe, expect, it } from "vitest";

import { site } from "./site";

describe("site copy", () => {
  it("names the product and carries the wellness notice", () => {
    expect(site.name).toBe("Zeitgeber");
    expect(site.tagline.length).toBeGreaterThan(0);
    expect(site.notice).toContain("not medical advice");
    expect(site.notice).toContain("talk to a doctor");
  });
});
