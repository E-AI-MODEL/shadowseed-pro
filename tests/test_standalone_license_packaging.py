from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_standalone import _install_license, _sha256


def test_install_license_copies_exact_terms_into_plain_bundle(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    bundle = tmp_path / "dist" / "Shadowseed"
    root.mkdir()
    bundle.mkdir(parents=True)
    source = root / "LICENSE"
    source.write_text("PolyForm terms\nRequired Notice: test\n", encoding="utf-8")

    target = _install_license(root, bundle, macos=False)

    assert target == bundle / "SHADOWSEED_LICENSE.txt"
    assert target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
    assert _sha256(target) == _sha256(source)


def test_install_license_uses_macos_resources_directory(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    bundle = tmp_path / "dist" / "Shadowseed.app"
    root.mkdir()
    bundle.mkdir(parents=True)
    (root / "LICENSE").write_text("license\n", encoding="utf-8")

    target = _install_license(root, bundle, macos=True)

    assert target == bundle / "Contents" / "Resources" / "SHADOWSEED_LICENSE.txt"
    assert target.is_file()


def test_install_license_fails_closed_when_terms_are_missing(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    bundle = tmp_path / "dist" / "Shadowseed"
    root.mkdir()
    bundle.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="requires repository LICENSE"):
        _install_license(root, bundle, macos=False)
