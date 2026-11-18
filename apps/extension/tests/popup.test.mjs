import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

let sequence = 0;

async function popup({ tabUrl, readError = false, openError = false, websiteOrigin, click = true } = {}) {
  const status = { textContent: "" };
  const button = {
    disabled: true,
    textContent: "Open CloudLink",
    click: null,
    addEventListener: (_event, callback) => { button.click = callback; },
  };
  let temporary;
  let target = new URL(`../popup.js?test=${sequence++}`, import.meta.url);
  if (websiteOrigin !== undefined) {
    temporary = mkdtempSync(join(tmpdir(), "cloudlink-popup-"));
    for (const filename of ["popup.js", "links.mjs"]) {
      writeFileSync(join(temporary, filename), readFileSync(new URL(`../${filename}`, import.meta.url)));
    }
    writeFileSync(join(temporary, "config.mjs"), `export const WEBSITE_ORIGIN = ${JSON.stringify(websiteOrigin)};\n`);
    target = pathToFileURL(join(temporary, "popup.js"));
  }
  const opened = [];
  let queries = 0;
  globalThis.document = { getElementById: id => id === "status" ? status : button };
  globalThis.chrome = {
    runtime: { lastError: null },
    tabs: {
      query: (_options, callback) => {
        queries++;
        globalThis.chrome.runtime.lastError = readError ? { message: "private browser detail" } : null;
        callback(tabUrl ? [{ url: tabUrl }] : []);
        globalThis.chrome.runtime.lastError = null;
      },
      create: (options, callback) => {
        opened.push(options.url);
        globalThis.chrome.runtime.lastError = openError ? { message: "private browser detail" } : null;
        callback();
        globalThis.chrome.runtime.lastError = null;
      },
    },
  };
  try {
    await import(target.href);
    if (click) button.click?.();
    return { status, button, opened, queries };
  } finally {
    delete globalThis.document;
    delete globalThis.chrome;
    if (temporary) rmSync(temporary, { recursive: true, force: true });
  }
}

test("popup opens a normalized fragment destination without private query data", async () => {
  const result = await popup({ tabUrl: "https://terabox.com/s/abcd?pwd=private" });
  assert.equal(result.button.disabled, false);
  assert.equal(result.button.textContent, "Open share in CloudLink");
  assert.deepEqual(result.opened, ["http://localhost:3000/#url=https%3A%2F%2Fterabox.com%2Fs%2Fabcd"]);
  assert.match(result.status.textContent, /The website can validate the link/);
});

test("unsupported or inaccessible tabs open the configured website without tab data", async () => {
  for (const options of [
    {},
    { tabUrl: "https://untrusted.example/s/abcd?private=detail#location" },
    { tabUrl: "https://terabox.com/s/ab?private=detail" },
    { tabUrl: "chrome://settings/", readError: true },
  ]) {
    const result = await popup(options);
    assert.equal(result.button.disabled, false);
    assert.equal(result.button.textContent, "Open CloudLink");
    assert.deepEqual(result.opened, ["http://localhost:3000/"]);
    assert.ok(!result.status.textContent.includes("private browser detail"));
  }
});

test("popup waits for a click before opening the website", async () => {
  const result = await popup({ click: false });
  assert.equal(result.button.disabled, false);
  assert.deepEqual(result.opened, []);
});

test("fallback navigation uses the packaged HTTPS origin", async () => {
  const result = await popup({ websiteOrigin: "https://Downloads.example:443" });
  assert.deepEqual(result.opened, ["https://downloads.example/"]);
});

test("tab creation failure produces a safe retry message", async () => {
  const result = await popup({ tabUrl: "https://terabox.com/s/abcd", openError: true });
  assert.match(result.status.textContent, /Cannot open the website/);
  assert.ok(!result.status.textContent.includes("private browser detail"));
});

test("invalid packaged configuration blocks even active-tab lookup", async () => {
  const result = await popup({ tabUrl: "https://terabox.com/s/abcd", websiteOrigin: "http://untrusted.example" });
  assert.equal(result.queries, 0);
  assert.equal(result.button.disabled, true);
  assert.deepEqual(result.opened, []);
  assert.match(result.status.textContent, /configuration is invalid/);
});
