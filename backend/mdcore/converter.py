from typing import List
from lxml import html, etree
from .types import ConvertOptions
from .cleaner import clean_html_tree
from html_to_markdown import convert as htm_convert, ConversionOptions

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
    # heading_style: "atx" (###) is standard
    bullets = "-*+"
    if options.unordered_marker:
        # Use the user preference as the first bullet, or exclusively?
        # html-to-markdown cycles. If we want consistent marker, maybe passing just one char works?
        # Let's assume passing string "marker" works.
        bullets = options.unordered_marker

    htm_options = ConversionOptions(
        heading_style="atx",
        list_indent_width=options.list_indent_spaces or 2,
        bullets=bullets,
    )
    
    try:
        return htm_convert(cleaned_html, htm_options).strip()
    except Exception as e:
        # Fallback or error reporting
        # For now return error as text or empty
        return f"Error converting to Markdown: {str(e)}"
