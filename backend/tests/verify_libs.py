
import sys
import os

# Add backend directory to sys.path to import mdcore
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown as current_convert
from html_to_markdown import convert as htm_convert
from markdownify import markdownify as mdify_convert

test_cases = [
    {
        "name": "Basic Formatting",
        "html": "<p>Hello <strong>World</strong> <em>Italic</em></p>"
    },
    {
        "name": "Nested Lists",
        "html": """
        <ul>
            <li>Item 1
                <ul>
                    <li>SubItem 1.1</li>
                    <li>SubItem 1.2</li>
                </ul>
            </li>
            <li>Item 2</li>
        </ul>
        """
    },
    {
        "name": "Code Block",
        "html": '<pre><code class="language-python">def foo():\n    return "bar"</code></pre>'
    },
    {
        "name": "Table",
        "html": """
        <table>
            <thead>
                <tr>
                    <th>Head 1</th>
                    <th>Head 2</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Cell 1</td>
                    <td>Cell 2</td>
                </tr>
            </tbody>
        </table>
        """
    },
    {
        "name": "Link and Image",
        "html": '<p>Check <a href="https://example.com">this</a> and <img src="img.png" alt="Image"></p>'
    }
]

def run_tests():
    print("Running verification tests...\n")
    
    for case in test_cases:
        print(f"=== Test Case: {case['name']} ===")
        print(f"HTML Input:\n{case['html'].strip()}\n")
        
        try:
            res_current = current_convert(case['html'])
        except Exception as e:
            res_current = f"ERROR: {e}"
            
        try:
            res_htm = htm_convert(case['html'])
        except Exception as e:
            res_htm = f"ERROR: {e}"
            
        try:
            res_mdify = mdify_convert(case['html'])
        except Exception as e:
            res_mdify = f"ERROR: {e}"
            
        print("--- Current Implementation ---")
        print(res_current)
        print("\n--- html-to-markdown (Library) ---")
        print(res_htm)
        print("\n--- markdownify (Library) ---")
        print(res_mdify)
        print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    run_tests()
