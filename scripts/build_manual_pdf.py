"""Render the Shadowseed manual from Markdown to a styled PDF.

The Markdown files in ``docs/manual/`` are the source. This script converts one
of them to HTML with a cover page and print styles, and prints it to PDF with a
headless Chromium through Playwright, so the PDF can be rebuilt from the
repository at any time.

Requirements (not project dependencies): ``pip install markdown playwright``
and a Chromium that Playwright can launch.

Usage:
    python scripts/build_manual_pdf.py docs/manual/shadowseed-manual-en.md
    python scripts/build_manual_pdf.py docs/manual/shadowseed-handleiding-nl.md \\
        [--output docs/manual/shadowseed-handleiding-nl.pdf] [--chromium PATH]
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

LABELS = {
    "en": {"contents": "Contents", "page": "Page", "of": "of"},
    "nl": {"contents": "Inhoud", "page": "Pagina", "of": "van"},
}

CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 20mm; }
:root { --brand: #0f6e5f; --ink: #1d2327; --muted: #5b6670; --line: #d9dee2; --tint: #f3f6f7; }
* { box-sizing: border-box; }
html { font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif; font-size: 10.2pt;
       line-height: 1.5; color: var(--ink); }
body { margin: 0; }
.cover { height: 240mm; display: flex; flex-direction: column; justify-content: space-between;
         page-break-after: always; }
.cover__band { background: var(--brand); color: #fff; padding: 30mm 14mm 16mm; border-radius: 4mm; }
.cover__mark { width: 18mm; height: 18mm; border-radius: 5mm; background: #fff; display: flex;
               align-items: center; justify-content: center; margin-bottom: 14mm; }
.cover__mark span { width: 8mm; height: 8mm; border-radius: 50%; border: 0.9mm dashed var(--brand); }
.cover h1 { font-size: 30pt; line-height: 1.15; margin: 0 0 4mm; padding: 0; border: 0; color: #fff;
            page-break-before: avoid; }
.cover p { font-size: 13pt; margin: 0; opacity: 0.92; }
.cover__foot { color: var(--muted); font-size: 9pt; border-top: 0.3mm solid var(--line); padding-top: 4mm; }
h1 { font-size: 19pt; color: var(--brand); margin: 0 0 5mm; padding-bottom: 2mm;
     border-bottom: 0.5mm solid var(--brand); page-break-before: always; }
h2 { font-size: 13.5pt; margin: 8mm 0 2.5mm; color: var(--ink); page-break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; color: var(--brand); page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: var(--brand); text-decoration: none; }
code { font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; font-size: 8.8pt;
       background: var(--tint); padding: 0.2mm 1mm; border-radius: 1mm; }
pre { background: var(--tint); border: 0.3mm solid var(--line); border-radius: 2mm; padding: 3mm 4mm;
      font-size: 8.4pt; line-height: 1.4; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 3mm 0 4mm; font-size: 9pt;
        page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; background: var(--brand); color: #fff; font-weight: 600; padding: 1.6mm 2.2mm; }
td { border-bottom: 0.3mm solid var(--line); padding: 1.6mm 2.2mm; vertical-align: top; }
tr:nth-child(even) td { background: #fafbfb; }
blockquote { margin: 4mm 0; padding: 3mm 4mm; background: #eef6f4; border-left: 1.2mm solid var(--brand);
             border-radius: 1.5mm; }
blockquote p { margin: 0; }
img { display: block; max-width: 100%; max-height: 120mm; margin: 4mm auto 1.5mm;
      border: 0.3mm solid var(--line); border-radius: 2mm; }
img[alt*="Ollama"] { max-height: 95mm; }
.caption { text-align: center; color: var(--muted); font-size: 8.8pt; font-style: italic;
           margin: 0 0 5mm; }
hr { display: none; }
.toc { page-break-after: always; }
.toc h1 { page-break-before: avoid; }
.toc ul { list-style: none; padding-left: 0; }
.toc ul ul { padding-left: 6mm; }
.toc li { margin: 1mm 0; }
"""


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        for line in text[4:end].splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
        text = text[end + 5 :]
    return meta, text


def _body_html(text: str) -> str:
    # The Markdown title and the hand-written contents list are replaced by the
    # cover and the generated table of contents.
    text = re.sub(r"\A\s*# [^\n]+\n", "", text)
    text = re.sub(
        r"\n## (Contents|Inhoud)\n.*?(?=\n---\n)", "\n", text, count=1, flags=re.S
    )
    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "1-2"}},
        output_format="html5",
    )
    # A paragraph that is only an emphasized sentence is a figure caption.
    return re.sub(
        r"<p><em>(.*?)</em></p>", r'<p class="caption">\1</p>', html_body, flags=re.S
    )


def _toc_html(body: str, label: str) -> str:
    items = re.findall(r'<h([12]) id="([^"]+)">(.*?)</h\1>', body)
    out = [f'<section class="toc"><h1>{html.escape(label)}</h1><ul>']
    open_sub = False
    for level, anchor, title in items:
        if level == "1":
            if open_sub:
                out.append("</ul></li>")
                open_sub = False
            out.append(f'<li><strong><a href="#{anchor}">{title}</a></strong><ul>')
            open_sub = True
        else:
            out.append(f'<li><a href="#{anchor}">{title}</a></li>')
    if open_sub:
        out.append("</ul></li>")
    out.append("</ul></section>")
    return "".join(out)


def build(source: Path, output: Path, chromium: str | None) -> None:
    meta, text = _split_front_matter(source.read_text(encoding="utf-8"))
    lang = meta.get("lang", "en")
    labels = LABELS.get(lang, LABELS["en"])
    body = _body_html(text)
    cover = (
        '<section class="cover"><div class="cover__band"><div class="cover__mark"><span></span></div>'
        f"<h1>{html.escape(meta.get('title', 'Shadowseed'))}</h1>"
        f"<p>{html.escape(meta.get('subtitle', ''))}</p></div>"
        '<div class="cover__foot">PolyForm Noncommercial License 1.0.0 · '
        "github.com/E-AI-MODEL/shadowseed-pro</div></section>"
    )
    document = (
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        f"<title>{html.escape(meta.get('title', 'Shadowseed'))}</title><style>{CSS}</style></head>"
        f"<body>{cover}{_toc_html(body, labels['contents'])}{body}</body></html>"
    )
    page_file = source.with_suffix(".print.html")
    page_file.write_text(document, encoding="utf-8")
    footer = (
        '<div style="font-size:7.5pt;color:#5b6670;width:100%;padding:0 20mm;display:flex;'
        'justify-content:space-between;font-family:DejaVu Sans,Arial,sans-serif">'
        f"<span>{html.escape(meta.get('title', 'Shadowseed'))} · {html.escape(meta.get('subtitle', ''))}</span>"
        f'<span>{labels["page"]} <span class="pageNumber"></span> {labels["of"]} '
        '<span class="totalPages"></span></span></div>'
    )
    try:
        with sync_playwright() as playwright:
            browser = (
                playwright.chromium.launch(executable_path=chromium)
                if chromium
                else playwright.chromium.launch()
            )
            page = browser.new_page()
            page.goto(page_file.resolve().as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(output),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=footer,
                margin={"top": "20mm", "bottom": "22mm", "left": "0", "right": "0"},
            )
            browser.close()
    finally:
        page_file.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--chromium", default=None, help="Path to a Chromium executable."
    )
    args = parser.parse_args(argv)
    output = args.output or args.source.with_suffix(".pdf")
    build(args.source, output, args.chromium)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
