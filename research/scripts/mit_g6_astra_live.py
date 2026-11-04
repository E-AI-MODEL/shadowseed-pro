"""Exploratory Astra-only study: real ShadowSeed birth and five blinded arms.

The fictional public scenario is not a G0 holdout. No retries, no model fallback,
no product Gate changes. A failed birth or incomplete response is preserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import urllib.error
import urllib.request
from pathlib import Path

from mit_matched_runner import make_messages, parse_reply

MODEL = "gpt-6-astra"
MAX_CALLS = 12
MAX_EMBEDS = 8
MAX_TOKENS = 52000

SCENE = {
    "id": "FICTIONAL-SENSORS",
    "history": "A fictional workshop has two sensors reading one material. Sensor A sometimes spikes after a firmware and controller update. Only application timestamps exist, not raw sensor timestamps. No external meter has been used. The cause is unknown.",
    "question": "Which competing explanations can we still test without assuming the cause?",
    "feedback": "A repeat reading shows no simultaneous spike in sensor B. A separate clock suggests sensor timestamps may differ. The magnitude of that difference remains unknown.",
    "ordinary": "Previous notes mention timestamp alignment, sensor calibration and spatial placement.",
    "sham": "A neutral note on cabinet labels and archived service documentation.",
}
DETECTOR_SYSTEM = "Follow the given detector prompt. A question is not evidence. Return NONE when appropriate."
HOST_SYSTEM = "Explain this fictional observation without inventing results. Identify competing explanations and uncertainties."


def digest(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


class Provider:
    def __init__(self, key):
        if not key:
            raise RuntimeError("No scoped OpenAI research credential")
        self.key = key
        self.calls = 0
        self.embeds = 0
        self.tokens = 0
        self.events = []

    def send(self, endpoint, payload):
        req = urllib.request.Request(
            "https://api.openai.com/v1/" + endpoint,
            json.dumps(payload).encode("utf-8"),
            {"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                return json.load(res)
        except urllib.error.HTTPError as exc:
            raise RuntimeError("Provider HTTP " + str(exc.code)) from None
        except Exception as exc:
            raise RuntimeError("Provider " + type(exc).__name__) from None

    def charge(self, amount):
        if type(amount) is not int or amount < 0:
            raise RuntimeError("Token usage missing")
        self.tokens += amount
        if self.tokens > MAX_TOKENS:
            raise RuntimeError("Total token cap exceeded")

    def complete(self, stage, messages, *, structured=False):
        if self.calls >= MAX_CALLS or self.tokens > MAX_TOKENS - 6000:
            raise RuntimeError("Model call/token limit reached")
        if sum(len(m["content"]) for m in messages) > 14000:
            raise RuntimeError("Prompt oversized")
        args = {"model": MODEL, "input": messages, "store": False,
                "reasoning": {"effort": "medium"}, "max_output_tokens": 2500}
        if structured:
            args["text"] = {"format": {"type": "json_schema", "name": "inquiry", "strict": True,
                "schema": {"type": "object", "properties": {
                    "question": {"type": "string"}, "experiment": {"type": "string"},
                    "expected_result": {"type": "string"}},
                    "required": ["question", "experiment", "expected_result"],
                    "additionalProperties": False}}}
        self.calls += 1
        event = {"stage": stage, "model": MODEL, "request_sha256": digest(json.dumps(args, sort_keys=True)),
                 "status": "attempted"}
        self.events.append(event)
        res = self.send("responses", args)
        if res.get("model") != MODEL or not isinstance(res.get("usage"), dict):
            raise RuntimeError("Model identity or usage missing")
        usage = res["usage"]
        self.charge(usage.get("input_tokens"))
        self.charge(usage.get("output_tokens"))
        if usage["output_tokens"] > 2500:
            raise RuntimeError("Output limit exceeded")
        text = "\n".join(
            part["text"] for item in res.get("output", []) if isinstance(item, dict)
            for part in item.get("content", []) if isinstance(part, dict)
            and part.get("type") == "output_text" and isinstance(part.get("text"), str)
        ).strip()
        event.update(status=res.get("status"), response_sha256=digest(text),
                     input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"])
        if res.get("status") != "completed" or not text:
            raise RuntimeError("Model did not return complete visible text")
        return text

    def embed(self, text):
        import numpy as np
        if self.embeds >= MAX_EMBEDS:
            raise RuntimeError("Embedding call cap reached")
        self.embeds += 1
        response = self.send("embeddings", {"model": "text-embedding-3-small", "input": [text]})
        self.charge(response.get("usage", {}).get("total_tokens"))
        data = response.get("data", [])
        if len(data) != 1:
            raise RuntimeError("Embedding cardinality mismatch")
        array = np.asarray(data[0]["embedding"], dtype=float)
        if array.ndim != 1 or len(array) != 1536 or not np.isfinite(array).all():
            raise RuntimeError("Bad embedding vector")
        norm = np.linalg.norm(array)
        if norm <= 0:
            raise RuntimeError("Zero embedding")
        return array / norm


class DetectorBridge:
    def __init__(self, provider):
        self.provider = provider

    def generate(self, prompt, **kwargs):
        return self.provider.complete("detector", [
            {"role": "system", "content": DETECTOR_SYSTEM},
            {"role": "user", "content": prompt},
        ])


def first_birth(provider):
    from shadowseed import ShadowseedEngine
    from shadowseed.detection.model_detector import OpenAIDetectorBackend
    from shadowseed_research.benchmark.weightless_birth_handoff import freeze_canonical_weightless_birth

    backend = OpenAIDetectorBackend(model_id=MODEL, prompt_variant="current_pair")
    backend.client = DetectorBridge(provider)
    engine = ShadowseedEngine(
        detector_backend=backend, embedding_fn=provider.embed,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
        max_seeds_per_turn=3)
    prepared = engine.prepare_turn(SCENE["history"] + "\nQUESTION: " + SCENE["question"])
    if prepared.model_context or prepared.selected_seed_ids or prepared.surfaced_seed_ids:
        raise RuntimeError("Ordinary host exposed to seed")
    answer = provider.complete("host_T0", [
        {"role": "system", "content": HOST_SYSTEM},
        {"role": "user", "content": SCENE["history"] + "\n" + SCENE["question"]},
    ])
    report = engine.observe_turn(prepared, answer)
    state = engine.export_state()
    ids = [ident for ident in report.get("seeds_born_weightless", [])
           if state.get("born_turn", {}).get(ident) == report.get("turn")]
    if not ids:
        return answer, None, {"status": "no_seed", "detector_output": backend.last_raw_output}
    checkpoint = freeze_canonical_weightless_birth(engine, report, ids[0], include_candidate_text=True)
    text = next(s["text"] for s in state["manager"]["seeds"] if s["id"] == ids[0])
    if digest(text) != checkpoint["candidate_text_sha256"]:
        raise RuntimeError("Candidate lineage mismatch")
    return answer, text, {"status": "canonical_birth", "checkpoint": checkpoint}


def run(provider):
    output = {"schema": "shadowseed-astra-exploratory-v1", "model": MODEL,
              "G0": "NOT_PASSED", "confirmatory": False, "sealed_holdout": False,
              "arms": {}, "status": "started"}
    try:
        first, candidate, birth = first_birth(provider)
        output["birth"] = birth
        if candidate is None:
            output["status"] = "no_seed"
            return output
        output["candidate_text"] = candidate
        context = {"history": SCENE["history"] + "\nHOST:\n" + first,
                   "t0_context": SCENE["question"], "feedback": SCENE["feedback"],
                   "ordinary_notes": SCENE["ordinary"], "candidate_text": candidate,
                   "sham_text": SCENE["sham"]}
        order = list("ABCDE")
        random.Random(20261104).shuffle(order)
        output["order"] = order
        for arm in order:
            events = []
            first_reply = None
            for turn in ("T1", "T3"):
                if turn == "T3" and first_reply is None:
                    events.append({"turn": turn, "status": "skipped_bad_T1"})
                    break
                msgs = make_messages({}, context, arm, turn, first_reply)
                entry = {"turn": turn, "input": msgs, "status": "attempted"}
                events.append(entry)
                try:
                    reply = provider.complete(arm + "_" + turn, msgs, structured=True)
                    parsed = parse_reply(reply)
                    entry.update(text=reply, parsed=parsed,
                                 status="parsed" if parsed["valid"] else "invalid_format")
                    if not parsed["valid"]:
                        break
                    if turn == "T1":
                        first_reply = reply
                except Exception as exc:
                    entry.update(status="failed", reason=type(exc).__name__)
                    break
            output["arms"][arm] = events
        output["status"] = "completed" if len(output["arms"]) == 5 and all(
            len(rows) == 2 and all(e["status"] == "parsed" for e in rows)
            for rows in output["arms"].values()) else "incomplete"
    except Exception as exc:
        output.update(status="failed_closed", error_type=type(exc).__name__,
                      error=str(exc)[:160])
    finally:
        output["usage"] = {"model_calls": provider.calls, "embedding_calls": provider.embeds,
                           "all_tokens": provider.tokens, "events": provider.events}
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    provider = Provider(os.environ.get("OPENAI_API_KEY"))
    result = run(provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({"status": result["status"], "model": MODEL,
                      "calls": provider.calls, "tokens": provider.tokens, "G0": "NOT_PASSED"}))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
