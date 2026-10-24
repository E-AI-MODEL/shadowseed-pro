# Shadowseed manual / handleiding

| | English | Nederlands |
| --- | --- | --- |
| Read online | [shadowseed-manual-en.md](shadowseed-manual-en.md) | [shadowseed-handleiding-nl.md](shadowseed-handleiding-nl.md) |
| PDF | [shadowseed-manual-en.pdf](shadowseed-manual-en.pdf) | [shadowseed-handleiding-nl.pdf](shadowseed-handleiding-nl.pdf) |

One manual in six parts, for users, testers, researchers, developers and
specialists. Both editions have the same chapters and numbering.

## Maintaining the manual

- Edit both editions in the same change; `tests/test_manual.py` checks that the
  chapters match, that every image exists and that the version is current.
- Screenshots in `images/` come from the offline demo of the web application.
- Rebuild the PDFs after a change:

  ```bash
  pip install markdown playwright
  python -m playwright install chromium   # or pass --chromium /path/to/chromium
  python scripts/build_manual_pdf.py docs/manual/shadowseed-manual-en.md
  python scripts/build_manual_pdf.py docs/manual/shadowseed-handleiding-nl.md
  ```
