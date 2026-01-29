
from html_to_markdown import convert_with_visitor, ConversionOptions

class DiscoveryVisitor:
    def visit_unordered_list(self, ctx, items):
        print("visit_unordered_list called")
        return {"type": "continue"}

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
opts = ConversionOptions(bullets="+")
res = convert_with_visitor(html, options=opts, visitor=DiscoveryVisitor())
print(f"Result:\n{res}")
