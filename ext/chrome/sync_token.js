
// sync_token.js
// This script is injected into the frontend dashboard (localhost:5173)
// It reads the JWT token from localStorage and sends it to the extension background script.

(function() {
    console.log("[HTML-to-Markdown] Sync script loaded");

    function syncToken() {
        const token = localStorage.getItem("token");
        const email = localStorage.getItem("user_email");
        if (token) {
            console.log("[HTML-to-Markdown] Found token, syncing to extension...");
            try {
                chrome.runtime.sendMessage({ type: "SYNC_TOKEN", token: token, email: email }, (response) => {
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

    // Listen for storage changes (e.g. login/logout)
    window.addEventListener("storage", (event) => {
        if (event.key === "token" || event.key === "user_email") {
            syncToken();
        }
    });

    // Also try to hook into pushState/replaceState or just poll if needed, 
    // but storage event works for cross-tab, and for same-tab explicit setItem usually doesn't trigger event in same window.
    // So we monkey-patch setItem/removeItem to detect changes within the same window (SPA login)
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key, value) {
        originalSetItem.apply(this, arguments);
        if (key === "token" || key === "user_email") syncToken();
    };

    const originalRemoveItem = localStorage.removeItem;
    localStorage.removeItem = function(key) {
        originalRemoveItem.apply(this, arguments);
        if (key === "token") {
             chrome.runtime.sendMessage({ type: "SYNC_TOKEN", token: null });
        }
    };
})();
