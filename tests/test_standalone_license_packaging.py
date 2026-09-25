from __future__ import annotations

from pathlib import Path

import pytest

import scripts.build_standalone as build_standalone
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


def test_macos_bundle_is_resealed_after_final_resource_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed.app"
    bundle.mkdir()
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path) -> None:
        assert cwd == bundle.parent
        commands.append(command)

    monkeypatch.setattr(build_standalone, "_run", fake_run)

    assert build_standalone._seal_macos_bundle(bundle, macos=True) == "adhoc"
    assert commands == [
        ["codesign", "--force", "--sign", "-", "--timestamp=none", str(bundle)],
        ["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(bundle)],
    ]



def test_macos_first_launch_helper_is_local_and_explicit(tmp_path: Path) -> None:
    distribution = tmp_path / "Shadowseed Workbench"
    distribution.mkdir()

    helper, readme = build_standalone._install_macos_first_launch_files(distribution)

    helper_text = helper.read_text(encoding="utf-8")
    readme_text = readme.read_text(encoding="utf-8")

    assert helper.name == "Open Shadowseed.command"
    assert helper.stat().st_mode & 0o111
    assert 'APP="$HERE/Shadowseed.app"' in helper_text
    assert 'xattr -dr com.apple.quarantine "$APP"' in helper_text
    assert 'open "$APP"' in helper_text
    assert "spctl --master-disable" not in helper_text
    assert "sudo" not in helper_text
    assert "does not require an Apple Developer ID" in readme_text
    assert "does not change global macOS security" in readme_text



def test_macos_archive_roundtrip_requires_extracted_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "shadowseed.zip"
    archive.write_bytes(b"placeholder")
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    def fake_run(command: list[str], *, cwd: Path) -> None:
        if command[:4] == ["ditto", "-x", "-k", str(archive)]:
            return
        raise AssertionError(f"unexpected command: {command} in {cwd}")

    monkeypatch.setattr(build_standalone, "_run", fake_run)

    with pytest.raises(RuntimeError, match="expected one Shadowseed.app"):
        build_standalone._verify_macos_archive_round_trip(
            archive,
            work_dir,
            macos=True,
        )
