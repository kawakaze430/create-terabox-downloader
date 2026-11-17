import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const packager = join(root, "scripts/package_extension.py");

test("release packaging is deterministic, minimal, and changes only packaged config", () => {
  const temporary = mkdtempSync(join(tmpdir(), "cloudlink-package-"));
  const sourceConfig = join(root, "apps/extension/config.mjs");
  const original = readFileSync(sourceConfig);
  try {
    const outputs = [join(temporary, "first.zip"), join(temporary, "second.zip")];
    for (const output of outputs) {
      const result = spawnSync("python3", [packager, "--website-origin", "https://files.example:443", "--output", output], { encoding: "utf8" });
      assert.equal(result.status, 0, result.stderr);
    }
    assert.deepEqual(readFileSync(outputs[0]), readFileSync(outputs[1]));
    assert.deepEqual(readFileSync(sourceConfig), original);
    const verify = spawnSync("python3", ["-c", `
import json, sys
from zipfile import ZipFile
with ZipFile(sys.argv[1]) as archive:
    assert sorted(archive.namelist()) == ['config.mjs', 'links.mjs', 'manifest.json', 'popup.css', 'popup.html', 'popup.js']
    assert '"https://files.example"' in archive.read('config.mjs').decode()
    manifest = json.loads(archive.read('manifest.json'))
    assert manifest['manifest_version'] == 3
    assert manifest['permissions'] == ['activeTab']
    assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
    assert archive.testzip() is None
`, outputs[0]], { encoding: "utf8" });
    assert.equal(verify.status, 0, verify.stderr);
  } finally {
    rmSync(temporary, { recursive: true, force: true });
  }
});

test("packaging rejects an unsafe destination before creating output", () => {
  const temporary = mkdtempSync(join(tmpdir(), "cloudlink-package-"));
  try {
    const output = join(temporary, "invalid.zip");
    const result = spawnSync("python3", [packager, "--website-origin", "https://user:password@files.example", "--output", output], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Invalid website origin/);
    assert.ok(!result.stderr.includes("password"));
    assert.throws(() => readFileSync(output));
  } finally {
    rmSync(temporary, { recursive: true, force: true });
  }
});
