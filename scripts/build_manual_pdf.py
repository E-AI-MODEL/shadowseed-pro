"""Render the Shadowseed manual from Markdown to a styled PDF.

The Markdown files in ``docs/manual/`` are the source. This script converts one
of them to HTML with a cover, a contents page with page numbers, part openers,
numbered figures and callouts, and prints it to PDF with a headless Chromium
through Playwright. It renders twice: the first pass finds the page of every
heading in the PDF outline, the second pass writes those pages into the
contents.

Requirements (not project dependencies): ``pip install markdown playwright pypdf``
and a Chromium that Playwright can launch. Fonts load from Google Fonts; without
network access the PDF falls back to DejaVu Sans.

Usage:
    python scripts/build_manual_pdf.py docs/manual/shadowseed-manual-en.md
    python scripts/build_manual_pdf.py docs/manual/shadowseed-handleiding-nl.md \\
        [--output docs/manual/shadowseed-handleiding-nl.pdf] [--chromium PATH]
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import urllib.request
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

LABELS = {
    "en": {
        "contents": "Contents",
        "page": "Page",
        "of": "of",
        "figure": "Figure",
        "part": "Part",
        "in_part": "In this part",
        "callouts": {
            "Caution": "warn",
            "Tip": "tip",
            "Important": "important",
            "About the examples": "info",
        },
    },
    "nl": {
        "contents": "Inhoud",
        "page": "Pagina",
        "of": "van",
        "figure": "Afbeelding",
        "part": "Deel",
        "in_part": "In dit deel",
        "callouts": {
            "Let op": "warn",
            "Tip": "tip",
            "Belangrijk": "important",
            "Over de voorbeelden": "info",
        },
    },
}

FONTS = (
    "https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400"
    "&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=JetBrains+Mono:wght@400;600"
    "&display=block"
)

CSS = """
@page { size: A4; margin: 20mm 21mm 21mm 21mm; }
@page cover { margin: 0; }
:root {
  --brand: #0f6e5f; --brand-dark: #0a4a40; --brand-tint: #eaf4f1; --accent: #d9480f;
  --ink: #1f2933; --muted: #5f6b75; --line: #dde3e6; --code: #f4f6f7;
  --warn: #b54708; --warn-tint: #fff6ea; --imp: #b42318; --imp-tint: #fdeeec;
  --sans: "Source Sans 3", "DejaVu Sans", Arial, sans-serif;
  --serif: "Source Serif 4", "DejaVu Serif", Georgia, serif;
  --mono: "JetBrains Mono", "DejaVu Sans Mono", monospace;
}
* { box-sizing: border-box; }
html { font-family: var(--sans); font-size: 10.6pt; line-height: 1.55; color: var(--ink);
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; }
p { margin: 0 0 2.6mm; orphans: 3; widows: 3; }
li { margin: 0 0 1.2mm; }
ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
a { color: var(--brand); text-decoration: none; }
strong { font-weight: 700; }
code { font-family: var(--mono); font-size: 8.4pt; background: var(--code); padding: 0.2mm 1mm;
       border-radius: 1mm; }
pre { background: var(--code); border-left: 1mm solid var(--brand); border-radius: 0 1.5mm 1.5mm 0;
      padding: 3mm 4mm; margin: 2mm 0 4mm; font-size: 8.2pt; line-height: 1.5; white-space: pre-wrap;
      break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
hr { display: none; }

/* Cover */
.cover { page: cover; height: 297mm; background: var(--brand); color: #fff; position: relative;
         padding: 52mm 24mm 0; break-after: page; overflow: hidden; }
.cover__ring { position: absolute; right: -40mm; top: 120mm; width: 190mm; height: 190mm; border-radius: 50%;
               border: 3mm dashed rgba(255,255,255,0.16); }
.cover__dot { position: absolute; right: 37mm; top: 197mm; width: 36mm; height: 36mm; border-radius: 50%;
              background: rgba(255,255,255,0.14); }
.cover__mark { width: 16mm; height: 16mm; border-radius: 4.5mm; background: #fff; display: flex;
               align-items: center; justify-content: center; margin-bottom: 18mm; }
.cover__mark span { width: 8mm; height: 8mm; border-radius: 50%; border: 0.9mm dashed var(--brand); }
.cover h1 { font-family: var(--serif); font-size: 46pt; font-weight: 700; line-height: 1.05; margin: 0;
            color: #fff; border: 0; padding: 0; }
.cover .subtitle { font-family: var(--serif); font-size: 26pt; font-weight: 600; margin: 3mm 0 10mm; opacity: 0.92; }
.cover .edition { font-size: 12pt; letter-spacing: 0.02em; opacity: 0.9; }
.cover__foot { position: absolute; left: 24mm; right: 24mm; bottom: 20mm; font-size: 9pt; opacity: 0.85;
               border-top: 0.3mm solid rgba(255,255,255,0.4); padding-top: 4mm; }

/* Preface and contents */
.preface { break-after: page; }
.preface h2, .toc h2 { font-family: var(--serif); font-size: 22pt; color: var(--brand-dark); margin: 0 0 4mm; border-top: 0; padding-top: 0;
                       font-weight: 700; }
.toc { break-after: page; }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0; }
.toc .toc-part { margin-top: 1.6mm; font-weight: 700; color: var(--brand-dark); font-size: 10.6pt; }
.toc .toc-part:first-child { margin-top: 0; }
.toc .toc-chapter { padding-left: 7mm; font-size: 9.4pt; line-height: 1.42; }
.toc a { display: flex; align-items: baseline; color: inherit; padding: 0.25mm 0; }
.toc a .t { flex: 0 1 auto; }
.toc a .dots { flex: 1 1 auto; border-bottom: 0.3mm dotted #b9c3c8; margin: 0 2mm; transform: translateY(-1mm); }
.toc a .p { flex: 0 0 auto; min-width: 7mm; text-align: right; font-variant-numeric: tabular-nums; }

/* Part openers */
.part { break-before: page; break-after: page; padding-top: 38mm; }
.part .label { font-size: 11pt; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent); }
.part h1 { font-family: var(--serif); font-size: 32pt; line-height: 1.12; color: var(--brand-dark); margin: 3mm 0 8mm;
           padding-bottom: 6mm; border-bottom: 0.8mm solid var(--brand); font-weight: 700; }
.part .intro { font-size: 13pt; color: var(--muted); max-width: 140mm; }
.part .in-part { margin-top: 16mm; }
.part .in-part h4 { font-size: 9pt; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin: 0 0 3mm; }
.part .in-part ol { list-style: none; padding: 0; margin: 0; }
.part .in-part li { font-size: 11.5pt; margin: 0 0 2mm; }
.part .in-part li span { display: inline-block; width: 9mm; color: var(--brand); font-weight: 700; }

/* Chapters */
h2 { font-family: var(--serif); font-size: 18pt; line-height: 1.2; color: var(--brand-dark); font-weight: 700;
     margin: 11mm 0 4mm; padding-top: 3mm; border-top: 0.3mm solid var(--line); break-after: avoid; }
.part + h2 { border-top: 0; padding-top: 0; margin-top: 0; }
h2 .num { display: inline-block; min-width: 10mm; color: var(--accent); }
h3 { font-size: 12pt; color: var(--ink); font-weight: 700; margin: 6mm 0 2mm; break-after: avoid; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: 2mm 0 5mm; font-size: 9.4pt; line-height: 1.45; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { text-align: left; background: var(--brand-tint); color: var(--brand-dark); font-weight: 700;
     padding: 1.8mm 2.4mm; border-bottom: 0.5mm solid var(--brand); }
td { border-bottom: 0.3mm solid var(--line); padding: 1.7mm 2.4mm; vertical-align: top; }
th:empty { background: transparent; border-bottom: 0.5mm solid var(--brand); }

/* Figures */
figure { margin: 4mm auto 6mm; text-align: center; break-inside: avoid; }
figure img { display: block; margin: 0 auto; max-width: 100%; max-height: 118mm; border-radius: 2mm;
             border: 0.3mm solid var(--line); box-shadow: 0 1mm 3mm rgba(16, 42, 38, 0.10); }
figure.diagram img { border: 0; box-shadow: none; border-radius: 0; max-height: 105mm; }
figure.narrow img { width: 56%; }
figure.small img { width: 40%; }
figcaption { font-size: 9pt; color: var(--muted); margin-top: 2.6mm; text-align: center; padding: 0 8mm; }
figcaption b { color: var(--ink); }

/* Callouts */
blockquote { margin: 4mm 0 5mm; padding: 3mm 4.5mm; border-radius: 2mm; background: var(--brand-tint);
             border-left: 1.2mm solid var(--brand); break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
blockquote.warn { background: var(--warn-tint); border-left-color: var(--warn); }
blockquote.warn strong:first-child { color: var(--warn); }
blockquote.important { background: var(--imp-tint); border-left-color: var(--imp); }
blockquote.important strong:first-child { color: var(--imp); }
blockquote.tip strong:first-child, blockquote.info strong:first-child { color: var(--brand-dark); }
blockquote.info { background: #f3f5f6; border-left-color: var(--muted); }
"""


def _font_css() -> str:
    """Google Fonts CSS with every font file inlined, or "" when offline.

    Inlining keeps the render independent of the browser's network access;
    the files are cached under ``~/.cache/shadowseed-manual-fonts``.
    """

    cache = Path.home() / ".cache" / "shadowseed-manual-fonts"
    agent = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}

    def fetch(url: str) -> bytes:
        name = re.sub(r"[^A-Za-z0-9._-]", "_", url)[-150:]
        path = cache / name
        if not path.exists():
            cache.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(urllib.request.Request(url, headers=agent), timeout=30) as response:
                path.write_bytes(response.read())
        return path.read_bytes()

    try:
        css = fetch(FONTS).decode("utf-8")
        return re.sub(
            r"url\((https://[^)]+)\)",
            lambda m: "url(data:font/woff2;base64," + base64.b64encode(fetch(m.group(1))).decode() + ")",
            css,
        )
    except OSError:
        return ""


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        for line in text[4:end].splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
        text = text[end + 5 :]
    return meta, text


def _md(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"toc_depth": "1-2"}},
        output_format="html5",
    )


def _sections(text: str) -> tuple[str, str]:
    """Split the source into the preface and the body.

    The title line and the version line are replaced by the cover, and the
    hand-written contents list by the generated one.
    """

    text = re.sub(r"\A\s*# [^\n]+\n+\*\*[^\n]+\*\*\n", "", text)
    preface, _, rest = text.partition("\n---\n")
    preface = re.sub(r"\n## (Contents|Inhoud)\n.*\Z", "\n", preface, flags=re.S)
    return preface, rest


def _figures(body: str, label: str) -> str:
    count = 0

    def figure(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        img, caption = match.group(1), match.group(2)
        classes = re.search(r'class="([^"]+)"', img)
        kind = classes.group(1) if classes else ""
        if img.find(".svg") != -1:
            kind = (kind + " diagram").strip()
        return (
            f'<figure class="{kind}">{img}<figcaption><b>{label} {count}</b> — '
            f"{caption}</figcaption></figure>"
        )

    return re.sub(
        r"<p>(<img [^>]+>)</p>\s*<p><em>(.*?)</em></p>", figure, body, flags=re.S
    )


def _callouts(body: str, kinds: dict[str, str]) -> str:
    def callout(match: re.Match[str]) -> str:
        word = match.group(1).rstrip(".")
        kind = kinds.get(word, "tip")
        return f'<blockquote class="{kind}">\n<p><strong>{match.group(1)}</strong>'

    return re.sub(r"<blockquote>\s*<p><strong>([^<]+)</strong>", callout, body)


def _chapters(body: str) -> str:
    return re.sub(
        r'<h2 id="([^"]+)">(\d+|[A-Z])\. (.*?)</h2>',
        r'<h2 id="\1"><span class="num">\2</span> \3</h2>',
        body,
    )


def _parts(body: str, labels: dict) -> str:
    """Turn each part heading and its first paragraph into an opener page."""

    pieces = re.split(r'(<h1 id="[^"]+">.*?</h1>)', body)
    out = [pieces[0]]
    for i in range(1, len(pieces), 2):
        heading, rest = pieces[i], pieces[i + 1]
        anchor, title = re.match(r'<h1 id="([^"]+)">(.*?)</h1>', heading).groups()
        number, _, name = title.partition(" — ")
        label = number if name else ""
        name = name or title
        intro = ""
        first = re.match(r"\s*<p>(.*?)</p>", rest, flags=re.S)
        if first and not first.group(1).startswith("<img"):
            intro = f'<p class="intro">{first.group(1)}</p>'
            rest = rest[first.end() :]
        chapters = re.findall(
            r'<h2 id="[^"]+"><span class="num">([^<]+)</span> (.*?)</h2>', rest
        )
        listing = ""
        if chapters:
            items = "".join(f"<li><span>{n}</span>{t}</li>" for n, t in chapters)
            listing = (
                f'<div class="in-part"><h4>{labels["in_part"]}</h4><ol>{items}</ol></div>'
            )
        out.append(
            f'<section class="part"><div class="label">{label}</div>'
            f'<h1 id="{anchor}">{name}</h1>{intro}{listing}</section>{rest}'
        )
    return "".join(out)


def _toc(body: str, label: str, pages: dict[str, int]) -> str:
    items = re.findall(
        r'<(?:h1|h2) id="([^"]+)">(?:<span class="num">([^<]+)</span> )?(.*?)</h(?:1|2)>',
        body,
    )
    out = [f'<section class="toc"><h2>{html.escape(label)}</h2><ol>']
    for anchor, number, title in items:
        is_part = not number
        page = pages.get(anchor, "")
        text = f"{number}&nbsp;&nbsp;{title}" if number else title
        css = "toc-part" if is_part else "toc-chapter"
        out.append(
            f'<li class="{css}"><a href="#{anchor}"><span class="t">{text}</span>'
            f'<span class="dots"></span><span class="p">{page}</span></a></li>'
        )
    out.append("</ol></section>")
    return "".join(out)


def _cover(meta: dict[str, str]) -> str:
    return (
        '<section class="cover"><div class="cover__ring"></div><div class="cover__dot"></div>'
        '<div class="cover__mark"><span></span></div>'
        f"<h1>{html.escape(meta.get('title', 'Shadowseed'))}</h1>"
        f'<div class="subtitle">{html.escape(meta.get("subtitle", ""))}</div>'
        f'<div class="edition">{html.escape(meta.get("edition", ""))}</div>'
        '<div class="cover__foot">PolyForm Noncommercial License 1.0.0 · '
        "github.com/E-AI-MODEL/shadowseed-pro</div></section>"
    )


def _document(meta: dict[str, str], inner: str, lang: str) -> str:
    title = html.escape(meta.get("title", "Shadowseed"))
    return (
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        f'<title>{title} — {html.escape(meta.get("subtitle", ""))}</title>'
        f"<style>{_font_css()}{CSS}</style></head><body>{inner}</body></html>"
    )


def _outline_pages(pdf: Path, titles: dict[str, str]) -> dict[str, int]:
    """Map heading anchors to 1-based page numbers through the PDF outline."""

    reader = PdfReader(str(pdf))
    by_title: dict[str, int] = {}

    def walk(items) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item)
                continue
            key = re.sub(r"\s+", " ", item.title).strip()
            by_title.setdefault(key, reader.get_destination_page_number(item) + 1)

    walk(reader.outline)
    pages = {}
    for anchor, title in titles.items():
        if title in by_title:
            pages[anchor] = by_title[title]
    return pages


def build(source: Path, output: Path, chromium: str | None) -> None:
    meta, text = _split_front_matter(source.read_text(encoding="utf-8"))
    lang = meta.get("lang", "en")
    labels = LABELS.get(lang, LABELS["en"])
    preface_md, body_md = _sections(text)
    preface = _callouts(_md(preface_md), labels["callouts"])
    body = _md(body_md)
    body = _chapters(body)
    body = _figures(body, labels["figure"])
    body = _callouts(body, labels["callouts"])
    body = _parts(body, labels)

    titles = {}
    for anchor, number, title in re.findall(
        r'<(?:h1|h2) id="([^"]+)">(?:<span class="num">([^<]+)</span> )?(.*?)</h(?:1|2)>',
        body,
    ):
        plain = html.unescape(re.sub(r"<[^>]+>", "", title))
        titles[anchor] = re.sub(r"\s+", " ", f"{number} {plain}" if number else plain).strip()

    footer = (
        '<div style="font-size:7.6pt;color:#5f6b75;width:100%;padding:0 21mm;display:flex;'
        'justify-content:space-between;font-family:\'Source Sans 3\',DejaVu Sans,Arial,sans-serif">'
        f"<span>{html.escape(meta.get('title', 'Shadowseed'))} — {html.escape(meta.get('subtitle', ''))}"
        f" · {html.escape(meta.get('edition', '').split(' · ')[0])}</span>"
        f'<span>{labels["page"]} <span class="pageNumber"></span> {labels["of"]} '
        '<span class="totalPages"></span></span></div>'
    )
    page_file = source.with_suffix(".print.html")
    cover_pdf = output.with_suffix(".cover.tmp.pdf")
    body_pdf = output.with_suffix(".body.tmp.pdf")
    try:
        with sync_playwright() as playwright:
            browser = (
                playwright.chromium.launch(executable_path=chromium)
                if chromium
                else playwright.chromium.launch()
            )
            page = browser.new_page()

            def render(inner: str, target: Path, numbered: bool) -> None:
                page_file.write_text(_document(meta, inner, lang), encoding="utf-8")
                page.goto(page_file.resolve().as_uri(), wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.pdf(
                    path=str(target),
                    prefer_css_page_size=True,
                    print_background=True,
                    display_header_footer=numbered,
                    header_template="<span></span>",
                    footer_template=footer,
                    outline=numbered,
                    tagged=True,
                )

            # The cover has no page number; the numbering starts on the page after it.
            render(_cover(meta), cover_pdf, numbered=False)
            pages: dict[str, int] = {}
            for _pass in range(2):
                toc = _toc(body, labels["contents"], pages)
                render(f'<section class="preface">{preface}</section>{toc}{body}', body_pdf, numbered=True)
                pages = _outline_pages(body_pdf, titles)
            browser.close()
        writer = PdfWriter()
        writer.append(str(cover_pdf))
        writer.append(str(body_pdf), import_outline=True)
        writer.add_metadata({"/Title": f"{meta.get('title', 'Shadowseed')} — {meta.get('subtitle', '')}"})
        with output.open("wb") as handle:
            writer.write(handle)
    finally:
        page_file.unlink(missing_ok=True)
        cover_pdf.unlink(missing_ok=True)
        body_pdf.unlink(missing_ok=True)


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
