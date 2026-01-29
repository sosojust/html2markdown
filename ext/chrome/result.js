function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderInline(s) {
  s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (m, alt, url) => {
    if (/^javascript:/i.test(url)) return esc(m);
    return `<img alt="${esc(alt)}" src="${esc(url)}">`;
  });
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, text, url) => {
    if (/^javascript:/i.test(url)) return esc(text);
    return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(text)}</a>`;
  });
  s = s.replace(/`([^`]+)`/g, (m, code) => `<code>${esc(code)}</code>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, (m, b) => `<strong>${esc(b)}</strong>`);
  s = s.replace(/\*([^*]+)\*/g, (m, i) => `<em>${esc(i)}</em>`);
  return s;
}

function renderMarkdown(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let i = 0;
  let inCode = false;
  let codeLang = "";
  const listStack = [];
  while (i < lines.length) {
    let line = lines[i];
    if (inCode) {
      if (/^```/.test(line) || /^~~~/.test(line)) {
        html += "</code></pre>";
        inCode = false;
        i++;
        continue;
      }
      html += esc(line) + "\n";
      i++;
      continue;
    }
    const fence = line.match(/^(```|~~~)([\w-]*)\s*$/);
    if (fence) {
      inCode = true;
      codeLang = fence[2] || "";
      html += `<pre><code${codeLang ? ` class="language-${esc(codeLang)}"` : ""}>`;
      i++;
      continue;
    }
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      while (listStack.length) {
        html += listStack.pop();
      }
      const level = h[1].length;
      html += `<h${level}>${renderInline(h[2].trim())}</h${level}>`;
      i++;
      continue;
    }
    const hr = line.match(/^\s*([-*_]){3,}\s*$/);
    if (hr) {
      while (listStack.length) {
        html += listStack.pop();
      }
      html += "<hr>";
      i++;
      continue;
    }
    const bq = line.match(/^>\s?(.*)$/);
    if (bq) {
      while (listStack.length) {
        html += listStack.pop();
      }
      let inner = bq[1];
      html += `<blockquote><p>${renderInline(inner)}</p></blockquote>`;
      i++;
      continue;
    }
    const ul = line.match(/^(\s*)([-*+])\s+(.*)$/);
    const ol = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
    if (ul || ol) {
      const isOl = !!ol;
      const indent = (ul ? ul[1] : ol[1]).length;
      const level = Math.floor(indent / 2);
      const text = (ul ? ul[3] : ol[3]).trim();
      while (listStack.length > level) {
        html += listStack.pop();
      }
      while (listStack.length < level + 1) {
        html += isOl ? "<ol>" : "<ul>";
        listStack.push(isOl ? "</ol>" : "</ul>");
      }
      html += `<li>${renderInline(text)}</li>`;
      i++;
      continue;
    }
    if (/^\s*$/.test(line)) {
      while (listStack.length) {
        html += listStack.pop();
      }
      i++;
      continue;
    }
    while (listStack.length) {
      html += listStack.pop();
    }
    html += `<p>${renderInline(line.trim())}</p>`;
    i++;
  }
  while (listStack.length) {
    html += listStack.pop();
  }
  return html;
}

function renderWithLib(md) {
  try {
    if (window.markdownit) {
      // Initialize markdown-it with common settings
      const mdIt = window.markdownit({
        html: true, // Enable HTML tags in source (we sanitize later)
        xhtmlOut: true, // Use '/' to close single tags (<br />)
        breaks: true, // Convert '\n' in paragraphs into <br>
        linkify: true, // Autoconvert URL-like text to links
        typographer: true // Enable some language-neutral replacement + quotes beautification
      });
      const html = mdIt.render(md);
      
      if (window.DOMPurify && typeof window.DOMPurify.sanitize === "function") {
        return window.DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
      }
      return html;
    }
    
    // Fallback to old check or manual if needed (but we replaced marked)
    return renderMarkdown(md);
  } catch (e) {
    console.error("Render error:", e);
    return renderMarkdown(md);
  }
}

async function load() {
  const { lastMarkdown, lastMetadata } = await chrome.storage.local.get({ lastMarkdown: "", lastMetadata: {} });
  const md = lastMarkdown || "";
  const ta = document.getElementById("md");
  const pv = document.getElementById("preview");
  ta.value = md;
  if (window.markdownit) {
    pv.innerHTML = renderWithLib(md);
  } else {
    pv.innerHTML = renderMarkdown(md);
  }

  // Obsidian Integration
  if (lastMetadata && lastMetadata.target === 'obsidian' && lastMetadata.obsidian && lastMetadata.obsidian.vault) {
      const btn = document.getElementById("btn-open-obsidian");
      if (btn) {
          btn.classList.remove("hidden");
          btn.onclick = () => {
              const content = document.getElementById("md").value;
              const vault = lastMetadata.obsidian.vault;
              
              // Simple title generation
              const date = new Date().toISOString().slice(0, 10);
              const title = `Clipped Note ${date} ${Date.now().toString().slice(-4)}`;
              
              const url = `obsidian://new?vault=${encodeURIComponent(vault)}&name=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`;
              
              // Check length roughly (URL limit varies, safe bet ~2k-32k depending on browser/OS, but for custom protocol it might be shorter or longer)
              // If extremely long, warn user.
              if (url.length > 8000) {
                  alert("内容过长，无法通过链接直接打开 Obsidian。\n建议使用下载功能，保存到 Vault 文件夹中。");
                  return;
              }
              
              window.location.href = url;
          };
      }
  }
}

document.getElementById("copy").addEventListener("click", async () => {
  const t = document.getElementById("md").value;
  await navigator.clipboard.writeText(t);
  
  const btn = document.getElementById("copy");
  const originalContent = btn.innerHTML;
  
  btn.classList.remove("btn-primary");
  btn.classList.add("btn-success", "text-white");
  btn.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 mr-1">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
    已复制
  `;
  
  setTimeout(() => {
    btn.classList.remove("btn-success", "text-white");
    btn.classList.add("btn-primary");
    btn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 mr-1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 8.25V6a2.25 2.25 0 00-2.25-2.25H6A2.25 2.25 0 003.75 6v8.25A2.25 2.25 0 006 16.5h2.25m8.25-8.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-7.5A2.25 2.25 0 018.25 18v-1.5m8.25-8.25h-6a2.25 2.25 0 00-2.25 2.25v1.5m0 0h-6" />
      </svg>
      复制
    `;
  }, 2000);
});

document.getElementById("download").addEventListener("click", async () => {
  const t = document.getElementById("md").value;
  const url = "data:text/markdown;charset=utf-8," + encodeURIComponent(t);
  chrome.downloads.download({ url, filename: "converted.md", saveAs: true });
});

document.getElementById("refresh").addEventListener("click", async () => {
  const t = document.getElementById("md").value;
  const pv = document.getElementById("preview");
  if (window.markdownit) {
    pv.innerHTML = renderWithLib(t);
  } else {
    pv.innerHTML = renderMarkdown(t);
  }
});

load();
