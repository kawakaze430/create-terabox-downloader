const hosts = new Set(["terabox.com", "www.terabox.com", "teraboxapp.com", "www.teraboxapp.com", "1024terabox.com", "www.1024terabox.com", "terasharefile.com", "www.terasharefile.com"]);
const statusElement = document.getElementById("status");
const openButton = document.getElementById("open");
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tabUrl = tabs[0]?.url;
  try {
    const parsed = new URL(tabUrl);
    const validPath = /^\/s\/[A-Za-z0-9_-]{4,128}\/?$/.test(parsed.pathname) || (parsed.pathname === "/sharing/link" && /^[A-Za-z0-9_-]{4,128}$/.test(parsed.searchParams.get("surl") || ""));
    if (parsed.protocol !== "https:" || !hosts.has(parsed.hostname.toLowerCase()) || !validPath) throw new Error("not supported");
    statusElement.textContent = "Supported TeraBox share link detected.";
    openButton.disabled = false;
    openButton.addEventListener("click", () => chrome.tabs.create({ url: "http://localhost:3000/?url=" + encodeURIComponent(tabUrl) }));
  } catch {
    statusElement.textContent = "Open a supported TeraBox share page to use this extension.";
  }
});
