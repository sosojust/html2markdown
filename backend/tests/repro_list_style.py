
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown
from mdcore.types import ConvertOptions

test_cases = [
    {
        "name": "Default list style",
        "html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
        "options": ConvertOptions(), # Default: marker='-', indent=2
        "expected": "- Item 1\n- Item 2"
    },
    {
        "name": "Asterisk marker",
        "html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
        "options": ConvertOptions(unordered_marker="*"),
        "expected": "* Item 1\n* Item 2"
    },
    {
        "name": "Plus marker",
        "html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
        "options": ConvertOptions(unordered_marker="+"),
        "expected": "+ Item 1\n+ Item 2"
    },
    {
        "name": "Indent 4 spaces",
        "html": "<ul><li>Item 1<ul><li>Subitem</li></ul></li></ul>",
        "options": ConvertOptions(list_indent_spaces=4),
        "expected": "- Item 1\n    - Subitem" # 4 spaces indent
    }
]

def run_tests():
    print("Running list style tests...\n")
    failed = False
    
    for case in test_cases:
        print(f"Testing: {case['name']}")
        res = convert_html_to_markdown(case['html'], case['options'])
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
