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
  const { lastMarkdown } = await chrome.storage.local.get({ lastMarkdown: "" });
  const md = lastMarkdown || "";
  const ta = document.getElementById("md");
  const pv = document.getElementById("preview");
  ta.value = md;
  if (window.markdownit) {
    pv.innerHTML = renderWithLib(md);
  } else {
    pv.innerHTML = renderMarkdown(md);
  }
}

document.getElementById("copy").addEventListener("click", async () => {
  const t = document.getElementById("md").value;
  await navigator.clipboard.writeText(t);
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
