"""V2 research-only prospective methods: preserve possibilities, do not promote them.

New study helper only. Does NOT revise the frozen six-case v1 execution,
interpret its invalid records retroactively as valid, change Shadowseed's
canonical atomicity/Gate/TTL/TrTL, or grant G0 approval.

A causal study needs an actual NEW multi-turn cohort plus human and,
eventually, independent RI validation.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

from shadowseed_research.benchmark.g0_multicase_real_ab import research_prompt
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    MAX_PROMPT_CHARS,
)

SCHEMA = "shadowseed-multicase-method-v2"
ANSWER_CAP_TIERS = (1800, 1200, 800, 400)
MAX_ALTERNATIVES_V2 = 12
MAX_PROPOSALS = 2
ALLOWED_ARMS = ("A", "B")
FAIL_CODES = {
    "invalid or oversized model prompt": "prompt_over_budget",
    "previous checkpoint is not the preceding history": "history_integrity",
    "previous event ledger prefix was modified": "eventlog_integrity",
    "first-birth product history no longer matches freeze": "birth_integrity",
    "candidate has crossed the Gate authority boundary": "authority_boundary",
    "ordinary answer route received SSL influence": "ordinary_route_exposure",
    "candidate is no longer authority-free": "authority_boundary",
    "original candidate is missing or ambiguous": "seed_identity",
    "recorded detector-to-first-birth item changed": "detector_lineage",
}


def parse_inquiry_v2(raw: str) -> dict[str, Any]:
    """Validate new open alternatives schema; never edit/repair model output.

    The old v1 rule of at most 3 alternatives still applies ONLY to its
    original immutable experiment. This is a prospective versioned protocol.
    """
    try:
        obj = json.loads(raw)
    except (TypeError, ValueError):
        return {"status": "invalid", "reason": "not_json",
                "proposals": [], "unresolved_alternatives": []}
    if not isinstance(obj, dict) or set(obj) != {
        "status", "proposals", "unresolved_alternatives",
    }:
        return {"status": "invalid", "reason": "bad_object",
                "proposals": [], "unresolved_alternatives": []}
    prop, alt = obj["proposals"], obj["unresolved_alternatives"]
    if not isinstance(prop, list) or len(prop) > MAX_PROPOSALS:
        return {"status": "invalid", "reason": "invalid_proposals_size",
                "proposals": [], "unresolved_alternatives": []}
    if not isinstance(alt, list) or len(alt) > MAX_ALTERNATIVES_V2:
        return {"status": "invalid", "reason": "invalid_alternatives_size",
                "proposals": [], "unresolved_alternatives": []}
    if not all(
        isinstance(v, str) and 3 <= len(v.strip()) <= 600
        for v in alt
    ):
        return {"status": "invalid", "reason": "invalid_alternative_text",
                "proposals": [], "unresolved_alternatives": []}
    if not all(
        isinstance(v, dict)
        and set(v) == {"question", "test", "depends_on"}
        and all(isinstance(v[k], str) and 5 <= len(v[k].strip()) <= 900
                for k in ("question", "test", "depends_on"))
        for v in prop
    ):
        return {"status": "invalid", "reason": "invalid_question_content",
                "proposals": [], "unresolved_alternatives": []}
    if obj["status"] not in {"questions", "none"} or (
        (obj["status"] == "none") != (len(prop) == 0)
    ):
        return {"status": "invalid", "reason": "status_mismatch",
                "proposals": [], "unresolved_alternatives": []}
    return {
        "status": "valid_none" if not prop else "valid_questions",
        "proposals": prop,
        "unresolved_alternatives": alt,
    }


V2_RESEARCH_INSTRUCTIONS = (
    "Onderzoek mogelijke maar onbewezen relaties in een fictieve casus. "
    "Het gaat niet om meer tekst, maar om wat na een volgende waarneming "
    "anders toetsbaar zou kunnen worden. Dwing geen uitkomst af en beschouw "
    "de kandidaat nooit als bewijs. Geef maximaal twee verschillende "
    "mogelijke onderzoeksvragen, ieder met een onafhankelijk onderscheidende "
    "test en een expliciete voorwaarde voor later onderzoek. "
    "Er mag ook geen bruikbare vraag bestaan; retourneer dan none. "
    "Geef uitsluitend een JSON object met exact de velden "
    'status ("questions" of "none"), proposals (maximaal 2 objecten met '
    'question, test, depends_on) en unresolved_alternatives (maximaal 12 '
    "onbewezen alternatieven). Elk onderdeel is alleen een voorlopige "
    "modeluitspraak, geen gevalideerde ontdekking."
)


def bounded_answer(answer: str, cap: int) -> tuple[str, dict]:
    """Explicit, identical *research-view* shortening; canonical host unedited."""
    if not isinstance(answer, str) or not answer:
        raise ValueError("empty or invalid ordinary host answer")
    if cap not in ANSWER_CAP_TIERS:
        raise ValueError("unexpected frozen research context cap")
    orig_sha = sha256(answer.encode("utf-8")).hexdigest()
    if len(answer) <= cap:
        return answer, {
            "original_chars": len(answer),
            "visible_chars": len(answer),
            "clipped": False,
            "original_sha256": orig_sha,
            "strategy": "unchanged",
        }
    # Do not selectively remove material based on experimental outcomes.
    marker = f"\n[RESEARCH-CONTEXT CLIPPED; original_sha256={orig_sha}]\n"
    first = (cap - len(marker)) * 3 // 4
    last = (cap - len(marker)) - first
    if first < 250 or last < 75:
        raise ValueError("insufficient transparent research context cap")
    visible = answer[:first] + marker + answer[-last:]
    if len(visible) != cap:
        raise AssertionError("bounded answer length contract broken")
    return visible, {
        "original_chars": len(answer),
        "visible_chars": len(visible),
        "clipped": True,
        "original_sha256": orig_sha,
        "strategy": "fixed_prefix_75pct_suffix_25pct_plus_hash_marker",
    }


def matched_prompts(
    case: dict,
    complete_visible_history: list[tuple[str, str]],
    ordinary_note: str,
    first_real_seed: str,
    turn: int,
    own_earlier: Mapping[str, dict | None],
) -> dict[str, Any]:
    """Choose one shared context tier before A/B calls; never clip own ideas.

    Both arms use the same subset of canonical ordinary host answer text.
    T2 still includes each arm's *own* complete parsed earlier questions,
    never another arm's private output or a fabricated external result.
    """
    if not isinstance(first_real_seed, str) or not first_real_seed.strip():
        raise ValueError("no actual first-birth candidate to compare")
    if not isinstance(ordinary_note, str) or not ordinary_note.strip():
        raise ValueError("ordinary T0 notes not shared")
    if set(own_earlier) != set(ALLOWED_ARMS):
        raise ValueError("missing an A/B own-prior record")
    if turn not in (1, 2) or len(complete_visible_history) != turn + 1:
        raise ValueError("invalid chronological input")
    if first_real_seed in ordinary_note:
        # This cannot establish what the LLM 'saw' in its internal states.
        # It only prevents claiming a clean literal A/B text exposure.
        raise ValueError("literal first seed already present in shared ordinary notes")
    versions = []
    for cap in ANSWER_CAP_TIERS:
        clipped, provenance = [], []
        for q, a in complete_visible_history:
            c, audit = bounded_answer(a, cap)
            clipped.append((q, c))
            provenance.append(audit)
        arms = {}
        for arm in ALLOWED_ARMS:
            raw = research_prompt(
                case, clipped, ordinary_note,
                first_real_seed if arm == "B" else None,
                turn, own_earlier[arm],
            )
            arms[arm] = raw
        versions.append((cap, provenance, arms))
        if all(0 < len(v) <= MAX_PROMPT_CHARS for v in arms.values()):
            return {
                "schema": SCHEMA,
                "turn": turn, "shared_answer_cap_chars": cap,
                "ordinary_host_canonical_answers_unmodified": True,
                "research_host_answer_provenance": provenance,
                "only_A_has_none_seed_field": True,
                "A_literal_seed_clean": first_real_seed not in arms["A"],
                "B_literal_seed_exposed": first_real_seed in arms["B"],
                "prompts": arms,
                "prompt_chars": {a: len(v) for a, v in arms.items()},
                "prompt_sha256": {
                    a: sha256(v.encode("utf-8")).hexdigest()
                    for a, v in arms.items()
                },
                "own_earlier_T1_only": turn == 2,
                "no_external_action_executed": True,
            }
    lengths = {a: len(v) for a, v in versions[-1][2].items()}
    # No dynamic answer rewrites, no hidden fallback, no API requests.
    raise ValueError(
        "matched research prompts still over declared cap at minimum "
        f"ordinary-history tier; prompt lengths {lengths}"
    )


def safe_failure_code(exc: Exception, *, phase: str) -> dict[str, Any]:
    """Persist closed, non-secret failure class and the last known stage."""
    if not isinstance(phase, str) or not phase or len(phase) > 100:
        raise ValueError("phase must be a short predeclared stage")
    msg = str(exc)
    if isinstance(exc, ValueError):
        if msg.startswith("matched research prompts still over"):
            code = "paired_prompt_over_budget"
        else:
            code = FAIL_CODES.get(msg, "other_validation_error")
    elif isinstance(exc, RuntimeError):
        if msg.startswith("provider HTTP "):
            code = "provider_http_error"
        elif "model returned no complete visible text" in msg:
            code = "provider_incomplete_model_text"
        elif "hard " in msg and "cap" in msg:
            code = "provider_budget_limit"
        else:
            code = "other_runtime_failure"
    else:
        code = "other_exception"
    return {
        "error_type": type(exc).__name__,
        "error_code": code,
        "last_stage": phase,
        "retry_automatically": False,
        "not_a_none_or_null_result": True,
        "does_not_approve_G0": True,
    }


def observe_rejection_counts(report: dict) -> dict[str, Any]:
    """Read current canonical rejection signals, without admitting them."""
    if not isinstance(report, dict):
        raise ValueError("real product turn report required")
    d = report.get("intake_diagnostics")
    if not isinstance(d, dict):
        raise ValueError("canonical intake diagnostics missing")
    accepted = d.get("accepted", [])
    rejected = d.get("rejected", [])
    if not isinstance(accepted, list) or not isinstance(rejected, list):
        raise ValueError("missing product accepted/rejected ledger")
    not_atomic = [
        item for item in rejected
        if isinstance(item, dict) and item.get("reason") == "not_atomic"
    ]
    return {
        "accepted_candidate_records": len(accepted),
        "rejected_candidate_records": len(rejected),
        "not_atomic_rejections": len(not_atomic),
        "not_atomic_text_sha256": [
            sha256(item["text"].encode("utf-8")).hexdigest()
            for item in not_atomic
            if isinstance(item.get("text"), str)
        ],
        "no_new_seed_created_by_observation": True,
        "not_a_truth_or_novelty_assessment": True,
    }
