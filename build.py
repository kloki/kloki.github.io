#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["mistune>=3"]
# ///

"""Build index.html from index.md.

index.md is the single source of truth:
  - the first "# " heading becomes the banner text
  - each "## " heading starts a <section>, rendered as <h1>
  - fenced code blocks tagged sh/shell/bash become the copyable
    installer rows ($ prompt)
The whole markdown source is embedded verbatim into the generated page
so the "agent view" toggle shows exactly what agents fetch at /index.md.

Usage:
  uv run build.py           regenerate index.html
  uv run build.py --check   exit 1 if index.html is stale
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "index.md"
TEMPLATE = ROOT / "template.html"
OUTPUT = ROOT / "index.html"

NOTE = "<!-- GENERATED from index.md — edit index.md, then run: uv run build.py -->"

CODE_LANGS = {"sh", "shell", "bash"}


class PageRenderer(mistune.HTMLRenderer):
    """markdown -> the site's HTML dialect.

    H1 is reserved for the banner (stripped before rendering), so H2
    headings render as section <h1>s, H3 as <h2>, and so on, keeping the
    Bauhaus color rotation (which keys off sibling <section>s) intact.
    """

    def heading(self, text: str, level: int, **attrs) -> str:
        tag = "h1" if level <= 2 else f"h{level - 1}"
        return f"<{tag}>{text}</{tag}>\n"

    def list_item(self, text: str) -> str:
        if " — " in text:
            link, desc = text.split(" — ", 1)
            return f'<li>{link} <span class="desc">{desc}</span></li>\n'
        return f"<li>{text}</li>\n"

    def block_code(self, code: str, info: str | None = None) -> str:
        lang = (info or "").split()[0] if info else ""
        if lang not in CODE_LANGS:
            return f"<pre><code>{html.escape(code, quote=False)}</code></pre>\n"
        rows = "".join(
            "<li>"
            '<span class="prompt">$</span>'
            f'<code class="copyable">{html.escape(line, quote=False)}</code>'
            "</li>\n"
            for line in code.strip("\n").splitlines()
            if line.strip()
        )
        return f"<ul>\n{rows}</ul>\n"


def split_banner(md_text: str) -> tuple[str, str]:
    """Return (banner_text, remaining_markdown)."""
    match = re.match(r"\A\s*#\s+(.+?)\s*\n", md_text)
    if not match:
        raise SystemExit("index.md must start with a '# ' heading (the banner)")
    return match.group(1), md_text[match.end() :]


def wrap_sections(rendered: str) -> str:
    """Wrap each <h1> group in a <section> (the template's CSS works on
    <section> siblings) and flag sections holding installer rows."""
    parts = re.split(r"(?=<h1>)", rendered)
    sections = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if not stripped.startswith("<h1>"):
            sections.append(stripped)  # stray content before the first <h1>
            continue
        cls = ' class="installers"' if 'class="copyable"' in stripped else ""
        sections.append(f"<section{cls}>\n{stripped}\n</section>")
    return "\n".join(sections)


def build() -> str:
    md_text = SOURCE.read_text()
    banner, body_md = split_banner(md_text)
    if "</script" in md_text:
        raise SystemExit("index.md contains '</script' — rephrase it")

    render = mistune.create_markdown(renderer=PageRenderer())
    content = wrap_sections(render(body_md))

    tpl = TEMPLATE.read_text()
    for marker in ("<!--banner-->", "<!--content-->", "<!--agent-source-->"):
        if marker not in tpl:
            raise SystemExit(f"template.html is missing {marker}")
    out = tpl.replace("<!--banner-->", html.escape(banner, quote=False))
    out = out.replace("<!--content-->", "\n" + content)
    out = out.replace("<!--agent-source-->", "\n" + md_text.rstrip("\n"))
    out = out.replace("<!doctype html>\n", f"<!doctype html>\n{NOTE}\n", 1)
    return out


def main() -> int:
    flags = set(sys.argv[1:])
    if flags - {"--check"}:
        raise SystemExit(f"unknown arguments: {sorted(flags - {'--check'})}")
    generated = build()
    if "--check" in flags:
        current = OUTPUT.read_text() if OUTPUT.exists() else ""
        if current != generated:
            print("index.html is stale — run: uv run build.py", file=sys.stderr)
            return 1
        print("index.html is up to date")
        return 0
    OUTPUT.write_text(generated)
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
