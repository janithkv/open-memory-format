#!/usr/bin/env python3
"""Render spec/<version>/OMF-<version>-draft.md into spec/<version>/index.html.

The Markdown file is the source of truth; the HTML page is generated from it so
the two never drift. Requires markdown-it-py (`pip install markdown-it-py`).

    python3 scripts/build_spec.py 0.2
"""
import html
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
CSS_SOURCE = ROOT / "spec" / "0.1" / "index.html"  # the house style


def gh_slug(text: str, seen: dict) -> str:
    """GitHub's heading-anchor rule, so links work on GitHub and on the page."""
    slug = re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def inline_text(token) -> str:
    return "".join(c.content for c in (token.children or [])
                   if c.type in ("text", "code_inline"))


def house_css() -> str:
    src = CSS_SOURCE.read_text(encoding="utf-8")
    return "\n".join(re.findall(r"<style>.*?</style>", src, flags=re.S))


def build(version: str) -> Path:
    spec_dir = ROOT / "spec" / version
    md_path = spec_dir / f"OMF-{version}-draft.md"
    source = md_path.read_text(encoding="utf-8")

    # The first H1 is the masthead; the status blockquote right after it
    # becomes the highlighted note. Both are rendered separately.
    lines = source.split("\n")
    assert lines[0].startswith("# "), "spec must open with a # title"
    body_start = 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    note_lines = []
    while body_start < len(lines) and lines[body_start].startswith(">"):
        note_lines.append(lines[body_start].lstrip("> ").rstrip())
        body_start += 1
    body_md = "\n".join(lines[body_start:])

    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = md.parse(body_md)
    seen: dict = {}
    toc = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            text = inline_text(tokens[i + 1])
            slug = gh_slug(text, seen)
            tok.attrSet("id", slug)
            if tok.tag == "h2" and re.match(r"^\d+\. ", text):
                toc.append((slug, text.replace(". ", " · ", 1)))
            elif tok.tag == "h1":
                tok.tag = "h2"
                tokens[i + 2].tag = "h2"
                toc.append((slug, text.split(" — ")[0] + " · " +
                            text.split(" — ", 1)[-1]))
        if tok.type in ("link_open",):
            href = tok.attrGet("href") or ""
            # Repo-relative links to a spec's Markdown resolve to its page.
            href = re.sub(r"(\.\./)?(\d+\.\d+)/OMF-[\d.]+-draft\.md",
                          r"\1\2/", href)
            tok.attrSet("href", href)
    rendered = md.renderer.render(tokens, md.options, {})
    rendered = rendered.replace("<table>", '<div class="tbl"><table>')
    rendered = rendered.replace("</table>", "</table></div>")
    # "## 3. Journal days" → numbered heading in the house style.
    rendered = re.sub(r'(<h2 id="[^"]+">)(\d+)\. ',
                      r'\1<span class="num">\2</span>', rendered)

    note_html = MarkdownIt("commonmark").renderInline(" ".join(note_lines))
    note_html = re.sub(r'href="(\.\./)?(\d+\.\d+)/OMF-[\d.]+-draft\.md"',
                       r'href="\1\2/"', note_html)
    note_html = re.sub(r'href="#', 'class="secref" href="#', note_html)
    toc_html = "\n".join(
        f'      <li><a href="#{s}">{html.escape(t)}</a></li>' for s, t in toc)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Open Memory Format — {version} (Draft)</title>
<meta name="description" content="Open Memory Format {version}: an open, portable format for a personal memory vault, as plain Markdown files in storage you control." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
{house_css()}
<style>@media (max-width:600px){{ .wrap {{ padding:0 16px 96px; }} }}</style>
</head>
<body>
<div class="wrap">

  <header class="masthead">
    <p class="eyebrow">Open Memory Format</p>
    <h1>OMF&nbsp;{version}</h1>
    <p class="lede">An open, portable format for a personal memory vault: plain Markdown files, in storage you control, that any app can read and write.</p>
    <div class="badges">
      <span class="badge draft">Draft · unstable</span>
      <span class="badge">Version {version}</span>
      <span class="badge">CommonMark · YAML · Wikilinks</span>
    </div>
  </header>

  <div class="note">{note_html}</div>

  <nav class="toc">
    <p>Contents</p>
    <ol>
{toc_html}
    </ol>
  </nav>

{rendered}
  <footer>
    Open Memory Format {version} (draft) · generated from
    <a href="OMF-{version}-draft.md">OMF-{version}-draft.md</a> ·
    <a href="../../">Open Memory Format home</a>
  </footer>

</div>
</body>
</html>
"""
    out = spec_dir / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_spec.py <version>   e.g. 0.2")
    print(build(sys.argv[1]))
