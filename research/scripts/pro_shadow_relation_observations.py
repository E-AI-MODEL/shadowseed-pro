"""Research-only ledger for possible later relations around real Pro seed IDs.

No LLM calls, no model introspection, no truth or atomicity scores. The calling
researcher supplies a source-attributed observation AFTER the Pro engine turn.
This does not write back to Pro, open the Validation Gate or steer the host.
Keep full private events OFF public GitHub/CI; publish only safe_aggregate().
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def record_observation(
    *,
    pro_state: Mapping[str, Any],
    source_seed_ids: Sequence[str],
    observer: str,
    source_ref: str,
    turn_index: int,
    event_index: int,
    proposed_text: str | None,
) -> dict[str, Any]:
    """Record a possible relation or no-proposal outcome without judging it.

    The independent observer's declaration is an AUDIT LABEL, not a verified
    assertion about internal model reasoning or actual relation formation.
    """
    if not isinstance(turn_index, int) or turn_index < 0:
        raise ValueError("turn_index must be a non-negative integer")
    if not isinstance(event_index, int) or event_index < 0:
        raise ValueError("event_index must be a non-negative integer")
    if not isinstance(observer, str) or not observer.strip():
        raise ValueError("observer provenance required")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise ValueError("source_ref required")
    if not isinstance(source_seed_ids, (list, tuple)) or not source_seed_ids:
        raise ValueError("at least one original seed ID required")
    if len(set(source_seed_ids)) != len(source_seed_ids):
        raise ValueError("duplicate source IDs must not count as independent inputs")
    if proposed_text is not None and (not isinstance(proposed_text, str) or not proposed_text.strip()):
        raise ValueError("a proposal must be nonempty, or explicitly None")

    original = pro_state.get("seeds")
    if not isinstance(original, list):
        raise ValueError("input must be an actual Pro inspection projection")
    seeds = {item["id"]: item for item in original}
    checked = []
    for seed_id in source_seed_ids:
        if not isinstance(seed_id, str) or seed_id not in seeds:
            raise ValueError("unknown source seed: use actual Pro state IDs")
        seed = seeds[seed_id]
        if seed.get("weight") != 0 or seed.get("scope_status") not in {"bounded", "unresolved"}:
            raise ValueError("the research observation must reference weightless Pro seeds")
        checked.append({
            "id": seed_id,
            "scope_status": seed["scope_status"],
            "text_sha256": sha256(seed["text"].encode("utf-8")).hexdigest(),
            "trace": seed.get("trace"),
            "status": seed.get("status"),
        })
    record = {
        "contract": "pro-weightless-relational-observation-v1",
        "event_type": "no_proposal" if proposed_text is None else "possible_relation_proposed",
        "turn_index": turn_index,
        "event_index": event_index,
        "observer_declared": observer.strip(),
        "source_ref": source_ref.strip(),
        "seed_origins": checked,
        "proposed_text": proposed_text,
        "semantic_verdict": None,
        "originality_verdict": None,
        "authority_contribution": 0,
        "host_answer_influence": False,
        "model_internal_novelty_proven": False,
        "pro_state_sha256": sha256(_canonical(pro_state)).hexdigest(),
    }
    record["event_id"] = sha256(_canonical(record)).hexdigest()
    return record


def safe_aggregate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Public provenance summary: never expose raw proposals, seed text or refs."""
    kinds: dict[str, int] = {}
    for record in records:
        if record.get("contract") != "pro-weightless-relational-observation-v1":
            raise ValueError("unrecognized record contract")
        kind = str(record["event_type"])
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "status": "author-attributed_interpretations_NOT_independent_scientific_review",
        "events": len(records),
        "by_event_type": kinds,
        "authoritative_gate_events": 0,
        "candidate_text_included": False,
        "q2_claim": "NOT TESTED BY THIS LEDGER",
    }
