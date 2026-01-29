
from html_to_markdown.api import _rust
from html_to_markdown import ConversionOptions as PyOptions
from typing import Optional

def patched_convert_with_visitor(html, options=None, preprocessing=None, visitor=None):
    # We need to create a _rust.ConversionOptions object manually and populate it
    # because we can't easily cast PyOptions (dataclass) to _rust.ConversionOptions
    
    rust_opts = _rust.ConversionOptions()
    if options:
        # Copy fields from dataclass to rust struct
        # Note: we need to map all relevant fields or just the ones we care about
        if hasattr(options, 'bullets'):
            rust_opts.bullets = options.bullets
        if hasattr(options, 'list_indent_width'):
            rust_opts.list_indent_width = options.list_indent_width
        # ... copy other fields if needed ...
        
    return _rust.convert_with_visitor(html, rust_opts, visitor)

class CodeBlockVisitor:
    def visit_code_block(self, ctx, language: Optional[str], code: str):
        lang = language if language else ""
        return {"type": "custom", "output": f"```{lang}\n{code.strip()}\n```\n"}

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
py_opts = PyOptions(bullets="*")
res = patched_convert_with_visitor(html, options=py_opts, visitor=CodeBlockVisitor())
print(f"Result with patched visitor (bullets='*'):\n{res}")
