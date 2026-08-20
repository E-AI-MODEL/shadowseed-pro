from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


def test_workbench_release_metadata_stays_aligned() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]

    assert version == "0.6.0"
    assert Path(f"docs/workbench/release-{version}.md").is_file()
    assert Path("LICENSE").is_file()
    assert project["license"]["file"] == "LICENSE"
    readme = Path("README.md").read_text(encoding="utf-8")
    assert f"repository-{version}-2f6f5e" in readme
    assert "PolyForm_Noncommercial_1.0.0" in readme


def test_release_workflow_is_main_gated_version_driven_and_standalone_backed() -> None:
    workflow = Path(".github/workflows/release-workbench.yml").read_text(encoding="utf-8")

    assert 'workflows: ["Standalone Workbench"]' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in workflow
    assert 'release_tag="v${release_version}"' in workflow
    assert 'notes_file="docs/workbench/release-${release_version}.md"' in workflow
    assert "actions/download-artifact@v4" in workflow
    assert "pattern: standalone-*" in workflow
    assert "PROVENANCE.json" in workflow
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
