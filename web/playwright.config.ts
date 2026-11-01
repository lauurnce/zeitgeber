import { defineConfig, devices } from "@playwright/test";

// The end-to-end test runs the real stack: the FastAPI app from the repository root and a
// production build of the web app pointed at it.
const API_PORT = 8000;
const WEB_PORT = 3000;

export default defineConfig({
  testDir: "e2e",
  timeout: 120_000,
  expect: { timeout: 90_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run uvicorn api.main:app --port ${API_PORT}`,
      cwd: "..",
      url: `http://localhost:${API_PORT}/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { MPLBACKEND: "Agg" },
    },
    {
      // exec so that stopping the server stops next itself, not only the shell.
      command: `pnpm build && exec ./node_modules/.bin/next start --port ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}/plan`,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: { NEXT_PUBLIC_ZEITGEBER_API_URL: `http://localhost:${API_PORT}` },
    },
  ],
});
