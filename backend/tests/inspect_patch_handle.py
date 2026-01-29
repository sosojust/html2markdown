
from html_to_markdown.api import _rust, create_options_handle
from html_to_markdown import ConversionOptions
from typing import Optional

def patched_convert_with_visitor(html, options=None, preprocessing=None, visitor=None):
    handle = create_options_handle(options=options, preprocessing=preprocessing)
    return _rust.convert_with_visitor(html, handle, visitor)

class CodeBlockVisitor:
    def visit_code_block(self, ctx, language: Optional[str], code: str):
        lang = language if language else ""
        return {"type": "custom", "output": f"```{lang}\n{code.strip()}\n```\n"}

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
opts = ConversionOptions(bullets="*")
res = patched_convert_with_visitor(html, options=opts, visitor=CodeBlockVisitor())
print(f"Result with patched visitor (bullets='*'):\n{res}")
