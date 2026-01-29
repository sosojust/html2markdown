from typing import List, Dict, Any
from ..base import BaseExporter
from .parser import MarkdownToNotionParser

class NotionExporter(BaseExporter):
    """
    Exporter for Notion format.
    Converts Markdown string to Notion Block objects (JSON/Dict).
    """
    def __init__(self):
        self.parser = MarkdownToNotionParser()

    def export(self, markdown: str) -> List[Dict[str, Any]]:
        return self.parser.parse(markdown)
