chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "convert-page", title: "转为 Markdown（整页）", contexts: ["page"] });
  chrome.contextMenus.create({ id: "convert-selection-strict", title: "转为 Markdown（选区-严格）", contexts: ["selection"] });
  chrome.contextMenus.create({ id: "convert-selection-expand", title: "转为 Markdown（选区-扩展）", contexts: ["selection"] });
});

async function getOptions() {
  const { endpoint, options, token, sessionToken } = await chrome.storage.sync.get({
    endpoint: "http://localhost:8000",
    options: {
      strong_delimiter: "**",
      emphasis_delimiter: "*",
      code_fence: "```",
      unknown_tag_strategy: "inline_text",
      expand_to_block_boundaries: true
    },
    token: "",
    sessionToken: ""
  });
  // enforce inline_text to avoid leaking raw HTML wrappers
  if (!options.unknown_tag_strategy || options.unknown_tag_strategy === "html_wrapper") {
    options.unknown_tag_strategy = "inline_text";
  }
  return { endpoint, options, token, sessionToken };
}

// Listen for token sync messages from content script
chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg.type === "convert-selection") {
     // Handled later in clicked listener, but we need to return false here so we don't block?
     // Actually, convert-selection is sent from background to content usually, or content to background?
     // Wait, background sends "convert-selection" to content.
     // Content script listens for it.
     // Here we are in background.js.
     // Is there any message sent TO background with type "convert-selection"? No.
     return false;
  }
  
  if (msg.type === "SYNC_TOKEN") {
      console.log("Received SYNC_TOKEN:", msg.token ? "Token present" : "Token cleared");
      // Save to storage.sync so it persists across devices if needed, or local if just this session.
      // Use sync for consistency with options.
      // Note: sessionToken is managed automatically.
      if (msg.token) {
        chrome.storage.sync.set({ sessionToken: msg.token, sessionEmail: msg.email || "" });
      } else {
        chrome.storage.sync.remove(["sessionToken", "sessionEmail"]);
      }
      respond({ status: "ok" });
      return true;
  }
});

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

async function performConversion(html, conversionOptions, token, endpoint) {
  const body = JSON.stringify({ html, options: conversionOptions });
  const headers = { "Content-Type": "application/json" };
  if (token && token.trim()) {
    headers["Authorization"] = "Bearer " + token.trim();
  }
  
  console.log("Sending conversion request to", endpoint, "with token length:", token ? token.length : 0);

  const r = await fetch(`${endpoint}/v1/convert`, { method: "POST", headers, body });
  if (!r.ok) {
    if (r.status === 401) {
      throw new Error("鉴权失败 (401)。请在扩展选项页检查 API Key 是否正确填写。");
    }
    throw new Error(`Server returned ${r.status} ${r.statusText}`);
  }
  const j = await r.json();
  if (!j || typeof j.markdown !== "string") {
    throw new Error("Invalid response format from server");
  }
  return j.markdown;
}

function showResult(markdown) {
  chrome.storage.local.set({ lastMarkdown: markdown }, () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("result.html") });
  });
}

function showError(err) {
  console.error("Conversion failed:", err);
  chrome.notifications.create({
    type: "basic",
    iconUrl: chrome.runtime.getURL("icon48.png"),
    title: "Conversion Failed",
    message: err.message
  });
  // Update storage to show error in result page if user opens it manually
  chrome.storage.local.set({ lastMarkdown: `# Error\n\nConversion failed: ${err.message}` });
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { endpoint, options, token, sessionToken } = await getOptions();
  
  // Logic: Prefer API Key (token) if set, otherwise use sessionToken (login state)
  // Or: Prefer sessionToken (current login) if available? 
  // User Requirement: "登录状态不需要使用APIKEY; 非登录态，可以通过APIKEY请求"
  // This implies if sessionToken exists, use it. If not, use API Key.
  // Actually, usually API Key is more "powerful" or persistent. 
  // But let's follow the requirement: If logged in (sessionToken), we don't need API Key.
  // So we can use either. Let's try sessionToken first, then API Key.
  // Wait, if I explicitly set an API Key in options, I probably want to use it?
  // But if I am logged in, I might expect that to work without configuring API Key.
  // So: effectiveToken = token || sessionToken (if API key is set, use it; else use session)
  // OR: effectiveToken = sessionToken || token (if logged in, use that; else use key)
  
  // Let's go with: Use API Key if present (explicit override), else use Session Token.
  // But the user said "Login state DOES NOT NEED ApiKey".
  // So if I have no API Key but have Session Token, it should work.
  // If I have API Key, it should also work.
  // UPDATE: Prioritize sessionToken (Login) over token (API Key) so SSO works seamlessly.
  
  const effectiveToken = sessionToken ? sessionToken : token;

  if (info.menuItemId === "convert-page") {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML
    }, async (res) => {
      try {
        if (!res || !res[0] || !res[0].result) throw new Error("Failed to retrieve page content");
        const html = res[0].result;
        const conversionOptions = { domain: new URL(tab.url).origin, ...options };
        
        const markdown = await performConversion(html, conversionOptions, effectiveToken, endpoint);
        showResult(markdown);
      } catch (err) {
        showError(err);
      }
    });
  }
  
  if (info.menuItemId === "convert-selection-strict" || info.menuItemId === "convert-selection-expand") {
    const expand = info.menuItemId === "convert-selection-expand";
    const res = await sendWithInjection(tab.id, { type: "convert-selection", expand });
    
    if (!res || !res.html) {
      showError(new Error("Could not retrieve selection content."));
      return;
    }
    
    try {
      const conversionOptions = { domain: new URL(tab.url).origin, ...options, expand_to_block_boundaries: expand };
      const markdown = await performConversion(res.html, conversionOptions, effectiveToken, endpoint);
      showResult(markdown);
    } catch (err) {
      showError(err);
    }
  }
});
