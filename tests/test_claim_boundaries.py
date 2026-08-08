"""Regression guards for public claim and assurance boundaries (#23)."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
OVERVIEW = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "docs/architecture/lifecycle-and-gate.md").read_text(
    encoding="utf-8"
)
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.split())


def test_atomicity_is_never_presented_as_a_semantic_guarantee() -> None:
    assert "The candidate is stored as an atomic shadow seed." not in README
    assert "A seed is one atomic candidate absence." not in README
    assert "A detector proposes an atomic candidate absence." not in OVERVIEW

    assert "normalization target and tested heuristic" in README
    assert "does not guarantee semantic atomicity" in README
    assert "can still produce a compound, vague, or weak candidate" in OVERVIEW


def test_non_bypassable_claim_is_scoped_to_supported_runtime_decisions() -> None:
    compact_overview = _compact(OVERVIEW)

    assert "single non-bypassable Validation Gate" not in compact_overview
    assert "supported runtime API" in compact_overview
    assert (
        "Restoration and explicitly unsafe test hooks remain outside"
        in compact_overview
    )
    assert '"Non-bypassable" is a public-API property' in README


def test_audit_and_point_of_use_claims_keep_their_limits_visible() -> None:
    assert "append-only, tamper-evident storage" in README
    assert "append-only or tamper-evident" in LIFECYCLE
    assert "specific eligibility checks, not universal safety" in LIFECYCLE
    assert "ordinary mutable Python objects" in LIFECYCLE
    assert "constructor field remains accepted for compatibility" in LIFECYCLE
    assert "both public configuration options" not in LIFECYCLE
    assert "both configurable" not in README
    assert "both are public opt-outs" not in README
    assert "not production-ready" in README


def test_claim_table_links_to_canonical_modules_after_modularization() -> None:
    for target in (
        "src/shadowseed/models.py",
        "src/shadowseed/intake.py",
        "src/shadowseed/lifecycle.py",
        "src/shadowseed/contradictions.py",
        "src/shadowseed/gate/runtime_adapter.py",
    ):
        assert target in README
    assert "[`ShadowSeed`](src/shadowseed/manager.py)" not in README
    assert "[`SeedOrigin`](src/shadowseed/manager.py)" not in README


def test_changelog_records_the_completed_modularization_contract() -> None:
    compact_changelog = _compact(CHANGELOG)

    assert "Unreleased - Manager modularization and Gate boundary completion" in CHANGELOG
    for module in (
        "shadowseed.models",
        "shadowseed.contradictions",
        "shadowseed.intake",
        "shadowseed.lifecycle",
        "shadowseed.vector_workflows",
        "shadowseed.gate.runtime_adapter",
    ):
        assert module in CHANGELOG

    assert "from an instance attribute to a property" in compact_changelog
    assert "has no effect on authorization" in compact_changelog
    assert "both configurable opt-outs" not in compact_changelog


def test_ci_assurance_choices_are_explicit() -> None:
    assert "Build wheel and sdist" in CI
    assert "Install from the built wheel in a clean venv" in CI
    assert "CLI smoke (installed package, outside the source tree)" in CI
    assert "Static type checking" in CI
    assert "Coverage" in CI
    assert "Optional backends" in CI
