"""Regression guards for public claim and assurance boundaries (#23)."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
OVERVIEW = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "docs/architecture/lifecycle-and-gate.md").read_text(
    encoding="utf-8"
)
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
STANDALONE_WORKFLOW = (
    ROOT / ".github/workflows/standalone-workbench.yml"
).read_text(encoding="utf-8")
RELEASE_WORKFLOW = (ROOT / ".github/workflows/release-workbench.yml").read_text(
    encoding="utf-8"
)


def _compact(text: str) -> str:
    return " ".join(text.split())


def test_atomicity_is_never_presented_as_a_semantic_guarantee() -> None:
    assert "The candidate is stored as an atomic shadow seed." not in README
    assert "A seed is one atomic candidate absence." not in README
    assert "A detector proposes an atomic candidate absence." not in OVERVIEW

    assert "normalization target and tested heuristic" in README
    assert "does not guarantee semantic atomicity" in README
    assert "can still produce a compound, vague, or weak candidate" in OVERVIEW


def test_readme_defines_the_general_bounded_candidate_contract() -> None:
    assert "bounded epistemic candidates for investigation" in README
    assert "records a possible omission as a **candidate for investigation**" not in README
    for candidate_kind in (
        "suspected gap",
        "doubt",
        "missing relation or boundary",
        "dependency",
        "unstated assumption",
        "alternative hypothesis",
        "contradiction to investigate",
        "relevant what-if direction",
    ):
        assert candidate_kind in README


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
    assert "durable tamper-evident authority ledger" in README
    assert "not an external immutable ledger" in README
    assert "append-only or tamper-evident" in LIFECYCLE
    assert "specific eligibility checks, not universal safety" in LIFECYCLE
    assert "ordinary mutable Python objects" in LIFECYCLE
    assert "constructor field remains accepted for compatibility" in LIFECYCLE
    assert "both public configuration options" not in LIFECYCLE
    assert "both configurable" not in README
    assert "both are public opt-outs" not in README
    assert "not yet production-ready" in README


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


def test_readme_keeps_onboarding_visible_and_details_balanced() -> None:
    first_screen = "\n".join(README.splitlines()[:100])

    assert "## Quick start" in first_screen
    assert "research-ready, not yet production-ready" in first_screen
    assert "PolyForm Noncommercial License 1.0.0" in first_screen
    assert "This is not an OSI open-source license" in first_screen
    assert "```mermaid" in README
    assert "For the complete command list" not in README
    assert "shadowseed --help" in README
    assert "run-dialectic-falsification" in README
    assert README.count("<details>") == README.count("</details>")
    assert 1 <= README.count("<details>") <= 6


def test_changelog_records_the_completed_modularization_contract() -> None:
    compact_changelog = _compact(CHANGELOG)

    assert "0.5.0 - Chat-first mass tester preview" in CHANGELOG
    assert (
        "Historical development notes - Manager modularization and Gate boundary completion"
        in CHANGELOG
    )
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


def test_external_github_actions_are_immutable() -> None:
    mutable = []
    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        for line_number, line in enumerate(
            workflow.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = re.search(r"\buses:\s*([^\s#]+)", line)
            if match is None:
                continue
            action = match.group(1)
            if action.startswith("./"):
                continue
            _, separator, ref = action.rpartition("@")
            if separator != "@" or re.fullmatch(r"[0-9a-f]{40}", ref) is None:
                mutable.append(f"{workflow.relative_to(ROOT)}:{line_number}: {action}")

    assert not mutable, "mutable external Action refs:\n" + "\n".join(mutable)


def test_dependency_updates_keep_the_lockfile_authoritative() -> None:
    # CI resolves the production closure from `uv.lock` and gates on
    # `uv lock --check`. The `pip` ecosystem updates only `pyproject.toml`, so
    # every automated bump would leave the lockfile stale and fail that gate.
    assert (ROOT / "uv.lock").is_file()
    assert "uv lock --check" in CI

    dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    ecosystems = set(re.findall(r"^\s*-?\s*package-ecosystem:\s*(\S+)", dependabot, re.M))

    assert ecosystems == {"uv", "github-actions"}


def test_release_candidate_is_refreshed_for_every_main_push() -> None:
    push_section = STANDALONE_WORKFLOW.split("  push:\n", 1)[1].split(
        "  workflow_dispatch:", 1
    )[0]

    assert "branches: [main]" in push_section
    assert "paths:" not in push_section


def test_release_revalidates_main_at_the_publication_boundary() -> None:
    publish_step = RELEASE_WORKFLOW.split(
        "      - name: Publish GitHub prerelease and exact source tag\n", 1
    )[1].split("      - name: Verify published tag and downloadable assets\n", 1)[0]

    assert publish_step.count("git fetch origin main --force") >= 2
    assert 'test "$(git rev-parse origin/main)" = "$RELEASE_SHA"' in publish_step
    assert 'gh release create "$RELEASE_TAG"' in publish_step
    assert 'if [ "$(git rev-parse origin/main)" != "$RELEASE_SHA" ]; then' in publish_step
    assert 'gh release delete "$RELEASE_TAG" --cleanup-tag --yes' in publish_step

    create_index = publish_step.index('gh release create "$RELEASE_TAG"')
    first_fetch_index = publish_step.index("git fetch origin main --force")
    second_fetch_index = publish_step.index("git fetch origin main --force", first_fetch_index + 1)
    rollback_index = publish_step.index(
        'gh release delete "$RELEASE_TAG" --cleanup-tag --yes'
    )
    assert first_fetch_index < create_index < second_fetch_index < rollback_index
