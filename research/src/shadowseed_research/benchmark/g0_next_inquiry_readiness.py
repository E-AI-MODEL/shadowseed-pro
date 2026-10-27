"""Research-only protections for the NEXT real-seed inquiry experiment.

The original six-case v1 run and its protocol are immutable evidence. This
module deliberately does not change the product Engine, existing v1 prompts,
Gate, TTL/TrTL, or any archived responses. No model call happens here.

It addresses three observed methodological faults: duplicated case content
exhausting the provider prompt ceiling, output instructions disagreeing with
the validator, and incomplete checkpoint failure diagnostics.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from shadowseed_research.benchmark.g0_multicase_real_ab import _parse_research
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    MAX_PROMPT_CHARS,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import _user_input

SCHEMA = "shadowseed-g0-next-inquiry-readiness-v1"
MAX_CHARS = MAX_PROMPT_CHARS  # Shared provider hard limit: not a new permission.
INQUIRY_INSTRUCTIONS_V2 = (
    "Onderzoek een fictieve situatie. Gebruik uitsluitend de gegeven "
    "waarnemingen; verzin geen feiten, metingen of uitkomsten. "
    "Formuleer nul, een of maximaal twee inhoudelijk verschillende, "
    "uitvoerbaar beschreven vervolgonderzoeken. Een onbewezen kandidaat "
    "is geen feit en geen opdracht. Geef exact een JSON-object met "
    'velden "status", "proposals", "unresolved_alternatives". '
    '"status" is "questions" of "none". '
    '"proposals" is een array van maximaal twee objecten met precies '
    '"question", "test" en "depends_on" (alle drie niet-lege strings). '
    '"unresolved_alternatives" is een array van maximaal drie korte '
    "strings (elk maximaal 400 tekens). Bij status none is proposals []. "
    "Een NONE-uitkomst is toegestaan. Voer geen experiment uit en "
    "beoordeel zelf geen originaliteit of wetenschappelijke meerwaarde."
)

# Only stable, source-code-defined invariant errors may be classified by text.
# Other exception messages are NEVER saved verbatim; keep their digest instead.
_CHECKPOINT_CODES = {
    "previous checkpoint is not the preceding history": "prior_history",
    "previous event ledger prefix was modified": "ledger_prefix",
    "first-birth product history no longer matches freeze": "birth_history",
    "original candidate is missing or ambiguous": "missing_seed",
    "original candidate text or origin changed": "seed_provenance",
    "first created-event has changed or been duplicated": "birth_event",
    "recorded detector-to-first-birth item changed": "item_lineage",
    "ordinary answer route received SSL influence": "answer_exposure",
    "candidate has crossed the Gate authority boundary": "gate_authority",
    "candidate is no longer authority-free": "nonzero_authority",
    "terminal expiry has no verified lifecycle Gate record": "expiry",
    "repeat candidate lacks recorded deduplication": "deduplication",
    "noncanonical or reordered live history": "history_order",
    "missing immediately preceding follow-up checkpoint": "missing_prior",
    "no complete subsequent chronological live turn": "incomplete_turn",
    "invalid Gate decision ledger": "gate_ledger",
    "invalid seed event ledger": "event_ledger",
    "previous snapshot hash mismatch": "prior_snapshot",
    "birth snapshot hash mismatch": "birth_snapshot",
}


def _sha_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_text(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ))


def check_output_contract() -> None:
    """Fail before a paid call if the requested JSON has drifted."""
    assert "maximaal twee" in INQUIRY_INSTRUCTIONS_V2
    assert "maximaal drie" in INQUIRY_INSTRUCTIONS_V2
    valid_none = '{"status":"none","proposals":[],"unresolved_alternatives":[]}'
    assert _parse_research(valid_none)["status"] == "valid_none"
    valid_one = json.dumps({
        "status": "questions",
        "proposals": [{
            "question": "Welke bron verklaart het verschil?",
            "test": "Vergelijk twee onafhankelijk gemeten condities.",
            "depends_on": "Een tweede conditie is nog niet gemeten.",
        }],
        "unresolved_alternatives": ["Er zijn nog andere verklaringen."],
    }, ensure_ascii=False)
    assert _parse_research(valid_one)["status"] == "valid_questions"
    invalid_four = json.loads(valid_one)
    invalid_four["unresolved_alternatives"] *= 4
    assert _parse_research(json.dumps(invalid_four))["reason"] == "bad_array_size"


def _common_history(case: dict, prior: list[tuple[str, str]],
                    ordinary_note: str, turn: int) -> str:
    """Deduplicate exactly repeated case/user input; preserve ALL raw answers.

    _user_input repeats case context on every turn. The inquiry sidecar can
    display it once without changing the normal Engine/host history. Each
    question and each external observation is still reproduced verbatim.
    Any unrecognized prior user format fails closed instead of being dropped.
    """
    turns = case.get("turns")
    if (not isinstance(turns, list) or not 1 <= turn < len(turns)
        or len(prior) != turn + 1):
        raise ValueError("incorrect inquiry turn or incomplete history")
    if not isinstance(case.get("context"), str):
        raise ValueError("case context missing")
    if not isinstance(ordinary_note, str) or not ordinary_note.strip():
        raise ValueError("ordinary note missing")
    parts = [
        "FICTIEVE CASUS (EENMALIG, GEEN INFORMATIE WEGGELATEN):",
        case["context"],
        "NORMALE GESPREKSHISTORIE EN VOORAF BEPAALDE WAARNEMINGEN:",
    ]
    for i, pair in enumerate(prior):
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2
            or not all(isinstance(item, str) for item in pair)):
            raise ValueError("ordinary history item malformed")
        q, a = pair
        expected = _user_input(case, turns[i])
        if q != expected:
            raise ValueError("ordinary input differs from actual canonical input")
        if not a.strip():
            raise ValueError("ordinary answer missing")
        parts.extend([
            f"VRAAG T{i}:", turns[i]["question"],
            f"EXTERNE WAARNEMING T{i}:",
            turns[i]["new_observation"] or "NONE",
            f"VOLLEDIG NORMAAL HOSTANTWOORD T{i}:", a,
        ])
    parts.extend([
        "DEZELFDE GEWONE T0-NOTITIE VOOR BEIDE CONDITIES:",
        ordinary_note,
        "ONBEWEZEN KANDIDAAT (GEEN BEWIJS, GEEN PRODUCTPROMPT):",
    ])
    return "\n".join(parts) + "\n"


def _tail(earlier: dict | None, turn: int, *, first_inquiry_turn: int = 1) -> str:
    parts = []
    if turn > first_inquiry_turn:
        parts.extend([
            "EIGEN EERDERE ONDERZOEKSVRAGEN (NIET UITGEVOERD):",
            json.dumps(earlier, sort_keys=True, ensure_ascii=False)
            if earlier is not None else "NONE",
            "Dit zijn eigen eerdere vragen, GEEN onafhankelijke observaties.",
        ])
    parts.extend([
        "VRAAG: Ontwerp vervolgonderzoek, geen antwoord op de gewone vraag.",
        "Voer de voorgestelde test niet zelf uit.",
    ])
    return "\n" + "\n".join(parts)


def prepare_inquiry_pair(
    case: dict, prior: list[tuple[str, str]], ordinary_note: str,
    real_seed: str, turn: int,
    earlier_by_arm: dict[str, dict | None],
    *, first_inquiry_turn: int = 1,
) -> dict[str, Any]:
    """Build paired research prompts with an explicit fail-closed hard cap.

    On the FIRST inquiry after genuine birth (T0, T1 or T2), the marked
    candidate slot is the ONLY difference. One turn later, arms also differ
    by their OWN earlier generated questions. No RI result is fabricated.
    The default first_inquiry_turn=1 preserves earlier T0-birth API behavior.
    """
    check_output_contract()
    if not isinstance(real_seed, str) or not real_seed.strip():
        raise ValueError("real canonical seed text required")
    if set(earlier_by_arm) != {"A", "B"}:
        raise ValueError("two segregated earlier question tracks required")
    if (type(first_inquiry_turn) is not int
        or first_inquiry_turn not in (1, 2, 3)
        or turn not in (first_inquiry_turn, first_inquiry_turn + 1)):
        raise ValueError("inquiry turn must follow the selected birth horizon")
    if turn == first_inquiry_turn and any(
        x is not None for x in earlier_by_arm.values()
    ):
        raise ValueError("first inquiry cannot inherit nonexistent prior research")
    common = _common_history(case, prior, ordinary_note, turn)
    if real_seed in common:
        raise ValueError("literal seed already in ordinary control context")
    prompts: dict[str, dict[str, Any]] = {}
    for arm, slot in (("A", "NONE"), ("B", real_seed)):
        earlier = earlier_by_arm[arm]
        if earlier is not None and not isinstance(earlier, dict):
            raise ValueError("earlier questions must be a validated object")
        suffix = _tail(earlier, turn, first_inquiry_turn=first_inquiry_turn)
        prompt = common + slot + suffix
        if arm == "A" and real_seed in prompt:
            raise ValueError("literal seed present in control's own earlier questions")
        if len(prompt) > MAX_CHARS:
            raise ValueError(
                "research prompt over predeclared provider cap: no provider call"
            )
        prompts[arm] = {
            "prompt": prompt,
            "prompt_sha256": _sha_json(prompt),
            "prompt_chars": len(prompt),
            "arm": arm, "turn": turn,
            "own_prior_questions_only": turn > first_inquiry_turn,
            "external_action_executed": False,
        }
    if turn == first_inquiry_turn:
        expected_b = prompts["A"]["prompt"].replace(
            common + "NONE" + _tail(None, turn, first_inquiry_turn=first_inquiry_turn),
            common + real_seed + _tail(None, turn, first_inquiry_turn=first_inquiry_turn),
        )
        if expected_b != prompts["B"]["prompt"]:
            raise ValueError("unmatched T1 arms")
    return {
        "schema": SCHEMA,
        "G0": "NOT_PASSED",
        "study_is_confirmatory": False,
        "normal_history_changed": False,
        "normal_history_contains_all_answers": True,
        "ordinary_context_sha256": _sha_json(common),
        "shared_instructions_sha256": _sha_json(INQUIRY_INSTRUCTIONS_V2),
        "not_external_RI_feedback": True,
        "first_inquiry_turn": first_inquiry_turn,
        "prompts": prompts,
    }


def safe_checkpoint_failure(
    exc: Exception, state: dict, *, case_id: str, turn: int,
    birth: dict | None, previous: dict | None,
) -> dict[str, Any]:
    """Save reproducible, non-text failure evidence before leaving the case.

    No arbitrary exception text, raw user history, candidate text, secrets,
    or provider envelopes. Unknown reasons stay UNKNOWN, not a guessed bug.
    """
    manager = state.get("manager", {}) if isinstance(state, dict) else {}
    manager = manager if isinstance(manager, dict) else {}
    reports = state.get("turn_reports", []) if isinstance(state, dict) else []
    events = manager.get("event_log", [])
    gates = manager.get("gate_events", [])
    message = str(exc)
    return {
        "schema": "shadowseed-g0-checkpoint-failure-record-v1",
        "case_id": case_id,
        "turn": turn,
        "exception_class": type(exc).__name__,
        "error_code": _CHECKPOINT_CODES.get(message, "unknown_checkpoint_error"),
        "error_message_sha256": _sha_text(message),
        "session_turn": state.get("turn") if isinstance(state, dict) else None,
        "history_count": len(reports) if isinstance(reports, list) else None,
        "history_prefix_sha256": _sha_json(reports[:turn])
        if isinstance(reports, list) else None,
        "event_log_count": len(events) if isinstance(events, list) else None,
        "event_log_sha256": _sha_json(events) if isinstance(events, list) else None,
        "gate_log_count": len(gates) if isinstance(gates, list) else None,
        "gate_log_sha256": _sha_json(gates) if isinstance(gates, list) else None,
        "birth_snapshot_sha256": (
            birth.get("snapshot_sha256") if isinstance(birth, dict) else None
        ),
        "prior_checkpoint_sha256": (
            previous.get("snapshot_sha256")
            if isinstance(previous, dict) else None
        ),
        "no_bypass_or_repair": True,
        "not_a_measured_zero_effect": True,
        "G0": "NOT_PASSED",
    }
