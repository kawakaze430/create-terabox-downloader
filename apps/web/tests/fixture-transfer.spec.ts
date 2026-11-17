import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

const fixtureBytes = 262144;
const fixtureHash = "2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9";

test("streams the local fixture and downloads independently verified bytes", async ({ page }) => {
  await page.goto("/");
  const fixture = page.getByRole("region", { name: "Local test transfer" });
  const start = fixture.getByRole("button", { name: "Start test transfer" });
  await page.getByRole("button", { name: "Validate link" }).focus();
  await page.keyboard.press("Tab");
  await expect(start).toBeFocused();
  await page.keyboard.press("Enter");
  const progress = fixture.getByRole("progressbar", { name: "Fixture transfer progress" });
  await expect.poll(() => progress.evaluate(element => {
    const bar = element as HTMLProgressElement;
    return bar.value > 0 && bar.value < bar.max;
  }), { intervals: [50, 100], timeout: 5000 }).toBe(true);
  await expect(fixture.getByRole("status")).toHaveText("Fixture transfer verified");
  await expect(progress).toHaveAttribute("value", String(fixtureBytes));
  const downloading = page.waitForEvent("download");
  await fixture.getByRole("button", { name: "Download verified fixture" }).click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("transfer-fixture.bin");
  const bytes = await readFile(await download.path());
  expect(bytes.byteLength).toBe(fixtureBytes);
  expect(createHash("sha256").update(bytes).digest("hex")).toBe(fixtureHash);
});

test("cancels a running fixture transfer before file delivery", async ({ page }) => {
  await page.goto("/");
  const fixture = page.getByRole("region", { name: "Local test transfer" });
  await fixture.getByRole("button", { name: "Start test transfer" }).click();
  await fixture.getByRole("button", { name: "Cancel transfer" }).click();
  await expect(fixture.getByRole("status")).toHaveText("Fixture transfer cancelled");
  await expect(fixture.getByRole("button", { name: "Download verified fixture" })).toHaveCount(0);
  await expect(fixture.getByRole("button", { name: "Start test transfer" })).toBeEnabled();
});
