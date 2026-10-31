import { expect, test, type Page } from "@playwright/test";

// Landing page: sections in order, links, no sideways scrolling, review screenshots.

async function noSideScroll(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
}

test("has every section in order and links to the planner", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Set your body clock, not just your alarm.",
  );
  const headings = await page.getByRole("heading", { level: 2 }).allTextContents();
  expect(headings).toEqual([
    "A bunker, a clock and a word",
    "The sun rises on your way home",
    "Three steps, about half a minute",
    "From a misaligned week to a planned one",
    "Built on published work",
    "What Zeitgeber is not",
  ]);
  await expect(page.getByRole("link", { name: "View on GitHub" })).toHaveAttribute(
    "href",
    "https://github.com/lauurnce/zeitgeber",
  );
  await expect(page.getByRole("link", { name: "lauurnce.is-a.dev" })).toBeVisible();
  await page.getByRole("button", { name: /animation/ }).click();
  await page.getByRole("link", { name: "Make my plan" }).click();
  await expect(page).toHaveURL(/\/plan$/);
});

test("switches to the light theme and keeps it", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("works on a 360 px phone without sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto("/");
  await noSideScroll(page);
});

for (const width of [390, 1440]) {
  test(`landing at ${width} px`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.setViewportSize({ width, height: width < 600 ? 844 : 900 });
    await page.goto("/");
    await noSideScroll(page);
    await page.screenshot({ path: `../docs/figures/landing-${width}.png`, fullPage: true });
  });
}
