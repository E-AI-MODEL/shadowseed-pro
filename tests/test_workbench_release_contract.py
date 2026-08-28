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

    assert version == "0.7.1"
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
