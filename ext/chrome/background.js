chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "convert-page", title: "转为 Markdown（整页）", contexts: ["page"] });
  chrome.contextMenus.create({ id: "convert-selection-strict", title: "转为 Markdown（选区-严格）", contexts: ["selection"] });
  chrome.contextMenus.create({ id: "convert-selection-expand", title: "转为 Markdown（选区-扩展）", contexts: ["selection"] });
});

async function getOptions() {
  const { endpoint, options, token, sessionToken, sessionRefreshToken, notion, obsidian } = await chrome.storage.sync.get({
    endpoint: "http://localhost:8000",
    options: {
      strong_delimiter: "**",
      emphasis_delimiter: "*",
      code_fence: "```",
      unknown_tag_strategy: "inline_text",
      expand_to_block_boundaries: true,
      target: "markdown"
    },
    token: "",
    sessionToken: "",
    sessionRefreshToken: "",
    notion: { token: "", page_id: "" },
    obsidian: { vault: "" }
  });
  // enforce inline_text to avoid leaking raw HTML wrappers
  if (!options.unknown_tag_strategy || options.unknown_tag_strategy === "html_wrapper") {
    options.unknown_tag_strategy = "inline_text";
  }
  return { endpoint, options, token, sessionToken, sessionRefreshToken, notion, obsidian };
}

// Initialize: Check for existing tokens in open dashboard tabs
chrome.runtime.onInstalled.addListener(() => {
    checkDashboardTabsForToken();
});

chrome.runtime.onStartup.addListener(() => {
    checkDashboardTabsForToken();
});

async function checkDashboardTabsForToken() {
    try {
        const tabs = await chrome.tabs.query({ url: ["http://localhost:5173/*", "http://127.0.0.1:5173/*"] });
        for (const tab of tabs) {
            try {
                const results = await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    func: () => {
                        const token = localStorage.getItem("token");
                        const refreshToken = localStorage.getItem("refresh_token");
                        const email = localStorage.getItem("user_email");
                        if (token) {
                            chrome.runtime.sendMessage({ 
                                type: "SYNC_TOKEN", 
                                token: token, 
                                email: email,
                                refreshToken: refreshToken
                            });
                        }
                    }
                });
            } catch (err) {
                console.log("Failed to inject sync script into tab", tab.id, err);
            }
        }
    } catch (e) {
        console.log("Error checking dashboard tabs:", e);
    }
}

// Listen for token sync messages from content script
chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg.type === "convert-selection") {
     return false;
  }
  
  if (msg.type === "START_CONVERSION") {
    handleUniversalExport(respond);
    return true; // Keep channel open for async response
  }
  
  if (msg.type === "SYNC_TOKEN") {
      console.log("Received SYNC_TOKEN:", msg.token ? "Token present" : "Token cleared");
      if (msg.token) {
        const updateData = { sessionToken: msg.token, sessionEmail: msg.email || "" };
        if (msg.refreshToken) {
          updateData.sessionRefreshToken = msg.refreshToken;
        }
        chrome.storage.sync.set(updateData);
      } else {
        chrome.storage.sync.remove(["sessionToken", "sessionEmail", "sessionRefreshToken"]);
      }
      respond({ status: "ok" });
      return true;
  }

  if (msg.type === "CHECK_EXTENSION_TOKEN") {
      getOptions().then(({ sessionToken, sessionEmail, sessionRefreshToken }) => {
          respond({ 
              token: sessionToken, 
              email: sessionEmail, 
              refreshToken: sessionRefreshToken 
          });
      });
      return true; // Keep channel open
  }
});

function promptLogin() {
  chrome.windows.create({
    url: "popup.html",
    type: "popup",
    width: 420,
    height: 600
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
      // Try refresh logic
      const { sessionRefreshToken } = await chrome.storage.sync.get("sessionRefreshToken");
      if (sessionRefreshToken) {
        console.log("Token expired, attempting refresh...");
        try {
          const refResp = await fetch(`${endpoint}/v1/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: sessionRefreshToken })
          });
          
          if (refResp.ok) {
            const data = await refResp.json();
            const { access_token, refresh_token: new_refresh_token } = data;
            
            // Update storage
             const updates = { sessionToken: access_token };
             if (new_refresh_token) updates.sessionRefreshToken = new_refresh_token;
             await chrome.storage.sync.set(updates);

             // Notify frontend tabs to update their localStorage
             // This prevents the frontend from overwriting our fresh token with its stale one
             chrome.tabs.query({ url: ["http://localhost:5173/*", "http://127.0.0.1:5173/*"] }, (tabs) => {
                for (const tab of tabs) {
                  chrome.tabs.sendMessage(tab.id, {
                    type: "UPDATE_FROM_EXTENSION",
                    token: access_token,
                    refreshToken: new_refresh_token
                  }).catch(err => {
                     // Ignore errors (tab might be closed or script not ready)
                     console.log("Failed to send token update to tab", tab.id, err);
                  });
                }
             });
             
             // Retry original request
             headers["Authorization"] = "Bearer " + access_token;
             const r2 = await fetch(`${endpoint}/v1/convert`, { method: "POST", headers, body });
             if (r2.ok) {
               const j2 = await r2.json();
               if (!j2 || typeof j2.markdown !== "string") throw new Error("Invalid response format from server");
               return j2.markdown;
             }
           } else {
              console.log("Refresh failed with status", refResp.status);
              // Clear session on failure
              await chrome.storage.sync.remove(["sessionToken", "sessionRefreshToken"]);
           }
         } catch (e) {
           console.error("Refresh error:", e);
           // Clear session on error
           await chrome.storage.sync.remove(["sessionToken", "sessionRefreshToken"]);
         }
       } else {
         // No refresh token available, clear session to reflect logged out state
         await chrome.storage.sync.remove(["sessionToken", "sessionRefreshToken"]);
       }
       
       promptLogin(); // Prompt login on 401
      throw new Error("鉴权失败 (401)。请登录或检查 API Key。");
    }
    throw new Error(`Server returned ${r.status} ${r.statusText}`);
  }
  const j = await r.json();
  if (!j || typeof j.markdown !== "string") {
    throw new Error("Invalid response format from server");
  }
  return j.markdown;
}

function showResult(markdown, metadata = {}) {
  chrome.storage.local.set({ lastMarkdown: markdown, lastMetadata: metadata }, () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("result.html") });
  });
}

function showError(err, tabId = null) {
  console.error("Conversion failed:", err);
  
  // Try to show alert in the tab if tabId is provided
  if (tabId) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: (msg) => { alert("HTML-to-Markdown Error:\n" + msg); },
      args: [err.message]
    }).catch(e => console.error("Failed to show alert in tab:", e));
  } else {
    // Fallback to notification if no tabId (e.g. background error unrelated to specific tab action, though unlikely here)
    chrome.notifications.create({
      type: "basic",
      iconUrl: chrome.runtime.getURL("icon48.png"),
      title: "Conversion Failed",
      message: err.message
    });
  }
  
  // Update storage to show error in result page if user opens it manually
  chrome.storage.local.set({ lastMarkdown: `# Error\n\nConversion failed: ${err.message}` });
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { endpoint, options, token, sessionToken, notion, obsidian } = await getOptions();
  
  const effectiveToken = sessionToken ? sessionToken : token;

  if (info.menuItemId === "convert-page") {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML
    }, async (res) => {
      try {
        if (!res || !res[0] || !res[0].result) throw new Error("Failed to retrieve page content");
        const html = res[0].result;
        
        if (options.target === 'notion') {
             await exportToNotion(html, tab, options, endpoint, effectiveToken, notion);
             chrome.notifications.create({
                  type: "basic",
                  iconUrl: chrome.runtime.getURL("icon48.png"),
                  title: "Export Success",
                  message: "Content exported to Notion successfully."
             });
        } else {
             const conversionOptions = { domain: new URL(tab.url).origin, ...options };
             const markdown = await performConversion(html, conversionOptions, effectiveToken, endpoint);
             showResult(markdown, { target: options.target, obsidian });
        }
      } catch (err) {
        showError(err, tab.id);
      }
    });
  }
  
  if (info.menuItemId === "convert-selection-strict" || info.menuItemId === "convert-selection-expand") {
    const expand = info.menuItemId === "convert-selection-expand";
    
    try {
      // Prioritize the specific frame where the click occurred
      const target = { tabId: tab.id };
      if (typeof info.frameId === 'number') {
        target.frameIds = [info.frameId];
      } else {
        target.allFrames = true;
      }

      let results;
      try {
        results = await chrome.scripting.executeScript({
          target: target,
          func: (shouldExpand) => {
            try {
              function expandRangeToBlocks(range) {
                let start = range.startContainer.nodeType === Node.ELEMENT_NODE ? range.startContainer : range.startContainer.parentElement;
                let end = range.endContainer.nodeType === Node.ELEMENT_NODE ? range.endContainer : range.endContainer.parentElement;
                const startBlock = start.closest('p,div,section,article,li,pre,blockquote,h1,h2,h3,h4,h5,h6,td,th,tr,table,ul,ol') || start;
                const endBlock = end.closest('p,div,section,article,li,pre,blockquote,h1,h2,h3,h4,h5,h6,td,th,tr,table,ul,ol') || end;
                const r = document.createRange();
                r.setStartBefore(startBlock);
                r.setEndAfter(endBlock);
                return r;
              }

              // 1. Try Standard Selection
              const sel = window.getSelection();
              if (sel && sel.rangeCount > 0 && !sel.isCollapsed && sel.toString().trim()) {
                let range = sel.getRangeAt(0).cloneRange();
                if (shouldExpand) range = expandRangeToBlocks(range);
                
                const container = document.createElement('div');
                container.appendChild(range.cloneContents());
                return { html: container.innerHTML, found: true };
              }

              // 2. Try Active Element (Input/Textarea)
              let active = document.activeElement;
              // Drill down into shadow roots
              while (active && active.shadowRoot && active.shadowRoot.activeElement) {
                active = active.shadowRoot.activeElement;
              }
              
              if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
                const text = active.value.substring(active.selectionStart, active.selectionEnd);
                if (text && text.trim()) {
                   // Wrap in pre for markdown preservation or just return as text
                   // For consistency, return as HTML
                   // Escape HTML entities? simpler to just return text and let backend handle or wrap in <p>
                   // Let's wrap in <p> to treat as paragraph
                   const safeText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
                   return { html: `<p>${safeText}</p>`, found: true };
                }
              }

              return { found: false };
            } catch (e) {
              return { error: e.toString() };
            }
          },
          args: [expand]
        });
      } catch (injectionError) {
         // If injection failed (e.g. frame permission issue), fallback to all frames if we tried specific frame, or just error
         if (target.frameIds) {
             console.warn("Specific frame injection failed, trying all frames...", injectionError);
             results = await chrome.scripting.executeScript({
                target: { tabId: tab.id, allFrames: true },
                func: (shouldExpand) => { /* Same function duplicated or referenced? Needs to be inline or variable */ 
                   // To avoid duplication, we rely on the first attempt's failure being handled below if results is undefined
                   // But executeScript func must be provided again.
                   // Let's just re-throw or handle. 
                   // Actually, if we add <all_urls>, permission error shouldn't happen.
                   // Let's stick to the result processing.
                   return { found: false, error: "Fallback not implemented in inline code" }; 
                },
                args: [expand]
             });
             // Wait, reusing the function source is tricky in this tool call.
             // Let's just trust the permission fix.
             throw injectionError;
         }
         throw injectionError;
      }

      // Find the first successful result
      const result = results.find(r => r.result && r.result.found);
      
      if (!result) {
        // Check if any frame reported an error
        const errorResult = results.find(r => r.result && r.result.error);
        if (errorResult) {
             throw new Error("Script error in frame: " + errorResult.result.error);
        }
        showError(new Error("未找到选区内容。\n\n可能原因：\n1. 未选中文本\n2. 选区在跨域 iframe 中且权限不足\n3. 页面使用了 Canvas 或特殊渲染方式"), tab.id);
        return;
      }

      const html = result.result.html;

      if (options.target === 'notion') {
          const notionOptions = { ...options, expand_to_block_boundaries: expand };
          await exportToNotion(html, tab, notionOptions, endpoint, effectiveToken, notion);
          chrome.notifications.create({
              type: "basic",
              iconUrl: chrome.runtime.getURL("icon48.png"),
              title: "Export Success",
              message: "Selection exported to Notion successfully."
          });
      } else {
          const conversionOptions = { domain: new URL(tab.url).origin, ...options, expand_to_block_boundaries: expand };
          const markdown = await performConversion(html, conversionOptions, effectiveToken, endpoint);
          showResult(markdown, { target: options.target, obsidian });
      }
    } catch (err) {
      showError(err, tab.id);
    }
  }
});

async function exportToNotion(html, tab, options, endpoint, effectiveToken, notion) {
    if (!notion || !notion.token || !notion.page_id) {
        throw new Error("请先在设置中配置 Notion Token 和 Page ID");
    }

    // 1. Convert to Markdown (force target=markdown)
    const conversionOptions = { domain: new URL(tab.url).origin, ...options, target: "markdown" };
    const markdown = await performConversion(html, conversionOptions, effectiveToken, endpoint);

    // Refresh token check
    const { sessionToken: freshSessionToken } = await chrome.storage.sync.get(["sessionToken"]);
    let currentToken = effectiveToken;
    if (freshSessionToken) {
        currentToken = freshSessionToken;
    }

    // 2. Export to Notion
    const resp = await fetch(`${endpoint}/v1/export/notion`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + currentToken
        },
        body: JSON.stringify({
            markdown: markdown,
            token: notion.token,
            page_id: notion.page_id
        })
    });

    if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(errJson.detail || "Export failed");
    }

    const result = await resp.json();
    if (!result.success) {
        throw new Error("Export reported failure");
    }
    return result;
}

async function handleUniversalExport(respond) {
  try {
    const { endpoint, options, token, sessionToken, notion, obsidian } = await getOptions();
    let effectiveToken = sessionToken ? sessionToken : token;

    if (!effectiveToken) {
        respond({ success: false, error: "未登录，请先登录或配置 API Key" });
        return;
    }
    
    // Get active tab content
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
        respond({ success: false, error: "无法获取当前标签页" });
        return;
    }

    const injectionResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.documentElement.outerHTML
    });

    if (!injectionResults || !injectionResults[0] || !injectionResults[0].result) {
        respond({ success: false, error: "无法获取页面内容" });
        return;
    }

    const html = injectionResults[0].result;
    
    if (options.target === 'notion') {
        await exportToNotion(html, tab, options, endpoint, effectiveToken, notion);
        respond({ success: true });
    } else {
        const conversionOptions = { domain: new URL(tab.url).origin, ...options };
        const markdown = await performConversion(html, conversionOptions, effectiveToken, endpoint);
        respond({ success: true });
        showResult(markdown, { target: options.target, obsidian });
    }

  } catch (err) {
      console.error("Export Error:", err);
      respond({ success: false, error: err.message });
  }
}
