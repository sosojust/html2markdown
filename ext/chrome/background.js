chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "convert-page", title: "转为 Markdown（整页）", contexts: ["page"] });
  chrome.contextMenus.create({ id: "convert-selection-strict", title: "转为 Markdown（选区-严格）", contexts: ["selection"] });
  chrome.contextMenus.create({ id: "convert-selection-expand", title: "转为 Markdown（选区-扩展）", contexts: ["selection"] });
});

async function getOptions() {
  const { endpoint, options, token } = await chrome.storage.sync.get({
    endpoint: "http://localhost:8000",
    options: {
      strong_delimiter: "**",
      emphasis_delimiter: "*",
      code_fence: "```",
      unknown_tag_strategy: "inline_text",
      expand_to_block_boundaries: true
    },
    token: ""
  });
  // enforce inline_text to avoid leaking raw HTML wrappers
  if (!options.unknown_tag_strategy || options.unknown_tag_strategy === "html_wrapper") {
    options.unknown_tag_strategy = "inline_text";
  }
  return { endpoint, options, token };
}

async function sendWithInjection(tabId, message) {
  return new Promise(async (resolve) => {
    chrome.tabs.sendMessage(tabId, message, async (res) => {
      if (chrome.runtime.lastError || !res) {
        try {
          await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
          chrome.tabs.sendMessage(tabId, message, (res2) => resolve(res2 || null));
        } catch (e) {
          resolve(null);
        }
      } else {
        resolve(res);
      }
    });
  });
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { endpoint, options, token } = await getOptions();
  if (info.menuItemId === "convert-page") {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML
    }, async (res) => {
      const html = res[0].result;
      const body = JSON.stringify({ html, options: { domain: new URL(tab.url).origin, ...options } });
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = "Bearer " + token;
      
      try {
        const r = await fetch(`${endpoint}/v1/convert`, { method: "POST", headers, body });
        if (!r.ok) {
          throw new Error(`Server returned ${r.status} ${r.statusText}`);
        }
        const j = await r.json();
        if (!j || typeof j.markdown !== "string") {
          throw new Error("Invalid response format from server");
        }
        chrome.storage.local.set({ lastMarkdown: j.markdown }, () => {
          chrome.tabs.create({ url: chrome.runtime.getURL("result.html") });
        });
      } catch (err) {
        console.error("Conversion failed:", err);
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icon.png", // Assuming icon exists, or use default
          title: "Conversion Failed",
          message: err.message
        });
        // Update storage to show error in result page if user opens it manually
        chrome.storage.local.set({ lastMarkdown: `# Error\n\nConversion failed: ${err.message}` });
      }
    });
  }
  if (info.menuItemId === "convert-selection-strict" || info.menuItemId === "convert-selection-expand") {
    const expand = info.menuItemId === "convert-selection-expand";
    const res = await sendWithInjection(tab.id, { type: "convert-selection", expand });
    if (!res || !res.html) {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon.png",
        title: "Conversion Failed",
        message: "Could not retrieve selection content."
      });
      return;
    }
    const bodyOptions = { domain: new URL(tab.url).origin, ...options, expand_to_block_boundaries: expand };
    const body = JSON.stringify({ html: res.html, options: bodyOptions });
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    
    try {
      const r = await fetch(`${endpoint}/v1/convert`, { method: "POST", headers, body });
      if (!r.ok) {
        throw new Error(`Server returned ${r.status} ${r.statusText}`);
      }
      const j = await r.json();
      if (!j || typeof j.markdown !== "string") {
        throw new Error("Invalid response format from server");
      }
      chrome.storage.local.set({ lastMarkdown: j.markdown }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL("result.html") });
      });
    } catch (err) {
      console.error("Conversion failed:", err);
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon.png",
        title: "Conversion Failed",
        message: err.message
      });
      chrome.storage.local.set({ lastMarkdown: `# Error\n\nConversion failed: ${err.message}` });
    }
  }
});
