
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from html_to_markdown import convert_with_visitor, ConversionOptions

class CodeBlockVisitor:
    def visit_pre(self, ctx, node):
        # Check for code child
        # Note: I need to know what 'node' exposes.
        # The documentation snippet didn't detail the node API, but usually it's similar to DOM.
        # However, let's see if we can just return a string or dict.
        # "return {'type': 'continue'}" was in the snippet.
        pass

# Since I don't know the exact API of the visitor node, I'll first try to inspect it.
# Or I can look for more docs.
# But for now, let's just use the basic convert. 
# If the user is okay with "Verify first", I have verified that it works well generally.
# The missing language in code blocks is a detail I can probably solve.
# Actually, let's check if the library supports language extraction out of the box.
# Maybe I need to pass a specific option?

# Let's try to verify if it extracts language if I use `data-language` attribute.
test_cases = [
    {
        "name": "Class Language",
        "html": '<pre><code class="language-python">print("hi")</code></pre>'
    },
    {
        "name": "Data Language",
        "html": '<pre data-language="python"><code>print("hi")</code></pre>'
    }
]

def run_tests():
    print("Running language detection tests...\n")
    
    options = ConversionOptions()
    
    for case in test_cases:
        print(f"=== {case['name']} ===")
        res = convert_with_visitor(case['html'], None, options) # Passing None as visitor just to use the function? No, convert() is enough.
        # Using simple convert
        from html_to_markdown import convert
        res = convert(case['html'], options)
        print(res)
        print("-" * 20)

if __name__ == "__main__":
    run_tests()
