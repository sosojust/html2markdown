from typing import List, Dict, Any, Optional, Union
from markdown_it import MarkdownIt
from markdown_it.token import Token
# from .exporter import NotionExporter # Removed circular import

class MarkdownToNotionParser:
    """
    Parses standard Markdown string into Notion Block objects using markdown-it-py.
    """
    def __init__(self):
        self.md = MarkdownIt()

    def parse(self, markdown: str) -> List[Dict[str, Any]]:
        tokens = self.md.parse(markdown)
        blocks = []
        i = 0
        while i < len(tokens):
            result, new_i = self._process_token(tokens, i)
            if result:
                if isinstance(result, list):
                    blocks.extend(result)
                else:
                    blocks.append(result)
            i = new_i
        return blocks

    def _process_token(self, tokens: List[Token], index: int) -> tuple[Union[Dict[str, Any], List[Dict[str, Any]], None], int]:
        token = tokens[index]
        
        # Mapping token types to Notion blocks
        if token.type == 'heading_open':
            return self._process_heading(tokens, index)
        elif token.type == 'paragraph_open':
            return self._process_paragraph(tokens, index)
        elif token.type == 'bullet_list_open':
            return self._process_list(tokens, index, 'bulleted_list_item')
        elif token.type == 'ordered_list_open':
            return self._process_list(tokens, index, 'numbered_list_item')
        elif token.type == 'fence' or token.type == 'code_block':
            return self._process_code(token), index + 1
        elif token.type == 'blockquote_open':
            return self._process_blockquote(tokens, index)
        elif token.type == 'hr':
            return {"object": "block", "type": "divider", "divider": {}}, index + 1
        
        # Skip unknown or closing tokens at root level
        return None, index + 1

    def _extract_inline_content(self, tokens: List[Token]) -> List[Dict[str, Any]]:
        """
        Convert inline tokens (text, bold, italic, link) to Notion Rich Text objects.
        """
        rich_text = []
        # Inline token usually contains children
        # But markdown-it structure: block_open -> inline -> block_close
        # The 'inline' token has .children which are text, strong_open, etc.
        
        # Simplified: We assume we are passed the 'inline' token's children, or we handle the inline token itself.
        # Actually, the caller should pass the list of inline tokens found inside a block.
        return rich_text # Placeholder

    def _process_heading(self, tokens: List[Token], index: int) -> tuple[Dict[str, Any], int]:
        token = tokens[index] # heading_open
        level = 0
        if token.tag == 'h1': level = 1
        elif token.tag == 'h2': level = 2
        elif token.tag == 'h3': level = 3
        else: level = 3 # Notion only supports h1-h3

        # Next token should be inline
        inline_token = tokens[index + 1]
        text_content = self._render_inline(inline_token)
        
        block_type = f"heading_{level}"
        block = {
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": text_content
            }
        }
        return block, index + 3 # open, inline, close

    def _process_paragraph(self, tokens: List[Token], index: int) -> tuple[Dict[str, Any], int]:
        # paragraph_open -> inline -> paragraph_close
        # Sometimes empty paragraph (newline)
        if index + 1 >= len(tokens):
             return None, index + 1
             
        inline_token = tokens[index + 1]
        if inline_token.type != 'inline':
             # Should not happen in standard md
             return None, index + 1
             
        text_content = self._render_inline(inline_token)
        
        # Check if it's actually a task list item (checkbox)? 
        # Markdown-it handles task lists as list items, not paragraphs usually.
        
        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": text_content
            }
        }
        return block, index + 3

    def _process_code(self, token: Token) -> Dict[str, Any]:
        content = token.content
        lang = token.info.strip() if token.info else "plain text"
        
        # Notion languages are limited, map generic ones or keep as is
        # Truncate content if too long (Notion limit is 2000 chars per text object)
        # We split into multiple text objects if needed, but for code block rich_text, 
        # it's an array of text objects.
        
        rich_text = self._chunk_text(content)
        
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": rich_text,
                "language": lang if lang else "plain text"
            }
        }

    def _process_blockquote(self, tokens: List[Token], index: int) -> tuple[Dict[str, Any], int]:
        # blockquote_open -> ... -> blockquote_close
        # Notion Quote block supports children, but simplified: just text content?
        # Let's try to extract text from immediate children paragraphs.
        
        # Find close token
        close_index = index
        depth = 0
        for i in range(index, len(tokens)):
            if tokens[i].type == 'blockquote_open': depth += 1
            elif tokens[i].type == 'blockquote_close': depth -= 1
            
            if depth == 0:
                close_index = i
                break
        
        # Extract content between open and close
        inner_tokens = tokens[index+1 : close_index]
        # Flatten text for now
        text_content = []
        for t in inner_tokens:
            if t.type == 'inline':
                text_content.extend(self._render_inline(t))
        
        if not text_content:
            text_content = [{"type": "text", "text": {"content": " "}}]

        block = {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": text_content
            }
        }
        return block, close_index + 1

    def _process_list(self, tokens: List[Token], index: int, notion_type: str) -> tuple[Dict[str, Any], int]:
        # Notion represents lists as individual blocks, not a container.
        # But markdown-it has `bullet_list_open` -> `list_item_open` ...
        
        # We need to flatten this structure.
        # Actually, `_process_token` is called by the main loop.
        # If we return a list of blocks, the main loop needs to handle it.
        # But for now, let's just skip the container tags and process items directly?
        # No, because we need to know the type (bullet vs number).
        
        # Strategy: When we see `bullet_list_open`, we don't return a block.
        # We assume the caller (main loop) will proceed to next tokens.
        # But we need to inform the loop about the list type context?
        
        # Simpler Strategy: Recursively process the list content here and return a LIST of blocks.
        # And update `parse` to handle a list of blocks returned.
        
        blocks = []
        current_i = index + 1
        while current_i < len(tokens):
            t = tokens[current_i]
            if t.type == 'bullet_list_close' or t.type == 'ordered_list_close':
                return blocks, current_i + 1
            
            if t.type == 'list_item_open':
                # Process item content
                # Usually paragraph_open -> inline -> paragraph_close
                # or just text?
                # We need to look ahead for the content.
                # Assuming simple list item with one paragraph for now.
                
                # Find content
                # We iterate until list_item_close
                item_blocks = []
                j = current_i + 1
                while j < len(tokens):
                    sub_t = tokens[j]
                    if sub_t.type == 'list_item_close':
                        current_i = j
                        break
                    
                    # If we find a paragraph, extract its inline content and make it the list item text
                    if sub_t.type == 'paragraph_open':
                         # Extract inline
                         inline = tokens[j+1]
                         text_content = self._render_inline(inline)
                         
                         block = {
                             "object": "block",
                             "type": notion_type,
                             notion_type: {
                                 "rich_text": text_content
                             }
                         }
                         item_blocks.append(block)
                         j += 2 # skip open, inline, close (wait, need to verify indices)
                         # paragraph_open(j), inline(j+1), paragraph_close(j+2)
                    
                    # Handle nested lists?
                    elif sub_t.type == 'bullet_list_open':
                        nested, new_j = self._process_list(tokens, j, 'bulleted_list_item')
                        # Notion supports children in list items.
                        # But here we are flat. 
                        # To support nesting, we would need to attach `nested` blocks as `children` to the PREVIOUS block.
                        if item_blocks:
                            parent = item_blocks[-1]
                            parent[parent["type"]]["children"] = nested
                            parent["has_children"] = True
                        else:
                            # Orphaned nested list? Just append
                            item_blocks.extend(nested)
                        j = new_j - 1 # loop increment will fix
                        
                    elif sub_t.type == 'ordered_list_open':
                        nested, new_j = self._process_list(tokens, j, 'numbered_list_item')
                        if item_blocks:
                            parent = item_blocks[-1]
                            parent[parent["type"]]["children"] = nested
                            parent["has_children"] = True
                        else:
                            item_blocks.extend(nested)
                        j = new_j - 1

                    j += 1
                
                blocks.extend(item_blocks)
            
            current_i += 1
            
        return blocks, current_i 
        
    # Refined main loop helper for lists
    def _render_inline(self, token: Token) -> List[Dict[str, Any]]:
        # token.children contains: text, strong_open, text, strong_close, etc.
        if not token.children:
            return [{"type": "text", "text": {"content": token.content}}]

        result = []
        current_style = {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "code": False,
            "url": None
        }
        
        for child in token.children:
            if child.type == 'text':
                annotations = {
                    "bold": current_style["bold"],
                    "italic": current_style["italic"],
                    "strikethrough": current_style["strikethrough"],
                    "code": current_style["code"],
                    "color": "default"
                }
                text_obj = {
                    "type": "text",
                    "text": {
                        "content": child.content
                    },
                    "annotations": annotations
                }
                if current_style["url"]:
                    text_obj["text"]["link"] = {"url": current_style["url"]}
                
                result.append(text_obj)
            elif child.type == 'strong_open': current_style["bold"] = True
            elif child.type == 'strong_close': current_style["bold"] = False
            elif child.type == 'em_open': current_style["italic"] = True
            elif child.type == 'em_close': current_style["italic"] = False
            elif child.type == 's_open': current_style["strikethrough"] = True
            elif child.type == 's_close': current_style["strikethrough"] = False
            elif child.type == 'code_inline':
                # code_inline doesn't have open/close, it's self-contained
                result.append({
                    "type": "text",
                    "text": {"content": child.content},
                    "annotations": {"code": True, "color": "default"}
                })
            elif child.type == 'link_open':
                href = child.attrs.get('href', '')
                current_style["url"] = href
            elif child.type == 'link_close':
                current_style["url"] = None
        
        return result

    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        # Notion limit 2000 chars per text object
        chunks = []
        for i in range(0, len(text), 2000):
            chunks.append({
                "type": "text",
                "text": {"content": text[i:i+2000]}
            })
        return chunks

# Update NotionExporter to use Parser
