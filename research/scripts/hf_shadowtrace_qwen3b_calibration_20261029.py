"""Bounded Qwen2.5-3B Shadow Trace calibration, never a Q1/Q2 efficacy test.

Reuse canonical product host/detector/surfacing/engine without changing the Gate.
Share one read-only model instance between host and detector to fit 16 GB CPU.
The simulated user sees only visible host turns, never the shadow state.
All raw model text, exact prompts and failed turns are retained, including NONE.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import torch
from huggingface_hub import model_info

from shadowseed.adapters.models import HFTransformersBackend
from shadowseed.detection.model_detector import (
    HFTransformersDetectorBackend,
    build_detection_prompt,
)
from shadowseed.engine import ShadowseedEngine
from shadowseed.surfacing import build_role_chat_messages

MODEL = "Qwen/Qwen2.5-3B-Instruct"
MODEL_TURNS = int(os.getenv("SHADOWTRACE_TURNS", "4"))
OUTPUT = Path(os.getenv("SHADOWTRACE_OUT", "/tmp/shadowtrace_3b_calibration.json"))
OPENINGS = [
    ("city", "Een fictieve stad wil haar binnenstad aantrekkelijker maken. Er is weinig budget en bewoners zijn verdeeld. Hoe zou je het probleem eerst verkennen?"),
    ("sensors", "Twee fictieve sensoren geven soms andere meetwaarden voor hetzelfde proces. Er is nog geen onafhankelijke ijking. Wat kunnen we wel en niet zeggen?"),
]
# Keep the user-simulator instruction literally identical to the 0.5B pilot:
SIM_SYSTEM = (
    "Je bent een nieuwsgierige gesprekspartner. Stel precies één natuurlijke "
    "vervolgvraag op het laatste antwoord. Reageer op wat er werkelijk gezegd "
    "is, niet op een vooraf bepaald script. Geen lijst of uitleg. Noem nooit "
    "detector, seeds, geheugen of experiment."
)


def iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalized_question(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"\s+", " ", value.strip().strip(' \t\n"\'-.,?!')).strip()


def render(backend: HFTransformersBackend, messages: list[dict[str, str]]) -> str:
    tokenizer = backend.tokenizer
    template = getattr(tokenizer, "apply_chat_template", None)
    if callable(template):
        try:
            return template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            try:
                return template(backend._fold_system_for_chat_template(messages), tokenize=False, add_generation_prompt=True)
            except Exception:
                pass
    return backend._render_plain_chat(messages)


class SharedTracedDetector(HFTransformersDetectorBackend):
    """Exactly the HF detector parser/prompt with host.generator shared in memory."""

    def __init__(self, host: HFTransformersBackend, revision: str):
        # Deliberately do not call parent __init__: it would allocate another 3B
        # model and exceed the capacity of a free GitHub Actions CPU runner.
        self.name = host.name
        self.model_id = host.model_id
        self.revision = revision
        self.prompt_variant = "current_pair"
        self.max_new_tokens = 150
        self.generator = host.generator
        self.tokenizer = host.tokenizer
        self.last_prompt_metadata = None
        self.last_raw_output = None
        self.last_parse_diagnostics = None
        self.last_full_prompt = ""

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        content = str(item.get("text") or item.get("input") or "").strip()
        self.last_full_prompt = (
            build_detection_prompt(
                content,
                max_seeds=max_seeds,
                variant=self.prompt_variant,
                question=str(item.get("question") or "").strip() or None,
                source_context=str(item.get("source_context") or "").strip() or None,
                conversation_context=str(item.get("conversation_context") or "").strip() or None,
            )
            if content else ""
        )
        # Canonical HFTransformersDetectorBackend.detect_seeds (prompt, parse).
        return super().detect_seeds(item, max_seeds=max_seeds)


def main() -> None:
    assert 1 <= MODEL_TURNS <= 4
    random.seed(291026)
    torch.manual_seed(291026)
    torch.set_num_threads(2)
    revision = model_info(MODEL).sha
    print("MODEL", MODEL, "REVISION", revision, flush=True)
    host = HFTransformersBackend(
        model_id=MODEL, max_new_tokens=170, revision=revision
    )
    detector = SharedTracedDetector(host, revision)
    record: dict = {
        "schema": "shadowtrace-hf-qwen3b-calibration-v1",
        "kind": "exploratory-instrument-calibration-not-Q1-or-Q2",
        "started_at_utc": iso(),
        "model": MODEL,
        "model_revision": revision,
        "source_repo": "E-AI-MODEL/shadowseed-pro",
        "decoder": "greedy do_sample=False",
        "model_instance_count": 1,
        "engine": "canonical ShadowseedEngine, gated weightless lifecycle",
        "simulator": "same model, 0.5B original simulator instruction, no seed access, no automatic retries",
        "question_repeat_rule": "stop after first literal repeat (normalized whitespace/case/terminal punctuation); retain failure",
        "max_turns_per_episode": MODEL_TURNS,
        "cases": [],
        "errors": [],
        "status": "running",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    def save() -> None:
        OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    for case_id, question in OPENINGS:
        engine = ShadowseedEngine(
            detector_backend=detector,
            embedding_backend="sentence-transformers",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            gate_policy_id="evidence_backed",
            max_seeds_per_turn=3,
        )
        history: list[tuple[str, str]] = []
        episode: dict = {
            "case_id": case_id,
            "opening": question,
            "status": "running",
            "turns": [],
            "simulator_failures": [],
        }
        record["cases"].append(episode)
        save()
        for turn in range(MODEL_TURNS):
            prepared = engine.prepare_turn(question)
            try:
                messages = build_role_chat_messages(
                    history,
                    question,
                    list(prepared.surfaced_seeds),
                    response_language="the same language as the user's current question",
                )
                host_prompt = render(host, messages)
                before_host = time.monotonic()
                host.max_new_tokens = 170
                answer = host.generate_messages(messages)
                host_seconds = time.monotonic() - before_host
                before_detector = time.monotonic()
                observation = engine.observe_turn(prepared, answer)
                detector_seconds = time.monotonic() - before_detector
                row = {
                    "case": case_id,
                    "turn": turn,
                    "started_at_utc": iso(),
                    "question": question,
                    "answer": answer,
                    "host_role_messages": list(messages),
                    "host_wire_prompt": host_prompt,
                    "host_wire_prompt_sha256": hash_text(host_prompt),
                    "host_seconds": round(host_seconds, 2),
                    "detector_full_prompt": detector.last_full_prompt,
                    "detector_prompt_sha256": hash_text(detector.last_full_prompt),
                    "detector_raw_response": detector.last_raw_output,
                    "detector_parse_diagnostics": detector.last_parse_diagnostics,
                    "detector_seconds": round(detector_seconds, 2),
                    "prepared": prepared.to_dict(),
                    "observation": observation,
                    "simulator": None,
                }
                episode["turns"].append(row)
                history.append((question, answer))
                save()
                print(
                    "TURN", case_id, turn,
                    "detected", len(observation.get("detected_candidates", [])),
                    "born", len(observation.get("seeds_born_weightless", [])),
                    "exposed", len(prepared.surfaced_seed_ids),
                    flush=True,
                )
                if turn >= MODEL_TURNS - 1:
                    continue
                context = "\n".join(
                    "User: " + q + "\nAssistant: " + a
                    for q, a in history[-2:]
                )
                sim_messages = [
                    {"role": "system", "content": SIM_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            "Dit is het recente gesprek:\n"
                            + context
                            + "\n\nGeef uitsluitend jouw volgende vraag."
                        ),
                    },
                ]
                sim_prompt = render(host, sim_messages)
                host.max_new_tokens = 80
                before_sim = time.monotonic()
                raw_next = host.generate_messages(sim_messages)
                sim_seconds = time.monotonic() - before_sim
                proposed_next = raw_next.strip().split("\n")[0].strip(' -"')
                seen_before = normalized_question(proposed_next) in {
                    normalized_question(q) for q, _ in history
                }
                malformed = len(proposed_next) < 12 or not proposed_next.endswith("?")
                sim_record = {
                    "role_messages": sim_messages,
                    "wire_prompt": sim_prompt,
                    "wire_prompt_sha256": hash_text(sim_prompt),
                    "raw_response": raw_next,
                    "selected_first_line": proposed_next,
                    "seconds": round(sim_seconds, 2),
                    "literal_repeat": seen_before,
                    "malformed_as_question": malformed,
                    "accepted_as_next_user_question": not seen_before and not malformed,
                }
                row["simulator"] = sim_record
                save()
                if seen_before or malformed:
                    episode["status"] = "stopped_simulator_repeat" if seen_before else "stopped_invalid_question"
                    episode["simulator_failures"].append(
                        {
                            "after_turn": turn,
                            "reason": episode["status"],
                            "raw_response": raw_next,
                        }
                    )
                    print("SIMULATOR_STOP", case_id, turn, episode["status"], flush=True)
                    break
                question = proposed_next
                save()
            except Exception as exc:
                if engine.has_pending_turn:
                    engine.abort_turn(prepared)
                episode["status"] = "error"
                record["errors"].append(
                    {"case_id": case_id, "turn": turn, "error": repr(exc)}
                )
                save()
                print("ERROR", case_id, turn, repr(exc), flush=True)
                break
        if episode["status"] == "running":
            episode["status"] = "completed"
        episode["final_engine_state"] = engine.export_state()
        save()
    record["finished_at_utc"] = iso()
    record["status"] = (
        "completed_without_runtime_error"
        if not record["errors"] else "completed_with_errors"
    )
    save()
    print(
        "SUMMARY",
        "status", record["status"],
        "turns", sum(len(ep["turns"]) for ep in record["cases"]),
        "stopped_repeats", sum(ep["status"] == "stopped_simulator_repeat" for ep in record["cases"]),
        "output", OUTPUT,
        flush=True,
    )


if __name__ == "__main__":
    main()
