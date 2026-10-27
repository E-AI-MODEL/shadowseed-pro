"""Prospective T0 versus late (T1/T2) birth-cohort selection.

Research sidecar ONLY. Observe genuine chronological live ShadowseedEngine
turns; never invent or promote a candidate and never revisit a missed birth.
Records ALL actual new births, including ineligible and too-late births.
Each selected seed must be observed on exactly two subsequent turns.
This is provenance/instrumentation, NOT evidence of Q1/Q2 efficacy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shadowseed import ShadowseedEngine
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    freeze_weightless_followup,
)
from shadowseed_research.benchmark.g0_next_inquiry_readiness import (
    safe_checkpoint_failure,
)

VALID_WINDOWS = {"T0_ONLY", "T1_T2_ONLY"}
LAST_ELIGIBLE_BIRTH = 2
TURN_COUNT = 5


@dataclass
class ProspectiveBirthCohort:
    case_id: str
    selection_window: str
    first_birth: dict[str, Any] | None = None
    seed_text: str | None = None
    followups: list[dict[str, Any]] = field(default_factory=list)
    all_births: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_failure: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.case_id or self.selection_window not in VALID_WINDOWS:
            raise ValueError("prospective cohort/window must be declared")

    @property
    def birth_turn(self) -> int | None:
        return self.first_birth["session_turn"] if self.first_birth else None

    @property
    def selected_id(self) -> str | None:
        return self.first_birth["seed_id"] if self.first_birth else None

    def observe(self, engine: ShadowseedEngine, report: dict, turn: int) -> dict:
        """Call exactly once, immediately after each actual observe_turn.

        The caller must retain the same Engine and chronological report. We
        do not tolerate skipped turns, fake seeds, or a second chosen seed.
        """
        if turn != len(self.all_births) or not 0 <= turn < TURN_COUNT:
            raise ValueError("cohort turn skipped or out of order")
        state = engine.export_state()
        if (
            state.get("turn") != turn + 1
            or not isinstance(state.get("turn_reports"), list)
            or state["turn_reports"][-1] != report
        ):
            raise ValueError("not the just-completed canonical Engine turn")
        actual_new = [
            sid for sid in report.get("seeds_born_weightless", [])
            if state.get("born_turn", {}).get(sid) == turn
        ]
        if len(actual_new) != len(set(actual_new)):
            raise ValueError("duplicate first-birth identity")
        eligible_turn = (
            (turn == 0 and self.selection_window == "T0_ONLY")
            or (turn in (1, 2) and self.selection_window == "T1_T2_ONLY")
        )
        to_select = (
            eligible_turn and not self.first_birth and bool(actual_new)
        )
        chosen = actual_new[0] if to_select else None
        row = {
            "turn": turn, "all_canonical_new_birth_ids": list(actual_new),
            "eligible_window_at_this_turn": eligible_turn,
            "first_chosen_seed_id": chosen,
            "later_births_not_retroactively_selected": turn > LAST_ELIGIBLE_BIRTH,
        }
        self.all_births.append(row)
        if to_select:
            birth = freeze_canonical_weightless_birth(engine, report, chosen)
            matching = [
                x for x in state["manager"]["seeds"] if x.get("id") == chosen
            ]
            if len(matching) != 1:
                raise ValueError("selected seed provenance ambiguous")
            seed = matching[0]
            if (
                seed.get("weight") != 0
                or seed.get("evidence_count") != 0
                or seed.get("authority_version") != 0
            ):
                raise ValueError("selected seed gained unearned authority")
            self.first_birth = birth
            self.seed_text = seed["text"]
            row["birth_snapshot_sha256"] = birth["snapshot_sha256"]
        elif self.first_birth and turn > self.birth_turn:
            previous = self.followups[-1] if self.followups else None
            try:
                checkpoint = freeze_weightless_followup(
                    engine, self.first_birth, previous=previous,
                )
            except ValueError as exc:
                self.checkpoint_failure = safe_checkpoint_failure(
                    exc, state, case_id=self.case_id, turn=turn,
                    birth=self.first_birth, previous=previous,
                )
                raise
            self.followups.append(checkpoint)
            row["followup_snapshot_sha256"] = checkpoint["snapshot_sha256"]
        return row

    def final_status(self) -> str:
        if len(self.all_births) != TURN_COUNT:
            return "INCOMPLETE_SESSION_NOT_ZERO_EFFECT"
        if self.checkpoint_failure:
            return "FAILED_CHECKPOINT_NOT_ZERO_EFFECT"
        if self.first_birth is None:
            return "NO_ELIGIBLE_BIRTH_NOT_Q2_ZERO"
        if self.birth_turn not in (0, 1, 2) or len(self.followups) < 2:
            return "INCOMPLETE_FOLLOWUP_NOT_ZERO_EFFECT"
        if self.followups[0]["turn"] != self.birth_turn + 1:
            return "INCOMPLETE_FOLLOWUP_NOT_ZERO_EFFECT"
        if self.followups[1]["turn"] != self.birth_turn + 2:
            return "INCOMPLETE_FOLLOWUP_NOT_ZERO_EFFECT"
        return "TWO_CANONICAL_FOLLOWUPS_NO_Q2_CLAIM"

    def snapshot(self) -> dict:
        return {
            "schema": "shadowseed-g0-prospective-birth-cohort-v1",
            "G0": "NOT_PASSED",
            "case_id": self.case_id,
            "selection_window": self.selection_window,
            "selected_seed_id": self.selected_id,
            "selected_birth_turn": self.birth_turn,
            "seed_text_owner_only": self.seed_text,
            "first_birth": self.first_birth,
            "canonical_followups": self.followups,
            "all_births_including_ineligible": self.all_births,
            "checkpoint_failure": self.checkpoint_failure,
            "status": self.final_status(),
            "ordinary_host_not_seed_exposed": True,
            "not_an_RI_experiment": True,
            "Q1_Q2_effect_not_proven": True,
        }
