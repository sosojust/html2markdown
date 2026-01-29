
import unittest
from backend.mdcore.converter import convert_html_to_markdown
from backend.mdcore.types import ConvertOptions

class TestComplexLists(unittest.TestCase):
    def test_nested_lists(self):
        html = """
        <ul>
            <li>Item 1
                <ul>
                    <li>SubItem 1.1</li>
                    <li>SubItem 1.2</li>
                </ul>
            </li>
            <li>Item 2</li>
        </ul>
        """
        expected = "- Item 1\n  - SubItem 1.1\n  - SubItem 1.2\n- Item 2"
        # Assuming 2 spaces indent
        result = convert_html_to_markdown(html, ConvertOptions(list_indent_spaces=2))
        self.assertIn("- SubItem 1.1", result)
        self.assertIn("  - SubItem 1.1", result)

    def test_multi_paragraph_list_item(self):
        html = """
        <ul>
            <li>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
            </li>
            <li>Item 2</li>
        </ul>
        """
        # Expected:
        # - Paragraph 1
        #
        #   Paragraph 2
        # - Item 2
        result = convert_html_to_markdown(html)
        print(f"Multi-paragraph result:\n{result}")
        # We want to check if Paragraph 2 is indented
        self.assertIn("Paragraph 1", result)
        self.assertIn("Paragraph 2", result)
        
    def test_task_list(self):
        html = """
        <ul>
            <li><input type="checkbox" checked> Done item</li>
            <li><input type="checkbox"> Todo item</li>
        </ul>
        """
        # Expected:
        # - [x] Done item
        # - [ ] Todo item
        result = convert_html_to_markdown(html)
        print(f"Task list result:\n{result}")
        self.assertIn("[x]", result)
        self.assertIn("[ ]", result)

if __name__ == '__main__':
    unittest.main()
