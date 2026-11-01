// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { ChartLegend, ClockChart, arcPath } from "./ClockChart";
import { LanguageToggle } from "./LanguageToggle";
import { Nudges } from "./Nudges";
import { PlanSummary } from "./PlanSummary";
import { Timeline } from "./Timeline";
import type { Lang } from "@/lib/plan";
import { samplePlan } from "@/test/sample-plan";

afterEach(cleanup);

describe("ClockChart", () => {
  it("has a text equivalent naming the biological night and the body-clock low", () => {
    render(<ClockChart plan={samplePlan()} dayIndex={1} lang="en" />);
    const chart = screen.getByRole("img", { name: "24-hour body clock for Tue 17 Nov" });
    const desc = document.getElementById(chart.getAttribute("aria-describedby")!)!.textContent!;
    expect(desc).toMatch(/^Biological night .* body clock lowest at \d/);
    expect(desc).toContain("Shift 12 AM to 7 AM");
    expect(desc).toContain(
      "Plan steps: Caffeine OK 12 AM to 2:30 AM; Sunglasses on 7 AM to 8:30 AM",
    );
    expect(screen.getByText(/Tue 17 Nov\./)).toBeTruthy(); // visible caption
  });

  it("draws arcs across midnight", () => {
    expect(arcPath(22, 7, 90, 120)).toMatch(/^M.* A120 120 0 0 1 .* A90 90 0 0 0 .* Z$/);
    expect(arcPath(8, 22, 90, 120)).toContain("A120 120 0 1 1");
  });

  it("has a key with every colour role", () => {
    render(<ChartLegend />);
    const key = within(screen.getByRole("list", { name: "Chart key" }));
    for (const item of ["Work", "Commute", "Sleep", "Plan step", "Biological night"]) {
      expect(key.getByText(item)).toBeTruthy();
    }
  });
});

describe("Timeline", () => {
  it("lists 14 days and selects one with the keyboard", async () => {
    function Harness() {
      const [day, setDay] = useState(0);
      return <Timeline plan={samplePlan()} lang="en" selected={day} onSelect={setDay} />;
    }
    render(<Harness />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(14);
    expect(buttons[0]!.getAttribute("aria-pressed")).toBe("true");
    const user = userEvent.setup();
    buttons[3]!.focus();
    await user.keyboard("{Enter}");
    expect(buttons[3]!.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("Tue 17 Nov: list of times")).toBeTruthy();
    expect(screen.getAllByText(/\(new\)$/).length).toBeGreaterThan(10);
  });
});

describe("plan text", () => {
  it("shows the score before and after and every recommendation", () => {
    render(<PlanSummary plan={samplePlan()} lang="en" />);
    expect(screen.getByText("3.7 h")).toBeTruthy();
    expect(screen.getByText("1.0 h")).toBeTruthy();
    expect(screen.getByText(/category 3/)).toBeTruthy();
    expect(screen.getByText(/Rest-day sleep: without it/)).toBeTruthy();
  });

  it("switches the reminders between English and Taglish", async () => {
    function Harness() {
      const [lang, setLang] = useState<Lang>("en");
      return (
        <>
          <LanguageToggle lang={lang} onChange={setLang} />
          <Nudges plan={samplePlan()} lang={lang} />
        </>
      );
    }
    render(<Harness />);
    expect(screen.getByText(/is your last coffee/)).toBeTruthy();
    const user = userEvent.setup();
    await user.click(screen.getByRole("radio", { name: "Taglish" }));
    expect(screen.getByText(/ang huling kape mo/)).toBeTruthy();
    expect(screen.queryByText(/is your last coffee/)).toBeNull();
    expect((screen.getByRole("radio", { name: "Taglish" }) as HTMLInputElement).checked).toBe(true);
  });
});
