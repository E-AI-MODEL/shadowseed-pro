"""Opt-in release update checks for the local Shadowseed Workbench.

The updater is intentionally separate from SSL runtime configuration. It reads
official GitHub Releases, verifies published checksums, and downloads a matching
standalone bundle only after an explicit user action. It never writes to Git or
modifies source files.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


_RELEASES_API = "https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/releases?per_page=20"
_USER_AGENT = "shadowseed-workbench-updater"


def _installed_version() -> str:
    try:
        return importlib.metadata.version("shadowseed")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _version_key(value: str) -> tuple[int, int, int]:
    base = str(value).strip().removeprefix("v").split("+", 1)[0].split("-", 1)[0]
    parts = base.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"unsupported release version: {value}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _checksum_map(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        digest, separator, name = line.partition("  ")
        if not separator or len(digest) != 64 or not name:
            raise ValueError("published SHA256SUMS contains a malformed entry")
        result[name] = digest.lower()
    return result


@dataclass(frozen=True)
class UpdateCandidate:
    version: str
    tag: str
    release_url: str
    manifest_url: str
    manifest_name: str
    archive_url: str
    archive_name: str
    checksums_url: str
    prerelease: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "tag": self.tag,
            "release_url": self.release_url,
            "manifest_url": self.manifest_url,
            "manifest_name": self.manifest_name,
            "archive_url": self.archive_url,
            "archive_name": self.archive_name,
            "checksums_url": self.checksums_url,
            "prerelease": self.prerelease,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UpdateCandidate":
        return cls(
            version=str(payload["version"]),
            tag=str(payload["tag"]),
            release_url=str(payload["release_url"]),
            manifest_url=str(payload["manifest_url"]),
            manifest_name=str(payload["manifest_name"]),
            archive_url=str(payload["archive_url"]),
            archive_name=str(payload["archive_name"]),
            checksums_url=str(payload["checksums_url"]),
            prerelease=bool(payload.get("prerelease", False)),
        )


class WorkbenchUpdateService:
    """Check and download official standalone releases with explicit opt-in."""

    def __init__(
        self,
        workspace: str | Path,
        *,
        current_version: str | None = None,
        system: str | None = None,
        machine: str | None = None,
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.current_version = current_version or _installed_version()
        self.system = (system or platform.system()).lower()
        self.machine = (machine or platform.machine()).lower()
        self.update_dir = self.workspace / "updates"
        self.preferences_path = self.update_dir / "preferences.json"

    def auto_check_enabled(self) -> bool:
        if not self.preferences_path.is_file():
            return False
        try:
            payload = json.loads(self.preferences_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return False
        return bool(payload.get("automatic_check", False))

    def set_auto_check(self, enabled: bool) -> bool:
        self.update_dir.mkdir(parents=True, exist_ok=True)
        payload = {"automatic_check": bool(enabled)}
        self.preferences_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            self.preferences_path.chmod(0o600)
        except OSError:
            pass
        return bool(enabled)

    @staticmethod
    def _get_json(url: str) -> Any:
        response = httpx.get(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": _USER_AGENT},
            follow_redirects=True,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_bytes(url: str) -> bytes:
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
            timeout=60.0,
        )
        response.raise_for_status()
        return response.content

    def check(self) -> dict[str, Any]:
        releases = self._get_json(_RELEASES_API)
        if not isinstance(releases, list):
            raise ValueError("GitHub release response is not a list")

        current_key = _version_key(self.current_version)
        candidates: list[tuple[tuple[int, int, int], UpdateCandidate]] = []
        for release in releases:
            if not isinstance(release, dict) or bool(release.get("draft")):
                continue
            tag = str(release.get("tag_name") or "")
            try:
                version_key = _version_key(tag)
            except ValueError:
                continue
            if version_key <= current_key:
                continue
            version = ".".join(str(part) for part in version_key)
            prefix = f"shadowseed-workbench-{version}-{self.system}-{self.machine}"
            expected_manifest = f"{prefix}.manifest.json"
            assets = {
                str(asset.get("name")): str(asset.get("browser_download_url"))
                for asset in release.get("assets", [])
                if isinstance(asset, dict) and asset.get("name") and asset.get("browser_download_url")
            }
            manifest_url = assets.get(expected_manifest)
            checksums_url = assets.get("SHA256SUMS")
            archives = [
                (name, url)
                for name, url in assets.items()
                if name.startswith(prefix) and name != expected_manifest
            ]
            if not manifest_url or not checksums_url or len(archives) != 1:
                continue
            archive_name, archive_url = archives[0]
            candidates.append(
                (
                    version_key,
                    UpdateCandidate(
                        version=version,
                        tag=tag,
                        release_url=str(release.get("html_url") or ""),
                        manifest_url=manifest_url,
                        manifest_name=expected_manifest,
                        archive_url=archive_url,
                        archive_name=archive_name,
                        checksums_url=checksums_url,
                        prerelease=bool(release.get("prerelease", False)),
                    ),
                )
            )

        if not candidates:
            return {
                "status": "up_to_date",
                "current_version": self.current_version,
                "automatic_check": self.auto_check_enabled(),
            }

        _key, candidate = max(candidates, key=lambda item: item[0])
        return {
            "status": "available",
            "current_version": self.current_version,
            "automatic_check": self.auto_check_enabled(),
            "candidate": candidate.to_dict(),
        }

    def download(self, candidate_payload: dict[str, Any]) -> dict[str, Any]:
        candidate = UpdateCandidate.from_dict(candidate_payload)
        if _version_key(candidate.version) <= _version_key(self.current_version):
            raise ValueError("selected release is not newer than the installed version")

        manifest_bytes = self._get_bytes(candidate.manifest_url)
        sums_bytes = self._get_bytes(candidate.checksums_url)
        checksums = _checksum_map(sums_bytes.decode("utf-8"))
        expected_manifest_sha = checksums.get(candidate.manifest_name)
        expected_archive_sha = checksums.get(candidate.archive_name)
        if not expected_manifest_sha or not expected_archive_sha:
            raise ValueError("published checksums do not cover the selected update")
        if _sha256_bytes(manifest_bytes) != expected_manifest_sha:
            raise ValueError("release manifest checksum verification failed")

        manifest = json.loads(manifest_bytes.decode("utf-8"))
        if str(manifest.get("version")) != candidate.version:
            raise ValueError("release manifest version does not match update candidate")
        if str(manifest.get("system")) != self.system:
            raise ValueError("release manifest targets a different operating system")
        if str(manifest.get("machine")).lower() != self.machine:
            raise ValueError("release manifest targets a different machine architecture")
        if str(manifest.get("archive")) != candidate.archive_name:
            raise ValueError("release manifest archive name does not match update candidate")
        manifest_archive_sha = str(manifest.get("archive_sha256") or "").lower()
        if manifest_archive_sha != expected_archive_sha:
            raise ValueError("release manifest and SHA256SUMS disagree about the archive")

        self.update_dir.mkdir(parents=True, exist_ok=True)
        destination = self.update_dir / candidate.archive_name
        partial = destination.with_suffix(destination.suffix + ".part")
        digest = hashlib.sha256()
        size = 0
        try:
            with httpx.stream(
                "GET",
                candidate.archive_url,
                headers={"User-Agent": _USER_AGENT},
                follow_redirects=True,
                timeout=httpx.Timeout(30.0, read=1200.0),
            ) as response:
                response.raise_for_status()
                with partial.open("wb") as handle:
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        handle.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
            if digest.hexdigest().lower() != expected_archive_sha:
                raise ValueError("downloaded update checksum verification failed")
            expected_size = int(manifest.get("archive_size") or 0)
            if expected_size and size != expected_size:
                raise ValueError("downloaded update size does not match release manifest")
            partial.replace(destination)
            (self.update_dir / candidate.manifest_name).write_bytes(manifest_bytes)
            (self.update_dir / "SHA256SUMS").write_bytes(sums_bytes)
            for path in (
                destination,
                self.update_dir / candidate.manifest_name,
                self.update_dir / "SHA256SUMS",
            ):
                try:
                    path.chmod(0o600)
                except OSError:
                    pass
        except Exception:
            partial.unlink(missing_ok=True)
            raise

        return {
            "status": "downloaded",
            "version": candidate.version,
            "archive": str(destination),
            "verified_sha256": expected_archive_sha,
            "size": size,
            "installation": (
                "Download is verified and staged. Close Shadowseed before replacing the "
                "installed application with the new standalone bundle."
            ),
        }
