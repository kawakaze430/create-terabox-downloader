import test from "node:test";
import assert from "node:assert/strict";
import { normalizeShareUrl, normalizeWebsiteOrigin, websiteUrl } from "../links.mjs";

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

for (const [input, expected] of [
  ["https://downloads.example", "https://downloads.example"],
  ["https://DOWNLOADS.example:443", "https://downloads.example"],
  ["http://localhost:3000", "http://localhost:3000"],
  ["http://127.0.0.1:3000", "http://127.0.0.1:3000"],
]) test(`accepts configured website origin ${input}`, () => {
  assert.equal(normalizeWebsiteOrigin(input), expected);
  const destination = new URL(websiteUrl("https://terabox.com/s/abcd?pwd=private", input));
  assert.equal(destination.origin, expected);
  assert.equal(destination.pathname, "/");
  assert.equal(destination.search, "");
  assert.equal(new URLSearchParams(destination.hash.slice(1)).get("url"), "https://terabox.com/s/abcd");
});

for (const input of [
  undefined, "", " http://localhost:3000", "https://downloads.example\n",
  "http://downloads.example", "javascript:alert(1)", "https://user:pass@downloads.example",
  "https://downloads.example/", "https://downloads.example/path", "https://downloads.example?url=private",
  "https://downloads.example#url=private", "https://downloads.example:8443",
  "http://localhost", "http://localhost:8000", "http://localhost:3000/path",
  "http://127.1:3000", "http://localhost.evil.example:3000", "https://downloads.example\\@evil.example",
  "https://downloads..example", "https://-downloads.example", "https://downloads.example.",
  "https://%65xample.com", "https://0x7f000001", "https://downloads.example:0443",
]) test(`rejects configured website origin ${JSON.stringify(input)}`, () => {
  assert.throws(() => normalizeWebsiteOrigin(input));
  if (input !== undefined) assert.throws(() => websiteUrl("https://terabox.com/s/abcd", input));
});
