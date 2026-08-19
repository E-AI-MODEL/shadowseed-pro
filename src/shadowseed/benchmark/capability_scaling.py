"""Runner-neutral capability-scaling harness for Shadow Seed Learning.

This module measures the canonical :class:`shadowseed.chat.ShadowChatSession`
runtime rather than reimplementing SSL. It intentionally separates:

* a live ``evidence_backed`` arm, where generated recurrence cannot manufacture
  authority and no external evidence is injected; and
* an evaluation ``exploratory`` arm used only to create cross-turn blinded A/B
  opportunities when recurrence causes a seed to surface.

The resulting bundle is self-describing, hash-verified, and review-ready. Raw
model output is evidence about model/runtime behaviour, not evidence that a seed
is true, useful, or production-safe.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.adapters.models import make_backend
from shadowseed.benchmark.ssl45_model_benefit_suite import blind_order
from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.detection.model_detector import (
    OPEN_SET_GENERATIVE_DETECTOR_ID,
    OPEN_SET_GENERATIVE_PROMPT,
    make_detector_backend,
)
from shadowseed.gate.events import GateDecision
from shadowseed.intake import is_atomic_seed, normalize_detection_candidates


BUNDLE_SCHEMA = "ssl-capability-scaling-bundle-v1"
REVIEW_SCHEMA = "ssl-capability-scaling-review-v1"
PREREG_SCHEMA = "ssl-capability-scaling-preregistration-v1"
DEFAULT_REVIEWERS = ("reviewer_a", "reviewer_b")
CANDIDATE_FIELDS = (
    "atomic",
    "relevant",
    "specific",
    "investigable",
    "nontrivial",
    "grounded_to_context",
    "assertion_masquerade",
    "duplicate_of_prior_candidate",
    "useful_to_investigate",
)
CATEGORICAL_VALUES = {"yes", "no", "unclear"}
EPISTEMIC_ROLES = {"gap", "doubt", "what_if", "other", "unclear"}
ANSWER_VALUES = {"A", "B", "tie"}


@dataclass(frozen=True)
class SuiteSpec:
    suite_id: str
    path: Path


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_provenance() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    revision = os.environ.get("GITHUB_SHA")
    dirty: bool | None = None
    try:
        if not revision:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    try:
        package_version = version("shadowseed")
    except PackageNotFoundError:  # pragma: no cover - source checkout without install
        package_version = None
    return {
        "source_revision": revision,
        "source_dirty": dirty,
        "package_version": package_version,
    }


def _write_environment_manifest(path: Path) -> dict[str, Any]:
    lines = [
        f"python={sys.version.replace(chr(10), ' ')}",
        f"platform={platform.platform()}",
    ]
    try:
        freeze = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        lines.extend(sorted(line for line in freeze.splitlines() if line.strip()))
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        lines.append(f"pip_freeze_error={type(exc).__name__}")
    content = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": _sha256_bytes(content.encode("utf-8")),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return data


def validate_preregistration(data: dict[str, Any]) -> None:
    if data.get("schema") != PREREG_SCHEMA:
        raise ValueError(f"preregistration schema must be {PREREG_SCHEMA!r}")
    required = {
        "protocol_id",
        "claim_boundary",
        "primary_metrics",
        "exclusion_rules",
        "review_contract",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"preregistration missing fields: {', '.join(missing)}")
    review = data["review_contract"]
    if not isinstance(review, dict):
        raise TypeError("review_contract must be an object")
    if set(review.get("candidate_fields", [])) != set(CANDIDATE_FIELDS):
        raise ValueError("preregistration candidate_fields do not match the harness contract")
    if set(review.get("epistemic_roles", [])) != EPISTEMIC_ROLES:
        raise ValueError("preregistration epistemic_roles do not match the harness contract")


def _parse_suite(value: str) -> SuiteSpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("suite must be written as ID=PATH")
    suite_id, raw_path = value.split("=", 1)
    suite_id = suite_id.strip()
    if not suite_id:
        raise argparse.ArgumentTypeError("suite ID must not be empty")
    path = Path(raw_path).expanduser().resolve()
    return SuiteSpec(suite_id=suite_id, path=path)


def _validate_suite(data: dict[str, Any], suite_id: str) -> list[dict[str, Any]]:
    if data.get("language") != "en":
        raise ValueError(f"suite {suite_id!r} must declare language='en'")
    conversations = data.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        raise ValueError(f"suite {suite_id!r} requires at least one conversation")
    for index, conversation in enumerate(conversations):
        if not isinstance(conversation, dict):
            raise TypeError(f"suite {suite_id!r} conversation {index} must be an object")
        turns = conversation.get("turns")
        if not isinstance(turns, list) or not turns:
            raise ValueError(f"suite {suite_id!r} conversation {index} has no turns")
        for turn_index, turn in enumerate(turns):
            question = turn.get("question") if isinstance(turn, dict) else None
            if not isinstance(question, str) or not question.strip():
                raise ValueError(
                    f"suite {suite_id!r} conversation {index} turn {turn_index} has no question"
                )
    return conversations


def _select_conversations(
    conversations: list[dict[str, Any]],
    selected_ids: set[str] | None,
) -> list[dict[str, Any]]:
    if not selected_ids:
        return conversations
    available = {str(item.get("id", "")) for item in conversations}
    unknown = sorted(selected_ids.difference(available))
    # A shared selection may name conversations from another suite. Only fail if
    # none of the selected ids exist in this suite; the caller validates global
    # coverage across all suites after loading them.
    selected = [item for item in conversations if str(item.get("id", "")) in selected_ids]
    if not selected and unknown:
        return []
    return selected


def _normalization(text: str, max_seed_words: int) -> list[str]:
    return [
        candidate
        for candidate in normalize_detection_candidates(
            [text], expand_short_fragments=False, split_broad=False
        )
        if is_atomic_seed(candidate, max_seed_words=max_seed_words)
    ]


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _review_id(prefix: str, *parts: object) -> str:
    raw = "|".join([prefix, *(str(part) for part in parts)])
    return f"{prefix}_{sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _blank_candidate_scores() -> dict[str, str]:
    payload = {field: "" for field in CANDIDATE_FIELDS}
    payload["epistemic_role"] = ""
    payload["notes"] = ""
    return payload


def _blank_answer_scores() -> dict[str, str]:
    return {"better_answer": "", "notes": ""}


def _candidate_duplicate_metrics(
    observations: list[dict[str, Any]],
    *,
    embed_fn: Any,
    semantic_threshold: float,
) -> dict[str, Any]:
    seen_exact: set[str] = set()
    prior_embeddings: list[np.ndarray] = []
    exact_duplicates = 0
    semantic_duplicates = 0
    admissible = 0
    malformed = 0
    for observation in observations:
        normalized = observation["normalized_candidates"]
        if not normalized:
            malformed += 1
            continue
        admissible += 1
        exact = False
        semantic = False
        for candidate in normalized:
            key = candidate.casefold()
            if key in seen_exact:
                exact = True
            embedding = np.asarray(embed_fn(candidate), dtype=float)
            if any(_cosine(embedding, prior) >= semantic_threshold for prior in prior_embeddings):
                semantic = True
            seen_exact.add(key)
            prior_embeddings.append(embedding)
        exact_duplicates += int(exact)
        semantic_duplicates += int(semantic)
        observation["exact_duplicate_of_prior"] = exact
        observation["semantic_duplicate_of_prior"] = semantic
    return {
        "candidate_occurrences": len(observations),
        "normalization_admissible_occurrences": admissible,
        "malformed_or_non_atomic_occurrences": malformed,
        "malformed_or_non_atomic_rate": round(malformed / len(observations), 6)
        if observations
        else 0.0,
        "exact_duplicate_occurrences": exact_duplicates,
        "exact_duplicate_rate": round(exact_duplicates / admissible, 6) if admissible else None,
        "semantic_duplicate_occurrences": semantic_duplicates,
        "semantic_duplicate_rate": round(semantic_duplicates / admissible, 6)
        if admissible
        else None,
        "semantic_duplicate_threshold": semantic_threshold,
    }


def _gate_summary(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    events = list(events)
    decisions = Counter(str(event.get("decision", "")) for event in events)
    positive_weight_events = sum(float(event.get("weight_delta", 0.0)) > 0.0 for event in events)
    external_support_events = sum(
        any(
            bool(signal.get("verified"))
            and signal.get("kind") in {"ssot", "human_feedback", "retrieval"}
            for signal in event.get("signals", [])
        )
        for event in events
    )
    return {
        "event_count": len(events),
        "decisions": dict(sorted(decisions.items())),
        "positive_weight_event_count": positive_weight_events,
        "verified_external_support_event_count": external_support_events,
        "contradiction_decision_count": decisions.get("contradicted", 0)
        + decisions.get("blocked", 0),
    }


def _parser_diagnostics_summary(counts: Counter[str] | dict[str, int]) -> dict[str, Any]:
    numbered = int(counts.get("numbered_lines", 0))
    dropped_blank = int(counts.get("dropped_blank_or_placeholder", 0))
    dropped_citation = int(counts.get("dropped_citation_or_stub", 0))
    dropped_fewshot = int(counts.get("dropped_fewshot_leak", 0))
    dropped_duplicate = int(counts.get("dropped_duplicate", 0))
    rejected = dropped_blank + dropped_citation + dropped_fewshot + dropped_duplicate
    return {
        "nonblank_lines": int(counts.get("nonblank_lines", 0)),
        "numbered_lines": numbered,
        "unnumbered_nonblank_lines": int(counts.get("unnumbered_nonblank_lines", 0)),
        "accepted_candidates": int(counts.get("accepted_candidates", 0)),
        "nested_numbering_prefixes_removed": int(
            counts.get("nested_numbering_prefixes_removed", 0)
        ),
        "dropped_blank_or_placeholder": dropped_blank,
        "dropped_citation_or_stub": dropped_citation,
        "dropped_fewshot_leak": dropped_fewshot,
        "dropped_duplicate": dropped_duplicate,
        "parser_rejection_rate": round(rejected / numbered, 6) if numbered else None,
        "fewshot_leakage_rate": round(dropped_fewshot / numbered, 6) if numbered else None,
        "dropped_citation_or_stub_rate": round(dropped_citation / numbered, 6)
        if numbered
        else None,
    }


def _assert_live_authority_invariants(events: list[dict[str, Any]]) -> None:
    for event in events:
        if float(event.get("weight_delta", 0.0)) > 1e-12:
            raise RuntimeError(
                "live evidence-backed capability arm changed authority without injected evidence"
            )
        if event.get("decision") in {GateDecision.PROMOTED.value, GateDecision.VALIDATED.value}:
            raise RuntimeError(
                "live evidence-backed capability arm promoted/validated without injected evidence"
            )


def _run_mode_for_suite(
    *,
    suite_id: str,
    suite_data: dict[str, Any],
    selected_ids: set[str] | None,
    mode: str,
    backend: str,
    model_id: str,
    max_new_tokens: int,
    embedding_backend: str,
    embedding_model: str | None,
    model_backend: Any,
    detector_backend: Any,
    embed_fn: Any,
    surface_threshold: float,
    surface_top_k: int,
    early_turn_margin: float,
    early_turn_history: int,
    resurface_margin: float,
    max_seeds_per_turn: int,
    recurrence_mode: str,
    cluster_threshold: float | None,
    semantic_duplicate_threshold: float,
    reviewers: tuple[str, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    conversations = _validate_suite(suite_data, suite_id)
    selected = _select_conversations(conversations, selected_ids)
    records: list[dict[str, Any]] = []
    candidate_packets: list[dict[str, Any]] = []
    candidate_keys: list[dict[str, Any]] = []
    answer_packets: list[dict[str, Any]] = []
    answer_keys: list[dict[str, Any]] = []
    mode_started = time.perf_counter()

    all_candidate_observations: list[dict[str, Any]] = []
    all_gate_events: list[dict[str, Any]] = []
    total_influence_records = 0
    total_surfaced_turns = 0
    total_suppressed = 0
    total_detected_on_surfaced = 0
    total_answer_calls = 0
    parser_diag_totals: Counter[str] = Counter()

    for conversation in selected:
        config = SSLCoreConfig()
        replacements: dict[str, Any] = {}
        for source_key, config_key, caster in (
            ("dedup_threshold", "dedup_threshold", float),
            ("min_occurrences", "min_occurrences_for_gate", int),
            ("promotion_threshold", "promotion_threshold", float),
        ):
            if conversation.get(source_key) is not None:
                replacements[config_key] = caster(conversation[source_key])
        if replacements:
            config = replace(config, **replacements)
        session = ShadowChatSession(
            backend=backend,
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            embedding_backend=embedding_backend,
            embedding_model=embedding_model,
            surface_threshold=float(conversation.get("surface_threshold", surface_threshold)),
            surface_top_k=int(conversation.get("surface_top_k", surface_top_k)),
            early_turn_margin=float(conversation.get("early_turn_margin", early_turn_margin)),
            early_turn_history=int(conversation.get("early_turn_history", early_turn_history)),
            resurface_margin=float(conversation.get("resurface_margin", resurface_margin)),
            max_seeds_per_turn=max_seeds_per_turn,
            recurrence_mode=str(conversation.get("recurrence_mode", recurrence_mode)),
            cluster_threshold=(
                float(conversation["cluster_threshold"])
                if conversation.get("cluster_threshold") is not None
                else cluster_threshold
            ),
            runtime_mode=mode,
            gate_policy_id="evidence_backed" if mode == "live" else "exploratory",
            model_backend=model_backend,
            detector_backend=detector_backend,
            embedding_fn=embed_fn,
            core_config=config,
        )
        turn_reports: list[dict[str, Any]] = []
        for turn_index, turn in enumerate(conversation["turns"]):
            report = session.turn(turn["question"])
            if mode == "live":
                parse_diagnostics = getattr(detector_backend, "last_parse_diagnostics", None)
                raw_detector_output = getattr(detector_backend, "last_raw_output", None)
                if isinstance(parse_diagnostics, dict):
                    report["detector_parse_diagnostics"] = dict(parse_diagnostics)
                    for key, value in parse_diagnostics.items():
                        if isinstance(value, int) and not isinstance(value, bool):
                            parser_diag_totals[key] += value
                if isinstance(raw_detector_output, str):
                    report["detector_raw_output"] = raw_detector_output
            turn_reports.append(report)
            total_answer_calls += 1 + int(
                mode == "evaluation" and bool(report.get("surfaced_seed_ids"))
            )
            surfaced = bool(report.get("surfaced_seed_ids"))
            total_surfaced_turns += int(surfaced)

            if mode == "live":
                raw_candidates = [str(value) for value in report.get("detected_candidates", [])]
                suppressed = {
                    str(value) for value in report.get("suppressed_self_attributed_candidates", [])
                }
                if surfaced:
                    total_detected_on_surfaced += len(raw_candidates)
                total_suppressed += len(suppressed)
                for candidate_index, raw_candidate in enumerate(raw_candidates):
                    normalized = _normalization(raw_candidate, config.max_seed_words)
                    observation = {
                        "suite_id": suite_id,
                        "conversation_id": str(conversation.get("id", "conversation")),
                        "domain": str(conversation.get("domain", "")),
                        "turn": turn_index,
                        "question": str(turn["question"]),
                        "answer": str(report.get("answer", "")),
                        "candidate_index": candidate_index,
                        "candidate": raw_candidate,
                        "normalized_candidates": normalized,
                        "ssl_exposed": surfaced,
                        "suppressed_same_turn": raw_candidate in suppressed,
                    }
                    all_candidate_observations.append(observation)
                    rid = _review_id(
                        "candidate",
                        suite_id,
                        conversation.get("id", "conversation"),
                        turn_index,
                        candidate_index,
                        raw_candidate,
                    )
                    candidate_packets.append(
                        {
                            "review_id": rid,
                            "domain": observation["domain"],
                            "question": observation["question"],
                            "answer": observation["answer"],
                            "candidate": raw_candidate,
                            "reviewer_instruction": (
                                "Judge the candidate as one epistemic direction to investigate. "
                                "Do not infer truth from fluency and do not reward it merely for being speculative."
                            ),
                            "reviewer_responses": [
                                {"reviewer_id": reviewer, "scores": _blank_candidate_scores()}
                                for reviewer in reviewers
                            ],
                        }
                    )
                    candidate_keys.append(
                        {
                            "review_id": rid,
                            **{key: observation[key] for key in (
                                "suite_id",
                                "conversation_id",
                                "turn",
                                "candidate_index",
                                "normalized_candidates",
                                "ssl_exposed",
                                "suppressed_same_turn",
                            )},
                        }
                    )

            if mode == "evaluation" and report.get("surfaced_seed_ids"):
                rid = _review_id(
                    "answer",
                    suite_id,
                    conversation.get("id", "conversation"),
                    turn_index,
                    turn["question"],
                )
                baseline = str(report.get("baseline_answer", ""))
                ssl_answer = str(report.get("ssl_answer", ""))
                first, second = blind_order(rid)
                answers = {"baseline": baseline, "ssl": ssl_answer}
                answer_packets.append(
                    {
                        "review_id": rid,
                        "domain": str(conversation.get("domain", "")),
                        "question": str(turn["question"]),
                        "option_a": answers[first],
                        "option_b": answers[second],
                        "reviewer_instruction": (
                            "Choose the more useful answer. Penalize invented, forced, repetitive, "
                            "or off-topic content. A carried-over angle only counts when it adds value."
                        ),
                        "reviewer_responses": [
                            {"reviewer_id": reviewer, "scores": _blank_answer_scores()}
                            for reviewer in reviewers
                        ],
                    }
                )
                answer_keys.append(
                    {
                        "review_id": rid,
                        "suite_id": suite_id,
                        "conversation_id": str(conversation.get("id", "conversation")),
                        "turn": turn_index,
                        "surfaced_seed_ids": list(report.get("surfaced_seed_ids", [])),
                        "option_a_source": first,
                        "option_b_source": second,
                    }
                )

        verified_records = session.audit()
        gate_events = [event.to_dict() for event in session.manager.gate_events]
        all_gate_events.extend(gate_events)
        if mode == "live":
            _assert_live_authority_invariants(gate_events)
        total_influence_records += len(session.influence_records)
        records.append(
            {
                "conversation_id": str(conversation.get("id", "conversation")),
                "domain": str(conversation.get("domain", "")),
                "turns": turn_reports,
                "gate_events": gate_events,
                "audit_records_verified": verified_records,
                "final_shadow": session.shadow_report(),
            }
        )

    duplicate_metrics = _candidate_duplicate_metrics(
        all_candidate_observations,
        embed_fn=embed_fn,
        semantic_threshold=semantic_duplicate_threshold,
    ) if mode == "live" else {
        "candidate_occurrences": 0,
        "normalization_admissible_occurrences": 0,
        "malformed_or_non_atomic_occurrences": 0,
        "malformed_or_non_atomic_rate": None,
        "exact_duplicate_occurrences": 0,
        "exact_duplicate_rate": None,
        "semantic_duplicate_occurrences": 0,
        "semantic_duplicate_rate": None,
        "semantic_duplicate_threshold": semantic_duplicate_threshold,
    }
    gate_summary = _gate_summary(all_gate_events)
    summary = {
        "suite_id": suite_id,
        "suite_version": suite_data.get("version"),
        "runtime_mode": mode,
        "gate_policy_id": "evidence_backed" if mode == "live" else "exploratory",
        "production_policy": mode == "live",
        "external_evidence_injected": False,
        "conversation_count": len(records),
        "turn_count": sum(len(record["turns"]) for record in records),
        "answer_generation_calls": total_answer_calls,
        "detector_calls": sum(len(record["turns"]) for record in records),
        "surfaced_turn_count": total_surfaced_turns,
        "influence_record_count": total_influence_records,
        "detected_on_surfaced_turns": total_detected_on_surfaced,
        "suppressed_self_attributed_occurrences": total_suppressed,
        "same_turn_deferral_rate": (
            round(total_suppressed / total_detected_on_surfaced, 6)
            if total_detected_on_surfaced
            else None
        ),
        "candidate_metrics": duplicate_metrics,
        "detector_parser": _parser_diagnostics_summary(parser_diag_totals),
        "gate": gate_summary,
        "wall_elapsed_seconds": round(time.perf_counter() - mode_started, 3),
        "claim_boundary": (
            "Live evidence-backed results establish observed runtime mechanics only. "
            "Evaluation is an explicitly non-production counterfactual used to create "
            "blind A/B opportunities. Neither arm establishes candidate truth or general benefit."
        ),
    }
    artifact = {"summary": summary, "conversations": records}
    return artifact, candidate_packets, candidate_keys, answer_packets, answer_keys


def _aggregate_run_summaries(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    live = [artifact["summary"] for artifact in artifacts if artifact["summary"]["runtime_mode"] == "live"]
    evaluation = [
        artifact["summary"] for artifact in artifacts if artifact["summary"]["runtime_mode"] == "evaluation"
    ]
    live_candidates = sum(item["candidate_metrics"]["candidate_occurrences"] for item in live)
    live_malformed = sum(item["candidate_metrics"]["malformed_or_non_atomic_occurrences"] for item in live)
    live_admissible = sum(item["candidate_metrics"]["normalization_admissible_occurrences"] for item in live)
    live_exact_dupes = sum(item["candidate_metrics"]["exact_duplicate_occurrences"] for item in live)
    live_semantic_dupes = sum(item["candidate_metrics"]["semantic_duplicate_occurrences"] for item in live)
    surfaced_detected = sum(item["detected_on_surfaced_turns"] for item in live)
    suppressed = sum(item["suppressed_self_attributed_occurrences"] for item in live)
    parser_counts: Counter[str] = Counter()
    for item in live:
        for key in (
            "nonblank_lines",
            "numbered_lines",
            "unnumbered_nonblank_lines",
            "accepted_candidates",
            "nested_numbering_prefixes_removed",
            "dropped_blank_or_placeholder",
            "dropped_citation_or_stub",
            "dropped_fewshot_leak",
            "dropped_duplicate",
        ):
            parser_counts[key] += int(item.get("detector_parser", {}).get(key, 0))
    parser_summary = _parser_diagnostics_summary(parser_counts)
    return {
        "live": {
            "suite_count": len(live),
            "turn_count": sum(item["turn_count"] for item in live),
            "candidate_occurrences": live_candidates,
            "malformed_or_non_atomic_occurrences": live_malformed,
            "malformed_or_non_atomic_rate": round(live_malformed / live_candidates, 6)
            if live_candidates
            else 0.0,
            "exact_duplicate_rate": round(live_exact_dupes / live_admissible, 6)
            if live_admissible
            else None,
            "semantic_duplicate_rate": round(live_semantic_dupes / live_admissible, 6)
            if live_admissible
            else None,
            "detector_parser": parser_summary,
            "surfaced_turn_count": sum(item["surfaced_turn_count"] for item in live),
            "same_turn_deferral_rate": round(suppressed / surfaced_detected, 6)
            if surfaced_detected
            else None,
            "positive_weight_event_count": sum(item["gate"]["positive_weight_event_count"] for item in live),
            "verified_external_support_event_count": sum(
                item["gate"]["verified_external_support_event_count"] for item in live
            ),
        },
        "evaluation": {
            "suite_count": len(evaluation),
            "turn_count": sum(item["turn_count"] for item in evaluation),
            "surfaced_turn_count": sum(item["surfaced_turn_count"] for item in evaluation),
            "answer_generation_calls": sum(item["answer_generation_calls"] for item in evaluation),
            "influence_record_count": sum(item["influence_record_count"] for item in evaluation),
        },
    }


def _write_report(
    path: Path,
    *,
    run_id: str,
    model_reference: str,
    aggregate: dict[str, Any],
    candidate_count: int,
    answer_count: int,
) -> None:
    live = aggregate["live"]
    evaluation = aggregate["evaluation"]
    lines = [
        f"# SSL capability scaling run: {run_id}",
        "",
        f"Model reference: `{model_reference}`",
        "",
        "## Automatic measurements",
        "",
        f"- Live turns: {live['turn_count']}",
        f"- Live candidate occurrences: {live['candidate_occurrences']}",
        f"- Detector parser rejection rate: {live['detector_parser']['parser_rejection_rate']}",
        f"- Detector few-shot leakage rate: {live['detector_parser']['fewshot_leakage_rate']}",
        f"- Nested numbering prefixes removed: {live['detector_parser']['nested_numbering_prefixes_removed']}",
        f"- Malformed/non-atomic prescreen rate after parsing: {live['malformed_or_non_atomic_rate']}",
        f"- Exact duplicate rate: {live['exact_duplicate_rate']}",
        f"- Semantic duplicate rate: {live['semantic_duplicate_rate']}",
        f"- Same-turn deferral rate when SSL surfaced: {live['same_turn_deferral_rate']}",
        f"- Live positive-weight Gate events without supplied evidence: {live['positive_weight_event_count']}",
        f"- Evaluation surfaced turns: {evaluation['surfaced_turn_count']}",
        "",
        "## Human review queue",
        "",
        f"- Candidate review items: {candidate_count}",
        f"- Blinded answer A/B items: {answer_count}",
        "",
        "## Claim boundary",
        "",
        "This bundle is raw research evidence about one pinned runtime/model configuration.",
        "Automatic metrics do not establish candidate truth, usefulness, general answer-quality",
        "improvement, or production readiness. Candidate-type mix and subjective quality require",
        "independent blind review. Answer benefit is reported only for turns where the evaluation",
        "arm actually surfaced an authorized seed.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_capability_scaling(
    *,
    suites: list[SuiteSpec],
    output_dir: Path,
    preregistration_path: Path,
    backend: str,
    model_id: str,
    model_reference: str,
    model_revision: str | None,
    model_digest: str | None,
    quantization: str | None,
    max_new_tokens: int,
    embedding_backend: str,
    embedding_model: str | None,
    embedding_reference: str | None,
    embedding_revision: str | None,
    surface_threshold: float,
    surface_top_k: int,
    early_turn_margin: float,
    early_turn_history: int,
    resurface_margin: float,
    max_seeds_per_turn: int,
    recurrence_mode: str,
    cluster_threshold: float | None,
    semantic_duplicate_threshold: float,
    evaluation_conversation_ids: set[str] | None,
    reviewers: tuple[str, ...],
    run_id: str | None = None,
) -> Path:
    if backend == "fixture":
        claim_level = "harness-smoke"
    else:
        claim_level = "real-model-research"
    prereg = _load_json(preregistration_path)
    validate_preregistration(prereg)
    if backend == "hf-transformers" and not model_revision:
        raise ValueError("hf-transformers capability runs require --model-revision")
    if backend == "ollama" and not model_digest:
        raise ValueError("ollama capability runs require --model-digest")
    if backend == "openai" and not model_revision:
        raise ValueError("openai capability runs require an explicit --model-revision/snapshot id")
    if embedding_backend == "sentence-transformers" and not embedding_revision:
        raise ValueError(
            "sentence-transformers capability runs require --embedding-revision"
        )
    if not suites:
        raise ValueError("at least one --suite is required")
    if len({suite.suite_id for suite in suites}) != len(suites):
        raise ValueError("suite IDs must be unique")
    if not reviewers:
        raise ValueError("at least one reviewer id is required")
    if len(set(reviewers)) != len(reviewers):
        raise ValueError("reviewer ids must be unique")

    source = _git_provenance()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    review_dir = output_dir / "review"
    inputs_dir = output_dir / "inputs"
    environment_path = output_dir / "environment.txt"
    environment = _write_environment_manifest(environment_path)
    environment["path"] = "environment.txt"
    if run_id is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        source_tag = (source.get("source_revision") or "unknown")[:8]
        model_tag = "".join(ch if ch.isalnum() else "-" for ch in model_reference).strip("-")[:32]
        run_id = f"{stamp}-{source_tag}-{model_tag or 'model'}"

    inputs_dir.mkdir(parents=True, exist_ok=True)
    copied_preregistration = inputs_dir / "preregistration.json"
    copied_preregistration.write_bytes(preregistration_path.read_bytes())
    suite_payloads: list[tuple[SuiteSpec, dict[str, Any], Path]] = []
    available_conversation_ids: set[str] = set()
    for suite in suites:
        payload = _load_json(suite.path)
        conversations = _validate_suite(payload, suite.suite_id)
        available_conversation_ids.update(str(item.get("id", "")) for item in conversations)
        copied_suite = inputs_dir / f"suite_{suite.suite_id}.json"
        copied_suite.write_bytes(suite.path.read_bytes())
        suite_payloads.append((suite, payload, copied_suite))
    if evaluation_conversation_ids:
        unknown = sorted(evaluation_conversation_ids.difference(available_conversation_ids))
        if unknown:
            raise ValueError(f"unknown evaluation conversation ids: {', '.join(unknown)}")

    setup_started = time.perf_counter()
    embed_fn, embedding_dimension = make_embedding_fn(embedding_backend, embedding_model)
    model = make_backend(
        backend=backend,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
        model_revision=model_revision,
    )
    detector = make_detector_backend(
        backend,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
        prompt_variant="generative",
        model_revision=model_revision,
    )
    setup_elapsed = time.perf_counter() - setup_started

    artifacts: list[dict[str, Any]] = []
    artifact_paths: list[Path] = []
    candidate_packets: list[dict[str, Any]] = []
    candidate_keys: list[dict[str, Any]] = []
    answer_packets: list[dict[str, Any]] = []
    answer_keys: list[dict[str, Any]] = []

    for suite, payload, _copied_suite in suite_payloads:
        live_artifact, candidates, candidate_key, _answers, _answer_key = _run_mode_for_suite(
            suite_id=suite.suite_id,
            suite_data=payload,
            selected_ids=None,
            mode="live",
            backend=backend,
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            embedding_backend=embedding_backend,
            embedding_model=embedding_model,
            model_backend=model,
            detector_backend=detector,
            embed_fn=embed_fn,
            surface_threshold=surface_threshold,
            surface_top_k=surface_top_k,
            early_turn_margin=early_turn_margin,
            early_turn_history=early_turn_history,
            resurface_margin=resurface_margin,
            max_seeds_per_turn=max_seeds_per_turn,
            recurrence_mode=recurrence_mode,
            cluster_threshold=cluster_threshold,
            semantic_duplicate_threshold=semantic_duplicate_threshold,
            reviewers=reviewers,
        )
        live_path = _write_json(raw_dir / f"live_{suite.suite_id}.json", live_artifact)
        artifact_paths.append(live_path)
        artifacts.append(live_artifact)
        candidate_packets.extend(candidates)
        candidate_keys.extend(candidate_key)

        if evaluation_conversation_ids:
            evaluation_artifact, _candidates, _candidate_key, answers, answer_key = _run_mode_for_suite(
                suite_id=suite.suite_id,
                suite_data=payload,
                selected_ids=evaluation_conversation_ids,
                mode="evaluation",
                backend=backend,
                model_id=model_id,
                max_new_tokens=max_new_tokens,
                embedding_backend=embedding_backend,
                embedding_model=embedding_model,
                model_backend=model,
                detector_backend=detector,
                embed_fn=embed_fn,
                surface_threshold=surface_threshold,
                surface_top_k=surface_top_k,
                early_turn_margin=early_turn_margin,
                early_turn_history=early_turn_history,
                resurface_margin=resurface_margin,
                max_seeds_per_turn=max_seeds_per_turn,
                recurrence_mode=recurrence_mode,
                cluster_threshold=cluster_threshold,
                semantic_duplicate_threshold=semantic_duplicate_threshold,
                reviewers=reviewers,
            )
            if evaluation_artifact["summary"]["conversation_count"]:
                evaluation_path = _write_json(
                    raw_dir / f"evaluation_{suite.suite_id}.json", evaluation_artifact
                )
                artifact_paths.append(evaluation_path)
                artifacts.append(evaluation_artifact)
                answer_packets.extend(answers)
                answer_keys.extend(answer_key)

    candidate_packet_path = _write_json(
        review_dir / "candidate_review_packet.json",
        {
            "schema": REVIEW_SCHEMA,
            "review_type": "candidate",
            "items": candidate_packets,
        },
    )
    candidate_key_path = _write_json(
        review_dir / "candidate_review_key.json",
        {"schema": REVIEW_SCHEMA, "review_type": "candidate_key", "items": candidate_keys},
    )
    answer_packet_path = _write_json(
        review_dir / "answer_review_packet.json",
        {"schema": REVIEW_SCHEMA, "review_type": "answer", "items": answer_packets},
    )
    answer_key_path = _write_json(
        review_dir / "answer_review_key.json",
        {"schema": REVIEW_SCHEMA, "review_type": "answer_key", "items": answer_keys},
    )
    artifact_paths.extend(
        [
            environment_path,
            copied_preregistration,
            *(copied_suite for _suite, _payload, copied_suite in suite_payloads),
            candidate_packet_path,
            candidate_key_path,
            answer_packet_path,
            answer_key_path,
        ]
    )

    aggregate = _aggregate_run_summaries(artifacts)
    summary_payload = {
        "schema": BUNDLE_SCHEMA,
        "run_id": run_id,
        "created_at": _utc_now(),
        "claim_level": claim_level,
        "automatic_metrics": aggregate,
        "candidate_review_item_count": len(candidate_packets),
        "answer_review_item_count": len(answer_packets),
        "review_status": "pending" if candidate_packets or answer_packets else "not_applicable",
        "claim_boundary": prereg["claim_boundary"],
    }
    summary_path = _write_json(output_dir / "summary.json", summary_payload)
    artifact_paths.append(summary_path)
    report_path = output_dir / "REPORT.md"
    _write_report(
        report_path,
        run_id=run_id,
        model_reference=model_reference,
        aggregate=aggregate,
        candidate_count=len(candidate_packets),
        answer_count=len(answer_packets),
    )
    artifact_paths.append(report_path)

    suite_manifest = [
        {
            "suite_id": suite.suite_id,
            "path": str(copied_suite.relative_to(output_dir)),
            "sha256": _sha256_file(copied_suite),
            "version": payload.get("version"),
        }
        for suite, payload, copied_suite in suite_payloads
    ]
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "run_id": run_id,
        "created_at": _utc_now(),
        "source": source,
        "model": {
            "backend": backend,
            "runtime_id": model_id,
            "reference": model_reference,
            "revision": model_revision,
            "digest": model_digest,
            "quantization": quantization,
            "max_new_tokens": max_new_tokens,
            "detector_prompt_variant": "generative",
            "detector_id": OPEN_SET_GENERATIVE_DETECTOR_ID,
            "detector_prompt_template_sha256": _sha256_bytes(
                OPEN_SET_GENERATIVE_PROMPT.encode("utf-8")
            ),
            "authority_effect_of_model_identity": "none",
        },
        "embedding": {
            "backend": embedding_backend,
            "runtime_model": embedding_model,
            "reference": embedding_reference or embedding_model,
            "revision": embedding_revision,
            "dimension": embedding_dimension,
            "semantic_duplicate_threshold": semantic_duplicate_threshold,
        },
        "runtime": {
            "surface_threshold": surface_threshold,
            "surface_top_k": surface_top_k,
            "early_turn_margin": early_turn_margin,
            "early_turn_history": early_turn_history,
            "resurface_margin": resurface_margin,
            "max_seeds_per_turn": max_seeds_per_turn,
            "recurrence_mode": recurrence_mode,
            "cluster_threshold": cluster_threshold,
            "live_gate_policy": "evidence_backed",
            "evaluation_gate_policy": "exploratory",
            "external_evidence_injected": False,
        },
        "evaluation_conversation_ids": sorted(evaluation_conversation_ids or []),
        "preregistration": {
            "path": str(copied_preregistration.relative_to(output_dir)),
            "sha256": _sha256_file(copied_preregistration),
            "protocol_id": prereg["protocol_id"],
        },
        "suites": suite_manifest,
        "environment": environment,
        "timing": {"adapter_setup_elapsed_seconds": round(setup_elapsed, 3)},
        "claim_boundary": prereg["claim_boundary"],
        "artifacts": {
            str(path.relative_to(output_dir)): {
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in artifact_paths
        },
    }
    manifest_path = _write_json(output_dir / "manifest.json", manifest)
    verify_capability_bundle(output_dir)
    return manifest_path


def verify_capability_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    manifest_path = output_dir / "manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("unsupported capability bundle schema")
    checked = 0
    for relative, metadata in manifest.get("artifacts", {}).items():
        path = output_dir / relative
        if not path.is_file():
            raise ValueError(f"bundle artifact is missing: {relative}")
        actual = _sha256_file(path)
        expected = metadata.get("sha256")
        if actual != expected:
            raise ValueError(f"bundle artifact hash mismatch: {relative}")
        checked += 1
    if checked == 0:
        raise ValueError("capability bundle manifest contains no artifacts")
    return {"verified": True, "artifact_count": checked, "run_id": manifest.get("run_id")}


def _cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    observed = sum(left == right for left, right in pairs) / len(pairs)
    left_counts = Counter(left for left, _right in pairs)
    right_counts = Counter(right for _left, right in pairs)
    categories = set(left_counts) | set(right_counts)
    expected = sum(
        (left_counts[category] / len(pairs)) * (right_counts[category] / len(pairs))
        for category in categories
    )
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else None
    return round((observed - expected) / (1.0 - expected), 6)


def _agreement(items: list[dict[str, Any]], field: str) -> dict[str, Any]:
    pairs: list[tuple[str, str]] = []
    for item in items:
        values = [
            str(response.get("scores", {}).get(field, "")).strip()
            for response in item.get("reviewer_responses", [])
        ]
        values = [value for value in values if value]
        if len(values) == 2:
            pairs.append((values[0], values[1]))
    return {
        "pair_count": len(pairs),
        "raw_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 6)
        if pairs
        else None,
        "cohen_kappa": _cohen_kappa(pairs),
    }


def summarize_reviews(
    *,
    candidate_packet_path: Path,
    candidate_key_path: Path,
    answer_packet_path: Path,
    answer_key_path: Path,
    output_path: Path,
) -> Path:
    candidate_packet = _load_json(candidate_packet_path)
    candidate_key = _load_json(candidate_key_path)
    answer_packet = _load_json(answer_packet_path)
    answer_key = _load_json(answer_key_path)
    if candidate_packet.get("schema") != REVIEW_SCHEMA or answer_packet.get("schema") != REVIEW_SCHEMA:
        raise ValueError("unsupported review packet schema")
    candidate_items = list(candidate_packet.get("items", []))
    answer_items = list(answer_packet.get("items", []))
    candidate_key_by_id = {item["review_id"]: item for item in candidate_key.get("items", [])}
    answer_key_by_id = {item["review_id"]: item for item in answer_key.get("items", [])}

    candidate_scores: dict[str, Counter[str]] = {field: Counter() for field in CANDIDATE_FIELDS}
    role_counts: Counter[str] = Counter()
    completed_candidate_reviews = 0
    for item in candidate_items:
        if item.get("review_id") not in candidate_key_by_id:
            raise ValueError(f"candidate review item lacks key: {item.get('review_id')}")
        for response in item.get("reviewer_responses", []):
            scores = response.get("scores", {})
            populated = False
            for field in CANDIDATE_FIELDS:
                value = str(scores.get(field, "")).strip()
                if value:
                    if value not in CATEGORICAL_VALUES:
                        raise ValueError(f"invalid candidate score {field}={value!r}")
                    candidate_scores[field][value] += 1
                    populated = True
            role = str(scores.get("epistemic_role", "")).strip()
            if role:
                if role not in EPISTEMIC_ROLES:
                    raise ValueError(f"invalid epistemic_role={role!r}")
                role_counts[role] += 1
                populated = True
            completed_candidate_reviews += int(populated)

    field_rates: dict[str, Any] = {}
    for field, counts in candidate_scores.items():
        decisive = counts["yes"] + counts["no"]
        field_rates[field] = {
            "yes": counts["yes"],
            "no": counts["no"],
            "unclear": counts["unclear"],
            "yes_rate_decisive": round(counts["yes"] / decisive, 6) if decisive else None,
            "agreement": _agreement(candidate_items, field),
        }

    answer_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    completed_answer_reviews = 0
    for item in answer_items:
        key = answer_key_by_id.get(item.get("review_id"))
        if key is None:
            raise ValueError(f"answer review item lacks key: {item.get('review_id')}")
        for response in item.get("reviewer_responses", []):
            value = str(response.get("scores", {}).get("better_answer", "")).strip()
            if not value:
                continue
            if value not in ANSWER_VALUES:
                raise ValueError(f"invalid better_answer={value!r}")
            answer_counts[value] += 1
            completed_answer_reviews += 1
            if value == "tie":
                source_counts["tie"] += 1
            else:
                source = key["option_a_source"] if value == "A" else key["option_b_source"]
                source_counts[source] += 1
    non_ties = source_counts["ssl"] + source_counts["baseline"]
    payload = {
        "schema": REVIEW_SCHEMA,
        "candidate": {
            "item_count": len(candidate_items),
            "completed_reviewer_rows": completed_candidate_reviews,
            "fields": field_rates,
            "epistemic_role_counts": dict(sorted(role_counts.items())),
        },
        "answer": {
            "item_count": len(answer_items),
            "completed_reviewer_rows": completed_answer_reviews,
            "blind_option_counts": dict(sorted(answer_counts.items())),
            "unblinded_source_counts": dict(sorted(source_counts.items())),
            "ssl_win_rate_non_tie": round(source_counts["ssl"] / non_ties, 6)
            if non_ties
            else None,
            "agreement": _agreement(answer_items, "better_answer"),
        },
        "claim_boundary": (
            "Review summaries describe this finite reviewed sample only. Agreement and win rates "
            "do not establish general model superiority, candidate truth, or production readiness."
        ),
    }
    return _write_json(output_path, payload)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post-alignment SSL capability scaling harness")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run live/evaluation capability measurements")
    run.add_argument("--suite", action="append", required=True, type=_parse_suite)
    run.add_argument("--output-dir", required=True, type=Path)
    run.add_argument("--preregistration", required=True, type=Path)
    run.add_argument("--backend", choices=["fixture", "hf-transformers", "ollama", "openai"], required=True)
    run.add_argument("--model-id", required=True)
    run.add_argument("--model-reference", default=None)
    run.add_argument("--model-revision", default=None)
    run.add_argument("--model-digest", default=None)
    run.add_argument("--quantization", default=None)
    run.add_argument("--max-new-tokens", type=int, default=320)
    run.add_argument(
        "--embedding-backend",
        choices=["lexical", "sentence-transformers", "openai"],
        default="sentence-transformers",
    )
    run.add_argument("--embedding-model", default=None)
    run.add_argument("--embedding-reference", default=None)
    run.add_argument("--embedding-revision", default=None)
    run.add_argument("--surface-threshold", type=float, default=0.30)
    run.add_argument("--surface-top-k", type=int, default=2)
    run.add_argument("--early-turn-margin", type=float, default=0.10)
    run.add_argument("--early-turn-history", type=int, default=5)
    run.add_argument("--resurface-margin", type=float, default=0.15)
    run.add_argument("--max-seeds-per-turn", type=int, default=5)
    run.add_argument("--recurrence-mode", choices=["pairwise", "cluster"], default="cluster")
    run.add_argument("--cluster-threshold", type=float, default=None)
    run.add_argument("--semantic-duplicate-threshold", type=float, default=0.85)
    run.add_argument("--evaluation-conversation", action="append", default=[])
    run.add_argument("--reviewer-id", action="append", default=[])
    run.add_argument("--run-id", default=None)

    verify = sub.add_parser("verify", help="verify artifact hashes in a capability bundle")
    verify.add_argument("output_dir", type=Path)

    summarize = sub.add_parser("summarize-reviews", help="summarize completed blind review packets")
    summarize.add_argument("--candidate-packet", required=True, type=Path)
    summarize.add_argument("--candidate-key", required=True, type=Path)
    summarize.add_argument("--answer-packet", required=True, type=Path)
    summarize.add_argument("--answer-key", required=True, type=Path)
    summarize.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "run":
        reviewers = tuple(args.reviewer_id or DEFAULT_REVIEWERS)
        manifest = run_capability_scaling(
            suites=args.suite,
            output_dir=args.output_dir,
            preregistration_path=args.preregistration,
            backend=args.backend,
            model_id=args.model_id,
            model_reference=args.model_reference or args.model_id,
            model_revision=args.model_revision,
            model_digest=args.model_digest,
            quantization=args.quantization,
            max_new_tokens=args.max_new_tokens,
            embedding_backend=args.embedding_backend,
            embedding_model=args.embedding_model,
            embedding_reference=args.embedding_reference,
            embedding_revision=args.embedding_revision,
            surface_threshold=args.surface_threshold,
            surface_top_k=args.surface_top_k,
            early_turn_margin=args.early_turn_margin,
            early_turn_history=args.early_turn_history,
            resurface_margin=args.resurface_margin,
            max_seeds_per_turn=args.max_seeds_per_turn,
            recurrence_mode=args.recurrence_mode,
            cluster_threshold=args.cluster_threshold,
            semantic_duplicate_threshold=args.semantic_duplicate_threshold,
            evaluation_conversation_ids=set(args.evaluation_conversation) or None,
            reviewers=reviewers,
            run_id=args.run_id,
        )
        print(manifest)
        return 0
    if args.command == "verify":
        print(json.dumps(verify_capability_bundle(args.output_dir), indent=2))
        return 0
    if args.command == "summarize-reviews":
        output = summarize_reviews(
            candidate_packet_path=args.candidate_packet,
            candidate_key_path=args.candidate_key,
            answer_packet_path=args.answer_packet,
            answer_key_path=args.answer_key,
            output_path=args.output,
        )
        print(output)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
