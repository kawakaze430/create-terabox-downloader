import { test, expect, type Page } from "@playwright/test";

const share = "https://terabox.com/s/1Abc_123";

test("validates a link with the real API and reports unavailable provider honestly", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByLabel("TeraBox share URL").press("Enter");
  await expect(page.getByText("Recognized TeraBox share URL", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Check downloader status" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("not been configured or approved");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("unsupported links show a clear backend error", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill("https://untrusted.example/s/abcd");
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("not on the supported");
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
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
});

test("a service outage leaves the form usable", async ({ page }) => {
  await page.route("**/api/v1/shares/validate", route => route.abort());
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByRole("button", { name: "Validate link" })).toBeEnabled();
});

// Simulated provider responses exercise client rendering; they do not establish
// actual TeraBox file access, preview, or completed transfer functionality.
const simulatedFile = {
  file_id: "fixture-file", name: "fixture.txt", kind: "file", size_bytes: 42,
  mime_type: "text/plain", qualities: [], preview_available: false, download_available: false,
};
const simulatedCapabilities = {
  metadata: true, preview: false, download: false, folders: false, batch: false,
  zip_download: false, quality_options: false,
};

async function validateSupportedLink(page: Page) {
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("button", { name: "Check downloader status" })).toBeVisible();
}

test("simulated metadata renders hostile names as text and clears when the link changes", async ({ page }) => {
  const hostileName = "<img src=x onerror=alert(1)>.txt";
  await page.route("**/api/v1/shares/resolve", route => route.fulfill({ json: {
    provider: "terabox", files: [{ ...simulatedFile, name: hostileName, qualities: ["source"], download_available: true }],
    capabilities: { ...simulatedCapabilities, download: true, quality_options: true },
  } }));
  await validateSupportedLink(page);
  await page.getByRole("button", { name: "Check downloader status" }).click();
  const metadata = page.getByRole("region", { name: "Shared file metadata" });
  await expect(metadata.getByRole("heading", { level: 3 })).toHaveText(hostileName);
  await expect(metadata).toContainText("42 bytes");
  await expect(metadata).toContainText("text/plain");
  await expect(metadata).toContainText("Reported qualities: source");
  await expect(metadata).not.toContainText("1080p");
  await expect(metadata.locator("img, script, button, a")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByLabel("TeraBox share URL").fill("https://terabox.com/s/different");
  await expect(metadata).toHaveCount(0);
});

test("simulated malformed successful metadata is rejected without partial rendering", async ({ page }) => {
  const payloads = [
    { provider: "terabox", files: [{ ...simulatedFile, size_bytes: -1 }], capabilities: simulatedCapabilities },
    { provider: "terabox", files: [{ ...simulatedFile, qualities: ["source", "source"] }], capabilities: simulatedCapabilities },
    { provider: "terabox", files: [{ ...simulatedFile, download_url: "https://untrusted.example/private" }], capabilities: simulatedCapabilities },
    { provider: "terabox", files: [simulatedFile], capabilities: { ...simulatedCapabilities, download: "yes" } },
  ];
  let request = 0;
  await page.route("**/api/v1/shares/resolve", route => route.fulfill({ json: payloads[request++] }));
  await validateSupportedLink(page);
  for (const _payload of payloads) {
    await page.getByRole("button", { name: "Check downloader status" }).click();
    await expect(page.getByRole("main").getByRole("alert")).toContainText("invalid response");
    await expect(page.getByRole("region", { name: "Shared file metadata" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Check downloader status" })).toBeEnabled();
  }
  expect(request).toBe(payloads.length);
});

test("simulated empty metadata shows an honest empty state", async ({ page }) => {
  await page.route("**/api/v1/shares/resolve", route => route.fulfill({ json: {
    provider: "terabox", files: [], capabilities: simulatedCapabilities,
  } }));
  await validateSupportedLink(page);
  await page.getByRole("button", { name: "Check downloader status" }).click();
  await expect(page.getByText("The provider returned no files.")).toBeVisible();
  await expect(page.getByRole("region", { name: "Shared file metadata" }).getByRole("listitem")).toHaveCount(0);
});

test("simulated delayed resolution cannot restore metadata after an edit", async ({ page }) => {
  let release: () => void = () => {};
  const started = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/shares/resolve", async route => {
    release();
    await new Promise(resolve => setTimeout(resolve, 300));
    await route.fulfill({ json: { provider: "terabox", files: [simulatedFile], capabilities: simulatedCapabilities } });
  });
  await validateSupportedLink(page);
  await page.getByRole("button", { name: "Check downloader status" }).click();
  await started;
  await page.getByLabel("TeraBox share URL").fill("https://terabox.com/s/different");
  await page.waitForTimeout(400);
  await expect(page.getByRole("region", { name: "Shared file metadata" })).toHaveCount(0);
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
});

test("simulated malformed validation success never enables resolution", async ({ page }) => {
  await page.route("**/api/v1/shares/validate", route => route.fulfill({ json: {
    valid: true, hostname: "terabox.com", normalized_url: "javascript:alert(1)",
  } }));
  await page.goto("/");
  await page.getByLabel("TeraBox share URL").fill(share);
  await page.getByRole("button", { name: "Validate link" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("invalid response");
  await expect(page.getByRole("button", { name: "Check downloader status" })).toHaveCount(0);
});
