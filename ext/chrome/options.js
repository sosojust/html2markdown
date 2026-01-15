async function load() {
  const { endpoint, options } = await chrome.storage.sync.get({
    endpoint: "http://localhost:8000",
    options: {
      strong_delimiter: "**",
      emphasis_delimiter: "*",
      code_fence: "```",
      unordered_marker: "-",
      list_indent_spaces: 2,
      unknown_tag_strategy: "inline_text",
      expand_to_block_boundaries: true
    }
  });
  document.getElementById("endpoint").value = endpoint;
  document.getElementById("strong_delimiter").value = options.strong_delimiter;
  document.getElementById("emphasis_delimiter").value = options.emphasis_delimiter;
  document.getElementById("code_fence").value = options.code_fence;
  document.getElementById("unordered_marker").value = options.unordered_marker;
  document.getElementById("list_indent_spaces").value = options.list_indent_spaces;
  document.getElementById("unknown_tag_strategy").value = options.unknown_tag_strategy;
  document.getElementById("expand_to_block_boundaries").checked = !!options.expand_to_block_boundaries;
  const { token } = await chrome.storage.sync.get({ token: "" });
  document.getElementById("token").value = token || "";
}

document.getElementById("save").addEventListener("click", async () => {
  const endpoint = document.getElementById("endpoint").value || "http://localhost:8000";
  const options = {
    strong_delimiter: document.getElementById("strong_delimiter").value,
    emphasis_delimiter: document.getElementById("emphasis_delimiter").value,
    code_fence: document.getElementById("code_fence").value,
    unordered_marker: document.getElementById("unordered_marker").value,
    list_indent_spaces: Number(document.getElementById("list_indent_spaces").value) || 2,
    unknown_tag_strategy: document.getElementById("unknown_tag_strategy").value,
    expand_to_block_boundaries: document.getElementById("expand_to_block_boundaries").checked
  };
  const token = document.getElementById("token").value || "";
  await chrome.storage.sync.set({ endpoint, options, token });
});

load();
