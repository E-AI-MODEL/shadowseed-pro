"""Offline research audit of the REAL ShadowChatSession detector/intake path.

The input contains PRE-RECORDED, investigator-authored text, not live LLM
answers. The existing OpenAIDetectorBackend.detect_seeds method is exercised
with a fake no-network transport so its original prompts, parser, and legacy
generative-prefix behavior are preserved. The existing ShadowChatSession then
performs canonical candidate normalization, intake, observations and seed birth.

This does NOT evaluate detector efficacy, model representations, H-Neurons,
actual model capabilities, or the full Q1/Q2 Shadowseed thesis.
Never use the output as evidence that a model found, missed or grew a gap.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from shadowseed.chat import ShadowChatSession
from shadowseed.detection.model_detector import OpenAIDetectorBackend

SCHEMA = "shadowseed-step1-recorded-detector-v0"
RESULT_SCHEMA = "shadowseed-step1-gap-birth-audit-v0"
VARIANTS = ("current_pair", "generative")
MAX_CASES = 3
MAX_TURNS = 8
MAX_TEXT_CHARS = 4000


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def validate_fixture(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise ValueError("unexpected recorded-detector fixture schema")
    if "SYNTHETIC" not in str(document.get("provenance", "")):
        raise ValueError("recorded fixtures must declare synthetic provenance")
    cases = document.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ValueError("require 1-3 recorded cases")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("each case needs an id")
        if not case["id"].strip() or case["id"] in ids:
            raise ValueError("missing or duplicate case id")
        ids.add(case["id"])
        turns = case.get("turns")
        if not isinstance(turns, list) or not 1 <= len(turns) <= MAX_TURNS:
            raise ValueError("case needs 1-8 turns")
        for index, turn in enumerate(turns):
            if not isinstance(turn, dict):
                raise ValueError(f"{case['id']} turn {index}: not an object")
            for field in ("question", "answer"):
                value = turn.get(field)
                if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT_CHARS:
                    raise ValueError(f"{case['id']} turn {index}: invalid {field}")
            outputs = turn.get("detector_outputs")
            if not isinstance(outputs, dict) or set(outputs) != set(VARIANTS):
                raise ValueError(f"{case['id']} turn {index}: both detector variants required")
            if any(
                not isinstance(outputs[name], str) or len(outputs[name]) > MAX_TEXT_CHARS
                for name in VARIANTS
            ):
                raise ValueError(f"{case['id']} turn {index}: invalid detector output")
    return cases


class _NoGeneration:
    """Product model role is supplied by the fixture, never by a live model."""

    name = "offline-recorded-answer-NO-MODEL"

    def generate(self, *_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("unexpected model call in recorded detector audit")

    def generate_messages(self, *_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("unexpected model call in recorded detector audit")


class _NoNetworkClient:
    """Strictly one recorded response per detector turn, no HTTP or retries."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []
        self.calls = 0

    def generate(self, prompt: str, *, max_new_tokens: int = 400) -> str:
        if not isinstance(prompt, str) or not prompt or max_new_tokens <= 0:
            raise ValueError("invalid detector prompt")
        if self.calls >= len(self._responses):
            raise AssertionError("scripted detector output exhausted")
        self.prompts.append(prompt)
        raw = self._responses[self.calls]
        self.calls += 1
        return raw


def _recorded_product_detector(responses: list[str], variant: str) -> tuple[
    OpenAIDetectorBackend, _NoNetworkClient
]:
    """Use the *existing* detector's prompt and parser without its API init.

    This is a test-only transport injection into the product backend method,
    not a detector rewrite or a claimed OpenAI model inference.
    """
    if variant not in VARIANTS:
        raise ValueError("unknown detector variant")
    transport = _NoNetworkClient(responses)
    detector = object.__new__(OpenAIDetectorBackend)
    detector.prompt_variant = variant
    detector.name = f"offline-recorded:{variant}:NO-MODEL"
    detector.model_id = "offline-NO-MODEL"
    detector.max_new_tokens = 400
    detector.last_prompt_metadata = None
    detector.last_raw_output = None
    detector.last_parse_diagnostics = None
    detector.client = transport
    return detector, transport


def _seed_snapshots(session: ShadowChatSession) -> dict[str, dict[str, Any]]:
    """Read existing canonical state; never assign or promote seed fields."""
    snapshots: dict[str, dict[str, Any]] = {}
    for sid, seed in sorted(session.manager.seeds.items()):
        snapshots[sid] = {
            "seed_id": sid,
            "text": seed.text,
            "status": seed.status.value,
            "trace": seed.trace,
            "weight": seed.weight,
            "evidence_count": seed.evidence_count,
            "occurrence_count": seed.occurrence_count,
            "turns_dormant": seed.turns_dormant,
            "origin": seed.origin.to_dict() if seed.origin is not None else None,
        }
    return snapshots


def _interpret_parser(
    raw: str,
    parsed: list[str],
    diagnostics: dict[str, int | bool] | None,
) -> str:
    diagnostics = diagnostics or {}
    if diagnostics.get("explicit_none"):
        return "explicit_NONE"
    if parsed:
        return "parsed_candidates_not_validated"
    if not raw.strip():
        return "empty_generation_not_abstention"
    return "nonempty_output_without_parsed_candidates_not_abstention"


def audit_case(case: dict[str, Any], variant: str) -> dict[str, Any]:
    """Pass recorded answers through the actual canonical live session."""
    scripted = [t["detector_outputs"][variant] for t in case["turns"]]
    detector, client = _recorded_product_detector(scripted, variant)
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        detector_backend=detector,
        model_backend=_NoGeneration(),
        revision_model_backend=_NoGeneration(),
        embedding_backend="lexical",  # offline toy fixture, NOT semantic evidence
        recurrence_mode="pairwise",
        allow_same_turn_revision=False,
        self_derived_signal_policy="fail_closed",
    )
    records: list[dict[str, Any]] = []
    for turn_no, turn in enumerate(case["turns"]):
        before = _seed_snapshots(session)
        before_event = len(session.manager.event_log)
        bounded_context = session._detector_conversation_context()
        prepared = session.prepare_turn(turn["question"])
        after_prepare = _seed_snapshots(session)
        if prepared.surfaced_seed_ids or prepared.model_context:
            session.abort_turn(prepared)
            raise AssertionError("fixture must never authorize candidate influence")
        try:
            report = session.observe_turn(prepared, turn["answer"])
        except Exception:
            # This error is not an observed NONE; no success report is produced.
            # Best effort rollback if the session still holds the prepared turn.
            if session._pending_live_turn is not None:
                try:
                    session.abort_turn(prepared)
                except Exception:
                    pass
            raise
        audit = report["detector_audit"]
        raw = audit["raw_output"]
        if raw != scripted[turn_no]:
            raise AssertionError("the real detector did not return frozen fixture output")
        prompt = client.prompts[turn_no]
        snapshots = _seed_snapshots(session)
        if report["surfaced_seed_ids"] or report["promoted_this_turn"]:
            raise AssertionError("weightless candidate must not influence answers")
        if any(s["weight"] != 0.0 or s["evidence_count"] != 0 for s in snapshots.values()):
            raise AssertionError("unverified recorded candidate gained authority")
        # A submitted Gate event may be a denial; no successful promotion is allowed.
        if any(s["status"] == "PROMOTED" for s in snapshots.values()):
            raise AssertionError("unverified recorded candidate was promoted")
        records.append({
            "turn": turn_no,
            "question": turn["question"],
            "answer": turn["answer"],
            "answer_origin": "INVESTIGATOR_SCRIPTED_NO_MODEL",
            "bounded_clean_context": bounded_context,
            "bounded_clean_context_sha256": _hash(bounded_context),
            "detector_variant": variant,
            "detector_prompt_sha256": _hash(prompt),
            "detector_prompt": prompt,
            "detector_prompt_contract": audit["prompt_contract"],
            "raw_detector_output": raw,
            "raw_detector_lines": raw.splitlines(),
            "parse_diagnostics": audit["parse_diagnostics"],
            "parse_status": _interpret_parser(
                raw, report["detected_candidates"], audit["parse_diagnostics"]
            ),
            "parsed_candidates": list(report["detected_candidates"]),
            "intake": report["intake_diagnostics"],
            "observation_ledger_entries": report["candidate_observations"],
            "seed_birth_ids_this_turn": list(report["seeds_born_weightless"]),
            "seed_state_before": before,
            "seed_state_after_prepare": after_prepare,
            "seed_state_after": snapshots,
            "manager_events_this_turn": [
                {"event_type": event.event_type, "seed_id": event.seed_id}
                for event in session.manager.event_log[before_event:]
            ],
            "gate_event_count": len(session.manager.gate_events),
            "authorized_influence_seed_ids": list(report["surfaced_seed_ids"]),
            "suppressed_self_attributed_candidates":
                list(report["suppressed_self_attributed_candidates"]),
            "research_observation_only": True,
        })
    if client.calls != len(case["turns"]):
        raise AssertionError("not all recorded detector turns were consumed")
    return {
        "case_id": case["id"],
        "variant": variant,
        "scripted_detector_calls": client.calls,
        "model_calls": 0,
        "embedding_backend": "lexical-offline-fixture",
        "birth_state": "product_SSLManager_and_ShadowChatSession",
        "turns": records,
        "seed_count": len(session.manager.seeds),
        "final_seed_state": _seed_snapshots(session),
        "total_gate_events": len(session.manager.gate_events),
        "total_influence_records": len(session.influence_records),
    }


def audit(document: dict[str, Any], fixture_sha256: str) -> dict[str, Any]:
    cases = validate_fixture(document)
    return {
        "schema": RESULT_SCHEMA,
        "status": "offline_recorded_product_pipeline_mechanics_only",
        "fixture_sha256": fixture_sha256,
        "claimed_efficacy": False,
        "independent_review": False,
        "model_calls": 0,
        "hosted_embedding_calls": 0,
        "no_network": True,
        "not_tested": [
            "actual LLM gap-detection ability, correct NONE behavior or relative model strength",
            "independent usefulness judgments, factual correctness or Q1/Q2 outcomes",
            "semantic retrieval quality of real embeddings, and text-only/strong-model baselines",
            "H-Neurons, internal representations, and causal interventions",
            "long-term validity or efficacy under actual model-compressed context",
        ],
        "runs": [
            audit_case(case, variant)
            for case in cases
            for variant in VARIANTS
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline scripted audit of actual gap→intake→seed product path; NO MODEL"
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    result = audit(json.loads(raw), sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "runs": len(result["runs"]),
        "recorded_detector_turns": sum(len(r["turns"]) for r in result["runs"]),
        "real_model_calls": 0,
        "report": str(args.output),
    }))


if __name__ == "__main__":
    main()
