import { normalizeWebsiteOrigin, normalizeShareUrl, websiteUrl } from "./links.mjs";
import { WEBSITE_ORIGIN } from "./config.mjs";

const statusElement = document.getElementById("status");
const openButton = document.getElementById("open");
let websiteOrigin;
try {
  websiteOrigin = normalizeWebsiteOrigin(WEBSITE_ORIGIN);
} catch {
  statusElement.textContent = "Website configuration is invalid. Reinstall a trusted build of the extension.";
}
if (websiteOrigin) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (chrome.runtime.lastError) {
      statusElement.textContent = "Cannot read this tab. Reopen the extension on a share page.";
      return;
    }
    try {
      const shareUrl = normalizeShareUrl(tabs[0]?.url);
      statusElement.textContent = "Supported TeraBox share link detected. Open the website to validate it; file access is not checked here.";
      openButton.disabled = false;
      openButton.addEventListener("click", () => {
        // Validate the configured destination again at navigation time.
        const destination = websiteUrl(shareUrl, websiteOrigin);
        chrome.tabs.create({ url: destination }, () => {
          if (chrome.runtime.lastError) {
            statusElement.textContent = "Cannot open the website. Please try again.";
          }
        });
      });
    } catch {
      statusElement.textContent = "Open a supported TeraBox share page to use this extension.";
    }
  });
}
