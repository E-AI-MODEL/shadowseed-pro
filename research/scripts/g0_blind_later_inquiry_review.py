#!/usr/bin/env python3
"""Independent-review handoff for Shadowseed G0, not an automatic novelty scorer.

The input is an OUT-OF-BAND research trace, never a detector prompt, new Gate,
product schema, model response, or a study result. We mask arm/candidate labels,
retain observable events and authorship, and create two *blank* independent
review sheets. All conclusions remain undecided until real reviewers submit
evidence-based decisions. A demo from PR #232 is investigator-authored and
CANNOT establish Q1/Q2, independent validity or G0 approval.

The mapping/salt file is OWNER-ONLY, never publish it with the blind packet.
Blind IDs conceal labels, not the informational differences in adaptive worlds.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
from pathlib import Path
from datetime import datetime
from typing import Any

SOURCE_SCHEMA = "g0-blind-later-inquiry-source-v0"
PACK_SCHEMA = "g0-blind-later-inquiry-pack-v0"
REVIEW_SCHEMA = "g0-independent-semantic-review-v0"
RECONCILE_SCHEMA = "g0-reviewed-traces-unblinded-v0"
MAX_EPISODES = 60
MAX_TURNS = 16
TEXT_LIMIT = 12000
REVIEW_DISTINCTNESS = ("materially_different", "paraphrase_or_repetition", "uncertain")
REVIEW_TESTABILITY = ("independently_testable", "not_testable_here", "uncertain")
REVIEW_CONSEQUENCE = ("verified_later_consequence", "not_demonstrated", "uncertain")
ALLOWED_PROVENANCE = ("investigator_scripted_calibration", "recorded_model_unverified")
ALLOWED_REGIME = ("MECHANICS_CALIBRATION", "RF", "RI")
PUBLIC_TURN_FIELDS = (
    "turn_id",
    "question",
    "question_origin",
    "host_answer",
    "host_answer_origin",
    "observed_world_before",
    "investigator_action",
    "world_action_origin",
    "world_action_status",
    "observed_world_after",
)
FORBIDDEN_MASKED_KEYS = (
    "private_arm",
    "private_case_id",
    "private_candidate_record",
    "detector_output_raw",
    "true_seed_born_this_turn",
    "weight",
    "trace",
    "seed_id",
    "model_internal_reasoning",
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _tag(secret: bytes, kind: str, value: str) -> str:
    return hmac.new(secret, f"{kind}:{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:20]


def _is_short_text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= TEXT_LIMIT


def _check_source(source: Any) -> list[dict[str, Any]]:
    if not isinstance(source, dict) or source.get("schema") != SOURCE_SCHEMA:
        raise ValueError("not a supported G0 reviewer input")
    provenance = source.get("provenance_class")
    regime = source.get("feedback_regime")
    if provenance not in ALLOWED_PROVENANCE or regime not in ALLOWED_REGIME:
        raise ValueError("unknown source provenance/feedback regime")
    if provenance == "investigator_scripted_calibration" and regime != "MECHANICS_CALIBRATION":
        raise ValueError("scripted calibration must not masquerade as RF/RI")
    if provenance == "recorded_model_unverified" and regime == "MECHANICS_CALIBRATION":
        raise ValueError("model records require a prospectively declared RF or RI regime")
    cases = source.get("episodes")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_EPISODES:
        raise ValueError("missing or unbounded source episodes")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("episode is not an object")
        case_id, arm, group = (
            case.get("private_case_id"),
            case.get("private_arm"),
            case.get("private_group"),
        )
        if not all(_is_short_text(v) for v in (case_id, arm, group)):
            raise ValueError("episode lacks private identity needed for later unblinding")
        if case_id in ids:
            raise ValueError("duplicate episode identity")
        ids.add(case_id)
        turns = case.get("turns")
        if not isinstance(turns, list) or not 2 <= len(turns) <= MAX_TURNS:
            raise ValueError("independent inquiry requires bounded multi-turn evidence")
        for index, turn in enumerate(turns):
            if not isinstance(turn, dict) or turn.get("turn_id") != f"T{index}":
                raise ValueError("nonconsecutive or missing turn identifier")
            for key in ("question", "question_origin", "host_answer", "host_answer_origin",
                        "world_action_origin", "world_action_status"):
                if not _is_short_text(turn.get(key)):
                    raise ValueError("missing or unbounded observable field: " + key)
            if not isinstance(turn.get("observed_world_before"), dict) or not isinstance(
                turn.get("observed_world_after"), dict
            ):
                raise ValueError("missing independent world observations")
            if turn.get("investigator_action") is not None and not isinstance(
                turn.get("investigator_action"), dict
            ):
                raise ValueError("tool action is not an object")
            for k in PUBLIC_TURN_FIELDS:
                if k not in turn:
                    raise ValueError("missing public observation: " + k)
        if provenance == "recorded_model_unverified":
            if not _is_short_text(case.get("private_raw_trace_ref")):
                raise ValueError("unverified model trace requires a private raw evidence reference")
            if not any(t["question_origin"] == "MODEL_GENERATED_RECORDED_UNVERIFIED" for t in turns):
                raise ValueError("model-origin input contains no recorded model-authored inquiry")
    return cases


def _safe_write_json(path: Path, value: dict[str, Any], private: bool = False) -> None:
    """Never overwrite an existing pack or owner map; owner creation uses mode 0600."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = "x"
    if private:
        import os
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return
    with path.open(flags, encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def create_pack(source: dict[str, Any], secret: bytes) -> tuple[dict, dict, dict]:
    episodes = _check_source(source)
    if len(secret) < 24:
        raise ValueError("unblinding secret must have at least 192 bits")
    provenance, regime = source["provenance_class"], source["feedback_regime"]
    package_id = "P" + _tag(secret, "package", fingerprint(source))
    cards = []
    owner_cases = []
    for case in episodes:
        case_id = case["private_case_id"]
        blind = "B" + _tag(secret, "episode", case_id)
        blinded_group = "G" + _tag(secret, "matched", case["private_group"])
        evidence = [
            {k: t[k] for k in PUBLIC_TURN_FIELDS}
            for t in case["turns"]
        ]
        cards.append({
            "blind_id": blind,
            "matched_group": blinded_group,
            "evidence_turns": evidence,
            "review_scope": (
                "RESEARCHER_SCRIPTED_CALIBRATION_NOT_ELIGIBLE_FOR_Q1_Q2"
                if provenance == "investigator_scripted_calibration"
                else "MODEL_OUTPUT_PROVENANCE_NOT_INDEPENDENTLY_VERIFIED"
            ),
            "review_instruction": (
                "Judge whether the final inquiry differs materially from earlier inquiries, "
                "is independently testable, and has an independently observed later consequence; "
                "cite turn IDs and competing explanations. Do not infer seed effects from state changes."
            ),
        })
        owner_cases.append({
            "blind_id": blind,
            "private_case_id": case_id,
            "private_arm": case["private_arm"],
            "private_group": case["private_group"],
            "private_candidate_record": case.get("private_candidate_record"),
            "private_raw_trace_ref": case.get("private_raw_trace_ref"),
            "private_independent_future_consequence_verified": case.get("private_independent_future_consequence_verified", False),
            "declared_provenance": provenance,
        })
    cards.sort(key=lambda x: _tag(secret, "display", x["blind_id"]))
    if len({c["blind_id"] for c in cards}) != len(cards):
        raise AssertionError("blind IDs not unique")
    packet = {
        "schema": PACK_SCHEMA,
        "packet_id": package_id,
        "source_provenance_class": provenance,
        "feedback_regime": regime,
        "G0_status": "NOT_PASSED",
        "independent_semantic_review_completed": False,
        "Q1_or_Q2_result_established": False,
        "reviewer_must_not_access_owner_map": True,
        "blinding_limits": (
            "Masking hides treatment and candidate identity, but may not hide "
            "arm-specific observation differences in adaptive trajectories. "
            "Public calibration sources are not sealed."
        ),
        "episodes": cards,
    }
    packet["content_sha256"] = fingerprint(packet)
    owner = {
        "schema": "g0-private-unblinding-map-v0",
        "packet_id": package_id,
        "packet_sha256": packet["content_sha256"],
        "source_sha256": fingerprint(source),
        "owner_only_never_publish": True,
        "mapping": owner_cases,
        "G0_status": "NOT_PASSED",
    }
    review = {
        "schema": REVIEW_SCHEMA,
        "packet_id": package_id,
        "packet_sha256": packet["content_sha256"],
        "reviewer_id": None,
        "human_independence_declared": None,
        "reviewer_role": "independent_semantic_reviewer",
        "reviewer_timestamp_iso8601": None,
        "reviews": [{
            "blind_id": c["blind_id"],
            "distinct_from_prior_questions": None,
            "testable_under_independent_rules": None,
            "later_consequence_observed": None,
            "evidence_turn_ids": [],
            "reasoned_explanation": None,
            "stronger_ordinary_model_or_human_explanation": None,
        } for c in cards],
        "automated_semantic_verdict": None,
        "G0_approval": False,
    }
    public_blob = canonical(packet)
    for field in FORBIDDEN_MASKED_KEYS:
        if f'"{field}":' in public_blob:
            raise AssertionError("review packet leaked a private treatment/candidate field")
    # An arm named "A" or a case named "x" will naturally occur in ordinary
    # research text. Never reject or rewrite an inquiry by searching for private
    # label substrings in prose: that silently filters new relationships.
    # Blindness is maintained by an explicit field whitelist, cryptic IDs,
    # reviewer isolation and a separate private owner map. An inquiry can still
    # itself disclose its origin; real reviewer masking must be independently audited.
    return packet, owner, review



def source_from_verified_bridge(bridge: dict[str, Any], source_bytes: bytes) -> dict:
    """Convert a *real* prior mechanics trace to a PUBLIC calibration example.

    Strictly investigator-scripted, zero model calls and zero influence.
    No hypothetical model behavior or downstream-seed effects are inferred.
    """
    if not isinstance(bridge, dict) or bridge.get("schema") != (
        "g0-real-shadowchat-discoveryworld-bridge-audit-v0"
    ):
        raise ValueError("wrong bridge evidence source")
    if (
        bridge.get("status") != "model_free_product_pipeline_plus_real_world_mechanics_only"
        or bridge.get("source") != "INVESTIGATOR_SCRIPTED_NO_LLM"
        or bridge.get("model_calls") != 0
        or bridge.get("embedding_hosted_calls") != 0
        or bridge.get("Q1_measured") is not False
        or bridge.get("Q2_measured") is not False
        or bridge.get("g0_passed") is not False
        or bridge.get("upstream_sha") != "fd591323920be0d3786ef350955de1945aa571e5"
    ):
        raise ValueError("bridge source provenance, claims or version unverified")
    arms = bridge.get("arms")
    if not isinstance(arms, dict) or set(arms) != {"scripted_seed", "explicit_none"}:
        raise ValueError("missing pinned counterfactual arms")
    if bridge.get("same_world_observations_and_investigator_actions_in_both_arms") is not True:
        raise ValueError("comparison does not have identical world actions and observations")

    episodes = []
    identical_worlds = []
    for arm in sorted(arms):
        run = arms[arm]
        if (
            run.get("seed_authority_uses") != 0
            or run.get("Gate_events") != 0
            or run.get("hosted_model_calls") != 0
            or run.get("has_real_persistent_ShadowChatSession") is not True
        ):
            raise ValueError("simulator bridge gained authority, model calls or lost canonical state")
        turns = run.get("turns")
        if not isinstance(turns, list) or len(turns) != 4:
            raise ValueError("incorrect bridge turn count")
        public = []
        for i, t in enumerate(turns):
            if t.get("turn_id") != f"T{i}":
                raise ValueError("incorrect source chronology")
            if (
                t.get("question_origin") != "INVESTIGATOR_SCRIPTED_NO_MODEL"
                or t.get("host_answer_origin") != "INVESTIGATOR_DEFINED_VISIBLE_STATE_SERIALIZER_NO_MODEL"
                or t.get("world_action_origin") != "INVESTIGATOR_SCRIPTED_INDEPENDENT_OF_SEEDS"
                or t.get("seed_authority_uses") != 0
                or t.get("Gate_events") != 0
                or t.get("semantic_novelty") != "NOT_ASSESSED"
                or t.get("semantic_seed_growth") != "NOT_ASSESSED"
                or t.get("new_later_investigability") != "NOT_ASSESSED"
            ):
                raise ValueError("bridge source contains stronger or untraceable claims")
            public.append({k: t[k] for k in PUBLIC_TURN_FIELDS})
        identical_worlds.append([
            (
                t["question"], t["host_answer"], t["investigator_action"],
                t["observed_world_before"], t["world_action_status"],
                t["observed_world_after"],
            ) for t in public
        ])
        episodes.append({
            "private_case_id": "recorded-pr232-" + arm,
            "private_arm": arm,
            "private_group": "pr232-fourturn-mechanics-control",
            "turns": public,
            "private_raw_trace_ref": (
                "GitHub Actions 40169010028; source SHA-256 "
                + hashlib.sha256(source_bytes).hexdigest()
            ),
            "private_candidate_record": [{
                "turn_id": t["turn_id"],
                "raw_detector_text": t["detector_output_raw"],
                "born_scripted": t["true_seed_born_this_turn"],
                "redetected_scripted": t["existing_seed_redetected_this_turn"],
            } for t in turns],
            "private_independent_future_consequence_verified": False,
        })
    if identical_worlds[0] != identical_worlds[1]:
        raise ValueError("claimed matched independent worlds are not actually identical")
    if not arms["scripted_seed"]["final_seed_state"] or arms["explicit_none"]["final_seed_state"]:
        raise ValueError("scripted weightless versus NONE state contradicts frozen record")

    source = {
        "schema": SOURCE_SCHEMA,
        "provenance_class": "investigator_scripted_calibration",
        "feedback_regime": "MECHANICS_CALIBRATION",
        "source_note": (
            "Real PR232 simulator output, but ALL later questions, host answers, "
            "detector text and actions are investigator authored. This is NOT "
            "a blinded holdout or evidence of model Q1/Q2 ability."
        ),
        "source_record_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "episodes": episodes,
    }
    _check_source(source)
    return source


def validate_completed_review(packet: dict, submission: dict) -> None:
    if packet.get("schema") != PACK_SCHEMA or submission.get("schema") != REVIEW_SCHEMA:
        raise ValueError("incorrect review schemas")
    if (packet.get("packet_id"), packet.get("content_sha256")) != (
        submission.get("packet_id"), submission.get("packet_sha256")
    ):
        raise ValueError("review does not correspond to original blind packet")
    if fingerprint({k: v for k, v in packet.items() if k != "content_sha256"}) != packet["content_sha256"]:
        raise ValueError("the original blind packet was changed")
    reviewer = submission.get("reviewer_id")
    if not _is_short_text(reviewer) or reviewer.strip().lower() in (
        "ai", "llm", "model", "auto", "unknown", "researcher", "test",
    ):
        raise ValueError("independent reviewer identity must be explicitly attributed")
    if submission.get("human_independence_declared") is not True:
        raise ValueError("human independence declaration required; not mechanically verified")
    if submission.get("reviewer_role") != "independent_semantic_reviewer":
        raise ValueError("reviewer role mismatch")
    timestamp = submission.get("reviewer_timestamp_iso8601")
    if not _is_short_text(timestamp):
        raise ValueError("dated human assessment required")
    try:
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("dated assessment must have a valid ISO-8601 timestamp") from exc
    if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
        raise ValueError("dated assessment must have a timezone")
    if submission.get("automated_semantic_verdict") is not None or submission.get("G0_approval") is not False:
        raise ValueError("automatic novelty judgment or G0 pass is forbidden")
    rows = submission.get("reviews")
    blind_ids = [c["blind_id"] for c in packet["episodes"]]
    if not isinstance(rows, list) or len(rows) != len(blind_ids):
        raise ValueError("review rows missing")
    if len({row.get("blind_id") for row in rows}) != len(rows) or set(
        row.get("blind_id") for row in rows
    ) != set(blind_ids):
        raise ValueError("review IDs differ from blinded cards")
    by_id = {c["blind_id"]: c for c in packet["episodes"]}
    for row in rows:
        if row.get("distinct_from_prior_questions") not in REVIEW_DISTINCTNESS:
            raise ValueError("a reviewer must judge or explicitly abstain from distinctness")
        if row.get("testable_under_independent_rules") not in REVIEW_TESTABILITY:
            raise ValueError("a reviewer must judge or explicitly abstain from testability")
        if row.get("later_consequence_observed") not in REVIEW_CONSEQUENCE:
            raise ValueError("a reviewer must judge or explicitly abstain from later consequence")
        for field in ("reasoned_explanation", "stronger_ordinary_model_or_human_explanation"):
            if not _is_short_text(row.get(field)):
                raise ValueError("human rationale and alternative explanation required")
        refs = row.get("evidence_turn_ids")
        available = {t["turn_id"] for t in by_id[row["blind_id"]]["evidence_turns"]}
        if not isinstance(refs, list) or not refs or set(refs) - available:
            raise ValueError("reviewer must point to evidence in the same blind card")
        if by_id[row["blind_id"]]["review_scope"].startswith("RESEARCHER_SCRIPTED"):
            if row["later_consequence_observed"] == "verified_later_consequence":
                raise ValueError("a public scripted-only demo cannot establish later consequence")


def reconcile(packet: dict, owner: dict, r1: dict, r2: dict) -> dict:
    validate_completed_review(packet, r1)
    validate_completed_review(packet, r2)
    if r1["reviewer_id"].strip().casefold() == r2["reviewer_id"].strip().casefold():
        raise ValueError("two distinct human reviewers required")
    if owner.get("packet_id") != packet["packet_id"] or owner.get("packet_sha256") != packet["content_sha256"] or owner.get("owner_only_never_publish") is not True:
        raise ValueError("private owner mapping does not correspond to the blind packet")
    mapping = {r["blind_id"]: r for r in owner["mapping"]}
    if set(mapping) != {c["blind_id"] for c in packet["episodes"]}:
        raise ValueError("private mapping incomplete or not the same review sample")
    by_review = [
        {r["blind_id"]: r for r in x["reviews"]}
        for x in (r1, r2)
    ]
    comparisons = []
    for card in packet["episodes"]:
        key = card["blind_id"]
        verdicts = [
            {
                "reviewer": x["reviewer_id"],
                "distinctness": m[key]["distinct_from_prior_questions"],
                "testability": m[key]["testable_under_independent_rules"],
                "later_consequence": m[key]["later_consequence_observed"],
                "evidence_turn_ids": m[key]["evidence_turn_ids"],
                "rationale": m[key]["reasoned_explanation"],
                "alternative": m[key]["stronger_ordinary_model_or_human_explanation"],
            }
            for x, m in zip((r1, r2), by_review)
        ]
        comparisons.append({
            "blind_id": key,
            "private_arm": mapping[key]["private_arm"],
            "private_case_id": mapping[key]["private_case_id"],
            "recorded_human_verdicts": verdicts,
            "human_disagreement_unresolved": any(
                verdicts[0][x] != verdicts[1][x]
                for x in ("distinctness", "testability", "later_consequence")
            ),
            "independent_reviewer_identity_verified": False,
            "causal_seed_contribution_established": False,
        })
    return {
        "schema": RECONCILE_SCHEMA,
        "packet_id": packet["packet_id"],
        "packet_sha256": packet["content_sha256"],
        "status": "STRUCTURAL_RECONCILIATION_NOT_G0_APPROVAL",
        "human_identity_and_independence_still_require_external_verification": True,
        "reviewer_count": 2,
        "G0_passed": False,
        "Q1_measured": False,
        "Q2_causality_established": False,
        "comparisons": comparisons,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    build = sub.add_parser("prepare", help="Make blind packet, blank sheet and PRIVATE owner map")
    source_group = build.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input", type=Path, help="Private future research trace source schema")
    source_group.add_argument("--bridge-json", type=Path, help="Existing verified PR232 mechanics run; calibration only")
    build.add_argument("--packet", type=Path, required=True)
    build.add_argument("--blank-review", type=Path, required=True)
    build.add_argument("--owner-map", type=Path, required=True)
    combine = sub.add_parser("reconcile", help="Unblind only after two completed review forms")
    for name in ("packet", "owner-map", "review-one", "review-two", "output"):
        combine.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    if args.command == "prepare":
        input_path = args.input if args.input is not None else args.bridge_json
        paths = [input_path, args.packet, args.blank_review, args.owner_map]
        if len({p.resolve() for p in paths}) != len(paths):
            ap.error("private map, source and public outputs must be different files")
        raw = input_path.read_bytes()
        input_data = json.loads(raw)
        source = (
            source_from_verified_bridge(input_data, raw)
            if args.bridge_json is not None else input_data
        )
        public, private, blank = create_pack(source, secrets.token_bytes(32))
        _safe_write_json(args.owner_map, private, private=True)
        _safe_write_json(args.packet, public)
        _safe_write_json(args.blank_review, blank)
        print(
            f"Created {len(public['episodes'])} arm-blinded research cards; "
            "all judgments PENDING; private map stored separately; G0 NOT PASSED."
        )
    else:
        paths = [args.packet, args.owner_map, args.review_one, args.review_two, args.output]
        if len({p.resolve() for p in paths}) != len(paths):
            ap.error("reviews, private mapping and reconciliation output must be separate")
        docs = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in paths[:4]
        ]
        result = reconcile(*docs)
        _safe_write_json(args.output, result, private=True)
        print("Review forms mechanically reconciled; independence NOT verified; G0 NOT PASSED.")


if __name__ == "__main__":
    main()
