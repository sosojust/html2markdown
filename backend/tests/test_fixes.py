from mdcore.converter import convert_html_to_markdown

def test_br():
    md = convert_html_to_markdown("A<br>B")
    # html-to-markdown uses 2 spaces + newline for br
    assert md.replace("  \n", "\n") == "A\nB"

def test_hr():
    md = convert_html_to_markdown("A<hr>B")
    assert "---" in md

def test_strong_lambda():
    md = convert_html_to_markdown("<strong>S</strong>")
    assert md == "**S**"

def test_em_lambda():
    md = convert_html_to_markdown("<em>E</em>")
    assert md == "*E*"

def test_ul_lambda():
    html = "<ul><li>A</li><li>B</li></ul>"
    md = convert_html_to_markdown(html)
    assert "- A" in md
    assert "- B" in md
