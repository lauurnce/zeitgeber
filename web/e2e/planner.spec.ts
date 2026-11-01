import { readFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

test("fills the form, gets a plan and downloads the calendar", async ({ page }) => {
  await page.goto("/plan");
  await expect(page.getByRole("heading", { name: "Make your plan" })).toBeVisible();
  await expect(
    page.getByText("Your schedule is used to make this plan and isn't stored."),
  ).toBeVisible();

  // Work Monday to Friday, 10 PM to 7 AM (the defaults), plus a longer commute home.
  await expect(page.getByLabel("Monday", { exact: true })).toBeChecked();
  await expect(page.getByLabel("Saturday", { exact: true })).not.toBeChecked();
  const home = page.getByRole("group", { name: "Commute home" });
  await home.getByLabel("Minutes, one way").fill("90");
  await home.getByLabel("Share outdoors, percent").fill("45");
  const sleep = page.getByRole("group", { name: "Sleep after a shift" });
  await sleep.getByLabel("Fall asleep").fill("09:00");
  await sleep.getByLabel("Wake up").fill("15:00");
  await page.getByLabel("First day of the 14-day plan").fill("2026-11-16");

  // A mistake first: plain-word message, nothing sent.
  await page.getByLabel("Wednesday shift ends").fill("23:00");
  await page.getByRole("button", { name: "Make my plan" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Please check" })).toContainText(
    "The Wednesday shift lasts 1 hour. Shifts need to be 4 to 14 hours.",
  );
  await page.getByLabel("Wednesday shift ends").fill("07:00");

  await page.getByRole("button", { name: "Make my plan" }).press("Enter");
  await expect(page.getByText(/This can take up to 30 seconds/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Your plan", exact: true })).toBeVisible();

  await expect(page.getByRole("heading", { name: "What to change" })).toBeVisible();
  await expect(page.getByRole("img", { name: /24-hour body clock for/ })).toBeVisible();
  await expect(page.getByRole("list", { name: "Chart key" })).toBeVisible();
  await expect(page.locator("#timeline-heading + p + div + ol > li")).toHaveCount(14);

  await page.getByText("Taglish", { exact: true }).click();
  await expect(page.getByText(/ang huling kape mo/).first()).toBeVisible();

  const downloading = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download calendar (.ics)" }).click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("zeitgeber-plan.ics");
  const text = await readFile((await download.path())!, "utf-8");
  expect(text.startsWith("BEGIN:VCALENDAR\r\n")).toBe(true);
  expect(text).toContain("TZID=Asia/Manila");
  expect(text).toContain("ang huling kape mo");
});
