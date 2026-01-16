document.addEventListener('DOMContentLoaded', async () => {
  let { endpoint, token, sessionToken, sessionEmail } = await chrome.storage.sync.get({ 
    endpoint: "http://localhost:8000",
    token: "",
    sessionToken: "",
    sessionEmail: ""
  });

  const statusAlert = document.getElementById('status-alert');
  const loginSection = document.getElementById('login-section');
  const userSection = document.getElementById('user-section');
  const userDisplay = document.getElementById('user-display');
  const loginMsg = document.getElementById('login-msg');

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
      
      // If we are using sessionToken (Login), show email
      // If we are using token (API Key) AND no sessionToken, show API Key msg
      // But effectiveToken is sessionToken || token.
      
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
      
      const emailFromToken = getEmailFromToken(newToken);
      sessionEmail = emailFromToken;
      sessionToken = newToken; // Update local variable
      
      // Save to sessionToken, NOT token (keep API Key separate)
      await chrome.storage.sync.set({ sessionToken: newToken, sessionEmail: emailFromToken });
      loginMsg.textContent = "";
      updateUI(newToken || token);
      
    } catch (err) {
      loginMsg.textContent = "登录失败: " + err.message;
    }
  });

  // Logout Logic
  document.getElementById('btn-logout').addEventListener('click', async () => {
    // Clear sessionToken, but KEEP token (API Key)
    await chrome.storage.sync.set({ sessionToken: "", sessionEmail: "" });
    sessionToken = ""; // Update local variable
    sessionEmail = "";
    
    // Update UI (fallback to API Key if present)
    const nextToken = token;
    updateUI(nextToken);
    
    // Sync logout to frontend
    chrome.tabs.create({ url: "http://localhost:5173/?logout=true" });
  });

  // Links
  document.getElementById('link-register').addEventListener('click', () => {
    chrome.tabs.create({ url: "http://localhost:5173/register" });
  });

  document.getElementById('btn-dashboard').addEventListener('click', async () => {
    // Use sessionToken for dashboard login. API Key (token) won't work for frontend auth.
    const { sessionToken } = await chrome.storage.sync.get({ sessionToken: "" });
    const url = sessionToken ? `http://localhost:5173/?token=${sessionToken}` : "http://localhost:5173/";
    chrome.tabs.create({ url });
  });

  document.getElementById('btn-options').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});
