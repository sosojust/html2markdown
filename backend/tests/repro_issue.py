
import sys
import os
from lxml import html, etree

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mdcore.converter import convert_html_to_markdown

def run_tests():
    print("Running reproduction tests...\n")
    
    # 模拟用户描述的结构
    # 假设结构如下（基于常见网页结构推测）：
    html_content = """
    <div class="code-wrapper">
        <div class="code-header">
            <span class="language">text</span>
            <span class="copy-btn">复制代码</span>
        </div>
        <pre><code class="language-text">规则转换（本地）
   ↓
低质量片段识别
   ↓
发送给 LLM
   ↓
局部修复 Markdown</code></pre>
    </div>
    """
    
    # 另一种可能的结构（直接在 pre 里）
    # Case 2 中的 text 节点被保留，因为它在 pre 里
    # 我们希望 cleaner 能识别并提取它
    html_content_2 = """
    <pre>
        <span class="lang">text</span>
        <span class="copy">复制代码</span>
        <code>content</code>
    </pre>
    """
    
    # Case 3: 用户反馈的可能结构
    # text 是 pre 的直接子文本？但如果是 pre 的文本，通常会被作为代码内容
    # 如果 text 是 span，cleaner 应该能处理
    html_content_3 = """
    <pre><span class="lang">text</span> <span>复制代码</span> <code>content</code></pre>
    """

    
    # Case 4: 用户反馈的 mathematica 案例
    # 语言标签在 pre 外部，作为兄弟节点
    # 注意：我们的修复是基于 element.getnext()，所以需要确保在 DOM 树中是正确的兄弟关系
    html_content_4 = """
    <div>
        <div class="header">mathematica</div>
        <pre><code>some code</code></pre>
    </div>
    """
    
    # Case 5: 语言标签在 pre 内部，作为首个子节点 (文本节点)
    # 这种情况最难，因为 text 是 pre 的 text 属性，而不是独立的 element
    # html-to-markdown 会直接渲染文本
    # 如果 text 是独立行，或许可以通过正则处理？
    # 但我们的 cleaner 基于 lxml tree，操作 text 比较微妙
    # 暂时 Case 5 可能无法通过 element 移除，除非我们检查 pre.text
    html_content_5 = """
    <pre>mathematica
    <code>some code</code>
    </pre>
    """
    
    # Case 5b: 语言标签在 pre 内部，包裹在 span/div 中
    html_content_5b = """
    <pre><span>mathematica</span>
    <code>some code</code>
    </pre>
    """

    print("=== Case 1 ===")
    print(convert_html_to_markdown(html_content))
    
    print("\n=== Case 2 ===")
    print(convert_html_to_markdown(html_content_2))
    
    print("\n=== Case 3 ===")
    print(convert_html_to_markdown(html_content_3))
    
    print("\n=== Case 4 ===")
    # 预期输出 ```mathematica
    print(convert_html_to_markdown(html_content_4))

    print("\n=== Case 5 ===")
    # 预期输出 ```mathematica (如果支持)
    print(convert_html_to_markdown(html_content_5))
    
    print("\n=== Case 5b ===")
    # 预期输出 ```mathematica
    print(convert_html_to_markdown(html_content_5b))

if __name__ == "__main__":
    run_tests()
