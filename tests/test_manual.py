from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

MANUAL = Path("docs/manual")
EDITIONS = ("shadowseed-manual-en.md", "shadowseed-handleiding-nl.md")


def _chapters(text: str) -> list[str]:
    return re.findall(r"^## (\d+)\. ", text, flags=re.M)


def test_editions_share_chapters_images_and_version() -> None:
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]
    texts = {name: (MANUAL / name).read_text(encoding="utf-8") for name in EDITIONS}

    chapters = {name: _chapters(text) for name, text in texts.items()}
    assert chapters[EDITIONS[0]] == [str(n) for n in range(1, 28)]
    assert chapters[EDITIONS[0]] == chapters[EDITIONS[1]]

    for name, text in texts.items():
        images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
        assert images, name
        for image in images:
            assert (MANUAL / image).is_file(), (name, image)
        assert re.findall(r"!\[[^\]]*\]\(([^)]+)\)", texts[EDITIONS[0]]) == images
        assert f"Version {version}" in text or f"Versie {version}" in text, name
        assert (MANUAL / name).with_suffix(".pdf").is_file(), name
