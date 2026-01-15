
import sys
import os
from lxml import html, etree

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.cleaner import clean_html_tree
from html_to_markdown import convert as htm_convert, ConversionOptions

def hybrid_convert(html_content, domain=None):
    # 1. Parse and Clean
    try:
        # Create a document to handle fragments correctly
        root = html.fromstring(html_content)
    except Exception:
        # Fallback for fragments
        root = html.fragment_fromstring(html_content, create_parent="div")
        
    # 2. Domain absolute URLs
    if domain:
        root.make_links_absolute(domain)
        
    # 3. Clean
    clean_html_tree(root)
    
    # 4. Serialize back to HTML string
    cleaned_html = etree.tostring(root, encoding="unicode")
    
    # 5. Convert to Markdown
    options = ConversionOptions(
        heading_style="atx",
        list_indent_width=2,
        bullets="-*+",
    )
    return htm_convert(cleaned_html, options)

def run_tests():
    print("Running hybrid conversion tests...\n")
    
    test_cases = [
        {
            "name": "Link Rewrite & Cleaning",
            "html": '<p>Link <a href="/foo">foo</a></p><script>alert(1)</script>',
            "domain": "https://example.com"
        },
        {
            "name": "Nested List & Formatting",
            "html": '<ul><li>Item 1 <b>Bold</b><ul><li>Sub</li></ul></li></ul>',
            "domain": None
        }
    ]
    
    for case in test_cases:
        print(f"=== {case['name']} ===")
        res = hybrid_convert(case['html'], case['domain'])
        print(res)
        print("-" * 20)

if __name__ == "__main__":
    run_tests()
