from pathlib import Path


README_TABLE_OLD = '''| Atomicity is a normalization target and tested heuristic, not a guarantee for every candidate | [`manager.py`](src/shadowseed/manager.py), [`seed_normalization.py`](src/shadowseed/seed_normalization.py) | [`test_atomic_seed_rules.py`](tests/test_atomic_seed_rules.py), [`test_seed_normalization.py`](tests/test_seed_normalization.py) |
| New seeds start weightless, and authority is encapsulated | [`ShadowSeed`](src/shadowseed/manager.py) (authority fields are `init=False` and guarded; the seed registry is a read-only view) | [`test_authority_encapsulation.py`](tests/test_authority_encapsulation.py) |
| Trace is separate from influence | [`manager.py`](src/shadowseed/manager.py) | [`test_manager_alignment.py`](tests/test_manager_alignment.py), [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py) |
| TTL decay and terminal expiry | [`SSLManager.decay_traces`](src/shadowseed/manager.py) | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py), [`test_bad_seed_dies_out.py`](tests/test_bad_seed_dies_out.py) |
| TrTL reactivation | [`SSLManager.reactivate_by_text`](src/shadowseed/manager.py) | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py) |
| Effects route through one Gate via typed signals and a named policy | [`SSLManager.submit_signals`](src/shadowseed/manager.py), [`shadowseed.gate`](src/shadowseed/gate/) | [`test_gate_contracts.py`](tests/test_gate_contracts.py), [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py), [`test_gate_path_unification.py`](tests/test_gate_path_unification.py) |
| Recurrence is never relabeled or double-counted as external evidence | [`shadowseed.gate.signals`](src/shadowseed/gate/signals.py), [`chat.py`](src/shadowseed/chat.py) | [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py) |
| Contradictions have an auditable lifecycle and Gate-controlled recovery | [`shadowseed.gate.contradictions`](src/shadowseed/gate/contradictions.py), [`SSLManager.resolve_contradiction`](src/shadowseed/manager.py) | [`test_contradiction_lifecycle.py`](tests/test_contradiction_lifecycle.py) |
'''

README_TABLE_NEW = '''| Atomicity is a normalization target and tested heuristic, not a guarantee for every candidate | [`intake.py`](src/shadowseed/intake.py), [`seed_normalization.py`](src/shadowseed/seed_normalization.py) | [`test_atomic_seed_rules.py`](tests/test_atomic_seed_rules.py), [`test_seed_normalization.py`](tests/test_seed_normalization.py), [`test_intake_extraction.py`](tests/test_intake_extraction.py) |
| New seeds start weightless, and authority is encapsulated | [`ShadowSeed`](src/shadowseed/models.py), [`intake.py`](src/shadowseed/intake.py) (authority fields are `init=False` and guarded; the seed registry is a read-only view) | [`test_authority_encapsulation.py`](tests/test_authority_encapsulation.py), [`test_models_extraction.py`](tests/test_models_extraction.py) |
| Trace is separate from influence | [`models.py`](src/shadowseed/models.py), [`lifecycle.py`](src/shadowseed/lifecycle.py) | [`test_manager_alignment.py`](tests/test_manager_alignment.py), [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py) |
| TTL decay and terminal expiry | [`lifecycle.py`](src/shadowseed/lifecycle.py) through the `SSLManager` compatibility facade | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py), [`test_bad_seed_dies_out.py`](tests/test_bad_seed_dies_out.py), [`test_lifecycle_extraction.py`](tests/test_lifecycle_extraction.py) |
| TrTL reactivation | [`lifecycle.py`](src/shadowseed/lifecycle.py) through the `SSLManager` compatibility facade | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py), [`test_lifecycle_extraction.py`](tests/test_lifecycle_extraction.py) |
| Gate-controlled effects route through one engine via typed signals and a named policy | [`runtime_adapter.py`](src/shadowseed/gate/runtime_adapter.py), [`SSLManager.submit_signals`](src/shadowseed/manager.py) facade | [`test_gate_contracts.py`](tests/test_gate_contracts.py), [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py), [`test_gate_path_unification.py`](tests/test_gate_path_unification.py), [`test_gate_boundary_completion.py`](tests/test_gate_boundary_completion.py) |
| Recurrence is never relabeled or double-counted as external evidence | [`shadowseed.gate.signals`](src/shadowseed/gate/signals.py), [`chat.py`](src/shadowseed/chat.py) | [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py) |
| Contradictions have an auditable lifecycle and Gate-controlled recovery | [`contradictions.py`](src/shadowseed/contradictions.py), [`runtime_adapter.py`](src/shadowseed/gate/runtime_adapter.py), [`shadowseed.gate.contradictions`](src/shadowseed/gate/contradictions.py) | [`test_contradiction_lifecycle.py`](tests/test_contradiction_lifecycle.py), [`test_contradictions_extraction.py`](tests/test_contradictions_extraction.py) |
'''

CLAIM_TEST = r'''"""Regression guards for public claim and assurance boundaries (#23)."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
OVERVIEW = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "docs/architecture/lifecycle-and-gate.md").read_text(
    encoding="utf-8"
)
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")


def test_atomicity_is_never_presented_as_a_semantic_guarantee() -> None:
    assert "The candidate is stored as an atomic shadow seed." not in README
    assert "A seed is one atomic candidate absence." not in README
    assert "A detector proposes an atomic candidate absence." not in OVERVIEW

    assert "normalization target and tested heuristic" in README
    assert "does not guarantee semantic atomicity" in README
    assert "can still produce a compound, vague, or weak candidate" in OVERVIEW


def test_non_bypassable_claim_is_scoped_to_supported_runtime_decisions() -> None:
    assert "single non-bypassable Validation Gate" not in OVERVIEW
    assert "supported runtime API" in OVERVIEW
    assert "Restoration and explicitly unsafe test hooks remain outside" in OVERVIEW
    assert '"Non-bypassable" is a public-API property' in README


def test_audit_and_point_of_use_claims_keep_their_limits_visible() -> None:
    assert "append-only, tamper-evident storage" in README
    assert "append-only or tamper-evident" in LIFECYCLE
    assert "specific eligibility checks, not universal safety" in LIFECYCLE
    assert "both public configuration options" in LIFECYCLE
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


def test_ci_assurance_choices_are_explicit() -> None:
    assert "Build wheel and sdist" in CI
    assert "Install from the built wheel in a clean venv" in CI
    assert "CLI smoke (installed package, outside the source tree)" in CI
    assert "Static type checking" in CI
    assert "Coverage" in CI
    assert "Optional backends" in CI
'''


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one anchor, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    readme = Path("README.md")
    replace_once(
        readme,
        "Shadow Seed Learning, or SSL, treats a possible omission in a model answer as a **candidate for investigation**, not as hidden truth. The candidate is stored as an atomic shadow seed. It may recur, decay, reactivate, collect evidence, face contradiction, and be promoted. It may influence retrieval or an answer only after a logged Validation Gate decision and a second point-of-use safety check.\n",
        "Shadow Seed Learning, or SSL, treats a possible omission in a model answer as a **candidate for investigation**, not as hidden truth. Normalization tries to represent it as one small, testable shadow seed, but does not guarantee semantic atomicity. The seed may recur, decay, reactivate, collect evidence, face contradiction, and be promoted. It may influence retrieval or an answer only after a logged Validation Gate decision and a second point-of-use eligibility check.\n",
    )
    replace_once(
        readme,
        "A seed is one atomic candidate absence.\n",
        "A seed is intended to represent one candidate absence. Atomicity is a normalization target and tested heuristic; a generated candidate can still be compound, vague, or poorly split.\n",
    )
    replace_once(
        readme,
        "    D --> N[Normalize into atomic seeds]\n",
        "    D --> N[Normalize toward one absence per seed]\n",
    )
    replace_once(readme, README_TABLE_OLD, README_TABLE_NEW)
    replace_once(
        readme,
        "Normalization splits candidates toward one absence each ([`seed_normalization.py`](src/shadowseed/seed_normalization.py), [`test_atomic_seed_rules.py`](tests/test_atomic_seed_rules.py)), but a model-generated candidate can still be compound, vacuous, or mis-split.",
        "Normalization splits candidates toward one absence each ([`intake.py`](src/shadowseed/intake.py), [`seed_normalization.py`](src/shadowseed/seed_normalization.py), [`test_atomic_seed_rules.py`](tests/test_atomic_seed_rules.py)), but a model-generated candidate can still be compound, vacuous, or mis-split.",
    )
    replace_once(
        readme,
        "[`SeedOrigin`](src/shadowseed/manager.py) records why a detector proposed a candidate",
        "[`SeedOrigin`](src/shadowseed/models.py) records why a detector proposed a candidate",
    )

    overview = Path("docs/architecture/overview.md")
    replace_once(
        overview,
        "1. A detector proposes an atomic candidate absence.\n",
        "1. A detector proposes a candidate intended to represent one absence; normalization uses tested heuristics and can still produce a compound, vague, or weak candidate.\n",
    )
    replace_once(
        overview,
        "Authority — whether a seed may eventually influence behavior — is governed by a\nsingle non-bypassable Validation Gate. The details live in dedicated documents;\nin summary:\n",
        "Authority — whether a seed may eventually influence behavior — is governed by one\nGate-controlled decision engine on the supported runtime API. Restoration and\nexplicitly unsafe test hooks remain outside that new-decision guarantee. The\ndetails live in dedicated documents; in summary:\n",
    )
    replace_once(
        overview,
        "  guarded; the manager's single transition path is the only writer, and the seed\n  registry is a read-only view. Deserialization uses `ShadowSeed.from_dict` /\n",
        "  guarded; `SSLManager._set_authority` is the only runtime writer, while Gate\n  decisions and mechanical intake/lifecycle transitions remain distinct. The\n  seed registry is a read-only view. Deserialization uses `ShadowSeed.from_dict` /\n",
    )
    replace_once(
        overview,
        "| `shadowseed_agent.agent_contract` | Zero-trust point-of-use influence decision |\n",
        "| `shadowseed_agent.agent_contract` | Bounded point-of-use eligibility decision with explicit configurable checks |\n",
    )

    lifecycle = Path("docs/architecture/lifecycle-and-gate.md")
    replace_once(
        lifecycle,
        "The manager models the lifecycle with states such as `NEW`, `ACTIVE`, `DECAYING`, `DORMANT`, `PROMOTED`, and `EXPIRED`.\n",
        "`ShadowSeed` defines states such as `NEW`, `ACTIVE`, `DECAYING`, `DORMANT`, `PROMOTED`, and `EXPIRED`; `shadowseed.lifecycle` implements the mechanical TTL, dormancy, TrTL, and expiry transitions.\n",
    )
    replace_once(
        lifecycle,
        "`weight` is steering power. New candidates start at `0.0`. The manager can raise weight only through a successful Validation Gate decision.\n",
        "`weight` is steering power. New candidates start at `0.0`. Gate-controlled increases are decided only inside the Validation Gate engine; explicit mechanical transitions may reduce or clear authority but do not validate a candidate.\n",
    )
    replace_once(
        lifecycle,
        "decision. Their manager call sites are pinned by an exact invariant-test allowlist.\nThe corresponding probe and contradiction-resolution methods on `SSLManager` are\n",
        "decision. Their canonical intake/lifecycle call sites are pinned by an exact\ninvariant-test allowlist. The corresponding probe and contradiction-resolution\nmethods on `SSLManager` are\n",
    )
    replace_once(
        lifecycle,
        "Promotion is necessary but not sufficient. `AgentSafetyContract` verifies the seed again before answer modification, retrieval, warnings, probes, or downstream action. It checks promotion state, positive weight, evidence suitability, and the presence of a logged promotion decision.\n",
        "Promotion is necessary but not sufficient. `AgentSafetyContract` applies specific eligibility checks, not universal safety, before answer modification, retrieval, warnings, probes, or downstream action. It always checks positive weight, `PROMOTED` status, and a live Gate-event link for the current `authority_version`. Blocking-contradiction and logged-promotion checks are enabled by default, but both public configuration options can relax them.\n",
    )
    replace_once(
        lifecycle,
        "- baseline and SSL outputs as separate fields.\n",
        "- baseline and SSL outputs as separate fields.\n\nThese records are immutable and replayable in process. The runtime does not yet persist them to append-only or tamper-evident storage, does not cryptographically chain them, and does not provide external timestamping. Durable audit integrity remains a production requirement rather than an implemented guarantee.\n",
    )

    Path("tests/test_claim_boundaries.py").write_text(CLAIM_TEST, encoding="utf-8")

    Path(".github/workflows/close-claim-boundaries.yml").unlink()
    Path(".github/scripts/close_claim_boundaries.py").unlink()


if __name__ == "__main__":
    main()
