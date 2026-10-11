import { expect, test } from "@playwright/test";

// The planner screenshot in README.md: a plan's summary and body clock at 1280 px.
test("README planner screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/plan");
  await page.getByLabel("First day of the 14-day plan").fill("2026-11-16");
  const sleep = page.getByRole("group", { name: "Sleep after a shift" });
  await sleep.getByLabel("Fall asleep").fill("09:00");
  await sleep.getByLabel("Wake up").fill("15:00");
  await page.getByRole("button", { name: "Make my plan" }).click();
  await expect(page.getByRole("heading", { name: "Your plan", exact: true })).toBeVisible();
  await page.getByRole("heading", { name: "Body clock on one day" }).scrollIntoViewIfNeeded();
  // The results column from the "Your plan" heading to the end of the chart key.
  const box = await page.evaluate(() => {
    const doc = (el: Element) => {
      const r = el.getBoundingClientRect();
      return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height };
    };
    const heading = [...document.querySelectorAll("h2")].find(
      (h) => h.textContent === "Your plan",
    )!;
    const key = document.querySelector("[aria-label='Chart key']")!;
    const column = heading.parentElement!.parentElement!;
    const a = doc(column);
    const b = doc(key);
    return { x: a.x - 24, y: a.y - 24, width: a.w + 48, height: b.y + b.h - a.y + 48 };
  });
  await page.screenshot({
    path: "../docs/figures/readme-planner.jpg",
    type: "jpeg",
    quality: 80,
    fullPage: true,
    clip: box,
  });
});
