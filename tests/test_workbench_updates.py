from __future__ import annotations

import hashlib
import json

import pytest

from shadowseed.workbench.updates import WorkbenchUpdateService


def _asset(name: str, url: str) -> dict[str, str]:
    return {"name": name, "browser_download_url": url}


def test_update_preferences_are_explicit_opt_in(tmp_path) -> None:
    service = WorkbenchUpdateService(
        tmp_path / "workspace",
        current_version="0.10.1",
        system="darwin",
        machine="arm64",
    )

    assert service.auto_check_enabled() is False
    assert service.set_auto_check(True) is True
    assert service.auto_check_enabled() is True
    assert service.set_auto_check(False) is False
    assert service.auto_check_enabled() is False


def test_check_selects_newest_matching_platform_release(tmp_path, monkeypatch) -> None:
    service = WorkbenchUpdateService(
        tmp_path / "workspace",
        current_version="0.10.1",
        system="darwin",
        machine="arm64",
    )
    releases = [
        {
            "tag_name": "v0.10.3",
            "draft": False,
            "prerelease": True,
            "html_url": "https://example/releases/v0.10.3",
            "assets": [
                _asset("SHA256SUMS", "https://example/0.10.3/sums"),
                _asset(
                    "shadowseed-workbench-0.10.3-darwin-arm64.manifest.json",
                    "https://example/0.10.3/manifest",
                ),
                _asset(
                    "shadowseed-workbench-0.10.3-darwin-arm64.zip",
                    "https://example/0.10.3/archive",
                ),
            ],
        },
        {
            "tag_name": "v0.11.0",
            "draft": False,
            "prerelease": True,
            "html_url": "https://example/releases/v0.11.0",
            "assets": [
                _asset("SHA256SUMS", "https://example/0.11.0/sums"),
                _asset(
                    "shadowseed-workbench-0.11.0-linux-x86_64.manifest.json",
                    "https://example/0.11.0/manifest",
                ),
                _asset(
                    "shadowseed-workbench-0.11.0-linux-x86_64.tar.gz",
                    "https://example/0.11.0/archive",
                ),
            ],
        },
    ]
    monkeypatch.setattr(service, "_get_json", lambda _url: releases)

    result = service.check()

    assert result["status"] == "available"
    assert result["candidate"]["version"] == "0.10.3"
    assert result["candidate"]["archive_name"].endswith("darwin-arm64.zip")


def test_check_reports_up_to_date_when_no_new_matching_release(tmp_path, monkeypatch) -> None:
    service = WorkbenchUpdateService(
        tmp_path / "workspace",
        current_version="0.10.1",
        system="darwin",
        machine="arm64",
    )
    monkeypatch.setattr(service, "_get_json", lambda _url: [])

    result = service.check()

    assert result["status"] == "up_to_date"


def test_download_verifies_manifest_and_archive_checksums(tmp_path, monkeypatch) -> None:
    service = WorkbenchUpdateService(
        tmp_path / "workspace",
        current_version="0.10.1",
        system="darwin",
        machine="arm64",
    )
    archive_name = "shadowseed-workbench-0.10.2-darwin-arm64.zip"
    manifest_name = "shadowseed-workbench-0.10.2-darwin-arm64.manifest.json"
    archive = b"verified archive bytes"
    archive_sha = hashlib.sha256(archive).hexdigest()
    manifest = json.dumps(
        {
            "version": "0.10.2",
            "system": "darwin",
            "machine": "arm64",
            "archive": archive_name,
            "archive_size": len(archive),
            "archive_sha256": archive_sha,
        },
        sort_keys=True,
    ).encode("utf-8")
    manifest_sha = hashlib.sha256(manifest).hexdigest()
    sums = (
        f"{archive_sha}  {archive_name}\n"
        f"{manifest_sha}  {manifest_name}\n"
    ).encode("utf-8")

    payloads = {
        "https://example/manifest": manifest,
        "https://example/sums": sums,
    }
    monkeypatch.setattr(service, "_get_bytes", lambda url: payloads[url])

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self, chunk_size: int):
            assert chunk_size == 1024 * 1024
            yield archive

    class FakeStream:
        def __enter__(self):
            return FakeResponse()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "shadowseed.workbench.updates.httpx.stream",
        lambda *args, **kwargs: FakeStream(),
    )

    result = service.download(
        {
            "version": "0.10.2",
            "tag": "v0.10.2",
            "release_url": "https://example/release",
            "manifest_url": "https://example/manifest",
            "manifest_name": manifest_name,
            "archive_url": "https://example/archive",
            "archive_name": archive_name,
            "checksums_url": "https://example/sums",
            "prerelease": True,
        }
    )

    assert result["status"] == "downloaded"
    assert result["verified_sha256"] == archive_sha
    assert (tmp_path / "workspace" / "updates" / archive_name).read_bytes() == archive


def test_download_rejects_manifest_checksum_mismatch(tmp_path, monkeypatch) -> None:
    service = WorkbenchUpdateService(
        tmp_path / "workspace",
        current_version="0.10.1",
        system="darwin",
        machine="arm64",
    )
    manifest_name = "shadowseed-workbench-0.10.2-darwin-arm64.manifest.json"
    archive_name = "shadowseed-workbench-0.10.2-darwin-arm64.zip"
    manifest = b"{}"
    sums = (
        f"{'1' * 64}  {manifest_name}\n"
        f"{'0' * 64}  {archive_name}\n"
    ).encode("utf-8")
    monkeypatch.setattr(
        service,
        "_get_bytes",
        lambda url: manifest if url.endswith("manifest") else sums,
    )

    with pytest.raises(ValueError, match="manifest checksum"):
        service.download(
            {
                "version": "0.10.2",
                "tag": "v0.10.2",
                "release_url": "https://example/release",
                "manifest_url": "https://example/manifest",
                "manifest_name": manifest_name,
                "archive_url": "https://example/archive",
                "archive_name": archive_name,
                "checksums_url": "https://example/sums",
                "prerelease": True,
            }
        )
