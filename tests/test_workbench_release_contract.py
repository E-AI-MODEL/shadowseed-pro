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
    assert f"`v{version}` is a published Research Preview with verified release assets." in research_status
    assert f"create a fresh immutable `v{version}` tag" not in research_status
    assert "current `main` contains unreleased 0.11 development" in research_status

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



def test_heavy_release_evidence_is_pr_scoped_or_explicitly_dispatched() -> None:
    for path in (
        ".github/workflows/workbench-ci.yml",
        ".github/workflows/workbench-portability.yml",
        ".github/workflows/research-package-ci.yml",
        ".github/workflows/standalone-workbench.yml",
    ):
        workflow = Path(path).read_text(encoding="utf-8")
        trigger_block = workflow[workflow.index("on:"):workflow.index("\n\npermissions:")]

        assert "pull_request:" in trigger_block
        assert "workflow_dispatch:" in trigger_block
        assert "push:" not in trigger_block

def test_release_workflow_is_main_gated_version_driven_and_standalone_backed() -> None:
    workflow = Path(".github/workflows/release-workbench.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "inputs.confirm == 'RELEASE'" in workflow
    assert "ref: main" in workflow
    assert 'test "$(git rev-parse HEAD)" = "$release_sha"' in workflow
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in workflow
    for required in (
        "ci.yml",
        "workbench-ci.yml",
        "workbench-portability.yml",
        "research-package-ci.yml",
        "standalone-workbench.yml",
    ):
        assert required in workflow
    assert "actions: write" in workflow
    assert "actions/workflows/ci.yml/runs?event=push&branch=main" in workflow
    assert 'gh workflow run "$workflow" --ref main' in workflow
    assert "workflow_dispatch&branch=main" in workflow
    assert '.event == "workflow_dispatch"' in workflow
    assert '.head_sha == $sha' in workflow
    assert 'gh run watch "$run_id" --exit-status' in workflow
    assert 'if [ "$conclusion" != "success" ]; then' in workflow
    assert "standalone_run_id" in workflow
    assert "steps.preflight.outputs.standalone_run_id" in workflow
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


def test_ci_push_runs_only_on_main_to_avoid_duplicate_feature_branch_runs() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    trigger_block = workflow[workflow.index("on:"):workflow.index("\n\npermissions:")]

    assert "push:\n    branches: [main]" in trigger_block
    assert "pull_request:" in trigger_block
