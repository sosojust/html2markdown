from lxml import html, etree
from typing import List, Optional
from ..types import TagType, Priority, ConvertOptions
from ..registry import RendererRegistry
from ..escape import escape_text, fence_block
from . import base as base_plugin

def _safe_tag(n: etree.Element) -> str:
    return (n.tag.lower() if isinstance(n.tag, str) else "")


def _domain_join(domain: Optional[str], url: Optional[str]) -> str:
    if not url:
        return ""
    if domain and url.startswith("/"):
        return f"{domain}{url}"
    return url


def _children_text(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    parts: List[str] = []
    for child in node:
        parts.append(convert(child, options, ctx))
    text = (node.text or "")
    if text:
        parts.insert(0, escape_text(text) if ctx.get("escape", True) else text)
    return "".join(parts)


def _wrap_inline(node: etree.Element, delim: str, convert, options: ConvertOptions, ctx) -> str:
    inner = _children_text(node, convert, options, ctx)
    return f"{delim}{inner}{delim}"


def _render_p(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    inner = _children_text(node, convert, options, ctx)
    return f"{inner}\n\n"

def _render_block_container(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    inner = _children_text(node, convert, options, ctx)
    return inner.strip() + "\n\n"

def _render_inline_container(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    return _children_text(node, convert, options, ctx)

def _render_heading(level: int):
    def r(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
        inner = _children_text(node, convert, options, ctx)
        return f"{'#' * level} {inner}\n\n"
    return r


def _render_a(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    text = _children_text(node, convert, options, ctx)
    href = _domain_join(options.domain, node.get("href"))
    if not href:
        return text
    return f"[{text}]({href})"


def _render_img(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    alt = node.get("alt") or ""
    src = _domain_join(options.domain, node.get("src"))
    return f"![{escape_text(alt)}]({src})"


def _render_inline_code(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    t = (node.text or "").replace("`", "\\`")
    return f"`{t}`"


def _render_pre(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    def _extract_lang(n: etree.Element) -> Optional[str]:
        # data-language on pre or code
        dl = n.get("data-language")
        if dl:
            return dl.strip()
        # class language-*/lang-*
        cls = n.get("class") or ""
        for token in cls.split():
            if token.startswith("language-"):
                return token.split("language-")[-1]
            if token.startswith("lang-"):
                return token.split("lang-")[-1]
        # if code child exists, check there
        for c in n.xpath(".//code"):
            v = c.get("data-language")
            if v:
                return v.strip()
            cc = c.get("class") or ""
            for t in cc.split():
                if t.startswith("language-"):
                    return t.split("language-")[-1]
                if t.startswith("lang-"):
                    return t.split("lang-")[-1]
        return None

    code = "".join([node.text or ""] + [etree.tostring(c, encoding="unicode", method="text") for c in node])
    lang = _extract_lang(node)
    fence = options.code_fence + (lang if lang else "")
    return fence + "\n" + code.strip("\n") + "\n" + options.code_fence + "\n\n"


def _render_blockquote(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    inner = "".join(convert(c, options, ctx) for c in node)
    lines = [l for l in inner.splitlines()]
    return "\n".join([f"> {l}" if l.strip() else ">" for l in lines]) + "\n\n"


def _render_list(node: etree.Element, ordered: bool, convert, options: ConvertOptions, ctx) -> str:
    res: List[str] = []
    idx = 1
    level = ctx.get("list_level", 0)
    for li in [c for c in node if _safe_tag(c) == "li"]:
        marker = f"{idx}. " if ordered else (options.unordered_marker + " ")
        task_prefix = ""
        inputs = li.xpath("./input[@type='checkbox']")
        if inputs:
            checked = any(i.get("checked") is not None for i in inputs)
            task_prefix = "[x] " if checked else "[ ] "
        inline_parts: List[str] = []
        block_parts: List[tuple] = []
        for child in li:
            tag = _safe_tag(child)
            if tag in ("ul", "ol", "p", "div", "blockquote", "pre", "table", "h1", "h2", "h3", "h4", "h5", "h6"):
                if tag in ("ul", "ol"):
                    block_parts.append(("list", convert(child, options, {"list_level": level + 1})))
                else:
                    block_parts.append(("block", convert(child, options, {"list_level": level + 1})))
            else:
                if tag and tag != "input":
                    inline_parts.append(convert(child, options, {"list_level": level + 1}))
                else:
                    t = child.tail or ""
                    if t:
                        inline_parts.append(escape_text(t))
        head_text = (li.text or "")
        if head_text:
            inline_parts.insert(0, escape_text(head_text))
        head = ("".join(inline_parts)).strip()
        indent_spaces = " " * (options.list_indent_spaces * level)
        line = indent_spaces + marker + task_prefix + head
        res.append(line)
        if block_parts:
            align_indent = " " * (options.list_indent_spaces * level + len(marker) + len(task_prefix))
            for kind, bp in block_parts:
                lines = bp.rstrip().splitlines()
                if kind == "list":
                    res.extend(lines)
                else:
                    for ln in lines:
                        res.append(align_indent + ln)
        idx += 1
    return "\n".join(res) + "\n\n"


def _render_table(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    def _is_complex(n: etree.Element) -> bool:
        rows = n.xpath(".//tr")
        if not rows:
            return True
        widths = []
        for tr in rows:
            cells = tr.xpath("./th|./td")
            w = 0
            for c in cells:
                try:
                    w += int(c.get("colspan") or "1")
                except Exception:
                    w += 1
                if c.get("rowspan") or c.get("colspan"):
                    return True
            widths.append(w)
        return len(set(widths)) > 1

    if _is_complex(node):
        strat = (options.table_incomplete_strategy or "wrap_html").lower()
        if strat == "wrap_html":
            return base_plugin.render_html(node, options) + "\n\n"
        # flatten_text: 近似输出为文本行（无对齐）
        text_lines = []
        for tr in node.xpath(".//tr"):
            t = " ".join([_children_text(c, convert, options, ctx).strip() for c in tr.xpath("./th|./td")])
            if t:
                text_lines.append(t)
        return "\n".join(text_lines) + "\n\n"
    rows: List[List[str]] = []
    for tr in node.xpath(".//tr"):
        cells = tr.xpath("./th|./td")
        if not cells:
            continue
        row = []
        for c in cells:
            row.append(_children_text(c, convert, options, ctx).strip())
        rows.append(row)
    if not rows:
        return ""
    header = rows[0]
    col_count = max(len(r) for r in rows)
    # 填充缺列为空，保证每行列数一致
    rows = [r + [""] * (col_count - len(r)) for r in rows]
    header = rows[0]
    align = ["---"] * len(header)
    body = rows[1:] if len(rows) > 1 else []
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n\n"


def register(reg: RendererRegistry) -> None:
    reg.register("p", TagType.Block, _render_p)
    reg.register("h1", TagType.Block, _render_heading(1))
    reg.register("h2", TagType.Block, _render_heading(2))
    reg.register("h3", TagType.Block, _render_heading(3))
    reg.register("h4", TagType.Block, _render_heading(4))
    reg.register("h5", TagType.Block, _render_heading(5))
    reg.register("h6", TagType.Block, _render_heading(6))
    reg.register("a", TagType.Inline, _render_a)
    reg.register("img", TagType.Inline, _render_img)
    reg.register("em", TagType.Inline, lambda n, c, o, x=None: _wrap_inline(n, o.emphasis_delimiter, c, o, x))
    reg.register("i", TagType.Inline, lambda n, c, o, x=None: _wrap_inline(n, o.emphasis_delimiter, c, o, x))
    reg.register("strong", TagType.Inline, lambda n, c, o, x=None: _wrap_inline(n, o.strong_delimiter, c, o, x))
    reg.register("b", TagType.Inline, lambda n, c, o, x=None: _wrap_inline(n, o.strong_delimiter, c, o, x))
    reg.register("code", TagType.Inline, _render_inline_code)
    reg.register("pre", TagType.Block, _render_pre)
    reg.register("blockquote", TagType.Block, _render_blockquote)
    reg.register("ul", TagType.Block, lambda n, c, o, x=None: _render_list(n, False, c, o, x or {}))
    reg.register("ol", TagType.Block, lambda n, c, o, x=None: _render_list(n, True, c, o, x or {}))
    reg.register("table", TagType.Block, _render_table)
    reg.register("div", TagType.Block, _render_block_container)
    reg.register("section", TagType.Block, _render_block_container)
    reg.register("article", TagType.Block, _render_block_container)
    reg.register("header", TagType.Block, _render_block_container)
    reg.register("footer", TagType.Block, _render_block_container)
    reg.register("main", TagType.Block, _render_block_container)
    reg.register("nav", TagType.Block, _render_block_container)
    reg.register("aside", TagType.Block, _render_block_container)
    reg.register("span", TagType.Inline, _render_inline_container)
