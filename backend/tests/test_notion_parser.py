
import unittest
from backend.mdcore.exporters.notion.parser import MarkdownToNotionParser

class TestNotionParser(unittest.TestCase):
    def setUp(self):
        self.parser = MarkdownToNotionParser()

    def test_paragraph(self):
        md = "Hello World"
        blocks = self.parser.parse(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "paragraph")
        self.assertEqual(blocks[0]["paragraph"]["rich_text"][0]["text"]["content"], "Hello World")

    def test_heading(self):
        md = "# Heading 1\n## Heading 2"
        blocks = self.parser.parse(md)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["type"], "heading_1")
        self.assertEqual(blocks[1]["type"], "heading_2")

    def test_inline_style(self):
        md = "Bold **text** and *italic*"
        blocks = self.parser.parse(md)
        # Should be one paragraph with multiple text objects
        # "Bold ", "text" (bold), " and ", "italic" (italic)
        rich_text = blocks[0]["paragraph"]["rich_text"]
        self.assertEqual(len(rich_text), 4)
        self.assertTrue(rich_text[1]["annotations"]["bold"])
        self.assertTrue(rich_text[3]["annotations"]["italic"])

    def test_list(self):
        md = "- Item 1\n- Item 2"
        blocks = self.parser.parse(md)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["type"], "bulleted_list_item")
        self.assertEqual(blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"], "Item 1")

    def test_nested_list(self):
        md = "- Parent\n  - Child"
        blocks = self.parser.parse(md)
        # Should be 1 block (Parent) with children (Child)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "bulleted_list_item")
        self.assertTrue(blocks[0].get("has_children"))
        self.assertEqual(len(blocks[0]["bulleted_list_item"]["children"]), 1)
        self.assertEqual(blocks[0]["bulleted_list_item"]["children"][0]["bulleted_list_item"]["rich_text"][0]["text"]["content"], "Child")

    def test_code_block(self):
        md = "```python\nprint('hi')\n```"
        blocks = self.parser.parse(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "code")
        self.assertEqual(blocks[0]["code"]["language"], "python")
        self.assertEqual(blocks[0]["code"]["rich_text"][0]["text"]["content"], "print('hi')\n")

if __name__ == '__main__':
    unittest.main()
