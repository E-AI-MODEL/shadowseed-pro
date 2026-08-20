"""Evidence-backed paired efficacy research for Shadow Seed Learning.

This module does not define a second authority system. It drives the canonical
:class:`shadowseed.chat.ShadowChatSession` in baseline-isolated evaluation mode
while selecting the shipped ``evidence_backed`` Gate policy. Predeclared,
operator-attested external support is submitted only through
:meth:`ShadowChatSession.submit_evidence`.

The purpose is narrow: create auditable opportunities to compare a baseline
answer with an SSL answer on a later turn where a genuinely authorized seed
actually surfaced. A missing candidate, rejected evidence event, point-of-use
block, or lack of later relevance remains a result rather than being repaired by
weakening the Gate.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.adapters.models import make_backend
from shadowseed.benchmark.capability_scaling import (
    DEFAULT_REVIEWERS,
    REVIEW_SCHEMA,
    _blank_answer_scores,
    _git_provenance,
    _review_id,
    _sha256_file,
    _utc_now,
    _write_environment_manifest,
    _write_json,
)
from shadowseed.benchmark.ssl45_model_benefit_suite import blind_order
from shadowseed.chat import ShadowChatSession
from shadowseed.detection.model_detector import make_detector_backend
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal


BUNDLE_SCHEMA = "ssl-evidence-efficacy-bundle-v1"
SUITE_SCHEMA = "ssl-evidence-efficacy-suite-v1"
PREREG_SCHEMA = "ssl-evidence-efficacy-preregistration-v1"
_EXTERNAL_KINDS = {SignalKind.SSOT, SignalKind.HUMAN_FEEDBACK, SignalKind.RETRIEVAL}


@dataclass(frozen=True)
class EvidenceSelector:
    """A preregistered way to identify one observed candidate without creating it."""

    born_turn: int | None = None
    seed_index: int | None = None
    seed_id: str | None = None
    text_contains: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSelector":
        selector = cls(
            born_turn=(None if data.get("born_turn") is None else int(data["born_turn"])),
            seed_index=(None if data.get("seed_index") is None else int(data["seed_index"])),
            seed_id=(None if data.get("seed_id") is None else str(data["seed_id"])),
            text_contains=(
                None if data.get("text_contains") is None else str(data["text_contains"]).strip()
            ),
        )
        methods = sum(
            (
                selector.seed_id is not None,
                selector.text_contains is not None,
                selector.born_turn is not None or selector.seed_index is not None,
            )
        )
        if methods != 1:
            raise ValueError(
                "evidence selector must use exactly one of seed_id, text_contains, "
                "or born_turn+seed_index"
            )
        if (selector.born_turn is None) != (selector.seed_index is None):
            raise ValueError("born_turn and seed_index must be supplied together")
        if selector.born_turn is not None and selector.born_turn < 0:
            raise ValueError("born_turn must be >= 0")
        if selector.seed_index is not None and selector.seed_index < 0:
            raise ValueError("seed_index must be >= 0")
        if selector.text_contains is not None and not selector.text_contains:
            raise ValueError("text_contains must not be blank")
        return selector

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "born_turn": self.born_turn,
                "seed_index": self.seed_index,
                "seed_id": self.seed_id,
                "text_contains": self.text_contains,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class EvidencePlanItem:
    evidence_id: str
    after_turn: int
    selector: EvidenceSelector
    kind: SignalKind
    source_ref: str
    strength: float
    independent: bool
    reason: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidencePlanItem":
        kind = SignalKind(str(data.get("kind", "")))
        if kind not in _EXTERNAL_KINDS:
            raise ValueError("efficacy evidence kind must be ssot, human_feedback, or retrieval")
        source_ref = str(data.get("source_ref", "")).strip()
        if not source_ref:
            raise ValueError("efficacy evidence requires a stable source_ref")
        evidence_id = str(data.get("evidence_id", "")).strip()
        if not evidence_id:
            raise ValueError("efficacy evidence requires evidence_id")
        after_turn = int(data.get("after_turn", -1))
        if after_turn < 0:
            raise ValueError("after_turn must be >= 0")
        reason = str(data.get("reason", "")).strip()
        if not reason:
            raise ValueError("efficacy evidence requires an operator/research reason")
        strength = float(data.get("strength", 1.0))
        if not 0.0 <= strength <= 1.0:
            raise ValueError("efficacy evidence strength must be in [0, 1]")
        return cls(
            evidence_id=evidence_id,
            after_turn=after_turn,
            selector=EvidenceSelector.from_dict(dict(data.get("selector", {}))),
            kind=kind,
            source_ref=source_ref,
            strength=strength,
            independent=bool(data.get("independent", True)),
            reason=reason,
        )


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def validate_preregistration(data: dict[str, Any]) -> None:
    if data.get("schema") != PREREG_SCHEMA:
        raise ValueError(f"preregistration schema must be {PREREG_SCHEMA!r}")
    required = {
        "protocol_id",
        "claim_boundary",
        "primary_metrics",
        "exclusion_rules",
        "evidence_contract",
        "review_contract",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"preregistration missing fields: {', '.join(missing)}")
    contract = data["evidence_contract"]
    if not isinstance(contract, dict):
        raise TypeError("evidence_contract must be an object")
    if contract.get("gate_policy_id") != "evidence_backed":
        raise ValueError("efficacy protocol must use gate_policy_id='evidence_backed'")
    if contract.get("generated_model_output_is_evidence") is not False:
        raise ValueError("protocol must explicitly reject generated model output as evidence")
    review = data["review_contract"]
    if not isinstance(review, dict) or review.get("blind_answer_preference") is not True:
        raise ValueError("protocol must require blind answer preference review")


def validate_suite(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("schema") != SUITE_SCHEMA:
        raise ValueError(f"suite schema must be {SUITE_SCHEMA!r}")
    if data.get("language") != "en":
        raise ValueError("evidence efficacy suite must declare language='en'")
    conversations = data.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        raise ValueError("evidence efficacy suite requires conversations")
    for conversation in conversations:
        if not isinstance(conversation, dict):
            raise TypeError("conversation must be an object")
        turns = conversation.get("turns")
        if not isinstance(turns, list) or len(turns) < 2:
            raise ValueError("efficacy conversation needs at least two turns")
        for turn in turns:
            if not isinstance(turn, dict) or not str(turn.get("question", "")).strip():
                raise ValueError("every efficacy turn requires a question")
        plans = [EvidencePlanItem.from_dict(dict(item)) for item in conversation.get("evidence_plan", [])]
        if not plans:
            raise ValueError("efficacy conversation requires at least one evidence_plan item")
        ids = [item.evidence_id for item in plans]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique within a conversation")
        for item in plans:
            if item.after_turn >= len(turns) - 1:
                raise ValueError(
                    "evidence must be scheduled before at least one later turn so surfacing can be measured"
                )
    return conversations


def _select_seed(
    session: ShadowChatSession,
    selector: EvidenceSelector,
    turn_reports: list[dict[str, Any]],
) -> tuple[str | None, str]:
    if selector.seed_id is not None:
        if selector.seed_id in session.manager.seeds:
            return selector.seed_id, "matched_seed_id"
        return None, "seed_id_not_observed"
    if selector.text_contains is not None:
        needle = selector.text_contains.casefold()
        matches = [
            seed_id
            for seed_id, seed in session.manager.seeds.items()
            if needle in seed.text.casefold()
        ]
        if len(matches) == 1:
            return matches[0], "matched_text_contains"
        if not matches:
            return None, "text_selector_not_observed"
        return None, "text_selector_ambiguous"
    assert selector.born_turn is not None and selector.seed_index is not None
    if selector.born_turn >= len(turn_reports):
        return None, "born_turn_not_reached"
    born = list(turn_reports[selector.born_turn].get("seeds_born_weightless", []))
    if selector.seed_index >= len(born):
        return None, "seed_index_not_observed"
    seed_id = str(born[selector.seed_index])
    if seed_id not in session.manager.seeds:
        return None, "selected_seed_missing"
    return seed_id, "matched_born_turn_index"


def _make_signal(item: EvidencePlanItem) -> ValidationSignal:
    return ValidationSignal(
        kind=item.kind,
        direction=SignalDirection.SUPPORT,
        strength=item.strength,
        source_ref=item.source_ref,
        verified=True,
        independent=item.independent,
        reason=item.reason,
    )


def _record_answer_pair(
    *,
    suite_id: str,
    conversation_id: str,
    domain: str,
    turn_index: int,
    report: dict[str, Any],
    reviewers: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, Any]]:
    rid = _review_id("evidence_answer", suite_id, conversation_id, turn_index, report["question"])
    first, second = blind_order(rid)
    answers = {
        "baseline": str(report.get("baseline_answer", "")),
        "ssl": str(report.get("ssl_answer", "")),
    }
    packet = {
        "review_id": rid,
        "domain": domain,
        "question": str(report["question"]),
        "option_a": answers[first],
        "option_b": answers[second],
        "reviewer_instruction": (
            "Choose the more useful answer. Penalize invented, forced, repetitive, or off-topic "
            "content. Do not reward SSL merely because an authorized seed was present."
        ),
        "reviewer_responses": [
            {"reviewer_id": reviewer, "scores": _blank_answer_scores()}
            for reviewer in reviewers
        ],
    }
    key = {
        "review_id": rid,
        "suite_id": suite_id,
        "conversation_id": conversation_id,
        "turn": turn_index,
        "surfaced_seed_ids": list(report.get("surfaced_seed_ids", [])),
        "option_a_source": first,
        "option_b_source": second,
    }
    return packet, key


def _finalize_opportunity(
    opportunity: dict[str, Any],
    turn_reports: list[dict[str, Any]],
) -> None:
    seed_id = opportunity.get("matched_seed_id")
    if not seed_id:
        opportunity["terminal_reason"] = opportunity.get("selector_result", "candidate_not_observed")
        return
    scheduled = int(opportunity["scheduled_after_turn"])
    later_reports = [report for report in turn_reports if int(report["turn"]) > scheduled]
    opportunity["later_selected_turns"] = [
        int(report["turn"])
        for report in later_reports
        if seed_id in report.get("selected_seed_ids", [])
    ]
    opportunity["later_surfaced_turns"] = [
        int(report["turn"])
        for report in later_reports
        if seed_id in report.get("surfaced_seed_ids", [])
    ]
    opportunity["ab_generated_turns"] = list(opportunity["later_surfaced_turns"])
    blocked: list[dict[str, Any]] = []
    for report in later_reports:
        if seed_id not in report.get("selected_seed_ids", []):
            continue
        for decision in report.get("influence_decisions", []):
            if str(decision.get("seed_id")) == seed_id and not bool(decision.get("allowed")):
                blocked.append(
                    {
                        "turn": int(report["turn"]),
                        "reason": str(decision.get("reason", "unknown")),
                    }
                )
    opportunity["point_of_use_blocks"] = blocked
    if opportunity.get("authority_granted") is not True:
        opportunity["terminal_reason"] = "gate_did_not_grant_authority"
    elif opportunity["later_surfaced_turns"]:
        opportunity["terminal_reason"] = "ab_generated"
    elif opportunity["later_selected_turns"]:
        opportunity["terminal_reason"] = "selected_but_not_authorized_at_point_of_use"
    else:
        opportunity["terminal_reason"] = "no_later_relevant_surfacing_opportunity"


def run_evidence_efficacy(
    *,
    suite_path: Path,
    preregistration_path: Path,
    output_dir: Path,
    backend: str,
    model_id: str,
    model_reference: str,
    model_revision: str | None,
    model_digest: str | None,
    max_new_tokens: int,
    embedding_backend: str,
    embedding_model: str | None,
    embedding_reference: str | None,
    embedding_revision: str | None,
    surface_threshold: float,
    surface_top_k: int,
    reviewers: tuple[str, ...],
    run_id: str | None = None,
) -> Path:
    prereg = _load_json(preregistration_path)
    validate_preregistration(prereg)
    suite = _load_json(suite_path)
    conversations = validate_suite(suite)
    if not reviewers or len(set(reviewers)) != len(reviewers):
        raise ValueError("reviewer ids must be non-empty and unique")
    if backend == "hf-transformers" and not model_revision:
        raise ValueError("hf-transformers efficacy runs require --model-revision")
    if backend == "ollama" and not model_digest:
        raise ValueError("ollama efficacy runs require --model-digest")
    if backend == "openai" and not model_revision:
        raise ValueError("openai efficacy runs require an explicit model snapshot/revision")
    if embedding_backend == "sentence-transformers" and not embedding_revision:
        raise ValueError("sentence-transformers efficacy runs require --embedding-revision")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    review_dir = output_dir / "review"
    inputs_dir = output_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    source = _git_provenance()
    if run_id is None:
        source_tag = str(source.get("source_revision") or "unknown")[:8]
        run_id = f"{_utc_now().replace(':', '').replace('-', '')[:15]}-{source_tag}-evidence-efficacy"

    copied_prereg = inputs_dir / "preregistration.json"
    copied_suite = inputs_dir / "suite.json"
    copied_prereg.write_bytes(preregistration_path.read_bytes())
    copied_suite.write_bytes(suite_path.read_bytes())
    environment_path = output_dir / "environment.txt"
    environment = _write_environment_manifest(environment_path)
    environment["path"] = "environment.txt"

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

    raw_conversations: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []
    answer_packets: list[dict[str, Any]] = []
    answer_keys: list[dict[str, Any]] = []

    for conversation in conversations:
        conversation_id = str(conversation.get("id", "conversation"))
        domain = str(conversation.get("domain", ""))
        session = ShadowChatSession(
            backend=backend,
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            embedding_backend=embedding_backend,
            embedding_model=embedding_model,
            surface_threshold=float(conversation.get("surface_threshold", surface_threshold)),
            surface_top_k=int(conversation.get("surface_top_k", surface_top_k)),
            early_turn_margin=float(conversation.get("early_turn_margin", 0.0)),
            early_turn_history=int(conversation.get("early_turn_history", 0)),
            resurface_margin=float(conversation.get("resurface_margin", 0.0)),
            max_seeds_per_turn=int(conversation.get("max_seeds_per_turn", 5)),
            recurrence_mode=str(conversation.get("recurrence_mode", "cluster")),
            cluster_threshold=(
                None
                if conversation.get("cluster_threshold") is None
                else float(conversation["cluster_threshold"])
            ),
            runtime_mode="evaluation",
            gate_policy_id="evidence_backed",
            model_backend=model,
            detector_backend=detector,
            embedding_fn=embed_fn,
        )
        plans = [EvidencePlanItem.from_dict(dict(item)) for item in conversation["evidence_plan"]]
        by_turn: dict[int, list[EvidencePlanItem]] = {}
        for item in plans:
            by_turn.setdefault(item.after_turn, []).append(item)
        turn_reports: list[dict[str, Any]] = []
        conversation_opportunities: list[dict[str, Any]] = []

        for turn_index, turn in enumerate(conversation["turns"]):
            report = session.turn(str(turn["question"]))
            turn_reports.append(report)
            if report.get("surfaced_seed_ids"):
                packet, key = _record_answer_pair(
                    suite_id=str(suite.get("version", "suite")),
                    conversation_id=conversation_id,
                    domain=domain,
                    turn_index=turn_index,
                    report=report,
                    reviewers=reviewers,
                )
                answer_packets.append(packet)
                answer_keys.append(key)

            for item in by_turn.get(turn_index, []):
                seed_id, selector_result = _select_seed(session, item.selector, turn_reports)
                opportunity: dict[str, Any] = {
                    "evidence_id": item.evidence_id,
                    "conversation_id": conversation_id,
                    "scheduled_after_turn": item.after_turn,
                    "selector": item.selector.to_dict(),
                    "selector_result": selector_result,
                    "candidate_observed": seed_id is not None,
                    "matched_seed_id": seed_id,
                    "evidence_kind": item.kind.value,
                    "source_ref": item.source_ref,
                    "evidence_submitted": False,
                    "gate_decision": None,
                    "authority_granted": False,
                }
                if seed_id is not None:
                    result = session.submit_evidence(seed_id, _make_signal(item))
                    opportunity["evidence_submitted"] = True
                    opportunity["gate_decision"] = result["decision"]
                    opportunity["weight_after_evidence"] = result["weight_after"]
                    opportunity["status_after_evidence"] = result["status_after"]
                    opportunity["evidence_count_after"] = result["evidence_count"]
                    opportunity["authority_granted"] = (
                        float(result["weight_after"]) > 0.0
                        and str(result["status_after"]) == "PROMOTED"
                    )
                    opportunity["gate_event"] = result["gate_event"]
                conversation_opportunities.append(opportunity)

        for opportunity in conversation_opportunities:
            _finalize_opportunity(opportunity, turn_reports)
        opportunities.extend(conversation_opportunities)
        session.audit()
        raw_conversations.append(
            {
                "conversation_id": conversation_id,
                "domain": domain,
                "turns": turn_reports,
                "opportunities": conversation_opportunities,
                "gate_events": [event.to_dict() for event in session.manager.gate_events],
                "final_shadow": session.shadow_report(),
            }
        )

    raw_path = _write_json(
        raw_dir / "evidence_backed_paired.json",
        {
            "schema": BUNDLE_SCHEMA,
            "runtime_mode": "evaluation",
            "gate_policy_id": "evidence_backed",
            "production_policy": False,
            "purpose": "baseline-isolated research measurement of evidence-backed influence",
            "conversations": raw_conversations,
        },
    )
    opportunity_path = _write_json(
        output_dir / "opportunity_audit.json",
        {
            "schema": BUNDLE_SCHEMA,
            "stage_order": [
                "candidate_observed",
                "evidence_submitted",
                "gate_authority_granted",
                "later_selected",
                "point_of_use_allowed",
                "surfaced",
                "ab_generated",
            ],
            "items": opportunities,
        },
    )
    candidate_packet_path = _write_json(
        review_dir / "candidate_review_packet.json",
        {"schema": REVIEW_SCHEMA, "review_type": "candidate", "items": []},
    )
    candidate_key_path = _write_json(
        review_dir / "candidate_review_key.json",
        {"schema": REVIEW_SCHEMA, "review_type": "candidate_key", "items": []},
    )
    answer_packet_path = _write_json(
        review_dir / "answer_review_packet.json",
        {"schema": REVIEW_SCHEMA, "review_type": "answer", "items": answer_packets},
    )
    answer_key_path = _write_json(
        review_dir / "answer_review_key.json",
        {"schema": REVIEW_SCHEMA, "review_type": "answer_key", "items": answer_keys},
    )

    reason_counts: dict[str, int] = {}
    for item in opportunities:
        reason = str(item["terminal_reason"])
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    summary_path = _write_json(
        output_dir / "summary.json",
        {
            "schema": BUNDLE_SCHEMA,
            "run_id": run_id,
            "created_at": _utc_now(),
            "claim_level": "harness-smoke" if backend == "fixture" else "real-model-research",
            "evidence_opportunity_count": len(opportunities),
            "candidate_observed_count": sum(bool(item["candidate_observed"]) for item in opportunities),
            "authority_granted_count": sum(bool(item["authority_granted"]) for item in opportunities),
            "surfaced_opportunity_count": sum(bool(item.get("later_surfaced_turns")) for item in opportunities),
            "answer_review_item_count": len(answer_packets),
            "terminal_reason_counts": dict(sorted(reason_counts.items())),
            "review_status": "pending" if answer_packets else "not_applicable",
            "claim_boundary": prereg["claim_boundary"],
        },
    )

    artifact_paths = [
        raw_path,
        opportunity_path,
        candidate_packet_path,
        candidate_key_path,
        answer_packet_path,
        answer_key_path,
        summary_path,
        environment_path,
        copied_prereg,
        copied_suite,
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
            "authority_effect_of_model_identity": "none",
        },
        "embedding": {
            "backend": embedding_backend,
            "runtime_model": embedding_model,
            "reference": embedding_reference or embedding_model,
            "revision": embedding_revision,
            "dimension": embedding_dimension,
        },
        "research_runtime": {
            "runtime_mode": "evaluation",
            "gate_policy_id": "evidence_backed",
            "baseline_history_isolated": True,
            "evidence_submission_api": "ShadowChatSession.submit_evidence",
            "generated_model_output_is_evidence": False,
        },
        "preregistration": {
            "path": "inputs/preregistration.json",
            "sha256": _sha256_file(copied_prereg),
            "protocol_id": prereg["protocol_id"],
        },
        "suite": {
            "path": "inputs/suite.json",
            "sha256": _sha256_file(copied_suite),
            "version": suite.get("version"),
        },
        "environment": environment,
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
    verify_evidence_efficacy_bundle(output_dir)
    return manifest_path


def verify_evidence_efficacy_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    manifest = _load_json(output_dir / "manifest.json")
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("unsupported evidence efficacy bundle schema")
    checked = 0
    for relative, metadata in manifest.get("artifacts", {}).items():
        path = output_dir / relative
        if not path.is_file():
            raise ValueError(f"bundle artifact is missing: {relative}")
        if _sha256_file(path) != metadata.get("sha256"):
            raise ValueError(f"bundle artifact hash mismatch: {relative}")
        checked += 1
    return {"verified": True, "artifact_count": checked, "run_id": manifest.get("run_id")}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence-backed SSL efficacy research runner")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--suite", required=True, type=Path)
    run.add_argument("--preregistration", required=True, type=Path)
    run.add_argument("--output-dir", required=True, type=Path)
    run.add_argument("--backend", choices=["fixture", "hf-transformers", "ollama", "openai"], required=True)
    run.add_argument("--model-id", required=True)
    run.add_argument("--model-reference", default=None)
    run.add_argument("--model-revision", default=None)
    run.add_argument("--model-digest", default=None)
    run.add_argument("--max-new-tokens", type=int, default=320)
    run.add_argument("--embedding-backend", choices=["lexical", "sentence-transformers", "openai"], default="sentence-transformers")
    run.add_argument("--embedding-model", default=None)
    run.add_argument("--embedding-reference", default=None)
    run.add_argument("--embedding-revision", default=None)
    run.add_argument("--surface-threshold", type=float, default=0.30)
    run.add_argument("--surface-top-k", type=int, default=2)
    run.add_argument("--reviewer-id", action="append", default=[])
    run.add_argument("--run-id", default=None)
    verify = sub.add_parser("verify")
    verify.add_argument("output_dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "run":
        manifest = run_evidence_efficacy(
            suite_path=args.suite,
            preregistration_path=args.preregistration,
            output_dir=args.output_dir,
            backend=args.backend,
            model_id=args.model_id,
            model_reference=args.model_reference or args.model_id,
            model_revision=args.model_revision,
            model_digest=args.model_digest,
            max_new_tokens=args.max_new_tokens,
            embedding_backend=args.embedding_backend,
            embedding_model=args.embedding_model,
            embedding_reference=args.embedding_reference,
            embedding_revision=args.embedding_revision,
            surface_threshold=args.surface_threshold,
            surface_top_k=args.surface_top_k,
            reviewers=tuple(args.reviewer_id or DEFAULT_REVIEWERS),
            run_id=args.run_id,
        )
        print(manifest)
        return 0
    if args.command == "verify":
        print(json.dumps(verify_evidence_efficacy_bundle(args.output_dir), indent=2))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
