import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

const live = process.env.MANAGED_E2E_LIVE === "1";
const size = live ? 11078 : 262144;
const sha256 = live
  ? "90ba2d5ad39d0e9a9ff62308ec5588df845550350f87b10ef190593086dfb9dd"
  : "2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9";

test("downloads hash-verified bytes through the managed API and the transfer engine", async ({ page }) => {
  const key = process.env.MANAGED_E2E_ACCESS_KEY;
  if (!key) throw new Error("Run through playwright.managed.config.ts");
  await page.goto("/");
  const managed = page.getByRole("region", { name: "Managed downloads" });
  await managed.getByLabel("Access key").fill(key);
  await managed.getByRole("button", { name: "Sign in" }).click();
  await managed.getByLabel("Managed file").selectOption("verified-download");
  await managed.getByRole("button", { name: "Start transfer" }).click();
  await expect(managed.getByRole("status")).toHaveText("Transfer verified by the service", { timeout: 15000 });
  const downloading = page.waitForEvent("download");
  await managed.getByRole("button", { name: "Download verified file" }).click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("verified-download.bin");
  const bytes = await readFile(await download.path());
  expect(bytes.byteLength).toBe(size);
  expect(createHash("sha256").update(bytes).digest("hex")).toBe(sha256);
  await managed.getByRole("button", { name: "Sign out" }).click();
  await expect(managed.getByLabel("Access key")).toHaveValue("");
  await expect(managed.getByRole("button", { name: "Download verified file" })).toHaveCount(0);
});
