import re
from .base import BaseExporter

class ObsidianExporter(BaseExporter):
    """
    Exporter for Obsidian format.
    Handles Callouts, MathJax, and WikiLinks adjustments.
    """
    def export(self, markdown: str) -> str:
        """
        Transforms standard Markdown into Obsidian-flavored Markdown.
        """
        content = markdown

        # 1. Convert Callouts
        # Standard pattern: "> **Note**" or "> **Warning**" inside a blockquote
        # Target: "> [!NOTE]" or "> [!WARNING]"
        # Regex to find blockquotes starting with bolded text
        # Matches: > **Type** ... or > **Type**: ...
        
        def callout_replacer(match):
            # match.group(1) is the indentation (if any) and >
            # match.group(2) is the type (e.g. Note, Warning)
            # match.group(3) is the rest of the line
            prefix = match.group(1)
            ctype = match.group(2).upper()
            rest = match.group(3)
            return f"{prefix} [!{ctype}]{rest}"

        # Regex explanation:
        # ^(\s*>)       : Start of line, optional whitespace, then >
        # \s*           : Optional whitespace
        # \*\*(.+?)\*\* : Bolded text (captured as type)
        # :?            : Optional colon
        # (.*)          : Rest of the line
        pattern = re.compile(r'^(\s*>)\s*\*\*(.+?)\*\*:?(.*)', re.MULTILINE)
        content = pattern.sub(callout_replacer, content)

        # 2. MathJax Compatibility
        # Ensure that if we have specific math markers, they are compatible.
        # (Currently assuming input is already reasonably standard, Obsidian handles $ and $$ well)
        
        # 3. Image Links
        # Obsidian can handle standard ![](url), but prefers ![[image.png]] for local.
        # For web clips, standard Markdown links are actually better (remote URLs).
        # So we keep standard links.

        return content
