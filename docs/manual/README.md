# Shadowseed manual / handleiding

| | English | Nederlands |
| --- | --- | --- |
| Read online | [shadowseed-manual-en.md](shadowseed-manual-en.md) | [shadowseed-handleiding-nl.md](shadowseed-handleiding-nl.md) |
| PDF | [shadowseed-manual-en.pdf](shadowseed-manual-en.pdf) | [shadowseed-handleiding-nl.pdf](shadowseed-handleiding-nl.pdf) |

One manual in seven parts, for users, testers, researchers, developers and
specialists. Both editions have the same chapters, numbering and figures. The
manual follows one example conversation, a backup plan for a school's student
administration, from the first question to a seed that is used in an answer.

## Maintaining the manual

- Edit both editions in the same change. `tests/test_manual.py` checks that the
  chapters match, that both editions use the same figures, that every image
  exists and that the version is current.
- Each edition has its own images in `images/en/` and `images/nl/`.
- **Screenshots** come from Shadowseed itself, playing the scenario in
  `scripts/manual/scenario-<lang>.json` against a scripted stand-in for Ollama
  (`scripts/manual/mock_ollama.py`). Detection, recurrence, the Gate and the
  timeline are the real code; only the model text is scripted, and chapter 2
  tells the reader so. Build the web client first (`npm run build` in
  `apps/web`), then:

  ```bash
  python scripts/manual/make_screenshots.py en docs/manual/images/en
  python scripts/manual/make_screenshots.py nl docs/manual/images/nl
  ```

- **Diagrams** are generated SVG:
  `python scripts/manual/diagrams.py docs/manual/images`.
- **PDFs** are rebuilt from the Markdown. Fonts (Source Sans 3, Source Serif 4,
  JetBrains Mono) are downloaded once and embedded; offline the build falls
  back to DejaVu.

  ```bash
  pip install markdown playwright pypdf
  python -m playwright install chromium   # or pass --chromium /path/to/chromium
  python scripts/build_manual_pdf.py docs/manual/shadowseed-manual-en.md
  python scripts/build_manual_pdf.py docs/manual/shadowseed-handleiding-nl.md
  ```

Markdown conventions the PDF build understands: a paragraph in italics right
after an image is its caption (figures are numbered automatically);
`{.narrow}` and `{.small}` after an image make it narrower; a block quote that
starts with **Tip.**, **Caution.**/**Let op.**, **Important.**/**Belangrijk.**
or **About the examples.**/**Over de voorbeelden.** becomes a coloured callout.
