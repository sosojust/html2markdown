document.addEventListener('DOMContentLoaded', async () => {
  let { endpoint, token, sessionToken, sessionEmail, options } = await chrome.storage.sync.get({ 
    endpoint: "http://localhost:8000",
    token: "",
    sessionToken: "",
    sessionEmail: "",
    options: { target: "markdown" }
  });

  const statusAlert = document.getElementById('status-alert');
  const loginSection = document.getElementById('login-section');
  const userSection = document.getElementById('user-section');
  const userDisplay = document.getElementById('user-display');
  const loginMsg = document.getElementById('login-msg');

  // Load Target Selector
  const targetEl = document.getElementById("target-format");
  
  async function checkConfiguration(targetVal) {
      const msg = document.getElementById("notion-msg");
      if (!msg) return;

      const { notion } = await chrome.storage.sync.get({ notion: {} });
      
      msg.classList.remove("text-error", "text-success");
      msg.classList.add("text-warning");

      if (targetVal === 'notion' && (!notion || !notion.token || !notion.page_id)) {
          msg.textContent = "提示: 请先在扩展设置中配置 Notion";
          msg.classList.remove("hidden");
      } else {
          msg.classList.add("hidden");
      }
  }

  if(targetEl) {
      const currentTarget = (options && options.target) ? options.target : "markdown";
      targetEl.value = currentTarget;
      
      // Initial check
      checkConfiguration(currentTarget);
      
      targetEl.addEventListener("change", async (e) => {
        const val = e.target.value;
        const { options: currentOptions } = await chrome.storage.sync.get({ options: {} });
        currentOptions.target = val;
        await chrome.storage.sync.set({ options: currentOptions });
        
        await checkConfiguration(val);
      });
  }

  function getEmailFromToken(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        const payload = JSON.parse(jsonPayload);
        return payload.email || "";
    } catch (e) {
        return "";
    }
  }

  function updateUI(effectiveToken) {
    if (effectiveToken) {
      statusAlert.classList.add('hidden');
      loginSection.classList.add('hidden');
      userSection.classList.remove('hidden');
      
      if (sessionToken) {
        // Logged In
        let displayEmail = sessionEmail;
        if (!displayEmail) {
            displayEmail = getEmailFromToken(sessionToken);
        }
        userDisplay.textContent = displayEmail ? `Logged In (${displayEmail})` : 'Logged In';
      } else {
        // Using API Key
         userDisplay.textContent = 'Using API Key';
      }
    } else {
      statusAlert.classList.remove('hidden');
      loginSection.classList.remove('hidden');
      userSection.classList.add('hidden');
    }
  }

  // Prioritize sessionToken (Login) over token (API Key)
  const effectiveToken = sessionToken || token;
  updateUI(effectiveToken);

  // Auto-sync logic: If not logged in, try to pull token from Dashboard tabs
  if (!sessionToken) {
      try {
          const tabs = await chrome.tabs.query({ url: ["http://localhost:5173/*", "http://127.0.0.1:5173/*"] });
          if (tabs.length > 0) {
              // Found a dashboard tab, try to read localStorage
              const tab = tabs[0];
              const results = await chrome.scripting.executeScript({
                  target: { tabId: tab.id },
                  func: () => {
                      return {
                          token: localStorage.getItem("token"),
                          refreshToken: localStorage.getItem("refresh_token"),
                          email: localStorage.getItem("user_email")
                      };
                  }
              });

              if (results && results[0] && results[0].result) {
                  const { token: remoteToken, refreshToken: remoteRefreshToken, email: remoteEmail } = results[0].result;
                  if (remoteToken) {
                      console.log("Auto-synced token from Dashboard tab");
                      
                      // Update local state
                      sessionToken = remoteToken;
                      sessionEmail = remoteEmail || getEmailFromToken(remoteToken);
                      
                      // Save to storage
                      await chrome.storage.sync.set({ 
                          sessionToken: sessionToken, 
                          sessionRefreshToken: remoteRefreshToken,
                          sessionEmail: sessionEmail 
                      });
                      
                      updateUI(sessionToken);
                  }
              }
          }
      } catch (e) {
          console.log("Auto-sync failed:", e);
      }
  }

  // Login Logic
  document.getElementById('btn-login').addEventListener('click', async () => {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (!email || !password) {
      loginMsg.textContent = "请输入邮箱和密码";
      return;
    }

    loginMsg.textContent = "登录中...";
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${endpoint}/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });
      
      if (!res.ok) {
        const j = await res.json();
        throw new Error(j.detail || "Login failed");
      }
      
      const data = await res.json();
      const newToken = data.access_token;
      const newRefreshToken = data.refresh_token;
      
      const emailFromToken = getEmailFromToken(newToken);
      sessionEmail = emailFromToken;
      sessionToken = newToken; // Update local variable
      
      // Save to sessionToken, NOT token (keep API Key separate)
      await chrome.storage.sync.set({ 
          sessionToken: newToken, 
          sessionRefreshToken: newRefreshToken,
          sessionEmail: emailFromToken 
      });
      
      updateUI(newToken);
      loginMsg.textContent = "";
      
    } catch (e) {
      loginMsg.textContent = "Error: " + e.message;
    }
  });

  document.getElementById('link-register').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "http://localhost:5173/register" });
  });

  document.getElementById('btn-logout').addEventListener('click', async () => {
    await chrome.storage.sync.remove(["sessionToken", "sessionRefreshToken", "sessionEmail"]);
    sessionToken = "";
    sessionEmail = "";
    updateUI(token); // Fallback to API Key if present
  });

  document.getElementById('btn-dashboard').addEventListener('click', () => {
    // Construct URL with token if available (SSO)
    let url = "http://localhost:5173";
    if (sessionToken) {
        url += `?token=${encodeURIComponent(sessionToken)}`;
        // We might also want to pass refresh token if available, though frontend usually handles exchange
        // Looking at frontend AuthContext, it checks 'token' and 'refresh_token' params
        // But sessionRefreshToken is not always in scope here? 
        // Let's check if we have it in storage or scope.
        // We have sessionToken in scope. sessionRefreshToken is not a global var here?
        // Wait, line 108: await chrome.storage.sync.set({ sessionToken: newToken, sessionRefreshToken: newRefreshToken... });
        // But we don't load sessionRefreshToken into a global variable on init (lines 20-30 only load token/sessionToken).
        // Let's fetch it from storage to be safe.
        chrome.storage.sync.get(["sessionRefreshToken"], (items) => {
             if (items.sessionRefreshToken) {
                 url += `&refresh_token=${encodeURIComponent(items.sessionRefreshToken)}`;
             }
             chrome.tabs.create({ url });
        });
    } else {
        chrome.tabs.create({ url });
    }
  });
  
  document.getElementById('btn-options').addEventListener('click', () => {
    if (chrome.runtime.openOptionsPage) {
        chrome.runtime.openOptionsPage();
    } else {
        window.open(chrome.runtime.getURL('options.html'));
    }
  });

  // Export Button Logic
  const btnExport = document.getElementById('btn-start-conversion');
  if (btnExport) {
      btnExport.addEventListener("click", async () => {
        const msg = document.getElementById("notion-msg");
        const originalText = btnExport.innerHTML;
        btnExport.disabled = true;
        btnExport.innerHTML = `<span class="loading loading-spinner loading-xs"></span> Processing...`;
        if (msg) {
             msg.classList.add("hidden");
             msg.textContent = "";
             msg.classList.remove("text-error", "text-success", "text-warning");
        }

        chrome.runtime.sendMessage({ type: "START_CONVERSION" }, (resp) => {
          btnExport.disabled = false;
          btnExport.innerHTML = originalText;
          
          if (chrome.runtime.lastError) {
             if (msg) {
                msg.textContent = "Error: " + chrome.runtime.lastError.message;
                msg.classList.remove("hidden");
                msg.classList.add("text-error");
             }
             return;
          }

          if (resp && !resp.success) {
             if (msg) {
                msg.textContent = "Error: " + (resp.error || "Unknown error");
                msg.classList.remove("hidden");
                msg.classList.add("text-error");
             }
          } else {
             // Success
             // If Notion, show success message. If Markdown, new tab opened, maybe show nothing or success.
             if (msg) {
                msg.textContent = "Success!";
                msg.classList.remove("hidden");
                msg.classList.add("text-success");
                setTimeout(() => {
                    msg.classList.add("hidden");
                }, 3000);
             }
          }
        });
      });
  }
});
