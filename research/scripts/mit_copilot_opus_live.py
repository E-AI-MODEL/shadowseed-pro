#!/usr/bin/env python3
"""Real, one-case five-arm inquiry via GitHub Copilot Claude Opus 5.5.

G0 remains NOT_PASSED. Not a sealed or confirmatory study. Canonical first
ShadowSeed birth, no Gate or answer authority, no external embedding provider.
The lexical embedder is a declared research-only toy; it is not semantic proof.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import tempfile
from pathlib import Path

from mit_matched_runner import make_messages, parse_reply

MODEL = "claude-opus-5.5"
MAX_REQUESTS = 12
SCENARIO = {
    "case_id": "FICTIONAL-SENSORS",
    "history": (
        "A fictional workshop has two independently built sensors that measure "
        "the same material. Sensor A sometimes spikes after a controller and "
        "firmware update. Only application timestamps are available, not sensor "
        "timestamps. No external reference meter has been used. The cause is unknown."
    ),
    "t0_context": (
        "What alternative explanations for the recorded spikes are still plausible, "
        "and which facts are missing?"
    ),
    "feedback": (
        "A repeat measurement reveals no corresponding spike in sensor B. "
        "A separate clock suggests the sensor logs might not be synchronized, "
        "but the size and direction of any timestamp discrepancy are unmeasured."
    ),
    "ordinary_notes": (
        "Earlier notes mention sensor calibration, the controller update, spatial "
        "sampling differences and possible timestamp misalignment, all unverified."
    ),
}
HOST_SYSTEM = (
    "You are analysing a fictional measurement problem. Distinguish recorded "
    "observations from hypotheses and do not invent measurements."
)
DETECTOR_SYSTEM = (
    "Follow the supplied detector prompt exactly. A candidate gap or question "
    "is not established evidence. Use NONE if no gap is appropriate."
)


def checksum(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def matched_sham(candidate: str) -> str:
    """Word-unit match only, NOT semantic equivalence or actual tokenizer parity."""
    count = len(candidate.split())
    if count < 2:
        raise ValueError("candidate too short to make a sham")
    words = (
        "The archived inventory lists neutral equipment labels and cabinet "
        "identifiers without recording an independent measurement or a causal explanation"
    ).split()
    return " ".join(words[i % len(words)] for i in range(count))


async def copilot_ask(prompt: str) -> str:
    from copilot import CopilotClient
    from copilot.rpc import PermissionDecisionReject
    from copilot.session_events import AssistantMessageData, SessionIdleData

    if not os.environ.get("GITHUB_TOKEN"):
        raise RuntimeError("GitHub Copilot Actions credential missing")
    if not prompt or len(prompt) > 18000:
        raise ValueError("empty or oversized research prompt")

    done = asyncio.Event()
    answers: list[str] = []

    def deny_all(request, invocation):
        return PermissionDecisionReject(feedback="No tools allowed in controlled experiment")

    # Explicit disposable storage, not a user's default Copilot workspace.
    with tempfile.TemporaryDirectory(prefix="copilot-opus-study-") as tmp:
        async with CopilotClient(mode="empty", base_directory=tmp) as client:
            async with await client.create_session(
                model=MODEL,
                available_tools=[],
                tools=[],
                on_permission_request=deny_all,
                enable_session_store=False,
                infinite_sessions={"enabled": False},
                streaming=False,
            ) as session:
                def on_event(event):
                    if isinstance(event.data, AssistantMessageData):
                        answers.append(event.data.content)
                    elif isinstance(event.data, SessionIdleData):
                        done.set()

                session.on(on_event)
                await session.send(prompt)
                await asyncio.wait_for(done.wait(), 200)
    answer = "\n".join(x for x in answers if isinstance(x, str) and x.strip()).strip()
    if not answer:
        raise RuntimeError("Claude Opus 5.5 returned no completed visible text")
    return answer


class Provider:
    """One fixed model, 12 explicit calls max, no hidden retry or fallback."""

    def __init__(self, complete_fn=None):
        self._complete_fn = complete_fn or (lambda p: asyncio.run(copilot_ask(p)))
        self.attempts = 0
        self.events: list[dict] = []

    def ask(self, *, stage: str, prompt: str) -> str:
        if self.attempts >= MAX_REQUESTS:
            raise RuntimeError("Research call cap reached")
        self.attempts += 1
        event = {"stage": stage, "model_requested": MODEL,
                 "request_sha256": checksum(prompt), "status": "attempted"}
        self.events.append(event)
        try:
            text = self._complete_fn(prompt)
            if not isinstance(text, str) or not text.strip():
                raise ValueError("missing response text")
            event.update(status="completed", output_sha256=checksum(text),
                         visible_characters=len(text))
            return text
        except Exception as exc:
            event.update(status="failed", failure_type=type(exc).__name__,
                         reason=str(exc)[:200])
            raise


class DetectorBridge:
    def __init__(self, provider: Provider):
        self.provider = provider

    def generate(self, prompt: str, **kwargs) -> str:
        return self.provider.ask(stage="canonical_detector_T0",
                                 prompt=DETECTOR_SYSTEM + "\n\n" + prompt)


def canonical_birth(provider: Provider):
    from shadowseed import ShadowseedEngine
    from shadowseed.detection.model_detector import OpenAIDetectorBackend
    from shadowseed_research.benchmark.weightless_birth_handoff import (
        freeze_canonical_weightless_birth,
    )

    detector = OpenAIDetectorBackend(model_id=MODEL, prompt_variant="current_pair")
    detector.client = DetectorBridge(provider)
    engine = ShadowseedEngine(
        detector_backend=detector,
        embedding_backend="lexical",
        allow_toy_embedder=True,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
        max_seeds_per_turn=3,
    )
    opening = SCENARIO["history"] + "\n" + SCENARIO["t0_context"]
    prepared = engine.prepare_turn(opening)
    if prepared.model_context or prepared.surfaced_seed_ids or prepared.selected_seed_ids:
        raise RuntimeError("Unauthorised seed in ordinary host context")
    answer = provider.ask(stage="ordinary_host_T0",
                          prompt=HOST_SYSTEM + "\n\n" + opening)
    observed = engine.observe_turn(prepared, answer)
    if observed.get("surfaced_seed_ids") or observed.get("selected_seed_ids"):
        raise RuntimeError("Candidate reached ordinary answer route")
    state = engine.export_state()
    first_ids = [
        sid for sid in observed.get("seeds_born_weightless", [])
        if state.get("born_turn", {}).get(sid) == observed.get("turn")
    ]
    record = {
        "detector_raw": detector.last_raw_output,
        "detector_diagnostics": detector.last_parse_diagnostics,
        "recorded_birth_ids": first_ids,
        "observed_turn": observed,
        "lexical_toy_embedder": True,
    }
    if not first_ids:
        return answer, None, record
    checkpoint = freeze_canonical_weightless_birth(
        engine, observed, first_ids[0], include_candidate_text=True
    )
    candidates = [
        seed["text"] for seed in state["manager"]["seeds"]
        if seed.get("id") == first_ids[0]
    ]
    if len(candidates) != 1 or checksum(candidates[0]) != checkpoint["candidate_text_sha256"]:
        raise RuntimeError("Canonical candidate lineage mismatch")
    record["checkpoint"] = checkpoint
    return answer, candidates[0], record


def run_study(provider: Provider) -> dict:
    report = {
        "schema": "shadowseed-opus-real-five-arm-exploratory-v1",
        "model_requested": MODEL,
        "case_id": SCENARIO["case_id"],
        "public_fictional_case": True,
        "sealed_holdout": False,
        "G0": "NOT_PASSED",
        "confirmatory": False,
        "embedding_mode": "lexical_TOY_research_only",
        "scientific_effect_established": False,
        "arm_results": {},
        "status": "started",
    }
    try:
        host, candidate, lineage = canonical_birth(provider)
        report["host_T0_answer"] = host
        report["birth"] = lineage
        if candidate is None:
            report["status"] = "no_canonical_birth"
            return report
        report["candidate_text"] = candidate
        sham = matched_sham(candidate)
        report["sham_text"] = sham
        payload = {
            "history": SCENARIO["history"] + "\nORDINARY HOST T0 ANSWER:\n" + host,
            "t0_context": SCENARIO["t0_context"],
            "feedback": SCENARIO["feedback"],
            "ordinary_notes": SCENARIO["ordinary_notes"],
            "candidate_text": candidate,
            "sham_text": sham,
        }
        # Source data never contains the actual candidate/sham before their arm slot.
        shared = "\n".join(payload[k] for k in ("history","t0_context","feedback","ordinary_notes"))
        if candidate in shared or sham in shared or candidate == sham:
            raise RuntimeError("Candidate/sham leaked outside the intended arm")
        order = list("ABCDE")
        random.Random(20261104).shuffle(order)
        report["execution_order"] = order
        report["common_history_sha256"] = checksum(payload["history"])
        report["common_feedback_sha256"] = checksum(payload["feedback"])
        for arm in order:
            events: list[dict] = []
            earlier: str | None = None
            for stage in ("T1", "T3"):
                if stage == "T3" and earlier is None:
                    events.append({"stage": stage, "status": "skipped_invalid_T1"})
                    break
                messages = make_messages({}, payload, arm, stage, earlier)
                text = "\n\n".join(msg["role"].upper() + ":\n" + msg["content"] for msg in messages)
                event = {"stage": stage, "request_sha256": checksum(text),
                         "request_text": text}
                events.append(event)
                try:
                    raw = provider.ask(stage=f"{arm}_{stage}", prompt=text)
                    parsed = parse_reply(raw)
                    event.update(raw=raw, parsed=parsed,
                                 status="parsed" if parsed["valid"] else "unscorable_format")
                    if not parsed["valid"]:
                        break
                    if stage == "T1":
                        earlier = raw
                except Exception as exc:
                    event.update(status="provider_error", error_type=type(exc).__name__,
                                 reason=str(exc)[:200])
                    break
            report["arm_results"][arm] = events
        report["status"] = "completed_exploratory" if (
            len(report["arm_results"]) == 5 and all(
                len(events) == 2 and all(e["status"] == "parsed" for e in events)
                for events in report["arm_results"].values()
            )
        ) else "incomplete_unscorable"
    except Exception as exc:
        report.update(status="failed_closed", failure_type=type(exc).__name__,
                      failure_reason=str(exc)[:240])
    finally:
        report["model_attempts"] = provider.attempts
        report["provider_events"] = provider.events
        report["reported_token_usage"] = None  # Copilot SDK does not expose it in this adapter.
    return report


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    provider = Provider()
    result = run_study(provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({
        "status": result["status"], "model": MODEL,
        "calls": provider.attempts, "G0": result["G0"],
    }))
    return 0 if result["status"] == "completed_exploratory" else 2


if __name__ == "__main__":
    raise SystemExit(main())
