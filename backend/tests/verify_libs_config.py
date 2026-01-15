
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from html_to_markdown import convert as htm_convert, ConversionOptions

test_cases = [
    {
        "name": "Code Block with Language",
        "html": '<pre><code class="language-python">def foo():\n    return "bar"</code></pre>'
    },
    {
        "name": "Nested Lists",
        "html": """
        <ul>
            <li>Item 1.1 (Text with dot)</li>
            <li>Item 2</li>
        </ul>
        """
    }
]

def run_tests():
    print("Running config tests for html-to-markdown...\n")
    
    # Try to configure for GFM-like behavior if possible
    # Note: The search result didn't explicitly list a "fenced code block" option, 
    # but hinted at "code_language". Let's see if it auto-detects.
    
    # The search result said:
    # ConversionOptions – Key configuration fields:
    # heading_style: ...
    # list_indent_width: ...
    # bullets: ...
    # wrap: ...
    # code_language: Default fenced code block language
    
    # It doesn't explicitly say "use_fenced_code_block". 
    # But usually Rust libraries (like pulldown-cmark) are compliant.
    
    options = ConversionOptions(
        heading_style="atx",
        list_indent_width=2,
        bullets="-*+",
    )
    
    for case in test_cases:
        print(f"=== Test Case: {case['name']} ===")
        print(f"HTML Input:\n{case['html'].strip()}\n")
        
        try:
            res = htm_convert(case['html'], options)
            print("--- html-to-markdown Output ---")
            print(res)
        except Exception as e:
            print(f"ERROR: {e}")
            
        print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    run_tests()
