// Background service worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Test Recorder installed');
});

// Handle keyboard shortcuts or other background tasks here
chrome.commands.onCommand.addListener((command) => {
  if (command === "toggle-recording") {
    // Toggle recording logic
  }
});
