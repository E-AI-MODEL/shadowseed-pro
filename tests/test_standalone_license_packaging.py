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

    monkeypatch.delenv("SHADOWSEED_MACOS_CODESIGN_IDENTITY", raising=False)
    monkeypatch.setattr(build_standalone, "_run", fake_run)

    assert build_standalone._seal_macos_bundle(bundle, macos=True) == "adhoc"
    assert commands == [
        ["codesign", "--force", "--sign", "-", "--timestamp=none", str(bundle)],
        ["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(bundle)],
    ]


def test_macos_developer_id_signing_uses_hardened_runtime_and_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed.app"
    bundle.mkdir()
    commands: list[list[str]] = []
    identity = "Developer ID Application: Example Org (TEAMID1234)"

    def fake_run(command: list[str], *, cwd: Path) -> None:
        assert cwd == bundle.parent
        commands.append(command)

    monkeypatch.setenv("SHADOWSEED_MACOS_CODESIGN_IDENTITY", identity)
    monkeypatch.setattr(build_standalone, "_run", fake_run)

    assert build_standalone._seal_macos_bundle(bundle, macos=True) == "developer-id"
    assert commands == [
        [
            "codesign",
            "--force",
            "--sign",
            identity,
            "--options",
            "runtime",
            "--timestamp",
            str(bundle),
        ],
        ["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(bundle)],
    ]


def test_non_macos_bundle_does_not_attempt_codesign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed"
    bundle.mkdir()

    def fail_run(command: list[str], *, cwd: Path) -> None:
        raise AssertionError(f"unexpected command: {command} in {cwd}")

    monkeypatch.setattr(build_standalone, "_run", fail_run)
    assert build_standalone._seal_macos_bundle(bundle, macos=False) is None


def test_notarization_is_optional_without_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed.app"
    bundle.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    monkeypatch.delenv("SHADOWSEED_MACOS_NOTARY_PROFILE", raising=False)

    def fail_run(command: list[str], *, cwd: Path) -> None:
        raise AssertionError(f"unexpected command: {command} in {cwd}")

    monkeypatch.setattr(build_standalone, "_run", fail_run)
    assert (
        build_standalone._notarize_macos_bundle(
            bundle,
            work_dir,
            signature_mode="developer-id",
            macos=True,
        )
        is False
    )


def test_notarization_requires_developer_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed.app"
    bundle.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.setenv("SHADOWSEED_MACOS_NOTARY_PROFILE", "shadowseed-notary")

    with pytest.raises(RuntimeError, match="requires Developer ID signing"):
        build_standalone._notarize_macos_bundle(
            bundle,
            work_dir,
            signature_mode="adhoc",
            macos=True,
        )


def test_notarization_submits_staples_and_assesses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "Shadowseed.app"
    bundle.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    keychain = tmp_path / "signing.keychain-db"
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path) -> None:
        commands.append(command)

    monkeypatch.setenv("SHADOWSEED_MACOS_NOTARY_PROFILE", "shadowseed-notary")
    monkeypatch.setenv("SHADOWSEED_MACOS_NOTARY_KEYCHAIN", str(keychain))
    monkeypatch.setattr(build_standalone, "_run", fake_run)

    assert (
        build_standalone._notarize_macos_bundle(
            bundle,
            work_dir,
            signature_mode="developer-id",
            macos=True,
        )
        is True
    )
    submit_zip = work_dir / "Shadowseed-notarization.zip"
    assert commands == [
        ["ditto", "-c", "-k", "--keepParent", str(bundle), str(submit_zip)],
        [
            "xcrun",
            "notarytool",
            "submit",
            str(submit_zip),
            "--keychain-profile",
            "shadowseed-notary",
            "--wait",
            "--keychain",
            str(keychain),
        ],
        ["xcrun", "stapler", "staple", str(bundle)],
        ["xcrun", "stapler", "validate", str(bundle)],
        ["spctl", "--assess", "--type", "execute", "--verbose=4", str(bundle)],
    ]


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

    with pytest.raises(RuntimeError, match="missing Shadowseed.app"):
        build_standalone._verify_macos_archive_round_trip(
            archive,
            work_dir,
            macos=True,
        )
