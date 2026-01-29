
// sync_token.js
// This script is injected into the frontend dashboard (localhost:5173)
// It reads the JWT token from localStorage and sends it to the extension background script.

(function() {
    console.log("[HTML-to-Markdown] Sync script loaded");

    function syncToken() {
        const token = localStorage.getItem("token");
        const email = localStorage.getItem("user_email");
        const refreshToken = localStorage.getItem("refresh_token");
        if (token) {
            console.log("[HTML-to-Markdown] Found token, syncing to extension...");
            try {
                chrome.runtime.sendMessage({ 
                    type: "SYNC_TOKEN", 
                    token: token, 
                    email: email,
                    refreshToken: refreshToken
                }, (response) => {
                    if (chrome.runtime.lastError) {
                         // Background script might be sleeping or not ready, or we are in a context where we can't send
                         // However, for content scripts defined in manifest, this should work.
                         // But note: externally_connectable is for web pages. Content scripts are part of extension.
                         console.log("[HTML-to-Markdown] Sync failed (runtime error):", chrome.runtime.lastError.message);
                    } else {
                        console.log("[HTML-to-Markdown] Token synced successfully");
                    }
                });
            } catch (e) {
                console.error("[HTML-to-Markdown] Sync error:", e);
            }
        }
    }

    // Sync on load
    syncToken();

    // Poll for changes in localStorage (workaround for Content Script isolation)
    // Content scripts share localStorage with the page, but cannot detect calls to setItem/removeItem
    // made by the page script because they run in isolated worlds.
    let lastToken = localStorage.getItem("token");
    let lastRefreshToken = localStorage.getItem("refresh_token");

    setInterval(() => {
        const token = localStorage.getItem("token");
        const refreshToken = localStorage.getItem("refresh_token");
        const email = localStorage.getItem("user_email");
        
        if (token !== lastToken || refreshToken !== lastRefreshToken) {
            // console.log("[HTML-to-Markdown] Token changed (detected via polling), syncing...");
            lastToken = token;
            lastRefreshToken = refreshToken;
            
            syncToken();
        }
    }, 1000);

    // Listen for storage changes (e.g. login/logout from other tabs)
    window.addEventListener("storage", (event) => {
        if (event.key === "token" || event.key === "user_email" || event.key === "refresh_token") {
            syncToken();
        }
    });

    // Listen for updates from extension (e.g. token refresh)
    chrome.runtime.onMessage.addListener((msg, sender, respond) => {
        if (msg.type === "UPDATE_FROM_EXTENSION") {
            console.log("[HTML-to-Markdown] Received token update from extension");
            if (msg.token) {
                localStorage.setItem("token", msg.token);
                lastToken = msg.token; // Update tracker to avoid echo
            }
            if (msg.refreshToken) {
                localStorage.setItem("refresh_token", msg.refreshToken);
                lastRefreshToken = msg.refreshToken;
            }
        }
    });
})();
