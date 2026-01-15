from typing import List, Optional
from lxml import html, etree
from .types import ConvertOptions
from .cleaner import clean_html_tree
from html_to_markdown import convert as htm_convert, convert_with_visitor, ConversionOptions

class CodeBlockVisitor:
    def visit_code_block(self, ctx, language: Optional[str], code: str):
        """
        Handle code blocks to ensure proper language tagging and strip extra newlines.
        """
        lang = language if language else ""
        # Strip leading/trailing whitespace from code to avoid extra newlines in markdown
        return {"type": "custom", "output": f"```{lang}\n{code.strip()}\n```\n"}

def convert_html_to_markdown(s: str, options: ConvertOptions = ConvertOptions()) -> str:
    """
    Convert HTML string to Markdown using html-to-markdown library.
    Pre-processes DOM to clean noise and handle absolute URLs.
    """
    if not s:
        return ""

    # 1. Parse HTML
    # Use fragment_fromstring with a parent div to handle fragments and multiple top-level elements
    try:
        root = html.fragment_fromstring(s, create_parent="div")
    except Exception:
        # Fallback
        return ""

    # 2. Domain absolute URLs
    if options.domain:
        try:
            root.make_links_absolute(options.domain)
        except Exception:
            pass

    # 3. Clean DOM tree (remove scripts, styles, hidden elements, etc.)
    clean_html_tree(root)

    # 4. Serialize back to HTML string
    # We use inner HTML of the wrapper div
    # etree.tostring returns bytes, decode to string
    # method="html" is standard
    cleaned_html = ""
    if len(root) > 0 or root.text:
        # If the root is the wrapper div, we want its children
        # But html-to-markdown expects a string.
        # Let's serialize the wrapper's content.
        # A simple way is to iterate children and serialize them.
        parts = []
        if root.text:
            parts.append(root.text)
        for child in root:
            parts.append(etree.tostring(child, encoding="unicode", method="html"))
        cleaned_html = "".join(parts)
    else:
        return ""

    # 5. Convert to Markdown
    # Map options
    bullets = "-*+"
    if options.unordered_marker:
        bullets = options.unordered_marker

    htm_options = ConversionOptions(
        heading_style="atx",
        list_indent_width=options.list_indent_spaces or 2,
        bullets=bullets,
    )
    
    try:
        visitor = CodeBlockVisitor()
        return convert_with_visitor(cleaned_html, options=htm_options, visitor=visitor).strip()
    except Exception as e:
        return f"Error converting to Markdown: {str(e)}"
