from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


# The release workflow must download build artifacts through an immutably pinned
# action. Assert the pin *shape*, not one specific revision: freezing the exact
# SHA here makes every legitimate Action update fail this contract test, which
# blocks the supply-chain maintenance the pin exists to support. Coverage that no
# workflow uses a mutable ref lives in
# `test_claim_boundaries.test_external_github_actions_are_immutable`.
DOWNLOAD_ARTIFACT_PIN = re.compile(r"actions/download-artifact@[0-9a-f]{40}\b")


def test_workbench_release_metadata_stays_aligned() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]

    assert re.fullmatch(r"\d+\.\d+\.\d+", version) is not None
    assert Path(f"docs/workbench/release-{version}.md").is_file()
    assert Path("docs/workbench/release-0.7.0.md").is_file()
    assert Path("LICENSE").is_file()
    assert project["license"]["file"] == "LICENSE"
    readme = Path("README.md").read_text(encoding="utf-8")
    assert f"repository-{version}-2f6f5e" in readme
    assert "PolyForm_Noncommercial_1.0.0" in readme

    citation = Path("CITATION.cff").read_text(encoding="utf-8")
    research_status = Path("docs/research/status.md").read_text(encoding="utf-8")
    assert f'version: "{version}"' in citation
    assert f"Source version {version} is the current production-local assurance candidate." in research_status
    assert f"create a fresh immutable `v{version}` tag" in research_status

    workbench_readme = Path("docs/workbench/README.md").read_text(encoding="utf-8")
    limitations = Path("docs/workbench/limitations.md").read_text(encoding="utf-8")
    tester_guidelines = Path("docs/workbench/tester-guidelines.md").read_text(encoding="utf-8")
    privacy = Path("docs/workbench/privacy.md").read_text(encoding="utf-8")
    assert f"Version {version}" in workbench_readme
    assert f"shadowseed-workbench:{version}" in workbench_readme
    assert f"# Workbench {version} limitations" in limitations
    assert f"Shadowseed Workbench {version}" in limitations
    assert f"Shadowseed Workbench {version}" in tester_guidelines
    assert f"Shadowseed Workbench {version}" in privacy


def test_release_workflow_is_main_gated_version_driven_and_standalone_backed() -> None:
    workflow = Path(".github/workflows/release-workbench.yml").read_text(encoding="utf-8")

    assert 'workflows: ["Standalone Workbench"]' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in workflow
    assert 'release_tag="v${release_version}"' in workflow
    assert 'notes_file="docs/workbench/release-${release_version}.md"' in workflow
    assert DOWNLOAD_ARTIFACT_PIN.search(workflow) is not None
    assert not re.search(r"actions/download-artifact@v\d", workflow)
    assert "pattern: standalone-*" in workflow
    assert "PROVENANCE.json" in workflow
    assert "SBOM.cdx.json" in workflow
    assert "uv.lock" in workflow
    assert "dependency_lock_sha256" in workflow
    assert "SHA256SUMS" in workflow
    assert "license_identifier" in workflow
    assert "license_sha256" in workflow
    assert "verify_distribution_license.py" in workflow
    assert 'test -f LICENSE' in workflow
    assert "-name 'shadowseed-[0-9]*.tar.gz' | wc -l" in workflow
    assert "-name 'shadowseed-*.tar.gz' | wc -l" not in workflow
    assert "gh release create" in workflow
    assert 'RELEASE_TAG: "v0.4.0"' not in workflow
    assert "scoped to v0.4.0" not in workflow


def test_macos_intel_release_omits_unmaintainable_hf_stack() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    non_intel = "sys_platform != 'darwin' or platform_machine != 'x86_64'"
    assert f'"sentence-transformers>=2.7; {non_intel}"' in pyproject
    assert f'"transformers>=5.10,<6; {non_intel}"' in pyproject
    assert f'"torch>=2.5; {non_intel}"' in pyproject
    assert "torch>=2.2,<2.3" not in pyproject
    assert "transformers>=4.51,<5" not in pyproject


def test_release_requires_both_macos_architectures_and_real_server_probe() -> None:
    standalone = Path(".github/workflows/standalone-workbench.yml").read_text(
        encoding="utf-8"
    )
    release = Path(".github/workflows/release-workbench.yml").read_text(
        encoding="utf-8"
    )
    builder = Path("scripts/build_standalone.py").read_text(encoding="utf-8")

    assert "macOS Apple Silicon" in standalone
    assert "macOS Intel" in standalone
    assert "macos-15-intel" in standalone
    assert "server_startup_probe" in standalone
    assert "archive_roundtrip_server_probe" in standalone
    assert "expected 4 standalone manifests" in release
    assert '("darwin", "arm64")' in release
    assert '("darwin", "x86_64")' in release
    assert "server_startup_probe" in release
    assert "archive_roundtrip_server_probe" in release
    assert "local_hf_stack_bundled" in standalone
    assert "local_hf_stack_bundled" in release
    assert "def _verify_frozen_server_startup" in builder
    assert "Open Shadowseed.command" in builder
    assert "Contents/MacOS/Shadowseed" in builder
    assert 'open "$APP"' not in builder
