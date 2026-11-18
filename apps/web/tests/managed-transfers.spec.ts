import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";

const accessKey = "sample-managed-browser-test-key-value";
const token = "t".repeat(43);
const jobId = "b".repeat(32);
const knownBytes = Buffer.from("Managed transfer test payload\n");
const digest = createHash("sha256").update(knownBytes).digest("hex");
const source = { source_id: "operator-file", name: "managed.txt", size_bytes: knownBytes.length, sha256: digest };
const baseJob = { id: jobId, bytes_written: 0, total_bytes: source.size_bytes, sha256: null };
const completed = { ...baseJob, state: "completed", bytes_written: source.size_bytes, sha256: digest };
const cors = {
  "access-control-allow-origin": "http://127.0.0.1:3000",
  "access-control-allow-headers": "authorization, content-type",
  "access-control-allow-methods": "GET, POST",
};

async function mockManagedApi(page: Page, mode: "download" | "tampered" | "cancel" | "oversized") {
  let starts = 0;
  let polls = 0;
  await page.route("**/api/v1/transfers/**", async route => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/v1/transfers", "");
    expect(url.search).toBe("");
    expect(url.pathname.includes(token) || url.pathname.includes(accessKey)).toBe(false);
    expect(request.headers()["referer"]).toBeUndefined();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    if (path === "/session") {
      expect(request.method()).toBe("POST");
      expect(request.headers()["authorization"]).toBeUndefined();
      expect(request.postDataJSON()).toEqual({ access_key: accessKey });
      if (mode === "oversized") {
        return route.fulfill({ json: { token, expires_in: 900, padding: "x".repeat(40000) }, headers: cors });
      }
      return route.fulfill({ json: { token, expires_in: 900 }, headers: cors });
    }
    expect(request.headers()["authorization"] === "Bearer " + token).toBe(true);
    if (path === "/session/logout") {
      expect(request.method()).toBe("POST");
      expect(request.postDataJSON()).toEqual({});
      return route.fulfill({ status: 204, headers: cors });
    }
    if (path === "/sources") return route.fulfill({ json: { sources: [source] }, headers: cors });
    if (path === "/jobs") {
      expect(request.method()).toBe("POST");
      expect(request.postDataJSON()).toEqual({ source_id: source.source_id });
      if (++starts === 2 && mode === "cancel") return route.fulfill({ status: 401, headers: cors });
      return route.fulfill({ json: { ...baseJob, state: "queued" }, status: 201, headers: cors });
    }
    if (path === `/jobs/${jobId}`) {
      const progress = { ...baseJob, state: "running", bytes_written: 5 };
      return route.fulfill({ json: ++polls > 1 && mode !== "cancel" ? completed : progress, headers: cors });
    }
    if (path === `/jobs/${jobId}/cancel`) {
      expect(request.postDataJSON()).toEqual({});
      return route.fulfill({ json: { ...baseJob, state: "cancelled" }, headers: cors });
    }
    if (path === `/jobs/${jobId}/file`) {
      const body = mode === "tampered" ? Buffer.alloc(knownBytes.length, 1) : knownBytes;
      return route.fulfill({ body, headers: {
        ...cors,
        "content-type": "application/octet-stream",
        "content-length": String(body.length),
      } });
    }
    return route.fulfill({ status: 404, headers: cors });
  });
}

async function signIn(page: Page) {
  await page.goto("/");
  const managed = page.getByRole("region", { name: "Managed downloads" });
  await managed.getByLabel("Access key").fill(accessKey);
  await managed.getByLabel("Access key").press("Enter");
  return managed;
}

test("downloads authorized bytes from the managed catalogue and clears the session on sign-out", async ({ page }) => {
  await mockManagedApi(page, "download");
  const managed = await signIn(page);
  await managed.getByLabel("Managed file").selectOption({ label: source.name });
  await managed.getByRole("button", { name: "Start transfer" }).click();
  await expect(managed.getByRole("progressbar")).toHaveAttribute("value", "5");
  await expect(managed.getByRole("status")).toHaveText("Transfer verified by the service");
  const downloading = page.waitForEvent("download");
  await managed.getByRole("button", { name: "Download verified file" }).click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe(source.name);
  expect(await readFile(await download.path())).toEqual(knownBytes);
  const revoking = page.waitForResponse(response => response.url().endsWith("/session/logout") && response.status() === 204);
  await managed.getByRole("button", { name: "Sign out" }).click();
  await revoking;
  await expect(managed.getByLabel("Access key")).toHaveValue("");
  await expect(managed.getByLabel("Managed file")).toHaveCount(0);
  await expect(managed.getByRole("button", { name: "Download verified file" })).toHaveCount(0);
  expect(await page.evaluate(({ key, bearer }) =>
    [window.location.href, document.body.textContent, JSON.stringify(localStorage), JSON.stringify(sessionStorage)]
      .every(value => !value?.includes(key) && !value?.includes(bearer)),
  { key: accessKey, bearer: token })).toBe(true);
});

test("rejects bytes that disagree with the registry hash", async ({ page }) => {
  await mockManagedApi(page, "tampered");
  const managed = await signIn(page);
  await managed.getByLabel("Managed file").selectOption(source.source_id);
  await managed.getByRole("button", { name: "Start transfer" }).click();
  await expect(managed.getByRole("status")).toHaveText("Transfer verified by the service");
  let delivered = false;
  page.on("download", () => { delivered = true; });
  await managed.getByRole("button", { name: "Download verified file" }).click();
  await expect(managed.getByRole("alert")).toContainText("The file could not be verified");
  expect(delivered).toBe(false);
});

test("cancels a managed job and drops state when the bearer expires", async ({ page }) => {
  await mockManagedApi(page, "cancel");
  const managed = await signIn(page);
  await managed.getByLabel("Managed file").selectOption(source.source_id);
  await managed.getByRole("button", { name: "Start transfer" }).click();
  await managed.getByRole("button", { name: "Cancel transfer" }).click();
  await expect(managed.getByRole("status")).toHaveText("Transfer cancelled");
  await managed.getByRole("button", { name: "Start transfer" }).click();
  await expect(managed.getByRole("alert")).toContainText("Your transfer session expired");
  await expect(managed.getByLabel("Access key")).toHaveValue("");
  await expect(managed.getByLabel("Managed file")).toHaveCount(0);
});

test("rejects an oversized authentication response", async ({ page }) => {
  await mockManagedApi(page, "oversized");
  const managed = await signIn(page);
  await expect(managed.getByRole("alert")).toContainText("Unable to sign in");
  await expect(managed.getByLabel("Access key")).toHaveValue("");
  await expect(managed.getByLabel("Managed file")).toHaveCount(0);
});
