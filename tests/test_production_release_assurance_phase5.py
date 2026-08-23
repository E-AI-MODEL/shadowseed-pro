from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_build_transitively_requires_cross_platform_production_acceptance() -> None:
    workflow = _text(".github/workflows/ci.yml")

    assert "production-local:" in workflow
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in workflow
    assert 'glob.glob("tests/test_workbench_*.py")' in workflow
    assert 'glob.glob("tests/test_production_*_phase4.py")' in workflow
    assert "build:\n    needs: [production-local]" in workflow


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


def test_release_runbook_keeps_native_signing_claims_explicitly_bounded() -> None:
    runbook = _text("docs/operations/production-local-release.md")

    assert "Native Apple notarization" in runbook
    assert "Windows Authenticode signing are **not claimed**" in runbook
    assert "at least 24 hours" in runbook
    assert "#95" in runbook
    assert "#97" in runbook
