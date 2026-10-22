"""Execute the actual release-workflow validation against altered artifacts."""

from __future__ import annotations

import json
import textwrap
from hashlib import sha256
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "a" * 40
COLLECT = "Validate standalone provenance and collect assets"
ASSURE = "Verify published provenance binds every standalone to the candidate"


def _run_step(workflow: str, name: str) -> None:
    source = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    step = source.split(f"      - name: {name}\n", 1)[1].split("\n      - ", 1)[0]
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    exec(compile(script, f"{workflow}:{name}", "exec"), {"__name__": "__main__"})


@pytest.fixture
def release_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RELEASE_SHA", SOURCE_SHA)
    monkeypatch.setenv("SOURCE_RUN_ID", "123")
    monkeypatch.setenv("RELEASE_VERSION", "0.12.3")
    (tmp_path / "LICENSE").write_bytes(b"release license")
    (tmp_path / "uv.lock").write_bytes(b"locked dependency inventory")
    assets = tmp_path / "web-assets"
    assets.mkdir()
    smoke = {
        "frozen": True, "static_assets_verified": True, "loopback_only": True,
        "runtime_mode": "live", "turn": 1,
    }
    http = dict.fromkeys((
        "http_healthy", "static_homepage", "host_rebinding_guard", "api_chat_roundtrip",
    ), True)
    for system in ("linux", "windows", "darwin"):
        stem = f"shadowseed-web-0.12.3-{system}-x86_64"
        archive = assets / f"{stem}.zip"
        archive.write_bytes(f"frozen test archive for {system}".encode())
        manifest = {
            "artifact": "shadowseed_web_only_candidate",
            "release_approved": False, "version": "0.12.3",
            "source_sha": SOURCE_SHA, "system": system, "machine": "x86_64",
            "archive": archive.name, "archive_sha256": sha256(archive.read_bytes()).hexdigest(),
            "license_identifier": "PolyForm-Noncommercial-1.0.0",
            "license_file": "SHADOWSEED_LICENSE.txt",
            "license_sha256": sha256((tmp_path / "LICENSE").read_bytes()).hexdigest(),
            "gradio_source_files_bundled": False, "web_static_assets_bundled": True,
            "self_contained_python_runtime": True, "loopback_only_default": True,
            "legacy_packages_excluded": ["gradio", "gradio-client", "pillow"],
            "self_test": smoke, "http_server_smoke": http,
            "macos_signature_mode": "adhoc", "macos_archive_roundtrip_verified": True,
            "archive_roundtrip_web_self_test": smoke,
            "archive_roundtrip_http_server_smoke": http,
        }
        (assets / f"{stem}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def _manifest(root: Path, system: str = "darwin") -> tuple[Path, dict]:
    path = next(root.glob(f"*-{system}-*.manifest.json"))
    return path, json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _collect_and_download(root: Path) -> Path:
    _run_step("release-workbench.yml", COLLECT)
    published = root / "verified-release"
    (root / "release-assets").rename(published)
    return published


def test_verified_web_archives_pass_collection_and_published_assurance(release_files: Path) -> None:
    published = _collect_and_download(release_files)
    _run_step("production-release-assurance.yml", ASSURE)
    _, manifest = _manifest(published)
    assert manifest["release_approved"] is True
    assert manifest["approval_scope"] == "research-preview"
    assert manifest["approved_source_sha"] == SOURCE_SHA


def test_release_rejects_changed_archive_bytes(release_files: Path) -> None:
    assets = release_files / "web-assets"
    _, manifest = _manifest(assets)
    (assets / manifest["archive"]).write_bytes(b"changed after candidate verification")
    with pytest.raises(SystemExit, match="archive checksum mismatch"):
        _run_step("release-workbench.yml", COLLECT)


@pytest.mark.parametrize("field,value,message", [
    ("source_sha", "b" * 40, "wrong source sha"),
    ("system", "linux", "duplicate platform"),
    ("archive", "../outside.zip", "invalid archive filename"),
    ("archive", "..\\outside.zip", "invalid archive filename"),
    ("gradio_source_files_bundled", True, "legacy Gradio included"),
    ("legacy_packages_excluded", ["gradio"], "legacy exclusion evidence missing"),
])
def test_release_rejects_wrong_candidate_evidence(
    release_files: Path, field: str, value: object, message: str,
) -> None:
    path, manifest = _manifest(release_files / "web-assets")
    manifest[field] = value
    _save(path, manifest)
    with pytest.raises(SystemExit, match=message):
        _run_step("release-workbench.yml", COLLECT)


@pytest.mark.parametrize("key", [
    "http_healthy", "static_homepage", "host_rebinding_guard", "api_chat_roundtrip",
])
def test_macos_roundtrip_requires_the_complete_user_path(release_files: Path, key: str) -> None:
    path, manifest = _manifest(release_files / "web-assets")
    manifest["archive_roundtrip_http_server_smoke"][key] = False
    _save(path, manifest)
    with pytest.raises(SystemExit, match="macOS archive HTTP smoke failed"):
        _run_step("release-workbench.yml", COLLECT)


@pytest.mark.parametrize("mutation,message", [
    ("archive", "archive checksum mismatch"),
    ("lock", "dependency lock hash"),
    ("provenance", "does not match the published web manifests"),
    ("legacy", "missing web-only inventory evidence"),
    ("approval", "missing web release approval"),
    ("platform", "duplicate platform"),
])
def test_assurance_rejects_inconsistent_published_evidence(
    release_files: Path, mutation: str, message: str,
) -> None:
    published = _collect_and_download(release_files)
    path, manifest = _manifest(published)
    if mutation == "archive":
        (published / manifest["archive"]).write_bytes(b"changed published archive")
    elif mutation == "lock":
        (published / "uv.lock").write_bytes(b"changed lock")
    elif mutation == "provenance":
        provenance = published / "PROVENANCE.json"
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        payload["web_bundles"] = []
        _save(provenance, payload)
    else:
        if mutation == "legacy":
            manifest["gradio_source_files_bundled"] = True
        elif mutation == "approval":
            manifest["release_approved"] = False
        elif mutation == "platform":
            manifest["system"] = "linux"
        _save(path, manifest)
    with pytest.raises(SystemExit, match=message):
        _run_step("production-release-assurance.yml", ASSURE)
