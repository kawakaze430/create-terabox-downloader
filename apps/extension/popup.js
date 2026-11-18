import { normalizeWebsiteOrigin, websiteUrl } from "./links.mjs";
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
    let destination = websiteOrigin + "/";
    if (chrome.runtime.lastError) {
      statusElement.textContent = "Cannot read the current tab.";
    } else {
      try {
        destination = websiteUrl(tabs[0]?.url, websiteOrigin);
        statusElement.textContent = "Supported TeraBox share link detected. The website can validate the link.";
        openButton.textContent = "Open share in CloudLink";
      } catch {
        statusElement.textContent = "No supported TeraBox share link found on this tab.";
      }
    }
    openButton.disabled = false;
    openButton.addEventListener("click", () => {
      chrome.tabs.create({ url: destination }, () => {
        if (chrome.runtime.lastError) {
          statusElement.textContent = "Cannot open the website. Please try again.";
        }
      });
    });
  });
}
