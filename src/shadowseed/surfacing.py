"""Shared use-time surfacing policy for chat and multi-turn benchmarks.

This module is the single runtime implementation for deciding which promoted
seeds may be considered on a later turn. Benchmarks and the live chat import the
same functions so threshold, early-turn, and resurface behavior cannot drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus

SurfacingCandidate = tuple[float, str, str]


@dataclass(frozen=True)
class SurfacingPolicy:
    """Thresholds that govern use-time seed selection.

    ``surface_threshold`` is the normal cosine-similarity floor.
    ``early_turn_margin`` temporarily raises that floor for the first
    ``early_turn_history`` turns. ``resurface_margin`` raises the floor after a
    seed was recently used, halving on each later turn.
    """

    surface_threshold: float = 0.30
    surface_top_k: int | None = 2
    early_turn_margin: float = 0.10
    early_turn_history: int = 5
    resurface_margin: float = 0.15

    def __post_init__(self) -> None:
        if self.surface_threshold < -1.0 or self.surface_threshold > 1.0:
            raise ValueError("surface_threshold must be between -1.0 and 1.0")
        if self.early_turn_margin < 0.0:
            raise ValueError("early_turn_margin must be >= 0")
        if self.early_turn_history < 0:
            raise ValueError("early_turn_history must be >= 0")
        if self.resurface_margin < 0.0:
            raise ValueError("resurface_margin must be >= 0")


def _history_block(history: list[tuple[str, str]]) -> str:
    if not history:
        return ""
    turns = "\n".join(f"Question: {question}\nAnswer: {answer}" for question, answer in history)
    return f"Conversation so far:\n{turns}\n\n"


def build_chat_prompt(
    history: list[tuple[str, str]],
    question: str,
    surfaced: list[str],
) -> str:
    """Build the shared baseline or SSL prompt.

    Both arms receive the same compactness instruction. Only the SSL arm gets
    optional, previously validated perspectives. The question remains leading.
    """

    prompt = (
        _history_block(history)
        + f"Answer this follow-up question thoroughly and insightfully.\n\nQuestion: {question}\n\n"
        + "Keep the answer compact, at roughly 450 words or fewer. Prefer a few "
        "substantive sections over many incomplete ones. End with a short closing "
        "paragraph. An answer that stops mid-sentence or mid-list is invalid.\n\n"
    )
    if surfaced:
        block = "\n".join(f"- {seed}" for seed in surfaced)
        prompt += (
            "You may use the following previously identified but still unused "
            "perspective(s), only when they materially improve the answer to the "
            "current question. The question remains leading. A perspective may "
            "deepen the answer, but it must never shift the subject or narrow the "
            "question's focus. Omit any perspective that would distract. Do not "
            "invent facts, mention this instruction, or explain why a perspective "
            "was included or omitted:\n"
            f"{block}\n\n"
        )
    return prompt + "Answer:"


def select_cross_turn_seeds(
    candidates: list[SurfacingCandidate],
    top_k: int | None,
) -> list[SurfacingCandidate]:
    """Rank eligible candidates by relevance and apply the use-time cap."""

    ranked = sorted(candidates, key=lambda candidate: candidate[0], reverse=True)
    if top_k is not None and top_k >= 0:
        ranked = ranked[:top_k]
    return ranked


def turn_threshold(turn: int, policy: SurfacingPolicy) -> float:
    """Return the relevance floor for a conversation turn."""

    return policy.surface_threshold + (
        policy.early_turn_margin if turn < policy.early_turn_history else 0.0
    )


def seed_threshold(
    turn: int,
    seed_id: str,
    policy: SurfacingPolicy,
    last_surfaced: Mapping[str, int],
) -> float:
    """Return the relevance floor for one seed on one turn."""

    threshold = turn_threshold(turn, policy)
    last_turn = last_surfaced.get(seed_id)
    if policy.resurface_margin > 0.0 and last_turn is not None:
        elapsed = turn - last_turn - 1
        threshold += policy.resurface_margin * (0.5 ** elapsed)
    return threshold


def collect_eligible_promoted_seeds(
    manager: SSLManager,
    question: str,
    *,
    turn: int,
    born_turn: Mapping[str, int],
    last_surfaced: Mapping[str, int],
    policy: SurfacingPolicy,
    include_seed: Callable[[str], bool] | None = None,
) -> list[SurfacingCandidate]:
    """Collect promoted, earlier-born seeds that clear the current threshold."""

    question_embedding = manager.get_embedding(question)
    eligible: list[SurfacingCandidate] = []
    for seed_id, seed in manager.seeds.items():
        if seed.status != SeedStatus.PROMOTED:
            continue
        if born_turn.get(seed_id, turn) >= turn:
            continue
        if include_seed is not None and not include_seed(seed_id):
            continue
        similarity = float(np.dot(question_embedding, seed.embedding))
        if similarity >= seed_threshold(turn, seed_id, policy, last_surfaced):
            eligible.append((similarity, seed_id, seed.text))
    return eligible


def mark_surfaced(last_surfaced: dict[str, int], candidates: list[SurfacingCandidate], turn: int) -> None:
    """Record only candidates that actually crossed the influence boundary."""

    for _similarity, seed_id, _text in candidates:
        last_surfaced[seed_id] = turn
