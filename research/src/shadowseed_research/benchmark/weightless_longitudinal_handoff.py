"""Read-only per-turn follow-up to an exact canonical first weightless birth.

This is a research sidecar, not a second Shadowseed memory or an inquiry role.
Call after EACH subsequent completed Engine turn, keeping the original first
birth checkpoint and the previous follow-up checkpoint. No model calls,
candidate prompting, Gate evidence or authorization are performed here.

These checks establish consistency between *recorded product events*. They
cannot authenticate the host model, prove semantic growth, or infer the
candidate's contribution to an unscripted later question.
"""

from __future__ import annotations

from typing import Any, Mapping

from shadowseed import ShadowseedEngine

from shadowseed_research.benchmark.weightless_birth_handoff import (
    SCHEMA as BIRTH_SCHEMA,
    _digest,
    _exact_birth_item_lineage,
    _hash_json,
)

SCHEMA = "shadowseed-weightless-longitudinal-checkpoint-v1"


def _verify_record_hash(record: Mapping[str, Any], label: str) -> None:
    digest = record.get("snapshot_sha256")
    if not isinstance(digest, str) or digest != _hash_json({
        key: value for key, value in record.items() if key != "snapshot_sha256"
    }):
        raise ValueError(f"{label} snapshot hash mismatch")


def freeze_weightless_followup(
    engine: ShadowseedEngine,
    birth: Mapping[str, Any],
    *,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect exactly one later observed turn of the SAME live Engine.

    The caller must freeze the real first birth immediately, then call this
    function once after every following turn. A missed checkpoint is rejected;
    its historical trace/status cannot be reliably reconstructed from a final
    manager state. The checkpoint contains no candidate or answer text.
    """
    if engine.has_pending_turn:
        raise ValueError("finish or abort the prepared turn before follow-up")
    if not isinstance(birth, Mapping) or birth.get("schema") != BIRTH_SCHEMA:
        raise ValueError("a canonical first-birth checkpoint is required")
    _verify_record_hash(birth, "birth")
    if (
        birth.get("raw_detector_item_to_seed_mapping_verified") is not True
        or birth.get("eligible_for_automatic_gate_or_prompt") is not False
        or birth.get("ordinary_answer_model_was_not_seed_exposed") is not True
    ):
        raise ValueError("birth did not prove the clean recorded item boundary")
    turn_of_birth = birth.get("session_turn")
    sid = birth.get("seed_id")
    if type(turn_of_birth) is not int or not isinstance(sid, str) or not sid:
        raise ValueError("invalid first-birth turn or seed identity")

    state = engine.export_state()
    reports = state.get("turn_reports")
    current = state.get("turn")
    if (
        type(current) is not int or not isinstance(reports, list)
        or len(reports) != current or current < turn_of_birth + 2
        or turn_of_birth < 0
    ):
        raise ValueError("no complete subsequent chronological live turn")
    for index, report in enumerate(reports):
        if (
            not isinstance(report, dict)
            or report.get("runtime_mode") != "live"
            or report.get("turn") != index
        ):
            raise ValueError("noncanonical or reordered live history")
    last_turn = current - 1
    if last_turn == turn_of_birth + 1:
        if previous is not None:
            raise ValueError("first follow-up must not have a prior checkpoint")
    else:
        if not isinstance(previous, Mapping) or previous.get("schema") != SCHEMA:
            raise ValueError("missing immediately preceding follow-up checkpoint")
        _verify_record_hash(previous, "previous")
        if (
            previous.get("seed_id") != sid
            or previous.get("birth_snapshot_sha256") != birth["snapshot_sha256"]
            or previous.get("turn") != last_turn - 1
            or previous.get("history_sha256") != _hash_json(reports[:last_turn])
        ):
            raise ValueError("previous checkpoint is not the preceding history")

    birth_report = reports[turn_of_birth]
    if (
        birth_report.get("prepared_turn_id") != birth.get("prepared_turn_id")
        or _digest(birth_report.get("question", "")) != birth.get("question_sha256")
        or _digest(birth_report.get("answer", "")) != birth.get("answer_sha256")
        or birth_report.get("first_pass_context_ref") != birth.get("origin", {}).get("context_ref")
        or birth_report.get("seeds_born_weightless", []).count(sid) != 1
        or state.get("born_turn", {}).get(sid) != turn_of_birth
    ):
        raise ValueError("first-birth product history no longer matches freeze")
    candidates = [
        seed for seed in state.get("manager", {}).get("seeds", [])
        if isinstance(seed, dict) and seed.get("id") == sid
    ]
    if len(candidates) != 1:
        raise ValueError("original candidate is missing or ambiguous")
    seed = candidates[0]
    if (
        not isinstance(seed.get("text"), str)
        or _digest(seed["text"]) != birth.get("candidate_text_sha256")
        or seed.get("origin") != birth.get("origin")
    ):
        raise ValueError("original candidate text or origin changed")

    manager = state["manager"]
    births = [
        event for event in manager.get("event_log", [])
        if event.get("seed_id") == sid and event.get("event_type") == "created"
    ]
    if (
        len(births) != 1
        or _hash_json(births[0]) != birth.get("origin_event_sha256")
        or births[0].get("detail", {}).get("text") != seed["text"]
        or births[0].get("detail", {}).get("origin") != seed.get("origin")
    ):
        raise ValueError("first created-event has changed or been duplicated")
    observations = birth_report.get("candidate_observations", [])
    accepted = [
        a for a in birth_report.get("intake_diagnostics", {}).get("accepted", [])
        if a.get("seed_id") == sid
    ]
    if (
        len(accepted) != 1
        or _hash_json(accepted[0]) != birth.get("accepted_candidate_sha256")
        or _hash_json(observations) != birth.get("detector_observations_sha256")
        or len(observations) != birth.get("detector_observation_count")
        or _exact_birth_item_lineage(
            birth_report, sid, seed["text"], birth["origin"]["context_ref"], observations
        ) != birth.get("raw_to_seed_item_lineage")
    ):
        raise ValueError("recorded detector-to-first-birth item changed")

    # There may be other seeds in a real session, but no product answer in
    # this bounded research trace may be steered by ANY seed.
    for report in reports[turn_of_birth:]:
        if (
            report.get("selected_seed_ids")
            or report.get("surfaced_seed_ids")
            or report.get("same_turn_revision_applied")
            or report.get("self_reinforcement_applied")
        ):
            raise ValueError("ordinary answer route received SSL influence")
    # A recurrence-only Gate attempt can be BLOCKED without granting weight.
    # Preserve that actual decision rather than treating "Gate was called"
    # as "authority was granted".
    gate_log = manager.get("gate_events", [])
    if not isinstance(gate_log, list) or any(
        not isinstance(event, dict) for event in gate_log
    ):
        raise ValueError("invalid Gate decision ledger")
    relevant_gate = [event for event in gate_log if event.get("seed_id") == sid]
    # Natural expiry is a legitimate LOSS of a weightless possibility. It
    # reaches the existing Gate as lifecycle_expiry, not evidentiary support.
    # Refusing it would silently exclude precisely the negative paths we need
    # to observe. Other expiry reasons and authoritative decisions still fail.
    natural_expiry = [
        event for event in relevant_gate
        if event.get("decision") == "expired"
        and event.get("policy_id") == "lifecycle_expiry"
        and event.get("reason") == "dormant_ttl"
        and event.get("status_before") == "DORMANT"
        and event.get("status_after") == "EXPIRED"
        and len(event.get("signals", [])) == 1
        and event["signals"][0].get("kind") == "lifecycle_expiry"
        and event["signals"][0].get("direction") == "neutral"
        and event["signals"][0].get("reason") == "dormant_ttl"
    ]
    allowed_lifecycle = (
        len(natural_expiry) == 1 and seed.get("status") == "EXPIRED"
    )
    if any(
        event.get("weight_before") != 0
        or event.get("weight_after") != 0
        or event.get("authority_version") != 0
        or event.get("status_before") == "PROMOTED"
        or event.get("status_after") == "PROMOTED"
        or (
            event.get("decision") not in {"blocked", "no_change"}
            and not (allowed_lifecycle and event is natural_expiry[0])
        )
        for event in relevant_gate
    ):
        raise ValueError("candidate has crossed the Gate authority boundary")
    if seed.get("status") == "EXPIRED" and not allowed_lifecycle:
        raise ValueError("terminal expiry has no verified lifecycle Gate record")
    if (
        seed.get("weight") != 0 or seed.get("evidence_count") != 0
        or seed.get("authority_version") != 0
        or seed.get("status") == "PROMOTED"
    ):
        raise ValueError("candidate is no longer authority-free")

    # The manager event ledger is append-only between successive checkpoints.
    # This is a local integrity check, not tamper-proof external notarization.
    event_log = manager.get("event_log", [])
    if not isinstance(event_log, list) or any(
        not isinstance(item, dict) for item in event_log
    ):
        raise ValueError("invalid seed event ledger")
    if previous is not None:
        prior_n = previous.get("event_log_count")
        prior_gate_n = previous.get("gate_log_count")
        if (
            type(prior_n) is not int or not 0 <= prior_n <= len(event_log)
            or _hash_json(event_log[:prior_n]) != previous.get("event_log_sha256")
            or type(prior_gate_n) is not int
            or not 0 <= prior_gate_n <= len(gate_log)
            or _hash_json(gate_log[:prior_gate_n]) != previous.get("gate_log_sha256")
        ):
            raise ValueError("previous event ledger prefix was modified")
        new_events = event_log[prior_n:]
        new_gate = gate_log[prior_gate_n:]
    else:
        birth_positions = [
            i for i, event in enumerate(event_log)
            if event.get("seed_id") == sid
            and event.get("event_type") == "created"
        ]
        if len(birth_positions) != 1:
            raise ValueError("first seed event is missing or ambiguous")
        # It includes any post-birth activity within T0; do not call it
        # exclusively later-turn events.
        new_events = event_log[birth_positions[0] + 1:]
        new_gate = gate_log

    report = reports[last_turn]
    reported_again = sid in report.get("seeds_born_weightless", [])
    if reported_again:
        rows = report.get("intake_diagnostics", {}).get("item_lineage", [])
        same = [
            item for item in rows
            if isinstance(item, dict)
            and item.get("seed_id") == sid
            and item.get("outcome") == "accepted"
            and item.get("seed_transition") == "deduplicated"
        ]
        if len(same) != 1:
            raise ValueError("repeat candidate lacks recorded deduplication")
    trtl = report.get("reactivated_trtl", [])
    if not isinstance(trtl, list):
        raise ValueError("missing or invalid TrTL report")

    current_seed = {
        "status": seed["status"],
        "trace": seed["trace"],
        "turns_dormant": seed["turns_dormant"],
        "occurrence_count": seed["occurrence_count"],
        "weight": seed["weight"],
        "evidence_count": seed["evidence_count"],
        "authority_version": seed["authority_version"],
    }
    followup = {
        "schema": SCHEMA,
        "seed_id": sid,
        "birth_turn": turn_of_birth,
        "birth_snapshot_sha256": birth["snapshot_sha256"],
        "turn": last_turn,
        "prepared_turn_id": report.get("prepared_turn_id"),
        "previous_checkpoint_sha256": (
            previous["snapshot_sha256"] if previous else None
        ),
        "history_sha256": _hash_json(reports[:last_turn + 1]),
        "turn_report_sha256": _hash_json(report),
        "event_log_count": len(event_log),
        "event_log_sha256": _hash_json(event_log),
        "gate_log_count": len(gate_log),
        "gate_log_sha256": _hash_json(gate_log),
        "new_seed_event_types": [
            event.get("event_type") for event in new_events
            if event.get("seed_id") == sid
        ],
        "new_gate_decisions": [
            event.get("decision") for event in new_gate
            if event.get("seed_id") == sid
        ],
        "question_sha256": _digest(report["question"]),
        "answer_sha256": _digest(report["answer"]),
        "candidate_text_sha256": birth["candidate_text_sha256"],
        "seed_state_after_turn": current_seed,
        "redetected_same_seed_reported": reported_again,
        "trtl_reactivated_same_seed": sid in trtl,
        "candidate_still_same_recorded_text": True,
        "product_answer_seed_influence_observed": False,
        "actual_llm_origin_verified": False,
        "semantic_growth_assessed": False,
        "later_model_originated_inquiry_assessed": False,
        "q1_or_q2_effect_established": False,
        "eligible_for_automatic_gate_or_prompt": False,
    }
    followup["snapshot_sha256"] = _hash_json(followup)
    return followup
