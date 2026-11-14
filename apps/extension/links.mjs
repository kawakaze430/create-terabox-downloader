// Keep this offline parser aligned with services/api/app/links.py.
const hosts = new Set(["terabox.com", "www.terabox.com", "teraboxapp.com", "www.teraboxapp.com", "1024terabox.com", "www.1024terabox.com", "terasharefile.com", "www.terasharefile.com"]);
const tokenPattern = /^[A-Za-z0-9_-]{4,128}$/;

export function normalizeShareUrl(raw) {
  if (typeof raw !== "string" || raw.length > 2048 || /[\x00-\x1f\x7f]/.test(raw)) throw new Error("Invalid share link");
  const input = raw.trim();
  // WHATWG URL silently rewrites backslashes and dot segments; reject first.
  if (input.includes("\\") || !/^https:\/\//i.test(input)) throw new Error("Invalid share link");
  const parsed = new URL(input);
  const path = input.replace(/^https:\/\/[^/?#]*/i, "").split(/[?#]/, 1)[0];
  if (parsed.protocol !== "https:" || parsed.username || parsed.password || parsed.port || !hosts.has(parsed.hostname.toLowerCase())) throw new Error("Unsupported share link");
  const match = /^\/s\/([A-Za-z0-9_-]{4,128})\/?$/.exec(path);
  if (match) return `https://${parsed.hostname}/s/${match[1]}`;
  const tokens = parsed.searchParams.getAll("surl");
  if (path === "/sharing/link" && tokens.length === 1 && tokenPattern.test(tokens[0])) {
    return `https://${parsed.hostname}/sharing/link?surl=${tokens[0]}`;
  }
  throw new Error("Invalid share path");
}

export function websiteUrl(shareUrl) {
  // Fragments are not sent to the web server or in HTTP Referrer headers.
  return "http://localhost:3000/#url=" + encodeURIComponent(normalizeShareUrl(shareUrl));
}
