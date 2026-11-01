// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScheduleForm } from "./ScheduleForm";
import { defaultForm } from "@/lib/schedule";

afterEach(cleanup);

function setup(serverErrors = {}) {
  const onSubmit = vi.fn();
  render(
    <ScheduleForm
      initial={defaultForm(new Date(2026, 10, 10))}
      busy={false}
      serverErrors={serverErrors}
      onSubmit={onSubmit}
    />,
  );
  return { onSubmit, user: userEvent.setup() };
}

describe("ScheduleForm", () => {
  it("labels every control and starts from a 10 PM to 7 AM week", () => {
    setup();
    expect((screen.getByRole("checkbox", { name: "Monday" }) as HTMLInputElement).checked).toBe(
      true,
    );
    expect((screen.getByLabelText("Monday shift starts") as HTMLInputElement).value).toBe("22:00");
    expect((screen.getByLabelText("Friday shift ends") as HTMLInputElement).value).toBe("07:00");
    expect((screen.getByLabelText("Saturday shift starts") as HTMLInputElement).disabled).toBe(
      true,
    );
    expect(screen.getByRole("group", { name: "Commute home" })).toBeTruthy();
    expect(
      screen.getByText("Your schedule is used to make this plan and isn't stored."),
    ).toBeTruthy();
    for (const input of document.querySelectorAll("input, select")) {
      const el = input as HTMLInputElement;
      expect(el.labels?.length ?? 0, el.outerHTML).toBeGreaterThan(0);
    }
  });

  it("submits the form from the keyboard alone", async () => {
    const { onSubmit, user } = setup();
    const button = screen.getByRole("button", { name: "Make my plan" });
    let steps = 0;
    while (document.activeElement !== button && steps < 60) {
      await user.tab();
      steps += 1;
    }
    expect(document.activeElement).toBe(button);
    await user.keyboard("{Enter}");
    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit.mock.calls[0]![0].days[0]).toEqual({
      works: true,
      start: "22:00",
      end: "07:00",
    });
  });

  it("shows plain-word errors, links them to fields and does not submit", async () => {
    const { onSubmit, user } = setup();
    for (const name of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) {
      await user.click(screen.getByRole("checkbox", { name }));
    }
    await user.click(screen.getByRole("button", { name: "Make my plan" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Tick at least one day that you work.");
  });

  it("marks a field invalid and describes it", async () => {
    const { user } = setup();
    const end = screen.getByLabelText("Wednesday shift ends");
    await user.clear(end);
    await user.type(end, "23:00");
    await user.click(screen.getByRole("button", { name: "Make my plan" }));
    expect(end.getAttribute("aria-invalid")).toBe("true");
    const described = document.getElementById(end.getAttribute("aria-describedby")!);
    expect(described?.textContent).toBe(
      "The Wednesday shift lasts 1 hour. Shifts need to be 4 to 14 hours.",
    );
  });

  it("shows errors that came back from the server", () => {
    setup({ form: "The sleep after the Monday shift starts before you get home." });
    expect(screen.getByRole("alert").textContent).toContain("before you get home");
  });
});
