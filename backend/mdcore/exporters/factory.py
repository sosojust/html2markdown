from typing import Dict, Type
from .base import BaseExporter
from .obsidian import ObsidianExporter
from .notion.exporter import NotionExporter

class ExporterFactory:
    _exporters: Dict[str, Type[BaseExporter]] = {
        "obsidian": ObsidianExporter,
        "notion": NotionExporter,
        # "markdown": None # Default handling (pass-through)
    }

    @staticmethod
    def get_exporter(target: str) -> BaseExporter:
        exporter_cls = ExporterFactory._exporters.get(target)
        if exporter_cls:
            return exporter_cls()
        return None
