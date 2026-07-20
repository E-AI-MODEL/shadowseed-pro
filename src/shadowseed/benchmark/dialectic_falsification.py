"""Dialectical falsification: can this candidate gap be argued away?

The Validation Gate has lexical and numerical contradiction checks. Generative
candidate seeds need an additional adversarial test: a model actively tries to
show that the seed is redundant, already covered, or contradicted by the source.

The legacy verdict tokens ``WEERLEGD``, ``HOUDT_STAND``, and ``ONBESLIST`` are
retained for result-artifact compatibility. Their meanings are refuted,
survives, and undecided.

A refuted verdict removes influence through the Gate. A surviving verdict can
apply bounded probe feedback but can never promote a seed. An undecided or
unparseable verdict is neutral.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

from shadowseed.text_similarity import lexical_embedding
from shadowseed.manager import SSLManager

VERDICT_WEERLEGD = "WEERLEGD"
VERDICT_HOUDT_STAND = "HOUDT_STAND"
VERDICT_ONBESLIST = "ONBESLIST"
_VERDICTS = (VERDICT_WEERLEGD, VERDICT_HOUDT_STAND, VERDICT_ONBESLIST)

# Canonical English names for the verdicts. These are the preferred identifiers
# in new code; the underlying token *values* remain the Dutch forms so existing
# result artifacts and model-output parsing stay compatible (see the module
# docstring). REFUTED = refuted, SURVIVES = survives, UNDECIDED = undecided.
VERDICT_REFUTED = VERDICT_WEERLEGD
VERDICT_SURVIVES = VERDICT_HOUDT_STAND
VERDICT_UNDECIDED = VERDICT_ONBESLIST


class DialecticVerdict(str, Enum):
    """Canonical dialectic verdicts.

    The member *names* are the canonical English identifiers; the member *values*
    are the legacy Dutch tokens, retained as serialization aliases so existing
    result artifacts and model-output parsing remain compatible. Prefer the enum
    members in new code; use :func:`normalize_verdict` to map any legacy or
    English token onto a member.
    """

    REFUTED = VERDICT_WEERLEGD
    SURVIVES = VERDICT_HOUDT_STAND
    UNDECIDED = VERDICT_ONBESLIST


#: Maps legacy Dutch tokens and canonical English names to enum members.
LEGACY_TO_VERDICT: dict[str, DialecticVerdict] = {
    VERDICT_WEERLEGD: DialecticVerdict.REFUTED,
    VERDICT_HOUDT_STAND: DialecticVerdict.SURVIVES,
    VERDICT_ONBESLIST: DialecticVerdict.UNDECIDED,
    "REFUTED": DialecticVerdict.REFUTED,
    "SURVIVES": DialecticVerdict.SURVIVES,
    "UNDECIDED": DialecticVerdict.UNDECIDED,
}


def normalize_verdict(token: str) -> DialecticVerdict:
    """Normalize a legacy Dutch or English verdict token to a canonical member."""

    return LEGACY_TO_VERDICT[str(token).strip().upper()]

_VERDICT_LINE_RE = re.compile(r"VERDICT\s*:\s*(.+)", re.IGNORECASE)
_VERDICT_TOKEN_RE = re.compile(r"WEERLEGD|HOUDT[_ ]STAND|ONBESLIST", re.IGNORECASE)
_REASON_RE = re.compile(r"(?:REASON|REDEN)\s*:\s*(.+)", re.IGNORECASE)


def build_dialectic_prompt(seed_text: str, source_text: str) -> str:
    """Ask the model to actively argue the seed away against the source."""
    return (
        "You are a strict dialectical reviewer. Below are a SOURCE TEXT and a "
        "CLAIM representing a candidate missing point. Try to argue the claim "
        "away: is it redundant, already covered, or contradicted by the source?\n\n"
        f"SOURCE TEXT:\n{source_text}\n\n"
        f"CLAIM:\n{seed_text}\n\n"
        "Answer in exactly this format and nothing else:\n"
        "VERDICT: WEERLEGD | HOUDT_STAND | ONBESLIST\n"
        "REASON: <one sentence>\n\n"
        "WEERLEGD means the claim is refuted, covered, redundant, or contradicted. "
        "HOUDT_STAND means it survives as a genuine testable absence. ONBESLIST "
        "means the source is insufficient to decide."
    )


def parse_dialectic_verdict(raw: str) -> dict[str, str]:
    """Parse the model output; anything but one unambiguous verdict fails safe.

    The verdict line must contain exactly one allowed option. A backend that
    echoes the format line ("VERDICT: WEERLEGD | HOUDT_STAND | ONBESLIST"), or
    hedges with multiple options, must land on ONBESLIST — never on a
    contradiction it did not actually assert.
    """
    line_match = _VERDICT_LINE_RE.search(raw or "")
    if not line_match:
        return {"verdict": VERDICT_ONBESLIST, "reason": "unparseable model output"}
    tokens = {
        t.upper().replace(" ", "_") for t in _VERDICT_TOKEN_RE.findall(line_match.group(1))
    }
    if len(tokens) != 1:
        return {
            "verdict": VERDICT_ONBESLIST,
            "reason": "ambiguous verdict: zero or multiple options on the VERDICT line",
        }
    reason_match = _REASON_RE.search(raw)
    reason = reason_match.group(1).strip() if reason_match else ""
    return {"verdict": tokens.pop(), "reason": reason}


class FixtureDialecticBackend:
    """Deterministic CI backend: verdict from lexical overlap with the source.

    A seed sharing no content tokens with the source is treated as arguable
    away (WEERLEGD); a seed sharing tokens holds (HOUDT_STAND). This checks the
    harness mechanics, not dialectic quality.
    """

    name = "fixture"

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zà-ÿ0-9]+", text.lower()) if len(t) > 4}

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        seed_text = scenario.get("seed_text", "")
        source_text = scenario.get("source_text", "")
        overlap = self._tokens(seed_text) & self._tokens(source_text)
        if overlap:
            return "VERDICT: HOUDT_STAND\nREASON: shares content words with the source."
        return "VERDICT: WEERLEGD\nREASON: has no content connection to the source."


def apply_dialectic_outcome(
    manager: SSLManager, seed_id: str, verdict: str
) -> dict[str, Any]:
    """Map a dialectic verdict onto the sanctioned lifecycle channels."""
    if verdict not in _VERDICTS:
        raise ValueError(f"Unknown dialectical verdict: {verdict!r}")
    seed = manager.seeds[seed_id]
    weight_before = float(seed.weight)
    if verdict == VERDICT_WEERLEGD:
        gate = manager.run_validation_gate_detailed(seed_id, contradiction=True)
        channel = "gate_contradiction"
        detail: dict[str, Any] = {"gate_verdict": gate.verdict}
    else:
        outcome = "reward" if verdict == VERDICT_HOUDT_STAND else "neutral"
        fb = manager.apply_probe_feedback(seed_id, outcome, probe_type="dialectic")
        channel = "probe_feedback"
        detail = {"outcome": fb.outcome, "delta_applied": fb.delta_applied, "skipped": fb.skipped}
    return {
        "seed_id": seed_id,
        "verdict": verdict,
        "channel": channel,
        "weight_before": weight_before,
        "weight_after": float(seed.weight),
        "status_after": seed.status.value,
        **detail,
    }


def run_dialectic_probe(
    manager: SSLManager, seed_id: str, source_text: str, model: Any
) -> dict[str, Any]:
    """One full dialectic pass for one seed: prompt -> verdict -> lifecycle."""
    seed = manager.seeds[seed_id]
    prompt = build_dialectic_prompt(seed.text, source_text)
    raw = model.generate(
        prompt, {"seed_text": seed.text, "source_text": source_text}, "dialectic", []
    )
    parsed = parse_dialectic_verdict(raw)
    record = apply_dialectic_outcome(manager, seed_id, parsed["verdict"])
    record["reason"] = parsed["reason"]
    record["raw_output"] = raw
    return record


def _promote_via_gate(manager: SSLManager, seed_id: str) -> None:
    """Drive a fixture seed to PROMOTED through the real Gate (no shortcuts)."""
    seed = manager.seeds[seed_id]
    for _ in range(8):
        if seed.status.value == "PROMOTED":
            return
        seed.occurrence_count += 1
        manager.run_validation_gate(seed_id, external_evidence=True)
    raise RuntimeError(f"Fixture seed {seed_id} was not promoted through the Gate")


def run_dialectic_falsification(
    input_path: str,
    output_path: str = "results/dialectic_falsification.json",
    backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 200,
) -> dict[str, Any]:
    """Run the dialectic probe over a case file and write a result artifact.

    Input schema: ``{"source_text": ..., "cases": [{"seed_text": ...,
    "expected_verdict": ...?}, ...]}``. Every seed is ingested weightless and
    promoted through the real Gate first, so the probe attacks exactly the
    seeds that would be allowed to steer — falsification where it matters.
    """
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    source_text = data["source_text"]
    if backend == "fixture":
        model: Any = FixtureDialecticBackend()
    else:
        from shadowseed.adapters.models import make_backend

        model = make_backend(backend=backend, model_id=model_id, max_new_tokens=max_new_tokens)

    manager = SSLManager(embedding_fn=lexical_embedding)
    records: list[dict[str, Any]] = []
    for case in data["cases"]:
        ingest = manager.ingest_detection_candidates([case["seed_text"]])
        accepted = ingest.get("accepted", [])
        if not accepted:
            records.append({"seed_text": case["seed_text"], "skipped": "not accepted"})
            continue
        sid = accepted[0]["seed_id"]
        _promote_via_gate(manager, sid)
        record = run_dialectic_probe(manager, sid, source_text, model)
        record["seed_text"] = case["seed_text"]
        expected = case.get("expected_verdict")
        if expected:
            record["expected_verdict"] = expected
            record["matches_expected"] = record["verdict"] == expected
        records.append(record)

    result = {
        "artifact": "dialectic_falsification",
        "backend": getattr(model, "name", backend),
        "doctrine": (
            "Dialectical review removes influence through a Gate contradiction or "
            "applies bounded probe feedback; it never promotes a seed."
        ),
        "source_text": source_text,
        "records": records,
        "summary": {
            "cases": len(records),
            "weerlegd": sum(1 for r in records if r.get("verdict") == VERDICT_WEERLEGD),
            "houdt_stand": sum(1 for r in records if r.get("verdict") == VERDICT_HOUDT_STAND),
            "onbeslist": sum(1 for r in records if r.get("verdict") == VERDICT_ONBESLIST),
        },
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result
