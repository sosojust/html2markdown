
from html_to_markdown import convert as htm_convert, ConversionOptions

html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
opts = ConversionOptions(bullets="*", list_indent_width=4)
res = htm_convert(html, opts)
print(f"Options: bullets='*', indent=4\nResult:\n{res}")

opts2 = ConversionOptions(bullets="+", list_indent_width=4)
res2 = htm_convert(html, opts2)
print(f"Options: bullets='+', indent=4\nResult:\n{res2}")
