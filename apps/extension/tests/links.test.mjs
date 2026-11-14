import test from "node:test";
import assert from "node:assert/strict";
import { normalizeShareUrl, websiteUrl } from "../links.mjs";

for (const [input, expected] of [
  ["https://terabox.com/s/1Abc_123?pwd=secret#private", "https://terabox.com/s/1Abc_123"],
  ["https://www.terabox.com:443/s/1Abc_123/", "https://www.terabox.com/s/1Abc_123"],
  ["https://terasharefile.com/sharing/link?surl=abcd&tracking=abc", "https://terasharefile.com/sharing/link?surl=abcd"],
]) test(`normalizes ${expected}`, () => assert.equal(normalizeShareUrl(input), expected));

for (const input of [
  undefined, "http://terabox.com/s/abcd", "https://terabox.com:8443/s/abcd",
  "https://user:secret@terabox.com/s/abcd", "https://terabox.com.evil.example/s/abcd",
  "https://terabox.com/sharing/link?surl=abcd&surl=efgh", "https://terabox.com/s/ab",
  "https://terabox.com/x/../s/abcd", "https://terabox.com/x/%2e%2e/s/abcd",
  "https://terabox.com\\s\\abcd", "https://terabox.com/s/abcd\n", "https:terabox.com/s/abcd",
]) test(`rejects ${JSON.stringify(input)}`, () => assert.throws(() => normalizeShareUrl(input)));

test("handoff puts only the normalized link in a fragment", () => {
  const destination = new URL(websiteUrl("https://terabox.com/s/abcd?pwd=secret#private"));
  assert.equal(destination.search, "");
  assert.equal(new URLSearchParams(destination.hash.slice(1)).get("url"), "https://terabox.com/s/abcd");
  assert.ok(!destination.href.includes("secret"));
});
