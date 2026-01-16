from lxml import etree
import re

REMOVE_TAGS = {
    "script", "style", "noscript", "iframe", "svg", "template", "embed", "object", "applet", "area", "map", "source", "track", "param"
}

COMMON_LANGS = {"text", "txt", "python", "py", "javascript", "js", "java", "c", "cpp", "go", "rust", "html", "css", "bash", "sh", "shell", "sql", "json", "yaml", "xml", "mathematica", "matlab", "r", "ruby", "php", "swift", "kotlin", "typescript", "ts"}

def is_inside_tag(node: etree.Element, tag: str) -> bool:
    curr = node.getparent()
    while curr is not None:
        if curr.tag == tag:
            return True
        curr = curr.getparent()
    return False

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
            
        # 0. 移除“复制”按钮文本和语言标识头
        # 使用 string(.) 获取包含子节点的完整文本
        full_text = node.xpath("string(.)").strip()
        cls = (node.get("class") or "").lower()
        
        # 0.1 处理复制按钮
        if full_text in ("复制代码", "Copy code", "Copy", "复制") or (("copy" in cls or "btn" in cls) and full_text in ("复制代码", "Copy", "复制")):
             if node.tail:
                prev = node.getprevious()
                if prev is not None:
                    prev.tail = (prev.tail or "") + node.tail
                else:
                    parent.text = (parent.text or "") + node.tail
             parent.remove(node)
             continue

        # 0.2 规范化 pre 结构 (包含处理嵌套的语言标识)
        if node.tag == "pre":
            # 搜索潜在的语言标签 (排除 code 内部)
            found_lang = None
            for child in node.iter():
                 if child.tag in ("span", "div"):
                     # 确保它不在 code 内部
                     # 注意：此时 child 肯定在 pre 内部（因为我们遍历的是 pre 的子孙）
                     # 我们只需要检查它是否在 code 内部
                     if is_inside_tag(child, "code"):
                         continue
                     
                     full_text = child.xpath("string(.)").strip()
                     if full_text.lower() in COMMON_LANGS:
                         found_lang = full_text.lower()
                         break

            code_node = node.find(".//code")
            if code_node is not None:
                # 提取语言
                lang_cls = ""
                for c in (code_node.get("class") or "").split():
                    if c.startswith("language-") or c.startswith("lang-"):
                        lang_cls = c
                        break
                
                # 如果 code 没语言，看 pre 自身有没有
                if not lang_cls:
                    for c in (node.get("class") or "").split():
                        if c.startswith("language-") or c.startswith("lang-"):
                            lang_cls = c
                            break
                
                # 如果还没找到，使用搜索到的语言
                if not lang_cls and found_lang:
                    lang_cls = f"language-{found_lang}"
                
                # 清理 pre，只保留 code
                # 注意：我们需要保留 code 的内容
                # 简单做法：创建一个新的 code 节点，或者移动现有的
                new_code = etree.Element("code")
                if lang_cls:
                    new_code.set("class", lang_cls)
                
                # 复制内容
                new_code.text = code_node.xpath("string(.)")
                
                # 替换 pre 的所有内容
                # 不要使用 node.clear()，因为它会清除 pre 自身的属性
                for child in list(node):
                    node.remove(child)
                node.text = None
                node.append(new_code)
                if lang_cls:
                    node.set("class", (node.get("class") or "") + " " + lang_cls)
                
                # 既然已经处理了 pre 的内部结构，就不需要再对 pre 进行首行检测了
                continue

        # 0.3 处理 Case 4: 语言作为 pre 的前置兄弟节点
        # 结构：<div> <div class="header">lang</div> <pre>...</pre> </div>
        # node 是 header div/span
        text = (node.text or "").strip()
        if node.tag in ("div", "span", "p") and text and len(text) < 20:
             # 检查下一个兄弟是否是 pre
             next_sibling = node.getnext()
             # 跳过空文本节点
             while next_sibling is not None and isinstance(next_sibling, etree._Element) == False:
                 next_sibling = next_sibling.getnext()
             
             if next_sibling is not None and next_sibling.tag == "pre":
                 # 检查内容是否是语言
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

        # 0.4 处理 Case 5: 语言作为 pre 的首行文本
        # 这是最难的，因为 text 混在 pre.text 里
        # 仅处理 pre 节点
        if node.tag == "pre":
            text = (node.text or "")
            if text:
                # 尝试匹配首行是否是语言（跳过开头的空行）
                text_lstripped = text.lstrip()
                lines = text_lstripped.splitlines()
                if lines:
                    first_line = lines[0].strip()
                    if first_line.lower() in COMMON_LANGS:
                        # 找到语言了！
                        lang = first_line
                        
                        # 从原始 text 中移除语言行及其后的换行符
                        # 找到语言在原始 text 中的位置
                        lang_pos = text.find(lang)
                        # 找到该行末尾的换行符
                        newline_pos = text.find("\n", lang_pos)
                        
                        if newline_pos != -1:
                            node.text = text[newline_pos+1:] # +1 跳过 \n
                        else:
                            node.text = "" # 只有语言名
                        
                        target_code = node.find("code")
                        if target_code is None:
                            target_code = node
                        
                        # 添加语言 class
                        current_cls = target_code.get("class") or ""
                        if f"language-{lang}" not in current_cls and f"lang-{lang}" not in current_cls:
                            target_code.set("class", (current_cls + f" language-{lang}").strip())
                        # 继续处理该节点（虽然 text 变了，但子节点还要遍历）



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
