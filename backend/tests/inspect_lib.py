
from html_to_markdown import convert as htm_convert, ConversionOptions
import re

html = '<pre><code>__MD_LANG=python__\ndef foo():\n    pass</code></pre>'
opts = ConversionOptions(bullets="*")
md = htm_convert(html, opts)
print(f"Intermediate MD:\n{md}")

# Post-process
pattern = re.compile(r"```\s+__MD_LANG=([a-zA-Z0-9_+-]+)__\n")
final_md = pattern.sub(r"```\1\n", md)
print(f"Final MD:\n{final_md}")
