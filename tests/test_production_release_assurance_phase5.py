from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_build_propagates_cross_platform_production_acceptance_result() -> None:
    workflow = _text(".github/workflows/ci.yml")

    assert "production-local:" in workflow
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in workflow
    assert 'glob.glob("tests/test_workbench_*.py")' in workflow
    assert 'glob.glob("tests/test_production_*_phase4.py")' in workflow
    assert 'glob.glob("tests/test_production_*_phase5.py")' in workflow
    assert "build:\n    if: ${{ always() }}\n    needs: [production-local]" in workflow
    assert "Require production-local acceptance success" in workflow
    assert "PRODUCTION_LOCAL_RESULT: ${{ needs.production-local.result }}" in workflow
    assert 'test "$PRODUCTION_LOCAL_RESULT" = "success"' in workflow


def test_supplementary_portability_runs_phase4_and_phase5_acceptance() -> None:
    workflow = _text(".github/workflows/workbench-portability.yml")

    assert '"tests/test_production_*_phase4.py"' in workflow
    assert '"tests/test_production_*_phase5.py"' in workflow
    assert "Phase 4/5 production-local adversarial acceptance" in workflow
    assert "tests/test_production_*_phase4.py" in workflow
    assert "tests/test_production_*_phase5.py" in workflow


def test_release_workflow_is_bound_to_exact_main_sha_and_post_download_verification() -> None:
    workflow = _text(".github/workflows/release-workbench.yml")

    assert 'ref: ${{ github.event.workflow_run.head_sha }}' in workflow
    assert 'test "$(git rev-parse HEAD)" = "$RELEASE_SHA"' in workflow
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in workflow
    assert '--target "$RELEASE_SHA"' in workflow
    assert "main advanced during publication" in workflow
    assert 'gh release download "$RELEASE_TAG"' in workflow
    assert "sha256sum -c SHA256SUMS" in workflow
    assert 'test "$(git rev-list -n 1 "$RELEASE_TAG")" = "$RELEASE_SHA"' in workflow


def test_release_workflow_attests_subject_set_before_publication() -> None:
    workflow = _text(".github/workflows/release-workbench.yml")

    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert workflow.count("actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d") == 2
    assert "subject-checksums: release-assets/SHA256SUMS" in workflow
    assert "subject-path: release-assets/SHA256SUMS" in workflow
    assert workflow.index("Attest pre-publication release subjects") < workflow.index(
        "Publish GitHub prerelease and exact source tag"
    )
    assert workflow.index("Attest immutable checksum manifest") < workflow.index(
        "Publish GitHub prerelease and exact source tag"
    )


def test_production_release_assurance_only_verifies_trusted_build_attestations() -> None:
    workflow = _text(".github/workflows/production-release-assurance.yml")

    assert "id-token: write" not in workflow
    assert "attestations: write" not in workflow
    assert "actions/attest@" not in workflow
    assert "Verify checksum manifest came from trusted pre-publication build" in workflow
    assert "gh attestation verify verified-release/SHA256SUMS" in workflow
    assert "checksum manifest does not exactly cover release files" in workflow
    assert "sha256sum -c SHA256SUMS" in workflow
    assert 'gh attestation verify "verified-release/$filename"' in workflow
    assert "$GITHUB_REPOSITORY/.github/workflows/release-workbench.yml" in workflow
    assert 'test "$(git rev-parse origin/main)" = "$release_sha"' in workflow
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in workflow


def test_release_runbook_keeps_native_signing_claims_explicitly_bounded() -> None:
    runbook = _text("docs/operations/production-local-release.md")

    assert "Sigstore-backed GitHub artifact attestation" in runbook
    assert "Native Apple notarization" in runbook
    assert "Windows Authenticode signing are **not claimed**" in runbook
    assert "at least 24 hours" in runbook
    assert "#95" in runbook
    assert "#97" in runbook
