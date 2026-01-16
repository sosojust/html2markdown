async function load() {
  const { options, token } = await chrome.storage.sync.get({
    options: {
      strong_delimiter: "**",
      emphasis_delimiter: "*",
      code_fence: "```",
      unordered_marker: "-",
      list_indent_spaces: 2,
      unknown_tag_strategy: "inline_text",
      expand_to_block_boundaries: true
    },
    token: ""
  });
  
  // Set values (safely)
  const setVal = (id, val) => { const el = document.getElementById(id); if(el) el.value = val; };
  const setCheck = (id, val) => { const el = document.getElementById(id); if(el) el.checked = !!val; };

  // setVal("endpoint", endpoint); // Hidden
  setVal("strong_delimiter", options.strong_delimiter);
  setVal("emphasis_delimiter", options.emphasis_delimiter);
  setVal("code_fence", options.code_fence);
  setVal("unordered_marker", options.unordered_marker);
  setVal("list_indent_spaces", options.list_indent_spaces);
  setVal("unknown_tag_strategy", options.unknown_tag_strategy);
  setCheck("expand_to_block_boundaries", options.expand_to_block_boundaries);
  setVal("token", token);
}

document.getElementById("dashboard-link").addEventListener("click", async (e) => {
  e.preventDefault();
  // Default to localhost dev server, but in production this should be the actual frontend URL
  const { token } = await chrome.storage.sync.get({ token: "" });
  const url = token ? `http://localhost:5173/?token=${token}` : "http://localhost:5173/";
  chrome.tabs.create({ url });
});

document.getElementById("save").addEventListener("click", async () => {
  // const endpoint = document.getElementById("endpoint").value || "http://localhost:8000";
  const options = {
    strong_delimiter: document.getElementById("strong_delimiter").value,
    emphasis_delimiter: document.getElementById("emphasis_delimiter").value,
    code_fence: document.getElementById("code_fence").value,
    unordered_marker: document.getElementById("unordered_marker").value,
    list_indent_spaces: Number(document.getElementById("list_indent_spaces").value) || 2,
    unknown_tag_strategy: document.getElementById("unknown_tag_strategy").value,
    expand_to_block_boundaries: document.getElementById("expand_to_block_boundaries").checked
  };
  const token = document.getElementById("token").value.trim();
  
  await chrome.storage.sync.set({ options, token });
  
  // Visual feedback
  const btn = document.getElementById("save");
  const originalText = btn.innerHTML;
  btn.textContent = "已保存!";
  setTimeout(() => btn.innerHTML = originalText, 1000);
});

load();
