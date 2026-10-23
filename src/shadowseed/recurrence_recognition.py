"""Model-based recognition of a returning gap.

Embedding similarity measures topic overlap, not whether two candidates name
the same open question (docs/research/seed-calibration.md). This module asks
the session's own model instead: given the open questions of the conversation
and this turn's new candidates, which new candidate repeats which open
question?

The answer is an observation only. It decides cluster membership, and through
that the recurrence count and trace. It never becomes evidence, weight or
authority. Embedding similarity is kept as a floor: a claimed repeat below the
floor is refused and logged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from shadowseed.prompt_contracts import prompt_contract_metadata

RECURRENCE_FLOOR = 0.3
MAX_OPEN_QUESTIONS = 12
RECOGNIZER_ID = "recurrence_recognition_v1"

PROMPT = """You keep track of open questions in one conversation.

Open questions noted earlier:
{open_questions}

New notes from the latest turn:
{new_notes}

For each new note, say whether it points at the same open question as one of the
earlier ones, even if it is worded differently. A note that only shares a topic
is not the same open question.

Answer with one line per new note, in this form:
a: 3
b: NONE
"""

RECOGNITION_PROMPT_META = prompt_contract_metadata(
    prompt_id=RECOGNIZER_ID,
    prompt_version="1",
    component="recurrence_recognition",
    template=PROMPT,
    input_contract=("open_questions", "new_notes"),
    output_contract="one_line_per_new_note_with_open_question_number_or_NONE",
)

_LINE = re.compile(r"^\s*([a-z])\s*[:.)-]\s*(none|\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class OpenQuestion:
    number: int
    cluster_id: int
    text: str


def build_prompt(open_questions: list[OpenQuestion], new_notes: list[str]) -> str:
    return PROMPT.format(
        open_questions="\n".join(f"{item.number}. {item.text}" for item in open_questions),
        new_notes="\n".join(f"{chr(ord('a') + i)}. {text}" for i, text in enumerate(new_notes)),
    )


def parse_answer(raw: str, new_count: int, open_count: int) -> dict[int, int | None] | None:
    """Map new-note index to an open-question number, or None for a new question.

    Returns None when no line could be read, so the caller can fall back.
    Out-of-range numbers count as a new question. Unmentioned notes are absent.
    """

    mapping: dict[int, int | None] = {}
    for line in raw.splitlines():
        match = _LINE.match(line)
        if not match:
            continue
        index = ord(match.group(1).lower()) - ord("a")
        if not 0 <= index < new_count or index in mapping:
            continue
        value = match.group(2).lower()
        number = None if value == "none" else int(value)
        mapping[index] = number if number is not None and 1 <= number <= open_count else None
    # Notes the answer does not mention stay absent, so the caller keeps
    # embedding clustering for them (for example after a truncated answer).
    return mapping or None


def recognize(
    generate: Callable[[str], str],
    open_questions: list[OpenQuestion],
    new_notes: list[str],
) -> tuple[dict[int, int | None] | None, str]:
    """Ask the model once; return (mapping or None on failure, raw answer)."""

    raw = generate(build_prompt(open_questions, new_notes))
    return parse_answer(raw or "", len(new_notes), len(open_questions)), (raw or "")
