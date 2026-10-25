"""Read-only dossier for historical SSOT automatic-support events.

This is a review aid, not an authority check, Gate, migration or verification
procedure. It MUST NOT create or submit a ValidationSignal, restore weight,
clear the point-of-use quarantine, or rewrite historical ledger records.

The dossier is built from caller-supplied canonical snapshots. It does not
certify that the source material exists, that it is independent, or that a
person actually reviewed any source-to-seed relationship.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from hashlib import sha256
import json
from typing import Any

from shadowseed_agent.agent_contract import (
    has_unreviewed_ssot_support,
    is_known_legacy_ssot_support_signal,
)

DOSSIER_SCHEMA = "legacy-ssot-review-dossier-v1"


def _payload(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    if callable(getattr(item, "to_dict", None)):
        converted = item.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if is_dataclass(item) and not isinstance(item, type):
        return asdict(item)
    raise TypeError("review input must be a typed record or mapping")


def _canonical_digest(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _name(value: Any) -> str:
    return str(getattr(value, "value", value))


def build_legacy_ssot_review_dossier(
    seed: Mapping[str, Any] | Any,
    gate_events: Iterable[Mapping[str, Any] | Any],
    influence_records: Iterable[Mapping[str, Any] | Any] = (),
    *,
    session_id: str | None = None,
    include_source_refs: bool = False,
) -> dict[str, Any]:
    """Inspect one seed without mutating any authoritative state.

    Historical events are listed in original order and hashed verbatim; a
    reported event weight delta MUST NOT be attributed solely to SSOT if
    other signals were present. Unrecognised SSOT provenance is never
    classified as independently verified. Source refs and rationales are
    withheld by default, but can be included in a trusted local inspector.
    No 'allowed' or 'authorized' verdict is emitted by this function.
    """
    snapshot = _payload(seed)
    seed_id = str(snapshot.get("id", "")).strip()
    if not seed_id:
        raise ValueError("a nonempty canonical seed id is required")
    events = [_payload(event) for event in gate_events]
    uses = [_payload(record) for record in influence_records]
    for event in events:
        if not isinstance(event.get("signals", ()), (list, tuple)):
            raise ValueError("Gate event signals must be an array")

    relevant = [
        event for event in events if str(event.get("seed_id", "")) == seed_id
    ]
    known_signals: list[dict[str, Any]] = []
    unknown_ssot_count = 0
    for sequence, event in enumerate(relevant):
        event_digest = _canonical_digest(event)
        for signal_index, raw_signal in enumerate(event.get("signals", ())):
            signal = _payload(raw_signal)
            kind = _name(signal.get("kind", ""))
            direction = _name(signal.get("direction", "support"))
            if kind != "ssot" or direction != "support":
                continue
            if not is_known_legacy_ssot_support_signal(signal):
                unknown_ssot_count += 1
                continue
            source_ref = str(signal.get("source_ref") or "")
            reason = str(signal.get("reason") or "")
            family = (
                "intermediate_self_attestation"
                if reason.startswith("relation-attested:ssot:")
                else "historical_similarity_producer"
            )
            record = {
                "event_order": sequence,
                "gate_event_id": event.get("event_id"),
                "gate_event_sha256": event_digest,
                "gate_decision": _name(event.get("decision", "")),
                "gate_policy_id": event.get("policy_id"),
                "gate_authority_version": event.get("authority_version"),
                "gate_weight_before": event.get("weight_before"),
                "gate_weight_after": event.get("weight_after"),
                "event_created_at": event.get("created_at"),
                "signal_index": signal_index,
                "signal_sha256": _canonical_digest(signal),
                "source_ref_sha256": sha256(source_ref.encode("utf-8")).hexdigest(),
                "reason_sha256": sha256(reason.encode("utf-8")).hexdigest(),
                "verified_flag_claimed": signal.get("verified") is True,
                "independent_flag_claimed": signal.get("independent") is True,
                "producer_family": family,
            }
            if include_source_refs:
                record["source_ref"] = source_ref
                record["recorded_reason"] = reason
            known_signals.append(record)

    recorded_use: list[dict[str, Any]] = []
    for index, raw in enumerate(uses):
        if str(raw.get("seed_id", "")) != seed_id:
            continue
        reason = str(raw.get("reason", ""))
        entry = {
            "record_order": index,
            "record_sha256": _canonical_digest(raw),
            "action": _name(raw.get("action", "")),
            "recorded_allowed": raw.get("allowed") is True,
            "recorded_reason_sha256": sha256(reason.encode("utf-8")).hexdigest(),
            "gate_event_ref": raw.get("gate_event_ref"),
            "authority_version": raw.get("authority_version"),
            "decided_at": raw.get("decided_at"),
        }
        if include_source_refs:
            entry["recorded_reason"] = reason
        recorded_use.append(entry)

    legacy_detected = has_unreviewed_ssot_support(seed_id, events)
    if legacy_detected != bool(known_signals):
        # Prevent two audit and point-of-use interpretations from drifting.
        raise ValueError("legacy SSOT review and quarantine classifiers disagree")
    text = snapshot.get("text")
    report = {
        "schema": DOSSIER_SCHEMA,
        "session_id": session_id,
        "seed_id": seed_id,
        "seed_snapshot": {
            "text_sha256": (
                sha256(text.encode("utf-8")).hexdigest()
                if isinstance(text, str) else None
            ),
            "status": _name(snapshot.get("status", "")),
            "weight": snapshot.get("weight"),
            "evidence_count": snapshot.get("evidence_count"),
            "authority_version": snapshot.get("authority_version"),
        },
        "known_legacy_producer_detected": legacy_detected,
        "legacy_signal_count": len(known_signals),
        "other_ssot_support_count": unknown_ssot_count,
        "gate_events_inspected": len(relevant),
        "recorded_prior_use_count": len(recorded_use),
        "recorded_prior_allowed_use_count": sum(
            item["recorded_allowed"] for item in recorded_use
        ),
        "historical_signals": known_signals,
        "historical_influence": recorded_use,
        "review_state": "not_requalified",
        "source_to_seed_truth_checked": False,
        "actor_identity_checked": False,
        "independence_verified": False,
        "requalification_performed": False,
        "source_refs_included": include_source_refs,
        "notes": (
            "Known legacy producer signatures are diagnostic, not a proof that "
            "all other evidence was verified. Prior Gate decisions and old use "
            "records remain historical facts. Only the existing authenticated "
            "production evidence path may request NEW Gate evaluation. This "
            "dossier cannot release a seed from point-of-use quarantine."
        ),
    }
    report["dossier_sha256"] = _canonical_digest(report)
    return report
