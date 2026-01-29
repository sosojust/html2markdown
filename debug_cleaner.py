
from lxml import html, etree
from backend.mdcore.cleaner import clean_html_tree

def test_cleaner():
    html_str = '<pre data-language="python">def foo():\n    pass</pre>'
    root = html.fragment_fromstring(html_str, create_parent="div")
    
    print("Before clean:")
    print(etree.tostring(root, encoding="unicode", pretty_print=True))
    
    clean_html_tree(root)
    
    print("\nAfter clean:")
    print(etree.tostring(root, encoding="unicode", pretty_print=True))

if __name__ == "__main__":
    test_cleaner()
