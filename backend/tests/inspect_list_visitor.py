
from html_to_markdown import convert_with_visitor, ConversionOptions

class ListVisitor:
    def visit_unordered_list(self, ctx, items):
        print(f"Items: {items}")
        # Manual list generation
        res = []
        for item in items:
            # item is presumably the markdown content of the list item
            res.append(f"* {item.strip()}")
        return {"type": "custom", "output": "\n".join(res) + "\n"}

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
opts = ConversionOptions(bullets="+") # Should be ignored by visitor if my theory is right
res = convert_with_visitor(html, options=opts, visitor=ListVisitor())
print(f"Result:\n{res}")
