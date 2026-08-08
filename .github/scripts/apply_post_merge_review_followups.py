from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


manager_test = Path("tests/test_manager_modularization_complete.py")
manager_test.write_text(
    '''"""Structural completion guards for manager modularization (#25)."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/shadowseed"
MANAGER = SOURCE_ROOT / "manager.py"

FORBIDDEN_CALL_PREFIXES = {
    ("np", "dot"),
    ("np", "mean"),
    ("np", "linalg"),
    ("math", "exp"),
    ("re", "findall"),
}


def _attribute_chain(node: ast.AST) -> tuple[str, ...] | None:
    """Return a complete dotted call target such as ``np.linalg.norm``."""

    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return (node.id, *reversed(parts))


def _forbidden_call_chains(source: str) -> set[tuple[str, ...]]:
    tree = ast.parse(source)
    found: set[tuple[str, ...]] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        chain = _attribute_chain(call.func)
        if chain is None:
            continue
        if any(
            chain[: len(prefix)] == prefix
            for prefix in FORBIDDEN_CALL_PREFIXES
        ):
            found.add(chain)
    return found


def test_manager_stays_a_bounded_orchestration_facade() -> None:
    source = MANAGER.read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 800

    tree = ast.parse(source)
    imported_modules = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "shadowseed"
        for alias in node.names
    }
    assert {"intake_engine", "lifecycle_engine", "vector_workflows"} <= imported_modules

    assert not _forbidden_call_chains(source)


def test_nested_numpy_attribute_chain_is_rejected() -> None:
    source = "def normalize(vector):\\n    return np.linalg.norm(vector)\\n"
    assert _forbidden_call_chains(source) == {("np", "linalg", "norm")}

    facade = (
        "def normalize(vector):\\n"
        "    return intake_engine.normalize_embedding(vector)\\n"
    )
    assert not _forbidden_call_chains(facade)


def test_modularized_runtime_has_explicit_authority_ownership() -> None:
    authority = (ROOT / "repository-authority.yaml").read_text(encoding="utf-8")
    for path in (
        "src/shadowseed/manager.py",
        "src/shadowseed/models.py",
        "src/shadowseed/contradictions.py",
        "src/shadowseed/intake.py",
        "src/shadowseed/lifecycle.py",
        "src/shadowseed/vector_workflows.py",
        "src/shadowseed/gate/**",
    ):
        assert f"- path: {path}" in authority


def test_active_ownership_docs_name_the_final_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    overview = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
    structure = (ROOT / "docs/architecture/repository-structure.md").read_text(
        encoding="utf-8"
    )

    for module in (
        "shadowseed.models",
        "shadowseed.contradictions",
        "shadowseed.intake",
        "shadowseed.lifecycle",
        "shadowseed.vector_workflows",
        "shadowseed.gate",
    ):
        assert module in readme
        assert module in overview
        assert module in structure

    assert "orchestration" in readme
    assert "orchestration" in overview
    assert "Manager modularization" in structure
''',
    encoding="utf-8",
)

agent = Path("src/shadowseed_agent/agent_contract.py")
replace_once(
    agent,
    '''    require_logged_promotion: bool = True
    block_contradicted_seed: bool = True
''',
    '''    # Retained for constructor compatibility. Point-of-use authorization
    # always requires a logged promotion and a live current-version GateEvent.
    require_logged_promotion: bool = True
    block_contradicted_seed: bool = True
''',
)
replace_once(
    agent,
    '''        if self.require_logged_promotion and not has_logged_promotion(seed_id, gate_log):
            return InfluenceDecision(seed_id, action_value, False, "missing_logged_promotion")
''',
    '''        # ``require_logged_promotion`` is retained for constructor compatibility,
        # but it cannot disable this safety requirement. Actual authorization also
        # requires a live current-version GateEvent link in ``decide_and_record``.
        if not has_logged_promotion(seed_id, gate_log):
            return InfluenceDecision(seed_id, action_value, False, "missing_logged_promotion")
''',
)
replace_once(
    agent,
    '''        To let a seed influence an action, use :meth:`decide_and_record`, which
        records the decision and links it to a Gate event.

        (The former public ``decide``/``can_influence`` methods were removed:
''',
    '''        To let a seed influence an action, use :meth:`decide_and_record`, which
        records the decision and links it to a Gate event. Legacy
        ``ValidationGateResult`` logs can show that a promotion occurred, but only
        ``GateEvent`` entries carry enough information for inspection to diagnose a
        stale current-version authorization.

        (The former public ``decide``/``can_influence`` methods were removed:
''',
)
replace_once(
    agent,
    '''        decision = self._decide(
            seed, action, gate_log, contradiction_blocking=contradiction_blocking
        )
        reasons: tuple[str, ...] = () if decision.allowed else (decision.reason,)
        return InfluenceInspection(
            seed_id=decision.seed_id, action=decision.action, blocking_reasons=reasons
        )
''',
    '''        entries = list(gate_log)
        decision = self._decide(
            seed, action, entries, contradiction_blocking=contradiction_blocking
        )
        reasons: tuple[str, ...] = () if decision.allowed else (decision.reason,)

        # ValidationGateResult-style logs can show that a promotion happened, but
        # only GateEvents can prove that the authorization is still current. When
        # GateEvents are supplied, inspection reports the same stale-link problem
        # that ``decide_and_record`` would enforce.
        if decision.allowed and any(
            _value(entry, "event_id", None) is not None for entry in entries
        ):
            current_version = _value(seed, "authority_version", None)
            ref, event_version, _policy_id = self._link_gate_event(
                decision.seed_id, entries, current_version
            )
            if ref is None or event_version != current_version:
                reasons = ("stale_gate_authorization",)

        return InfluenceInspection(
            seed_id=decision.seed_id, action=decision.action, blocking_reasons=reasons
        )
''',
)
replace_once(
    agent,
    '''        Returns the recorded ``AgentInfluenceRecord``.
        """
''',
    '''        ``require_logged_promotion`` is retained as a constructor-compatible
        field, but setting it to ``False`` never bypasses the logged-promotion or
        current-version Gate-event requirements.

        Returns the recorded ``AgentInfluenceRecord``.
        """
''',
)

point_tests = Path("tests/test_point_of_use.py")
point_text = point_tests.read_text(encoding="utf-8")
new_tests = '''


def test_logged_promotion_flag_cannot_bypass_point_of_use_link():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract(require_logged_promotion=False)
    ledger: list = []

    inspection = contract.inspect(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        [],
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=[],
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )

    assert inspection.blocking_reasons == ("missing_logged_promotion",)
    assert record.allowed is False
    assert record.reason == "missing_logged_promotion"


def test_inspect_reports_stale_authorization_for_gate_event_ledgers():
    manager, seed_id = _promoted_manager()
    stale = _promotion_event(
        seed_id,
        version=manager.seeds[seed_id].authority_version - 1,
    )

    inspection = AgentSafetyContract(require_logged_promotion=False).inspect(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        [stale],
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )

    assert inspection.blocking_reasons == ("stale_gate_authorization",)
    assert inspection.is_blocked is True
'''
if "test_logged_promotion_flag_cannot_bypass_point_of_use_link" not in point_text:
    point_tests.write_text(point_text.rstrip() + new_tests + "\n", encoding="utf-8")

lifecycle = Path("docs/architecture/lifecycle-and-gate.md")
replace_once(
    lifecycle,
    '''Promotion is necessary but not sufficient. `AgentSafetyContract` applies specific eligibility checks, not universal safety, before answer modification, retrieval, warnings, probes, or downstream action. It always checks positive weight, `PROMOTED` status, and a live Gate-event link for the current `authority_version`. Blocking-contradiction and logged-promotion checks are enabled by default, but both public configuration options can relax them.
''',
    '''Promotion is necessary but not sufficient. `AgentSafetyContract` applies specific eligibility checks, not universal safety, before answer modification, retrieval, warnings, probes, or downstream action. Actual authorization through `decide_and_record` always checks positive weight, `PROMOTED` status, and a live Gate-event link for the current `authority_version`. `block_contradicted_seed=False` can relax the contradiction check. The legacy `require_logged_promotion` constructor field remains accepted for compatibility, but setting it to `False` does not disable the logged-promotion requirement. `inspect` also reports stale authorization when it receives GateEvents; legacy validation-result logs cannot prove current-version linkage and remain diagnostic only.
''',
)
replace_once(
    lifecycle,
    '''These records are immutable and replayable in process. The runtime does not yet persist them to append-only or tamper-evident storage, does not cryptographically chain them, and does not provide external timestamping. Durable audit integrity remains a production requirement rather than an implemented guarantee.
''',
    '''`GateEvent` and `AgentInfluenceRecord` are frozen and support strict in-process replay. Other retained logs, including `SeedEvent`, `ValidationGateResult`, and `ProbeFeedbackResult`, are ordinary mutable Python objects. None of these records is yet persisted to append-only or tamper-evident storage, cryptographically chained, or externally timestamped. Durable audit integrity remains a production requirement rather than an implemented guarantee.
''',
)

overview = Path("docs/architecture/overview.md")
replace_once(
    overview,
    '''| `shadowseed_agent.agent_contract` | Bounded point-of-use eligibility decision with explicit configurable checks |
''',
    '''| `shadowseed_agent.agent_contract` | Bounded point-of-use eligibility decision with a mandatory current-version Gate-event link and a configurable contradiction check |
''',
)

readme = Path("README.md")
replace_once(
    readme,
    '''| Influence requires one atomic point-of-use decision enforcing specific checks (weight > 0, promoted, live current-version Gate-event link; blocking-contradiction and logged-promotion checks on by default, both configurable) | [`AgentSafetyContract.decide_and_record`](src/shadowseed_agent/agent_contract.py) | [`test_point_of_use.py`](tests/test_point_of_use.py) |
''',
    '''| Influence requires one atomic point-of-use decision enforcing positive weight, promoted status, and a live current-version Gate-event link; the contradiction check is configurable, but the Gate-event requirement is not | [`AgentSafetyContract.decide_and_record`](src/shadowseed_agent/agent_contract.py) | [`test_point_of_use.py`](tests/test_point_of_use.py) |
''',
)
replace_once(
    readme,
    '''- **The point-of-use contract enforces specific checks, not universal safety.** [`AgentSafetyContract.decide_and_record`](src/shadowseed_agent/agent_contract.py) always requires that the seed has `weight > 0`, is promoted, and links to a live Gate event of the seed's *current* `authority_version` (stale authorizations are rejected). In the **default configuration** it also blocks a seed with a blocking contradiction (`block_contradicted_seed=True`) and requires a logged promotion (`require_logged_promotion=True`) — but both are public opt-outs on the contract, so an integration that constructs, e.g., `AgentSafetyContract(block_contradicted_seed=False)` relaxes them. Every decision — allowed or denied — is recorded ([`test_point_of_use.py`](tests/test_point_of_use.py), [`test_agent_safety_contract.py`](tests/test_agent_safety_contract.py)). "Zero-trust at the agent boundary" names this specific gate under its default configuration; it does **not** imply complete policy enforcement, protection against every integration that ignores or reconfigures the contract, or safety against all prompt-injection or evidence-poisoning attacks (see [Not established](#not-established)).
''',
    '''- **The point-of-use contract enforces specific checks, not universal safety.** [`AgentSafetyContract.decide_and_record`](src/shadowseed_agent/agent_contract.py) always requires that the seed has `weight > 0`, is promoted, and links to a live Gate event of the seed's *current* `authority_version` (stale authorizations are rejected). In the **default configuration** it also blocks a seed with a blocking contradiction (`block_contradicted_seed=True`); that contradiction check can be relaxed with `block_contradicted_seed=False`. The legacy `require_logged_promotion` constructor field remains accepted for compatibility, but setting it to `False` does not bypass logged-promotion checks, and `decide_and_record()` still requires a live current-version Gate-event link. When `inspect()` receives GateEvents, it reports stale authorization too; legacy validation-result logs cannot prove current-version linkage and remain diagnostic only. Every decision — allowed or denied — is recorded ([`test_point_of_use.py`](tests/test_point_of_use.py), [`test_agent_safety_contract.py`](tests/test_agent_safety_contract.py)). "Zero-trust at the agent boundary" names this specific gate under its default configuration; it does **not** imply complete policy enforcement, protection against every integration that ignores or reconfigures the contract, or safety against all prompt-injection or evidence-poisoning attacks (see [Not established](#not-established)).
''',
)

claims = Path("tests/test_claim_boundaries.py")
replace_once(
    claims,
    '''    assert "specific eligibility checks, not universal safety" in LIFECYCLE
    assert "both public configuration options" in LIFECYCLE
    assert "not production-ready" in README
''',
    '''    assert "specific eligibility checks, not universal safety" in LIFECYCLE
    assert "ordinary mutable Python objects" in LIFECYCLE
    assert "constructor field remains accepted for compatibility" in LIFECYCLE
    assert "both public configuration options" not in LIFECYCLE
    assert "both configurable" not in README
    assert "both are public opt-outs" not in README
    assert "not production-ready" in README
''',
)
