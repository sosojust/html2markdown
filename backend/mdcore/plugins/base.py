from lxml import html, etree
from typing import Any
from ..types import TagType, Priority, ConvertOptions
from ..registry import RendererRegistry
from ..escape import escape_text


def render_html(node: etree.Element, options: ConvertOptions) -> str:
    return etree.tostring(node, encoding="unicode", with_tail=False)

def _render_input(node: etree.Element, convert, options: ConvertOptions, ctx) -> str:
    return ""


def register(reg: RendererRegistry) -> None:
    reg.register("script", TagType.Remove, None)
    reg.register("style", TagType.Remove, None)
    reg.register("meta", TagType.Remove, None)
    reg.register("link", TagType.Remove, None)
    reg.register("input", TagType.Inline, _render_input)
    reg.register("br", TagType.Inline, lambda n, c, o, x=None: "\n")
    reg.register("hr", TagType.Block, lambda n, c, o, x=None: "\n---\n")
