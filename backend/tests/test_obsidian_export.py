
import unittest
from backend.mdcore.exporters.obsidian import ObsidianExporter

class TestObsidianExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = ObsidianExporter()

    def test_callout_conversion(self):
        # Case 1: Standard bold header in blockquote
        md = "> **Note**\n> This is a note."
        expected = "> [!NOTE]\n> This is a note."
        self.assertEqual(self.exporter.export(md), expected)

    def test_callout_with_colon(self):
        # Case 2: Bold header with colon
        md = "> **Warning**: Watch out!"
        expected = "> [!WARNING] Watch out!"
        self.assertEqual(self.exporter.export(md), expected)

    def test_nested_callout(self):
        # Case 3: Nested (though regex assumes start of line, let's see)
        # Our regex currently uses ^, so it handles top-level well.
        md = "Some text\n\n> **Tip**\n> Helpful info."
        expected = "Some text\n\n> [!TIP]\n> Helpful info."
        self.assertEqual(self.exporter.export(md), expected)

    def test_no_change(self):
        md = "> Just a quote."
        self.assertEqual(self.exporter.export(md), md)

if __name__ == '__main__':
    unittest.main()
