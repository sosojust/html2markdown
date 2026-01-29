from typing import List, Optional
import re
from lxml import html, etree
from .types import ConvertOptions
from .cleaner import clean_html_tree
from html_to_markdown import convert as htm_convert, convert_with_visitor, ConversionOptions
import html_to_markdown._html_to_markdown as _rust

def patched_convert_with_visitor(html: str, options: ConversionOptions, visitor) -> str:
    """
    Workaround for bug in html_to_markdown.api.convert_with_visitor where options are ignored.
    """
    rust_opts = _rust.ConversionOptions()
    # Map fields manually
    if hasattr(options, 'bullets') and options.bullets:
        rust_opts.bullets = options.bullets
    if hasattr(options, 'list_indent_width') and options.list_indent_width is not None:
        rust_opts.list_indent_width = options.list_indent_width
    if hasattr(options, 'heading_style') and options.heading_style:
        rust_opts.heading_style = options.heading_style
    
    return _rust.convert_with_visitor(html, rust_opts, visitor)

class CodeBlockVisitor:
    def __init__(self, indent_width: int = 2):
        self.indent_width = indent_width

    def visit_code_block(self, ctx, language: Optional[str], code: str):
        """
        Handle code blocks to ensure proper language tagging and strip extra newlines.
        """
        lang = language if language else ""
        
        # Check for injected language marker from cleaner.py
        # Format: __MD_LANG={lang}__\n
        if code:
            match = re.match(r"^__MD_LANG=(.*?)__\n", code)
            if match:
                lang = match.group(1)
                code = code[match.end():]  # Remove marker
        
        # Check for raw blockquote marker (workaround for list indentation)
        if lang == "__RAW_BLOCKQUOTE__":
            # This is our manually formatted blockquote
            # We just need to indent it if inside list, but skip code block formatting
            output = f"\n{code.strip()}\n"
            
            if isinstance(ctx, dict) and ctx.get('parent_tag') == 'li':
                indent = " " * self.indent_width
                indented_lines = []
                for line in output.split('\n'):
                     if line:
                        indented_lines.append(indent + line)
                     else:
                        indented_lines.append(line)
                output = '\n'.join(indented_lines)
            
            return {"type": "custom", "output": output}

        # Strip leading/trailing whitespace from code to avoid extra newlines in markdown
        # Add newline before code block to ensure it separates from previous content
        # print(f"DEBUG: ctx={ctx} type={type(ctx)}")
        
        output = f"\n```{lang}\n{code.strip()}\n```\n"
        
        # If inside a list item, we need to indent the code block manually
        # because "custom" output type bypasses the library's indentation logic for children
        if isinstance(ctx, dict) and ctx.get('parent_tag') == 'li':
            indent = " " * self.indent_width
            # Indent all non-empty lines
            lines = output.split('\n')
            indented_lines = []
            for line in lines:
                if line:
                    indented_lines.append(indent + line)
                else:
                    indented_lines.append(line)
            output = '\n'.join(indented_lines)
            
        return {"type": "custom", "output": output}

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

    # 3.5. Preprocess tables to ensure they have a header (required for Markdown tables)
    for table in root.xpath('//table'):
        # Check if table has thead
        if table.find('thead') is not None:
            continue
            
        # Check for tbody or direct tr
        tbody = table.find('tbody')
        first_row = None
        
        if tbody is not None:
            rows = tbody.findall('tr')
            if rows:
                first_row = rows[0]
        else:
            rows = table.findall('tr')
            if rows:
                first_row = rows[0]
        
        if first_row is not None:
            # Create thead
            thead = html.Element('thead')
            # Insert thead before tbody or as first child
            if tbody is not None:
                table.insert(table.index(tbody), thead)
            else:
                table.insert(0, thead)
            
            # Move first row to thead
            thead.append(first_row)
            
            # Convert td to th in the header row for better semantics
            for td in first_row.findall('td'):
                td.tag = 'th'

    # 3.6. Preprocess blockquotes in lists (manual indentation workaround)
    # Workaround for html-to-markdown library issue where blockquotes in lists are not indented
    try:
        # Use list() to copy since we modify tree
        list_items = root.xpath('//li')
        for li in list_items:
            # Find blockquotes inside this li
            # We must use xpath relative to li
            bqs = li.xpath('.//blockquote')
            for bq in bqs:
                # Check if bq is still in tree (might be removed if nested)
                if bq.getparent() is None:
                    continue
                    
                # Get inner HTML
                parts = []
                if bq.text:
                    parts.append(bq.text)
                for child in bq:
                    parts.append(etree.tostring(child, encoding="unicode", method="html"))
                bq_inner_html = "".join(parts)
                
                if not bq_inner_html.strip():
                    continue

                # Recursive convert content
                # Note: This handles nested blockquotes correctly because recursive call will process them
                bq_md = convert_html_to_markdown(bq_inner_html, options)
                
                # Prefix with > 
                quoted_lines = []
                for line in bq_md.splitlines():
                    quoted_lines.append(f"> {line}")
                bq_md_quoted = "\n".join(quoted_lines)
                
                # Create replacement <pre><code class="language-__RAW_BLOCKQUOTE__">...</code></pre>
                pre = html.Element('pre')
                code_elem = html.Element('code')
                code_elem.set('class', 'language-__RAW_BLOCKQUOTE__')
                code_elem.text = bq_md_quoted
                pre.append(code_elem)
                
                # Preserve tail
                pre.tail = bq.tail
                
                # Replace
                parent = bq.getparent()
                parent.replace(bq, pre)
    except Exception as e:
        # If something fails in preprocessing, ignore and let standard conversion proceed
        print(f"Warning: Blockquote preprocessing failed: {e}")
        pass

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
        visitor = CodeBlockVisitor(indent_width=options.list_indent_spaces or 2)
        return patched_convert_with_visitor(cleaned_html, options=htm_options, visitor=visitor).strip()
    except Exception as e:
        # Fallback to basic conversion if visitor fails (e.g. RefCell panic)
        try:
            return htm_convert(cleaned_html, options=htm_options).strip()
        except Exception as e2:
             return f"Error converting to Markdown: {str(e)} (Fallback failed: {str(e2)})"
