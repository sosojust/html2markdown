function expandRangeToBlocks(range) {
  let start = range.startContainer.nodeType === Node.ELEMENT_NODE ? range.startContainer : range.startContainer.parentElement;
  let end = range.endContainer.nodeType === Node.ELEMENT_NODE ? range.endContainer : range.endContainer.parentElement;
  const startBlock = start.closest('p,div,section,article,li,pre,blockquote,h1,h2,h3,h4,h5,h6,td,th,tr,table,ul,ol') || start;
  const endBlock = end.closest('p,div,section,article,li,pre,blockquote,h1,h2,h3,h4,h5,h6,td,th,tr,table,ul,ol') || end;
  const r = document.createRange();
  r.setStartBefore(startBlock);
  r.setEndAfter(endBlock);
  return r;
}

function getSelectedHtml(expand) {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return null;
  let range = sel.getRangeAt(0).cloneRange();
  if (expand) range = expandRangeToBlocks(range);
  const container = document.createElement('div');
  container.appendChild(range.cloneContents());
  return container.innerHTML;
}

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg.type === "convert-selection") {
    const html = getSelectedHtml(!!msg.expand);
    respond({ html });
    return true;
  }
});
