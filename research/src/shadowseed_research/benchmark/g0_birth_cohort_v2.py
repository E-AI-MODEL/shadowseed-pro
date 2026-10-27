"""Prospective late-birth cohort selection. Offline research only; no API calls.

Never replace an actual canonical birth by a synthetic seed. Preserve all
originally observed opportunities, including rejected or too-late births.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)

@dataclass(frozen=True)
class BirthDecision:
    status: str
    birth_turn: int | None
    first_inquiry_turn: int | None
    second_inquiry_turn: int | None
    seed_id: str | None
    checkpoint: dict[str, Any] | None


def select_first_eligible_birth(engine, observed: dict, *,
                                turn: int, total_turns: int,
                                already_selected: bool = False) -> BirthDecision:
    """Only first eligible real birth; require two future observed turns.

    'Too late' and 'no birth' must remain distinct in the full case census.
    The research sidecar must not call the detector, modify normal prompts,
    or inject an unapproved candidate into the ordinary product answer.
    """
    if type(turn) is not int or type(total_turns) is not int or not (
        0 <= turn < total_turns
    ):
        raise ValueError("invalid prospective chronology")
    if not isinstance(observed, dict) or observed.get("turn") != turn:
        raise ValueError("wrong recorded product turn")
    if already_selected:
        return BirthDecision("previous_selection_retained", None, None,
                             None, None, None)
    state = engine.export_state()
    candidates = [
        sid for sid in observed.get("seeds_born_weightless", [])
        if state.get("born_turn", {}).get(sid) == turn
    ]
    if not candidates:
        return BirthDecision("no_canonical_birth_this_turn", None, None,
                             None, None, None)
    if turn + 2 >= total_turns:
        return BirthDecision("real_birth_too_late_for_two_followups", turn,
                             None, None, None, None)
    # First actual accepted item only, without investigator selection.
    sid = candidates[0]
    checkpoint = freeze_canonical_weightless_birth(engine, observed, sid)
    return BirthDecision("selected_real_weightless_birth", turn, turn + 1,
                         turn + 2, sid, checkpoint)


def cohort_census(decisions: list[BirthDecision], total_cases: int) -> dict:
    """Count full predeclared case denominator, never effect-size inflate."""
    if type(total_cases) is not int or total_cases < 1:
        raise ValueError("invalid study census")
    categories = {
        "selected_real_weightless_birth": 0,
        "real_birth_too_late_for_two_followups": 0,
        "no_birth_observed_by_end": 0,
        "failed_or_incomplete": 0,
    }
    if len(decisions) != total_cases:
        raise ValueError("case census is incomplete")
    for decision in decisions:
        status = decision.status
        if status not in categories:
            raise ValueError("not a terminal case outcome")
        categories[status] += 1
    return {
        "cases_attempted": total_cases,
        "outcomes": categories,
        "G0": "NOT_PASSED",
        "q2_proven": False,
        "late_birth_not_reclassified_as_T0": True,
    }
