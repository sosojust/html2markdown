
from html_to_markdown.api import _options_payload, _rust
from html_to_markdown import ConversionOptions, PreprocessingOptions
import json
from typing import Optional

def patched_convert_with_visitor(html, options=None, preprocessing=None, visitor=None):
    if options is None:
        options = ConversionOptions()
    if preprocessing is None:
        preprocessing = PreprocessingOptions()
        
    payload = _options_payload(options, preprocessing)
    return _rust.convert_with_visitor(html, json.dumps(payload), visitor)

class CodeBlockVisitor:
    def visit_code_block(self, ctx, language: Optional[str], code: str):
        lang = language if language else ""
        return {"type": "custom", "output": f"```{lang}\n{code.strip()}\n```\n"}

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
opts = ConversionOptions(bullets="*")
res = patched_convert_with_visitor(html, options=opts, visitor=CodeBlockVisitor())
print(f"Result with patched visitor (bullets='*'):\n{res}")

html_code = '<pre><code class="language-python">def foo():\n    pass</code></pre>'
res_code = patched_convert_with_visitor(html_code, options=opts, visitor=CodeBlockVisitor())
print(f"Result code:\n{res_code}")
