import { defineConfig, devices } from "@playwright/test";

const fixtureMode = process.env.NEXT_PUBLIC_ENABLE_TRANSFER_FIXTURE === "1";
const managedMode = process.env.NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS === "1";
const reuseExistingServer = !fixtureMode && !managedMode && !process.env.CI;
const testIgnore = ["**/managed-transfer-integration.spec.ts"];
if (!fixtureMode) testIgnore.push("**/fixture-transfer.spec.ts");
if (!managedMode) testIgnore.push("**/managed-transfers.spec.ts");

export default defineConfig({
  testDir: "./tests",
  testIgnore,
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "off", // Shared URLs must not be retained in CI traces.
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
      : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
  webServer: [
    { command: "npm run start -- --hostname 127.0.0.1", url: "http://127.0.0.1:3000", reuseExistingServer, timeout: 60000 },
    {
      command: "python -m uvicorn app.main:app --app-dir ../../services/api --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers",
      env: { ENABLE_TRANSFER_FIXTURE: fixtureMode ? "1" : "0" },
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer,
      timeout: 15000,
    },
  ],
});
