from lxml import etree
import re

REMOVE_TAGS = {
    "script", "style", "noscript", "iframe", "svg", "template", "embed", "object", "applet", "area", "map", "source", "track", "param", "textarea"
}

def clean_html_tree(root: etree.Element) -> etree.Element:
    """
    预处理 DOM 树，彻底移除噪声节点
    """
    # 移除黑名单标签
    etree.strip_elements(root, *REMOVE_TAGS, with_tail=False)

    # 安全遍历：先收集再处理，避免迭代中修改导致跳过
    nodes = list(root.iter())
    
    for node in nodes:
        parent = node.getparent()
        if parent is None:
            continue
            
        # 0. 移除“复制”按钮文本
        # 常见的复制按钮文本或 class
        text = (node.text or "").strip()
        cls = (node.get("class") or "").lower()
        if text in ("复制代码", "Copy code", "Copy", "复制") or (("copy" in cls or "btn" in cls) and text in ("复制代码", "Copy", "复制")):
             if node.tail:
                prev = node.getprevious()
                if prev is not None:
                    prev.tail = (prev.tail or "") + node.tail
                else:
                    parent.text = (parent.text or "") + node.tail
             parent.remove(node)
             continue

        # 0.1 识别并规范化代码块语言
        # 如果 text 是简单的语言标识（如 "text", "python", "js"），且位于 pre/div[code] 的开头，可能是语言标记
        # 仅当它是独立节点时处理
        if node.tag in ("span", "div") and text and len(text) < 20 and parent.tag in ("pre", "div"):
            # 检查父容器是否像是代码块容器
            # 简单启发式：父容器有 pre 子节点，或者父容器本身就是 pre
            is_code_block_context = False
            if parent.tag == "pre":
                is_code_block_context = True
            elif "code" in (parent.get("class") or "").lower():
                is_code_block_context = True
            elif parent.xpath(".//pre"):
                is_code_block_context = True
            
            if is_code_block_context:
                 # 检查是否看起来像语言
                 # 简单列表，避免误伤
                 COMMON_LANGS = {"text", "txt", "python", "py", "javascript", "js", "java", "c", "cpp", "go", "rust", "html", "css", "bash", "sh", "shell", "sql", "json", "yaml", "xml", "mathematica", "matlab", "r", "ruby", "php", "swift", "kotlin", "typescript", "ts"}
                 if text.lower() in COMMON_LANGS:
                     # 尝试找到对应的 pre/code 元素
                     target_code = None
                     if parent.tag == "pre":
                         # 父级是 pre，寻找 code 子节点，或者自身就是 pre
                         # html-to-markdown 通常把 pre > code 视为代码块
                         # 如果 pre 直接包含文本，可能是代码块
                         # 如果我们在这里移除语言标记，并把它加到 pre 的 class 里？
                         # 或者加到 code 子节点里
                         code_child = parent.find("code")
                         if code_child is not None:
                             target_code = code_child
                         else:
                             # 如果没有 code 子节点，尝试为 pre 设置 class
                             # html-to-markdown 可能也会看 pre 的 class
                             target_code = parent
                     else:
                         # 父级是 wrapper，找 pre 兄弟或子节点
                         pre_node = parent.find("pre")
                         if pre_node is not None:
                             target_code = pre_node.find("code")
                             if target_code is None:
                                 target_code = pre_node # fallback to pre
                         else:
                             # 也许父级本身就是代码块的 wrapper，而代码块是兄弟节点？
                             # 例如 <div>Header</div> <pre>...</pre>
                             # 在遍历中，我们是在 div(header) 内部，还是 div(wrapper) 内部？
                             # 这里的 parent 是 div(wrapper)
                             # 所以上面的 pre_node = parent.find("pre") 应该能找到兄弟 pre
                             pass
                    
                     if target_code is not None:
                         # 移除当前语言节点
                         if node.tail:
                            prev = node.getprevious()
                            if prev is not None:
                                prev.tail = (prev.tail or "") + node.tail
                            else:
                                parent.text = (parent.text or "") + node.tail
                         
                         parent.remove(node)
                         
                         # 添加语言 class
                         current_cls = target_code.get("class") or ""
                         if f"language-{text}" not in current_cls and f"lang-{text}" not in current_cls:
                             target_code.set("class", (current_cls + f" language-{text}").strip())
                         continue
         
        # 0.2 处理 Case 4: 语言作为 pre 的前置兄弟节点
        # 结构：<div> <div class="header">lang</div> <pre>...</pre> </div>
        # node 是 header div/span
        if node.tag in ("div", "span", "p") and text and len(text) < 20:
             # 检查下一个兄弟是否是 pre
             next_sibling = node.getnext()
             # 跳过空文本节点
             while next_sibling is not None and isinstance(next_sibling, etree._Element) == False:
                 next_sibling = next_sibling.getnext()
             
             if next_sibling is not None and next_sibling.tag == "pre":
                 # 检查内容是否是语言
                 COMMON_LANGS = {"text", "txt", "python", "py", "javascript", "js", "java", "c", "cpp", "go", "rust", "html", "css", "bash", "sh", "shell", "sql", "json", "yaml", "xml", "mathematica", "matlab", "r", "ruby", "php", "swift", "kotlin", "typescript", "ts"}
                 if text.lower() in COMMON_LANGS:
                     target_code = next_sibling.find("code")
                     if target_code is None:
                         target_code = next_sibling
                     
                     # 移除当前语言节点
                     parent.remove(node)
                     
                     # 添加语言 class
                     current_cls = target_code.get("class") or ""
                     if f"language-{text}" not in current_cls and f"lang-{text}" not in current_cls:
                         target_code.set("class", (current_cls + f" language-{text}").strip())
                     continue

        # 0.3 处理 Case 5: 语言作为 pre 的首行文本
        # 这是最难的，因为 text 混在 pre.text 里
        # 仅处理 pre 节点
        if node.tag == "pre":
            text = (node.text or "")
            if text:
                # 尝试匹配首行是否是语言
                # 例如 "mathematica\ncode..."
                lines = text.splitlines()
                if lines:
                    first_line = lines[0].strip()
                    COMMON_LANGS = {"text", "txt", "python", "py", "javascript", "js", "java", "c", "cpp", "go", "rust", "html", "css", "bash", "sh", "shell", "sql", "json", "yaml", "xml", "mathematica", "matlab", "r", "ruby", "php", "swift", "kotlin", "typescript", "ts"}
                    
                    if first_line.lower() in COMMON_LANGS:
                        # 找到语言了！
                        lang = first_line
                        # 移除首行
                        # 剩余部分作为新的 text
                        # 注意 lines[1:] 重新组合时要保留换行
                        # 但 splitlines 丢掉了换行符，简单的 join 可能会改变原有换行
                        # 更稳妥的是找到第一个换行符的位置
                        
                        # 如果只有一行，那可能整个 pre 就是个语言标记？不太可能
                        # 假设至少有两行
                        newline_pos = text.find("\n")
                        if newline_pos != -1:
                            node.text = text[newline_pos+1:] # +1 to skip \n
                        else:
                            node.text = "" # 只有语言名？
                        
                        target_code = node.find("code")
                        if target_code is None:
                            target_code = node
                        
                        # 添加语言 class
                        current_cls = target_code.get("class") or ""
                        if f"language-{lang}" not in current_cls and f"lang-{lang}" not in current_cls:
                            target_code.set("class", (current_cls + f" language-{lang}").strip())
                        # 继续处理该节点（虽然 text 变了，但子节点还要遍历）

        # 0.4 处理 Case 5b: 语言作为 pre 内部的第一个 span/div 子节点
        # 结构：<pre><span>lang</span><code>...</code></pre>
        # 这种情况通常会被上面的 0.1 处理，因为 node 是 span，parent 是 pre
        # 但是如果 span 后面紧跟的是 code，我们需要确保逻辑覆盖
        # 上面的 0.1 已经处理了 node.tag in (span, div) and parent.tag == pre
        # 并且将 class 加到了 target_code (parent.find("code"))
        # 所以 Case 5b 应该已经被覆盖了，只要 "mathematica" 在 COMMON_LANGS 里


        # 1. 移除隐藏元素
        style = (node.get("style") or "").lower()
        cls = (node.get("class") or "").lower()
        if "display:none" in style or "display: none" in style or "visibility:hidden" in style or "hidden" in cls.split():
            if node.tail:
                prev = node.getprevious()
                if prev is not None:
                    prev.tail = (prev.tail or "") + node.tail
                else:
                    parent.text = (parent.text or "") + node.tail
            parent.remove(node)
            continue
        
        # 2. 移除 hidden input
        if node.tag == "input" and (node.get("type") or "").lower() == "hidden":
            if node.tail:
                prev = node.getprevious()
                if prev is not None:
                    prev.tail = (prev.tail or "") + node.tail
                else:
                    parent.text = (parent.text or "") + node.tail
            parent.remove(node)
            continue
            
        # 3. 移除 Base64 图片
        if node.tag == "img":
            src = node.get("src") or ""
            if src.startswith("data:"):
                if node.tail:
                    prev = node.getprevious()
                    if prev is not None:
                        prev.tail = (prev.tail or "") + node.tail
                    else:
                        parent.text = (parent.text or "") + node.tail
                parent.remove(node)
                continue
        
        # 4. 移除包含 JSON 数据的文本节点
        text = node.text or ""
        if text and ('"hotsearch":' in text or '"card_title":' in text or (text.strip().startswith("{") and text.strip().endswith("}"))):
            node.text = ""
            
        tail = node.tail or ""
        if tail and ('"hotsearch":' in tail or '"card_title":' in tail or (tail.strip().startswith("{") and tail.strip().endswith("}"))):
            node.tail = ""

        # 5. 清理属性（可选，防止 CSS 干扰，但保留 href/src/alt/title）
        # 这里只清理 style/id/on*，保留 class 以支持 language-*
        for attr in list(node.attrib.keys()):
            if attr in ("style", "id") or attr.startswith("on"):
                del node.attrib[attr]

    return root
