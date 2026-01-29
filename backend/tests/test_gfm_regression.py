
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown
from mdcore.types import ConvertOptions

class TestGFMRegression(unittest.TestCase):
    def test_list_with_code_block(self):
        """Task 1.2 regression"""
        html = """
        <ul>
          <li>
            Item 1
            <pre><code class="language-python">print("hello")</code></pre>
          </li>
        </ul>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("  ```python", result)
        self.assertIn("  print(\"hello\")", result)
        self.assertIn("  ```", result)

    def test_list_with_blockquote(self):
        html = """
        <ul>
          <li>
            Item 1
            <blockquote>
              <p>Quote inside list</p>
            </blockquote>
          </li>
        </ul>
        """
        # Usually represented as:
        # - Item 1
        #   > Quote inside list
        result = convert_html_to_markdown(html)
        print(f"Blockquote result:\n{result}")
        # Note: Implementation might vary, but indentation is key
        self.assertIn("  > Quote inside list", result)

    def test_nested_mixed_lists(self):
        html = """
        <ul>
          <li>Item 1
            <ol>
              <li>Ordered 1</li>
              <li>Ordered 2</li>
            </ol>
          </li>
        </ul>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("- Item 1", result)
        self.assertIn("  1. Ordered 1", result)

    def test_task_list_nested(self):
        html = """
        <ul>
          <li><input type="checkbox" checked> Done
            <ul>
               <li>Subtask</li>
            </ul>
          </li>
        </ul>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("- [x] Done", result)
        self.assertIn("  - Subtask", result)

    def test_table_basic(self):
        html = """
        <table>
          <thead>
            <tr><th>Head 1</th><th>Head 2</th></tr>
          </thead>
          <tbody>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
          </tbody>
        </table>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("| Head 1 | Head 2 |", result)
        self.assertIn("| --- | --- |", result)
        self.assertIn("| Cell 1 | Cell 2 |", result)

    def test_list_with_paragraphs(self):
        html = """
        <ul>
          <li>
            <p>Para 1</p>
            <p>Para 2</p>
          </li>
        </ul>
        """
        result = convert_html_to_markdown(html)
        print(f"Paragraph result:\n{result}")
        self.assertIn("- Para 1", result)
        # Check indentation of second paragraph
        # It usually comes after a blank line
        self.assertIn("  Para 2", result)

if __name__ == '__main__':
    unittest.main()
