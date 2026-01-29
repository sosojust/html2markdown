
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown
from mdcore.types import ConvertOptions

test_cases = [
    {
        "name": "List with sub-paragraph",
        "html": """
<ul>
  <li>
    Item 1
    <p>Paragraph 2</p>
  </li>
</ul>
""",
        "expected_snippet": "  Paragraph 2" # Expect indentation (2 spaces default)
    },
    {
        "name": "List with code block",
        "html": """
<ul>
  <li>
    Item 1
    <pre><code>code</code></pre>
  </li>
</ul>
""",
        "expected_snippet": "  ```" # Expect indentation
    },
    {
        "name": "List with blockquote",
        "html": """
<ul>
  <li>
    Item 1
    <blockquote><p>Quote</p></blockquote>
  </li>
</ul>
""",
        "expected_snippet": "  > Quote"
    }
]

def run_tests():
    print("Running sub-paragraph alignment tests...\n")
    failed = False
    
    for case in test_cases:
        print(f"Testing: {case['name']}")
        res = convert_html_to_markdown(case['html'])
        print(f"Result:\n{res}")
        
        if case['expected_snippet'] in res:
            print("PASS")
        else:
            print(f"FAIL: Expected '{case['expected_snippet']}' in output")
            failed = True
        print("-" * 20)
    
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
