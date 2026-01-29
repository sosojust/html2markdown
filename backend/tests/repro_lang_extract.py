
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown
from mdcore.types import ConvertOptions

test_cases = [
    {
        "name": "Pre data-language",
        "html": '<pre data-language="python">def foo():\n    pass</pre>',
        "expected": "```python"
    },
    {
        "name": "Code data-language",
        "html": '<pre><code data-language="javascript">console.log("hello")</code></pre>',
        "expected": "```javascript"
    },
    {
        "name": "Pre class language-",
        "html": '<pre class="language-rust">fn main() {}</pre>',
        "expected": "```rust"
    },
    {
        "name": "Child element indicator",
        "html": '<pre><div class="lang">Python</div>def foo(): pass</pre>',
        "expected": "```python"
    }
]

def run_tests():
    print("Running language extraction tests...\n")
    failed = False
    
    for case in test_cases:
        print(f"Testing: {case['name']}")
        res = convert_html_to_markdown(case['html'])
        print(f"Result:\n{res}")
        
        if case['expected'] in res:
            print("PASS")
        else:
            print(f"FAIL: Expected '{case['expected']}' in output")
            failed = True
        print("-" * 20)
    
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
