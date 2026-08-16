"""Measure the real one-generation live runtime on multi-turn suites.

The historical :mod:`ssl_session_suite` is an evaluation harness with an
isolated baseline arm. This module deliberately does not reproduce that loop.
It drives :class:`shadowseed.chat.ShadowChatSession` directly so measurements
cover visible-answer history, same-turn provenance deferral, point-of-use
authorization, and the live Gate policy.

Two arms are available:

``evidence-backed``
    The shipped policy, without manufacturing external evidence. It measures
    how much the live runtime can observe while granting no unsupported
    authority.

``counterfactual``
    An explicitly non-production recurrence-only policy. It creates organic
    surfacing opportunities when recurrence reaches the configured thresholds;
    it does not guarantee promotion. Its promotions are not evidence and must
    not be interpreted as product behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import replace
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.adapters.models import make_backend
from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.detection.model_detector import make_detector_backend
from shadowseed.intake import is_atomic_seed, normalize_detection_candidates
from shadowseed.recurrence_clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    auto_calibrated_min_occurrences,
)


LIVE_ARM_POLICIES = {
    "evidence-backed": "evidence_backed",
    "counterfactual": "exploratory",
}


def _provenance() -> dict[str, Any]:
    try:
        package_version = version("shadowseed")
    except PackageNotFoundError:  # pragma: no cover - source tree without installation
        package_version = None
    revision = os.environ.get("GITHUB_SHA")
    dirty: bool | None = None
    repository = Path(__file__).resolve().parents[3]
    try:
        if not revision:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return {
        "package_version": package_version,
        "source_revision": revision,
        "source_dirty": dirty,
    }


def _requested_arms(live_arms: str) -> list[str]:
    if live_arms == "both":
        return ["evidence-backed", "counterfactual"]
    if live_arms not in LIVE_ARM_POLICIES:
        allowed = ", ".join((*LIVE_ARM_POLICIES, "both"))
        raise ValueError(f"live_arms must be one of: {allowed}")
    return [live_arms]


def _validate_suite(data: dict[str, Any]) -> list[dict[str, Any]]:
    conversations = data.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        raise ValueError("live session measurement requires at least one conversation")
    for conversation_index, conversation in enumerate(conversations):
        turns = conversation.get("turns") if isinstance(conversation, dict) else None
        if not isinstance(turns, list) or not turns:
            raise ValueError(
                "live session measurement requires at least one turn per conversation; "
                f"invalid conversation index: {conversation_index}"
            )
        for turn_index, turn in enumerate(turns):
            question = turn.get("question") if isinstance(turn, dict) else None
            if not isinstance(question, str) or not question.strip():
                raise ValueError(
                    "live session measurement requires a non-empty question for every turn; "
                    f"invalid: {conversation.get('id', conversation_index)}:{turn_index}"
                )
    return conversations


def _effective_config(
    conversation: dict[str, Any],
    *,
    dedup_threshold: float | None,
    min_occurrences: int | None,
    promotion_threshold: float | None,
    auto_calibrate: bool,
) -> SSLCoreConfig:
    config = SSLCoreConfig()
    effective_min_occurrences = conversation.get("min_occurrences", min_occurrences)
    if effective_min_occurrences is None and conversation.get(
        "auto_calibrate", auto_calibrate
    ):
        effective_min_occurrences = auto_calibrated_min_occurrences(
            len(conversation.get("turns", []))
        )
    replacements: dict[str, Any] = {}
    effective_dedup = conversation.get("dedup_threshold", dedup_threshold)
    effective_promotion = conversation.get("promotion_threshold", promotion_threshold)
    if effective_dedup is not None:
        replacements["dedup_threshold"] = float(effective_dedup)
    if effective_min_occurrences is not None:
        replacements["min_occurrences_for_gate"] = int(effective_min_occurrences)
    if effective_promotion is not None:
        replacements["promotion_threshold"] = float(effective_promotion)
    return replace(config, **replacements)


def _normalized_candidates(text: str, max_seed_words: int) -> list[str]:
    return [
        candidate
        for candidate in normalize_detection_candidates([text])
        if is_atomic_seed(candidate, max_seed_words=max_seed_words)
    ]


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _resolved_embedding_model(backend: str, model_id: str | None) -> str | None:
    if model_id:
        return model_id
    if backend == "sentence-transformers":
        return "sentence-transformers/all-MiniLM-L6-v2"
    if backend == "openai":
        from shadowseed.adapters.openai_client import DEFAULT_EMBEDDING_MODEL

        return DEFAULT_EMBEDDING_MODEL
    return None


def _deferral_metrics(
    session: ShadowChatSession,
    turns: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build objective opportunity-cost proxies for fail-closed deferral.

    A suppressed candidate is marked as recovered when a semantically matching
    candidate appears on a later turn that had no SSL-attributed suppression.
    Matching uses the same embedder and dedup threshold as the measured session.
    This is deliberately not called a usefulness judgment.
    """

    records: list[dict[str, Any]] = []
    influenced_turns = sum(bool(turn.get("surfaced_seed_ids")) for turn in turns)
    detected_on_influenced_turns = sum(
        len(turn.get("detected_candidates", []))
        for turn in turns
        if turn.get("surfaced_seed_ids")
    )

    later_candidates: list[tuple[int, str]] = []
    for later_turn in turns:
        if later_turn.get("suppressed_self_attributed_candidates"):
            continue
        later_candidates.extend(
            (int(later_turn["turn"]), str(candidate))
            for candidate in later_turn.get("detected_candidates", [])
        )

    embedding_cache: dict[str, np.ndarray] = {}

    def _embedding(text: str) -> np.ndarray:
        if text not in embedding_cache:
            embedding_cache[text] = session.manager.get_embedding(text)
        return embedding_cache[text]

    max_words = session.manager.config.max_seed_words
    threshold = session.manager.config.dedup_threshold
    for turn in turns:
        suppressed_turn = int(turn["turn"])
        for raw_candidate in turn.get("suppressed_self_attributed_candidates", []):
            normalized = _normalized_candidates(str(raw_candidate), max_words)
            best_match: dict[str, Any] | None = None
            best_similarity = float("-inf")
            for later_turn, later_raw in later_candidates:
                if later_turn <= suppressed_turn:
                    continue
                later_normalized = _normalized_candidates(later_raw, max_words)
                for candidate in normalized:
                    for later_candidate in later_normalized:
                        similarity = _cosine(
                            _embedding(candidate),
                            _embedding(later_candidate),
                        )
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = {
                                "turn": later_turn,
                                "candidate": later_raw,
                                "normalized_candidate": later_candidate,
                                "similarity": round(similarity, 6),
                            }
            recovered = bool(
                best_match is not None and best_similarity >= threshold
            )
            records.append(
                {
                    "turn": suppressed_turn,
                    "candidate": str(raw_candidate),
                    "normalized_candidates": normalized,
                    "normalization_admissible": bool(normalized),
                    "later_recovered": recovered,
                    "recovery_match": best_match if recovered else None,
                }
            )

    suppressed_count = len(records)
    admissible_count = sum(record["normalization_admissible"] for record in records)
    recovered_count = sum(record["later_recovered"] for record in records)
    unrecovered_admissible_count = sum(
        record["normalization_admissible"] and not record["later_recovered"]
        for record in records
    )
    affected_turns = len({record["turn"] for record in records})
    distinct_candidates = len(
        {candidate.casefold() for record in records for candidate in record["normalized_candidates"]}
    )
    return {
        "method": "normalization admissibility plus later unsuppressed semantic recovery",
        "dedup_similarity_threshold": threshold,
        "influenced_turns": influenced_turns,
        "affected_turns": affected_turns,
        "detected_on_influenced_turns": detected_on_influenced_turns,
        "suppressed_candidate_occurrences": suppressed_count,
        "distinct_normalized_suppressed_candidates": distinct_candidates,
        "normalization_admissible_occurrences": admissible_count,
        "later_recovered_occurrences": recovered_count,
        "unrecovered_admissible_occurrences": unrecovered_admissible_count,
        "suppression_rate_on_influenced_turns": (
            round(suppressed_count / detected_on_influenced_turns, 6)
            if detected_on_influenced_turns
            else 0.0
        ),
        "later_recovery_rate": (
            round(recovered_count / admissible_count, 6) if admissible_count else 0.0
        ),
        "candidate_records": records,
        "interpretation": (
            "These counts measure deferred candidate opportunities and later recovery. "
            "They do not establish that a candidate was true, relevant, or useful."
        ),
    }


def _aggregate_deferrals(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [conversation["deferral_metrics"] for conversation in conversations]
    additive = (
        "influenced_turns",
        "affected_turns",
        "detected_on_influenced_turns",
        "suppressed_candidate_occurrences",
        "normalization_admissible_occurrences",
        "later_recovered_occurrences",
        "unrecovered_admissible_occurrences",
    )
    totals = {key: sum(int(metric[key]) for metric in metrics) for key in additive}
    unique_candidates = {
        candidate.casefold()
        for metric in metrics
        for record in metric["candidate_records"]
        for candidate in record["normalized_candidates"]
    }
    totals["distinct_normalized_suppressed_candidates"] = len(unique_candidates)
    detected = totals["detected_on_influenced_turns"]
    admissible = totals["normalization_admissible_occurrences"]
    totals["suppression_rate_on_influenced_turns"] = (
        round(totals["suppressed_candidate_occurrences"] / detected, 6)
        if detected
        else 0.0
    )
    totals["later_recovery_rate"] = (
        round(totals["later_recovered_occurrences"] / admissible, 6)
        if admissible
        else 0.0
    )
    totals["interpretation"] = (
        "Aggregate opportunity-cost proxies; no truth or usefulness label is inferred."
    )
    return totals


def run_live_session_measurement(
    data: dict[str, Any],
    output_path: str,
    *,
    backend: str,
    model_id: str | None,
    max_new_tokens: int,
    embedding_backend: str,
    embedding_model: str | None,
    surface_threshold: float,
    surface_top_k: int,
    early_turn_margin: float,
    early_turn_history: int,
    resurface_margin: float,
    max_seeds_per_turn: int,
    dedup_threshold: float | None,
    min_occurrences: int | None,
    promotion_threshold: float | None,
    recurrence_mode: str,
    cluster_threshold: float | None,
    auto_calibrate: bool,
    live_arms: str,
) -> Path:
    """Run one or both live measurement arms and write a self-describing artifact."""

    if backend == "fixture":
        raise ValueError(
            "live session measurement requires a real model backend; fixture output "
            "cannot establish live-runtime behavior"
        )
    if embedding_backend == "lexical":
        raise ValueError(
            "live session measurement requires sentence-transformers or openai embeddings"
        )

    arms = _requested_arms(live_arms)
    suite_conversations = _validate_suite(data)
    artifact_started = time.perf_counter()
    adapter_setup_started = time.perf_counter()
    embed_fn, _dimension = make_embedding_fn(embedding_backend, embedding_model)
    model = make_backend(
        backend=backend,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
    )
    detector = make_detector_backend(
        backend,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
        prompt_variant="generative",
    )
    adapter_setup_elapsed = time.perf_counter() - adapter_setup_started
    suite_digest = sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    arm_results: list[dict[str, Any]] = []

    for arm_id in arms:
        arm_started = time.perf_counter()
        arm_live_turn_elapsed = 0.0
        arm_deferral_scoring_elapsed = 0.0
        gate_policy_id = LIVE_ARM_POLICIES[arm_id]
        conversations: list[dict[str, Any]] = []
        for conversation in suite_conversations:
            config = _effective_config(
                conversation,
                dedup_threshold=dedup_threshold,
                min_occurrences=min_occurrences,
                promotion_threshold=promotion_threshold,
                auto_calibrate=auto_calibrate,
            )
            effective_recurrence = conversation.get("recurrence_mode", recurrence_mode)
            effective_cluster_threshold = conversation.get(
                "cluster_threshold", cluster_threshold
            )
            session = ShadowChatSession(
                backend=backend,
                model_id=model_id,
                max_new_tokens=max_new_tokens,
                embedding_backend=embedding_backend,
                embedding_model=embedding_model,
                surface_threshold=conversation.get("surface_threshold", surface_threshold),
                surface_top_k=conversation.get("surface_top_k", surface_top_k),
                early_turn_margin=conversation.get("early_turn_margin", early_turn_margin),
                early_turn_history=conversation.get("early_turn_history", early_turn_history),
                resurface_margin=conversation.get("resurface_margin", resurface_margin),
                max_seeds_per_turn=max_seeds_per_turn,
                recurrence_mode=effective_recurrence,
                cluster_threshold=effective_cluster_threshold,
                runtime_mode="live",
                gate_policy_id=gate_policy_id,
                model_backend=model,
                detector_backend=detector,
                embedding_fn=embed_fn,
                core_config=config,
            )
            live_turn_started = time.perf_counter()
            turn_reports = [session.turn(turn["question"]) for turn in conversation["turns"]]
            live_turn_elapsed = time.perf_counter() - live_turn_started
            arm_live_turn_elapsed += live_turn_elapsed
            verified_records = session.audit()
            deferral_scoring_started = time.perf_counter()
            deferrals = _deferral_metrics(session, turn_reports)
            deferral_scoring_elapsed = time.perf_counter() - deferral_scoring_started
            arm_deferral_scoring_elapsed += deferral_scoring_elapsed
            conversations.append(
                {
                    "conversation_id": conversation.get("id", "conversation"),
                    "domain": conversation.get("domain", ""),
                    "runtime_mode": "live",
                    "gate_policy_id": gate_policy_id,
                    "applied_thresholds": {
                        "dedup_threshold": config.dedup_threshold,
                        "min_occurrences": config.min_occurrences_for_gate,
                        "promotion_threshold": config.promotion_threshold,
                        "recurrence_mode": effective_recurrence,
                        "cluster_threshold": (
                            (
                                effective_cluster_threshold
                                if effective_cluster_threshold is not None
                                else DEFAULT_CLUSTER_THRESHOLD
                            )
                            if effective_recurrence == "cluster"
                            else None
                        ),
                        "surface_threshold": session.surface_threshold,
                        "surface_top_k": session.surface_top_k,
                        "early_turn_margin": session.early_turn_margin,
                        "early_turn_history": session.early_turn_history,
                        "resurface_margin": session.resurface_margin,
                    },
                    "turns": turn_reports,
                    "deferral_metrics": deferrals,
                    "final_shadow": session.shadow_report(),
                    "gate_events": [event.to_dict() for event in session.manager.gate_events],
                    "audit_records_verified": verified_records,
                    "timing": {
                        "live_turn_elapsed_seconds": round(live_turn_elapsed, 3),
                        "deferral_scoring_elapsed_seconds": round(
                            deferral_scoring_elapsed, 3
                        ),
                    },
                }
            )

        total_turns = sum(len(item["turns"]) for item in conversations)
        authority_events = sum(
            len(item["final_shadow"]["influence_records"]) for item in conversations
        )
        promoted_seed_count = sum(
            len(
                {
                    seed_id
                    for turn in item["turns"]
                    for seed_id in turn["promoted_this_turn"]
                }
            )
            for item in conversations
        )
        arm_wall_elapsed = time.perf_counter() - arm_started
        arm_results.append(
            {
                "arm_id": arm_id,
                "runtime_mode": "live",
                "gate_policy_id": gate_policy_id,
                "production_policy": arm_id == "evidence-backed",
                "external_evidence_injected": False,
                "answer_generation_calls": total_turns,
                "detector_calls": total_turns,
                "influence_record_count": authority_events,
                "promoted_seed_count": promoted_seed_count,
                "timing": {
                    "live_turn_elapsed_seconds": round(arm_live_turn_elapsed, 3),
                    "deferral_scoring_elapsed_seconds": round(
                        arm_deferral_scoring_elapsed, 3
                    ),
                    "other_arm_overhead_seconds": round(
                        max(
                            0.0,
                            arm_wall_elapsed
                            - arm_live_turn_elapsed
                            - arm_deferral_scoring_elapsed,
                        ),
                        3,
                    ),
                    "wall_elapsed_seconds": round(arm_wall_elapsed, 3),
                },
                "deferral_metrics": _aggregate_deferrals(conversations),
                "conversations": conversations,
                "interpretation": (
                    "Shipped evidence-backed policy without external support."
                    if arm_id == "evidence-backed"
                    else "Non-production recurrence-only counterfactual used only to measure deferral."
                ),
            }
        )

    total_turns = sum(arm["answer_generation_calls"] for arm in arm_results)
    total_live_turn_elapsed = sum(
        arm["timing"]["live_turn_elapsed_seconds"] for arm in arm_results
    )
    total_deferral_scoring_elapsed = sum(
        arm["timing"]["deferral_scoring_elapsed_seconds"] for arm in arm_results
    )
    payload = {
        "summary": {
            "artifact": "ssl_live_session_measurement",
            "runtime_mode": "live",
            "backend": getattr(model, "name", backend),
            "detector": getattr(detector, "name", backend),
            "embedding_backend": embedding_backend,
            "embedding_model": _resolved_embedding_model(
                embedding_backend, embedding_model
            ),
            "detector_prompt_variant": "generative",
            "model_id": model_id,
            "max_new_tokens": max_new_tokens,
            "input_version": data.get("version"),
            "input_sha256": suite_digest,
            "conversation_count": len(suite_conversations),
            "arms": arms,
            "answer_generation_calls": total_turns,
            "detector_calls": total_turns,
            "timing": {
                "adapter_setup_elapsed_seconds": round(adapter_setup_elapsed, 3),
                "live_turn_elapsed_seconds": round(total_live_turn_elapsed, 3),
                "deferral_scoring_elapsed_seconds": round(
                    total_deferral_scoring_elapsed, 3
                ),
                "measurement_wall_elapsed_seconds": round(
                    time.perf_counter() - artifact_started, 3
                ),
            },
            "claim_boundary": (
                "The evidence-backed arm measures shipped live behavior without supplied "
                "evidence. The exploratory arm is a counterfactual for measuring same-turn "
                "deferral and is not production authority. Deferral metrics are objective "
                "opportunity proxies, not usefulness or truth judgments."
            ),
            **_provenance(),
        },
        "arms": arm_results,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
