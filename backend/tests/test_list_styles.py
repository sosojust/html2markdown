
import unittest
from backend.mdcore.converter import convert_html_to_markdown
from backend.mdcore.types import ConvertOptions

class TestListStyles(unittest.TestCase):
    def test_unordered_marker_asterisk(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        options = ConvertOptions(unordered_marker="*")
        result = convert_html_to_markdown(html, options)
        expected = "* Item 1\n* Item 2"
        self.assertEqual(result, expected)

    def test_unordered_marker_plus(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        options = ConvertOptions(unordered_marker="+")
        result = convert_html_to_markdown(html, options)
        expected = "+ Item 1\n+ Item 2"
        self.assertEqual(result, expected)

    def test_unordered_marker_dash(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        options = ConvertOptions(unordered_marker="-")
        result = convert_html_to_markdown(html, options)
        expected = "- Item 1\n- Item 2"
        self.assertEqual(result, expected)

    def test_list_indent_spaces_4(self):
        html = "<ul><li>Item 1<ul><li>SubItem A</li></ul></li></ul>"
        options = ConvertOptions(list_indent_spaces=4, unordered_marker="-")
        result = convert_html_to_markdown(html, options)
        # Assuming nested list indentation follows the rule
        # Note: html-to-markdown library behavior might vary on how it indents nested lists
        print(f"Result (indent 4):\n{result}")
        # Standard expectation: 4 spaces for nested item
        self.assertIn("    - SubItem A", result)

    def test_list_indent_spaces_2(self):
        html = "<ul><li>Item 1<ul><li>SubItem A</li></ul></li></ul>"
        options = ConvertOptions(list_indent_spaces=2, unordered_marker="-")
        result = convert_html_to_markdown(html, options)
        print(f"Result (indent 2):\n{result}")
        # Standard expectation: 2 spaces for nested item
        self.assertIn("  - SubItem A", result)

if __name__ == '__main__':
    unittest.main()
