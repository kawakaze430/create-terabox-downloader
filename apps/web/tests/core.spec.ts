import { test, expect } from "@playwright/test";

const share = "https://terabox.com/s/1Abc_123";

test("validates a link with the real API and reports unavailable provider honestly", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByLabel("TeraBox share URL").press("Enter");
  await expect(page.getByText("Recognized TeraBox share URL", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Check downloader status" }).click();
  await expect(page.getByRole("alert")).toContainText("not been configured or approved");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("unsupported links show a clear backend error", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill("https://untrusted.example/s/abcd");
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("alert")).toContainText("not on the supported");
  await expect(page.getByRole("button", { name: "Check downloader status" })).toHaveCount(0);
});

test("extension handoff is consumed without retaining a private URL in page location", async ({ page }) => {
  await page.goto("/#url=" + encodeURIComponent(share));
  await expect(page.getByLabel("TeraBox share URL")).toHaveValue(share);
  await expect(page).toHaveURL("http://127.0.0.1:3000/");
  await expect(page.getByRole("button", { name: "Check downloader status" })).toHaveCount(0);
});

test("editing a link cancels validation and prevents stale results", async ({ page }) => {
  let release: () => void = () => {};
  const ready = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/shares/validate", async route => {
    release();
    await new Promise(resolve => setTimeout(resolve, 300));
    await route.fulfill({ json: { valid: true, hostname: "terabox.com", normalized_url: share } });
  });
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByRole("button", { name: "Validate link" }).click();
  await ready;
  await page.getByLabel("TeraBox share URL").fill("https://terabox.com/s/another");
  await expect(page.getByRole("button", { name: "Validate link" })).toBeEnabled();
  await page.waitForTimeout(400);
  await expect(page.getByRole("button", { name: "Check downloader status" })).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("a service outage leaves the form usable", async ({ page }) => {
  await page.route("**/api/v1/shares/validate", route => route.abort());
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("button", { name: "Validate link" })).toBeEnabled();
});
