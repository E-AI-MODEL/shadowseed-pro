from pathlib import Path

root = Path("README.md")
text = root.read_text(encoding="utf-8")

paper_section = """## Research paper

**Shadowseed: Remembering Without Trusting**
*A Validation-Gated Memory Architecture for Language Model Systems*

[Read the paper (PDF)](paper/shadowseed-paper.pdf) · [LaTeX source](paper/main.tex) · [Bibliography](paper/references.bib)

"""
if "## Research paper\n" not in text:
    marker = "## Start here\n"
    if marker not in text:
        raise SystemExit("README.md: Start here heading not found")
    text = text.replace(marker, paper_section + marker, 1)

paper_row = "| Read the research paper | [Paper PDF](paper/shadowseed-paper.pdf) |\n"
if paper_row not in text:
    table_marker = "| Goal | Start here |\n|---|---|\n"
    if table_marker not in text:
        raise SystemExit("README.md: Start here table header not found")
    text = text.replace(table_marker, table_marker + paper_row, 1)

status_note = (
    "The methods/systems manuscript for the current architecture is available in "
    "[`paper/`](paper/README.md), with the compiled version at "
    "[`paper/shadowseed-paper.pdf`](paper/shadowseed-paper.pdf). "
    "It describes the frozen 0.4.2 implementation and keeps the existing efficacy claim boundary unchanged.\n\n"
)
if status_note not in text:
    status_marker = "## Research status\n\n"
    if status_marker not in text:
        raise SystemExit("README.md: Research status heading not found")
    text = text.replace(status_marker, status_marker + status_note, 1)

root.write_text(text, encoding="utf-8")

paper = Path("paper/README.md")
ptext = paper.read_text(encoding="utf-8")
pdf_link = "[Read the compiled paper (PDF)](shadowseed-paper.pdf)\n\n"
authors_marker = "**Authors:** H. Visser, ChatGPT, Claude, Kimi, GLM\n\n"
if pdf_link not in ptext:
    if authors_marker not in ptext:
        raise SystemExit("paper/README.md: authors marker not found")
    ptext = ptext.replace(authors_marker, authors_marker + pdf_link, 1)

pdf_file_row = "- `shadowseed-paper.pdf` — compiled manuscript PDF\n"
if pdf_file_row not in ptext:
    files_marker = "## Files\n\n"
    if files_marker not in ptext:
        raise SystemExit("paper/README.md: Files heading not found")
    ptext = ptext.replace(files_marker, files_marker + pdf_file_row, 1)

paper.write_text(ptext, encoding="utf-8")
