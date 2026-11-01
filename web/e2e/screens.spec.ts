import { expect, test, type Page } from "@playwright/test";

// Screenshots for review (docs/figures/planner-*.png) and the narrow-phone layout check.

async function makePlan(page: Page) {
  await page.goto("/plan");
  await page.getByLabel("First day of the 14-day plan").fill("2026-11-16");
  const sleep = page.getByRole("group", { name: "Sleep after a shift" });
  await sleep.getByLabel("Fall asleep").fill("09:00");
  await sleep.getByLabel("Wake up").fill("15:00");
  await page.getByRole("button", { name: "Make my plan" }).click();
  await expect(page.getByRole("heading", { name: "Your plan", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What to change" })).toBeVisible();
}

async function noSideScroll(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
}

for (const width of [390, 1440]) {
  test(`plan at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width < 600 ? 844 : 900 });
    await makePlan(page);
    await noSideScroll(page);
    await page.screenshot({ path: `../docs/figures/planner-${width}.png`, fullPage: true });
  });
}

test("works on a 360 px phone without sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto("/plan");
  await noSideScroll(page);
  await makePlan(page);
  await noSideScroll(page);
});
