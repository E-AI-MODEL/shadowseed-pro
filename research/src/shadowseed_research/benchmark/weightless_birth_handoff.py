"""Freeze an ACTUAL product seed birth for later, separately reviewed inquiry.

Research-only snapshot. It consumes the unchanged public ShadowseedEngine
prepare_turn -> host generation -> observe_turn -> export_state sequence.
It does NOT create a seed, reinterpret detector prose, call a model, build
an inquiry prompt, submit Gate evidence, or allow seed influence. It only
checks a canonical first birth before a future Q1/Q2 experimental handoff.

The returned hashes bind *locally provided* records; they are not source
authenticity, independent review, or evidence of latent model representations.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

from shadowseed import ShadowseedEngine

SCHEMA = "shadowseed-first-birth-research-handoff-v0"


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _hash_json(data: Any) -> str:
    return _digest(
        json.dumps(data, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False)
    )


def freeze_canonical_weightless_birth(
    engine: ShadowseedEngine,
    observed_turn: Mapping[str, Any],
    seed_id: str,
    *,
    include_candidate_text: bool = False,
) -> dict[str, Any]:
    """Produce a read-only research *candidate identity* checkpoint.

    Only a first birth in the just-completed observed turn qualifies.
    A repeat detector hit cannot masquerade as a second birth, even though
    product turn reports retain the older 'seeds_born_weightless' list name.

    This function grants NO approval to feed a candidate to the ordinary
    answer model. A separate prospective research protocol, source reviewer,
    independent evaluator and matched ablation must approve any next step.
    """
    if engine.has_pending_turn:
        raise ValueError("complete or abort the prepared turn before freezing")
    if not isinstance(seed_id, str) or not seed_id:
        raise ValueError("seed_id must be a nonempty canonical ID")
    state = engine.export_state()
    reports = state.get("turn_reports", [])
    if not reports or not isinstance(reports[-1], dict):
        raise ValueError("no completed canonical turn report")
    canonical = reports[-1]
    if dict(observed_turn) != canonical:
        raise ValueError("provided turn report is not the latest canonical report")
    turn = canonical.get("turn")
    if not isinstance(turn, int) or isinstance(turn, bool):
        raise ValueError("canonical report has no valid turn index")
    if state.get("turn") != turn + 1:
        raise ValueError("turn chronology mismatch")
    if canonical.get("runtime_mode") != "live":
        raise ValueError("only the canonical live runtime is eligible")
    if canonical.get("surfaced_seed_ids") or canonical.get("selected_seed_ids"):
        raise ValueError("the birth turn already exposed an answer-influencing seed")
    if canonical.get("same_turn_revision_applied"):
        raise ValueError("same-turn revision is not eligible")
    if seed_id not in canonical.get("seeds_born_weightless", []):
        raise ValueError("seed_id was not accepted on this turn")
    if state.get("born_turn", {}).get(seed_id) != turn:
        raise ValueError("accepted recurrence is not a new seed birth")

    candidates = [
        s for s in state.get("manager", {}).get("seeds", [])
        if s.get("id") == seed_id
    ]
    if len(candidates) != 1:
        raise ValueError("exact canonical seed is missing or duplicated")
    seed = candidates[0]
    if (
        seed.get("weight") != 0
        or seed.get("evidence_count") != 0
        or seed.get("occurrence_count") != 1
        or seed.get("authority_version") != 0
        or seed.get("status") == "PROMOTED"
    ):
        raise ValueError("candidate is not an unpromoted first-birth seed")

    ref = canonical.get("first_pass_context_ref")
    origin = seed.get("origin")
    if not isinstance(origin, dict) or (
        origin.get("context_ref") != ref
        or origin.get("detection_basis") != "visible_answer_non_ssl_attributed"
    ):
        raise ValueError("seed origin is not the clean first-pass generation")

    created = [
        event for event in state["manager"].get("event_log", [])
        if event.get("event_type") == "created" and event.get("seed_id") == seed_id
    ]
    if (
        len(created) != 1
        or created[0].get("detail", {}).get("origin") != origin
        or created[0].get("detail", {}).get("text") != seed.get("text")
    ):
        raise ValueError("canonical created event and seed origin disagree")
    if any(
        event.get("seed_id") == seed_id
        for event in state["manager"].get("gate_events", [])
    ):
        raise ValueError("seed already has Gate evidence or a Gate decision")

    accepted = [
        entry for entry in canonical.get("intake_diagnostics", {}).get("accepted", [])
        if entry.get("seed_id") == seed_id
    ]
    if len(accepted) != 1 or accepted[0].get("text") != seed.get("text"):
        raise ValueError("intake acceptance does not match canonical seed text")
    if not isinstance(seed.get("text"), str) or not seed["text"].strip():
        raise ValueError("empty seed text")

    observations = canonical.get("candidate_observations", [])
    if not observations or any(
        item.get("ssl_exposed") or item.get("context_ref") != ref
        for item in observations
    ):
        raise ValueError("missing or SSL-contaminated detector observation trace")

    snapshot = {
        "schema": SCHEMA,
        "session_turn": turn,
        "prepared_turn_id": canonical.get("prepared_turn_id"),
        "seed_id": seed_id,
        "candidate_text_sha256": _digest(seed["text"]),
        "origin": dict(origin),
        "origin_event_sha256": _hash_json(created[0]),
        "accepted_candidate_sha256": _hash_json(accepted[0]),
        "detector_observations_sha256": _hash_json(observations),
        "detector_prompt_contract": canonical.get("detector_audit", {}).get(
            "prompt_contract", None
        ),
        "origin_of_visible_answer_not_verified": True,
        "question_sha256": _digest(canonical["question"]),
        "answer_sha256": _digest(canonical["answer"]),
        "authority_at_birth": {
            "weight": seed["weight"],
            "evidence_count": seed["evidence_count"],
            "occurrence_count": seed["occurrence_count"],
            "authority_version": seed["authority_version"],
            "status": seed["status"],
        },
        "candidate_origin_is_observed_not_independently_validated": True,
        "ordinary_answer_model_was_not_seed_exposed": True,
        "subsequent_inquiry_generated": False,
        "independent_question_or_evidence_review": False,
        "q1_or_q2_effect_established": False,
        "eligible_for_automatic_gate_or_prompt": False,
    }
    if include_candidate_text:
        snapshot["candidate_text"] = seed["text"]
    snapshot["snapshot_sha256"] = _hash_json(snapshot)
    return snapshot
