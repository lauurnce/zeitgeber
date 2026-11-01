import { describe, expect, it } from "vitest";

import { biologicalNight, clock, clockOf, groupOf, segmentsOn } from "./plan";
import { samplePlan } from "@/test/sample-plan";

describe("clock", () => {
  it("writes times the way the plan text does", () => {
    expect(clock(2)).toBe("2 AM");
    expect(clock(9.5)).toBe("9:30 AM");
    expect(clock(0)).toBe("12 AM");
    expect(clock(12)).toBe("12 PM");
    expect(clock(-1)).toBe("11 PM");
    expect(clockOf("2026-11-17T16:30:00+08:00")).toBe("4:30 PM");
  });
});

describe("segments", () => {
  it("clip events to the local day, including ones from the night before", () => {
    const plan = samplePlan();
    const tuesday = segmentsOn(plan, "2026-11-17");
    const shiftParts = tuesday.filter((s) => s.event.kind === "shift");
    expect(shiftParts.map((s) => [s.start, s.end])).toEqual([
      [0, 7],
      [22, 24],
    ]);
    expect(tuesday.some((s) => s.event.kind === "sleep" && s.start === 9)).toBe(true);
    expect(groupOf("light_brake")).toBe("plan");
  });

  it("place the biological night around the body-clock low", () => {
    expect(biologicalNight("2026-11-17T13:45:00+08:00")).toEqual({
      start: 7.75,
      end: 15.75,
      low: 13.75,
    });
  });
});
