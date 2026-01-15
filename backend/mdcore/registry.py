from typing import Callable, Dict, Tuple
from .types import TagType, Priority


Renderer = Callable[..., str]


class RendererRegistry:
    def __init__(self) -> None:
        self._map: Dict[str, Tuple[TagType, Renderer, Priority]] = {}

    def register(self, tag: str, tag_type: TagType, renderer: Renderer, priority: Priority = Priority.Standard) -> None:
        prev = self._map.get(tag)
        if prev is None or priority <= prev[2]:
            self._map[tag] = (tag_type, renderer, priority)

    def get(self, tag: str) -> Tuple[TagType, Renderer, Priority]:
        return self._map.get(tag, (TagType.Inline, None, Priority.Late))
