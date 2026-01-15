from typing import Optional, Set
from pydantic import BaseModel


class ConvertOptions(BaseModel):
    domain: Optional[str] = None
    collapse_whitespace: bool = True
    remove_tags: Optional[Set[str]] = None
    keep_tags: Optional[Set[str]] = None
    strong_delimiter: str = "**"
    emphasis_delimiter: str = "*"
    code_fence: str = "```"
    image_alt_fallback: bool = True
    table_alignment: Optional[str] = None
    unknown_tag_strategy: str = "inline_text"
    expand_to_block_boundaries: bool = True
    table_incomplete_strategy: str = "wrap_html"
    list_incomplete_strategy: str = "expand_item"
    unordered_marker: str = "-"
    list_indent_spaces: int = 2
