import { websiteUrl } from "./links.mjs";

const statusElement = document.getElementById("status");
const openButton = document.getElementById("open");
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (chrome.runtime.lastError) {
    statusElement.textContent = "Cannot read this tab. Reopen the extension on a share page.";
    return;
  }
  try {
    const destination = websiteUrl(tabs[0]?.url);
    statusElement.textContent = "Supported TeraBox share link detected.";
    openButton.disabled = false;
    openButton.addEventListener("click", () => chrome.tabs.create({ url: destination }));
  } catch {
    statusElement.textContent = "Open a supported TeraBox share page to use this extension.";
  }
});
