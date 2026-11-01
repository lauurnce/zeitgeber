import { describe, expect, it } from "vitest";

import {
  defaultForm,
  fieldErrorsFromProblem,
  nextMonday,
  spanHours,
  toRequest,
  validate,
} from "./schedule";

describe("defaults", () => {
  it("start on the next Monday with a 10 PM to 7 AM week", () => {
    expect(nextMonday(new Date(2026, 10, 10))).toBe("2026-11-16");
    expect(nextMonday(new Date(2026, 10, 16))).toBe("2026-11-16");
    const form = defaultForm(new Date(2026, 10, 10));
    expect(form.days.filter((d) => d.works)).toHaveLength(5);
    expect(form.days[0]).toEqual({ works: true, start: "22:00", end: "07:00" });
    expect(validate(form)).toEqual({});
  });
});

describe("validation in plain words", () => {
  it("asks for at least one workday", () => {
    const form = defaultForm();
    form.days.forEach((d) => (d.works = false));
    expect(validate(form).days).toBe("Tick at least one day that you work.");
  });

  it("explains a shift that is too long", () => {
    const form = defaultForm();
    form.days[2] = { works: true, start: "06:00", end: "22:00" };
    expect(validate(form)["day-2"]).toBe(
      "The Wednesday shift lasts 16 hours. Shifts need to be 4 to 14 hours.",
    );
  });

  it("checks sleep windows and commutes", () => {
    const form = defaultForm();
    form.restDaySleep = { start: "23:00", end: "00:30" };
    form.home.minutes = 400;
    form.toWork.outdoorPercent = 120;
    const errors = validate(form);
    expect(errors.restDaySleep).toBe(
      "Your sleep on rest days lasts 1.5 hours. Enter a window of 3 to 12 hours.",
    );
    expect(errors["home-minutes"]).toMatch(/0 to 300/);
    expect(errors["toWork-outdoor"]).toMatch(/0 to 100 percent/);
  });

  it("counts windows across midnight", () => {
    expect(spanHours("22:00", "07:00")).toBe(9);
    expect(spanHours("09:00", "09:00")).toBe(24);
  });
});

describe("request body", () => {
  it("matches the schedule model", () => {
    const body = toRequest(defaultForm(new Date(2026, 10, 10)));
    expect(body.schedule.anchor_date).toBe("2026-11-16");
    expect(body.schedule.shifts).toHaveLength(5);
    expect(body.schedule.shifts[4]).toEqual({ weekday: 4, start: "22:00", end: "07:00" });
    expect(body.schedule.commute_home).toEqual({
      duration_min: 60,
      outdoor_share: 0.3,
      mode: "jeepney_bus",
    });
    expect(body.schedule.rest_days).toEqual({ mode: "flip_to_days" });
  });
});

describe("server errors", () => {
  it("land on the field they are about, as sentences", () => {
    const errors = fieldErrorsFromProblem([
      {
        location: ["schedule"],
        message:
          "schedule conflicts: the sleep after the Monday shift would start 20 h after you get home",
      },
      { location: ["schedule", "sleep", "rest_day"], message: "sleep window too short" },
    ]);
    expect(errors.form).toBe(
      "The sleep after the Monday shift would start 20 h after you get home.",
    );
    expect(errors.restDaySleep).toBe("Sleep window too short.");
  });
});
