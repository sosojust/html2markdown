from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

class BaseExporter(ABC):
    """
    Abstract base class for all exporters.
    Exporters take a Markdown string (produced by the core converter)
    and transform it into a target format (string or structured data).
    """

    @abstractmethod
    def export(self, markdown: str) -> Any:
        """
        Transform standard markdown to target format.
        
        Args:
            markdown: The input markdown string.
            
        Returns:
            The transformed content. 
            - For text-based targets (e.g., Obsidian), returns str.
            - For API-based targets (e.g., Notion), returns List[Dict] or similar structure.
        """
        pass
