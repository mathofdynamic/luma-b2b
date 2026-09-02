const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function safeHref(value) {
  const href = String(value || "").trim();
  if (/^(https?:\/\/|\/repo\/|\/demo\/)/i.test(href)) return href;
  return "#";
}

function inline(value) {
  let result = escapeHtml(value);
  result = result.replace(/`([^`]+)`/g, "<code>$1</code>");
  result = result.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  result = result.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${escapeHtml(safeHref(href))}" target="_blank" rel="noopener noreferrer">${label}</a>`);
  return result;
}

export function renderMarkdown(markdown) {
  const source = String(markdown || "").replaceAll("\r\n", "\n");
  const lines = source.split("\n");
  const output = [];
  let paragraph = [];
  let listType = null;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    output.push(`<p>${paragraph.map(inline).join(" ")}</p>`);
    paragraph = [];
  };
  const closeList = () => {
    if (!listType) return;
    output.push(`</${listType}>`);
    listType = null;
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = Math.min(4, heading[1].length);
      output.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }
    if (/^([-*_])(?:\s*\1){2,}$/.test(trimmed)) {
      flushParagraph();
      closeList();
      output.push("<hr>");
      continue;
    }
    const bullet = trimmed.match(/^[-*+]\s+(.+)$/);
    const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (bullet || ordered) {
      flushParagraph();
      const desired = ordered ? "ol" : "ul";
      if (listType !== desired) {
        closeList();
        listType = desired;
        output.push(`<${listType}>`);
      }
      output.push(`<li>${inline((bullet || ordered)[1])}</li>`);
      continue;
    }
    if (trimmed.startsWith(">")) {
      flushParagraph();
      closeList();
      output.push(`<blockquote>${inline(trimmed.replace(/^>\s?/, ""))}</blockquote>`);
      continue;
    }
    paragraph.push(trimmed);
  }
  flushParagraph();
  closeList();
  return output.join("") || `<p class="empty-copy">متنی برای نمایش وجود ندارد.</p>`;
}

export { escapeHtml };
