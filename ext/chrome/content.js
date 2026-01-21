// This file is currently kept for potential future use or specific frame targeting.
// The selection logic has been moved to background.js using chrome.scripting.executeScript
// to better handle multi-frame scenarios (iframes) and avoid injection timing issues.

// Previously:
// chrome.runtime.onMessage.addListener((msg, sender, respond) => {
//   if (msg.type === "convert-selection") { ... }
// });
