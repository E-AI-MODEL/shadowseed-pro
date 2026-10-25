"""G0-PENDING exploratory LIVE stage-1: real host, product detector and shadow travel.

This is NOT G0 validation, a Q1/Q2 effect study, or an inquiry generator.
No new Shadowseed manager, Gate, lifecycle, normalization or prompt contract.
A single actual ShadowseedEngine persists across four independent observed turns.
Researcher-authored future observations enter only their designated later turn.

The regular host never receives a weightless candidate. A separate NONE Engine
receives the same visible host answers solely as a mechanical zero-memory control.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request

import numpy as np

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import OpenAIDetectorBackend
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    freeze_weightless_followup,
)

MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"
SCHEMA = "shadowseed-real-stage1-exploratory-v2"
OUTPUT_SCHEMA = "shadowseed-real-stage1-recorded-observations-v2"
MAX_CASES = 2
TURNS_PER_CASE = 4
MAX_MODEL_CALLS = 24
MAX_EMBEDDING_CALLS = 48
MAX_ALL_TOKENS = 85000
MAX_OUTPUT_TOKENS = 1600
MAX_PROMPT_CHARS = 12500

HOST_INSTRUCTIONS = (
    "Je helpt bij een fictieve wetenschappelijke waarneming. Beantwoord de "
    "gestelde vraag helder met de op dat moment gegeven gegevens. Benoem "
    "onzekerheden zonder feiten of metingen te verzinnen. Geen vaste opmaak."
)
ORDINARY_INSTRUCTIONS = HOST_INSTRUCTIONS
DETECTOR_INSTRUCTIONS = (
    "Volg de instructies van de aangeleverde detectorprompt. "
    "Een mogelijke kandidaat is een onderzoeksvraag, geen vastgesteld feit. "
    "Geef NONE indien passend."
)


def _sha(data: Any) -> str:
    return sha256(json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def validate_fixture(data: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("invalid exploratory stage-1 fixture schema")
    if data.get("model") != MODEL or data.get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("pin the supported strong model and embedding model")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != MAX_CASES:
        raise ValueError("exactly two fictional scenarios required")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        cid = case.get("id")
        if not isinstance(cid, str) or not cid.isupper() or cid in ids:
            raise ValueError("case IDs must be unique uppercase labels")
        ids.add(cid)
        context = case.get("context")
        if not isinstance(context, str) or not 40 <= len(context) <= 2500:
            raise ValueError(f"{cid}: invalid opening context")
        turns = case.get("turns")
        if not isinstance(turns, list) or len(turns) != TURNS_PER_CASE:
            raise ValueError(f"{cid}: exactly four chronological turns required")
        if any(
            not isinstance(t, dict)
            or not isinstance(t.get("question"), str)
            or not 25 <= len(t["question"]) <= 700
            or any(field not in ("question", "new_observation") for field in t)
            for t in turns
        ):
            raise ValueError(f"{cid}: invalid turn request")
        for index, row in enumerate(turns):
            extra = row.get("new_observation")
            if not isinstance(extra, str) or (index and len(extra) < 20):
                raise ValueError(f"{cid}: every turn needs its own observation slot")
            if index == 0 and extra:
                raise ValueError("initial context belongs in context, not future feedback")
            if len(extra) > 1200:
                raise ValueError("observation too long")
        if any(k in case for k in ("ideal_question", "answer_key", "target_terms", "reward")):
            raise ValueError("do not put evaluator keys or target question hints in prompts")
    return cases


class BoundedProvider:
    """OpenAI Responses/Embeddings with shared hard caps and no retries.

    Caller supplies a credential from a scoped GitHub Environment. No secret
    values, request headers, raw HTTP exceptions or full provider envelopes
    appear in the persisted audit output.
    """

    def __init__(
        self, key: str, *, transport: Any = None,
        model_call_cap: int = MAX_MODEL_CALLS,
        embedding_call_cap: int = MAX_EMBEDDING_CALLS,
        all_token_cap: int = MAX_ALL_TOKENS,
        output_token_cap: int = MAX_OUTPUT_TOKENS,
    ):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("missing scoped OpenAI research credential")
        if (
            type(model_call_cap) is not int or not 1 <= model_call_cap <= 48
            or type(embedding_call_cap) is not int or not 1 <= embedding_call_cap <= 64
            or type(all_token_cap) is not int or not 5000 <= all_token_cap <= 160000
            or type(output_token_cap) is not int or not 800 <= output_token_cap <= 4096
        ):
            raise ValueError("invalid or excessive research provider cap")
        self.model_call_cap = model_call_cap
        self.embedding_call_cap = embedding_call_cap
        self.all_token_cap = all_token_cap
        self.output_token_cap = output_token_cap
        self._key = key
        self._transport = transport or urllib.request.urlopen
        self.model_calls = 0
        self.embedding_calls = 0
        self.total_tokens = 0
        self.events: list[dict[str, Any]] = []
        self._embedding_cache: dict[str, np.ndarray] = {}

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            "https://api.openai.com/v1/" + endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._transport(req, timeout=105) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code} at {endpoint}") from None
        except Exception as exc:
            raise RuntimeError(
                f"provider {type(exc).__name__} at {endpoint}"
            ) from None
        if not isinstance(result, dict):
            raise RuntimeError("provider returned invalid response type")
        return result

    def _consume(self, count: Any) -> int:
        if type(count) is not int or count < 0:
            raise RuntimeError("provider token usage is absent or invalid")
        self.total_tokens += count
        if self.total_tokens > self.all_token_cap:
            raise RuntimeError("hard combined provider-token cap exceeded")
        return count

    def generate(self, *, stage: str, case_id: str, prompt: str,
                 instructions: str) -> str:
        if self.model_calls >= self.model_call_cap:
            raise RuntimeError("hard model-call cap reached")
        if self.total_tokens > self.all_token_cap - (self.output_token_cap + 1200):
            raise RuntimeError("insufficient remaining token budget")
        if not isinstance(prompt, str) or not 1 <= len(prompt) <= MAX_PROMPT_CHARS:
            raise ValueError("invalid or oversized model prompt")
        self.model_calls += 1  # pessimistic count even if a request fails
        response = self._post("responses", {
            "model": MODEL,
            "instructions": instructions,
            "input": prompt,
            "max_output_tokens": self.output_token_cap,
            "reasoning": {"effort": "low"},
            "store": False,
        })
        usage = response.get("usage")
        if not isinstance(usage, dict):
            raise RuntimeError("model usage missing; cannot enforce budget")
        input_count = usage.get("input_tokens")
        output_count = usage.get("output_tokens")
        self._consume(input_count)
        self._consume(output_count)
        text = "\n".join(
            part["text"]
            for item in response.get("output", [])
            if isinstance(item, dict)
            for part in item.get("content", [])
            if isinstance(part, dict)
            and part.get("type") == "output_text"
            and isinstance(part.get("text"), str)
        ).strip()
        status = response.get("status")
        self.events.append({
            "kind": "model", "stage": stage, "case_id": case_id,
            "requested_model": MODEL, "returned_model": response.get("model"),
            "response_id": response.get("id"),
            "status": status, "prompt_sha256": _sha(prompt),
            "response_sha256": _sha(text),
            "input_tokens": input_count, "output_tokens": output_count,
        })
        print(json.dumps({
            "stage": stage, "case": case_id, "status": status,
            "model_calls": self.model_calls,
            "tokens_so_far": self.total_tokens,
        }), flush=True)
        if status != "completed" or not text:
            raise RuntimeError("model returned no complete visible text")
        return text

    def embed(self, text: str) -> np.ndarray:
        if not isinstance(text, str) or not text.strip() or len(text) > 8000:
            raise ValueError("invalid embedding input")
        if text in self._embedding_cache:
            return self._embedding_cache[text].copy()
        if self.embedding_calls >= self.embedding_call_cap:
            raise RuntimeError("hard embedding call cap reached")
        if self.total_tokens > self.all_token_cap - 2000:
            raise RuntimeError("insufficient embedding budget")
        self.embedding_calls += 1
        response = self._post("embeddings", {
            "model": EMBEDDING_MODEL, "input": [text],
        })
        data = response.get("data")
        if not isinstance(data, list) or len(data) != 1:
            raise RuntimeError("embedding cardinality mismatch")
        vector = np.asarray(data[0].get("embedding"), dtype=float)
        if vector.ndim != 1 or vector.size != 1536 or not np.isfinite(vector).all():
            raise RuntimeError("embedding dimension or value invalid")
        norm = np.linalg.norm(vector)
        if norm <= 0:
            raise RuntimeError("embedding cannot have zero norm")
        usage = response.get("usage")
        if not isinstance(usage, dict):
            raise RuntimeError("embedding token usage missing")
        self._consume(usage.get("total_tokens"))
        embedding = vector / norm
        self._embedding_cache[text] = embedding
        self.events.append({
            "kind": "embedding", "model": EMBEDDING_MODEL,
            "input_sha256": _sha(text), "tokens": usage["total_tokens"],
        })
        return embedding.copy()


class DetectorClientBridge:
    """Use the REAL current-pair OpenAIDetectorBackend, not a new detector."""

    def __init__(self, provider: BoundedProvider):
        self.provider = provider
        self.case_id = ""
        self.turn = -1

    def generate(self, prompt: str, *, max_new_tokens: int = 400, **_: Any) -> str:
        if max_new_tokens > self.provider.output_token_cap:
            raise ValueError("detector output request exceeds provider cap")
        return self.provider.generate(
            stage=f"detector_t{self.turn}", case_id=self.case_id,
            prompt=prompt, instructions=DETECTOR_INSTRUCTIONS,
        )


class NoneDetector:
    name = "control-explicit-NONE-no-provider"
    prompt_variant = "none"

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        return []


def _host_prompt(case: dict[str, Any], earlier: list[tuple[str, str]],
                 question: str, observation: str) -> str:
    parts = ["BEGIN FICTIEVE ONDERZOEKSSITUATIE", case["context"]]
    for index, (q, a) in enumerate(earlier):
        parts += [
            f"EERDERE VRAAG {index}: {q}",
            f"ZICHTBAAR ANTWOORD {index}: {a}",
        ]
    if observation:
        parts += ["NIEUWE EXTERNE WAARNEMING IN DEZE BEURT:", observation]
    parts += ["NIEUWE VRAAG:", question, "EINDE BESCHIKBARE INFORMATIE"]
    return "\n".join(parts)


def run_case(case: dict[str, Any], provider: BoundedProvider) -> dict[str, Any]:
    cid = case["id"]
    detector = OpenAIDetectorBackend(model_id=MODEL, prompt_variant="current_pair")
    client = DetectorClientBridge(provider)
    detector.client = client
    engine = ShadowseedEngine(
        detector_backend=detector,
        embedding_fn=provider.embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
        max_seeds_per_turn=3,
    )
    empty = ShadowseedEngine(
        detector_backend=NoneDetector(), embedding_backend="lexical",
        allow_toy_embedder=True, recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    history: list[tuple[str, str]] = []
    turn_log: list[dict[str, Any]] = []
    birth: dict[str, Any] | None = None
    last_checkpoint: dict[str, Any] | None = None
    ordinary_samples: list[str] = []
    for t, row in enumerate(case["turns"]):
        question = row["question"]
        incoming = row["new_observation"]
        # v2 research adapter correction: the host received case.context at T0.
        # Make that SAME original case description visible to the real current-
        # pair detector at T0. Later turns continue via the canonical bounded
        # clean conversation history; do not create a new detector or inject
        # the retained seed into normal answer generation.
        if t == 0:
            current_user = (
                "BEGIN FICTIEVE ONDERZOEKSSITUATIE\n"
                + case["context"] + "\nVRAAG: " + question
            )
        else:
            current_user = question + (
                "\nEXTERNE WAARNEMING: " + incoming if incoming else ""
            )
        prompt = _host_prompt(case, history, question, incoming)
        if t == 0:
            # Budget-relative ordinary selection sample, BEFORE detector or
            # seed exposure. No inference of internal absence from nonappearance.
            for replicate in (1, 2):
                ordinary_samples.append(provider.generate(
                    stage=f"t0_ordinary_replicate_{replicate}",
                    case_id=cid, prompt=prompt,
                    instructions=ORDINARY_INSTRUCTIONS,
                ))
        prepared = engine.prepare_turn(current_user)
        neutral = empty.prepare_turn(current_user)
        if prepared.model_context or prepared.surfaced_seed_ids or prepared.selected_seed_ids:
            raise RuntimeError("weightless context reached the ordinary host")
        if neutral.model_context or neutral.surfaced_seed_ids:
            raise RuntimeError("NONE control unexpectedly received seed context")
        answer = provider.generate(
            stage=f"host_t{t}", case_id=cid, prompt=prompt,
            instructions=HOST_INSTRUCTIONS,
        )
        client.case_id, client.turn = cid, t
        observed = engine.observe_turn(prepared, answer)
        control = empty.observe_turn(neutral, answer)
        if control["answer"] != observed["answer"]:
            raise RuntimeError("same-answer NONE comparison broke")
        if empty.inspect()["seeds"] or control.get("seeds_born_weightless"):
            raise RuntimeError("NONE control created shadow state")
        if birth is None:
            candidate_ids = [
                seed_id for seed_id in observed.get("seeds_born_weightless", [])
                if engine.export_state().get("born_turn", {}).get(seed_id) == t
            ]
            if candidate_ids:
                # Predeclared rule: first exact new seed, not post-hoc best seed.
                birth = freeze_canonical_weightless_birth(
                    engine, observed, candidate_ids[0]
                )
        else:
            last_checkpoint = freeze_weightless_followup(
                engine, birth, previous=last_checkpoint
            )
        history.append((current_user, answer))
        turn_log.append({
            "turn": t, "question": question,
            "new_observation": incoming,
            "host_answer": answer,
            "detector_raw_output": detector.last_raw_output,
            "canonical_turn_report": observed,
            "none_control_answer_identical": control["answer"] == answer,
            "first_seed_checkpoint": birth if birth and birth["session_turn"] == t else None,
            "followup_checkpoint": last_checkpoint,
        })
    if engine.inspect()["influence_records"]:
        raise RuntimeError("seed ever received an influence record")
    if engine.audit() != 0 or empty.audit() != 0:
        raise RuntimeError("unexpected authorized influence")
    seed_id = birth["seed_id"] if birth else None
    if seed_id:
        final = next(
            (s for s in engine.export_state()["manager"]["seeds"] if s["id"] == seed_id),
            None,
        )
        if final is None or final["weight"] != 0 or final["evidence_count"] != 0:
            raise RuntimeError("first seed lost its zero-authority boundary")
    return {
        "case_id": cid,
        "ordinary_t0_samples_before_detection": ordinary_samples,
        "turns": turn_log,
        "selected_first_seed_id": seed_id,
        "selected_first_seed_birth_turn": birth["session_turn"] if birth else None,
        "final_shadow_seed_count": len(engine.inspect()["seeds"]),
        "none_control_seed_count": len(empty.inspect()["seeds"]),
        "model_origin_inferred_from_api_receipts_not_internal_activations": True,
        "semantic_gap_validity_independently_reviewed": False,
        "new_later_inquiry_assessed": False,
        "q1_or_q2_effect_established": False,
    }


def run(document: dict[str, Any], provider: BoundedProvider) -> dict[str, Any]:
    cases = validate_fixture(document)
    result = {
        "schema": OUTPUT_SCHEMA,
        "status": "completed_exploratory_real_model_stage1_only",
        "model": MODEL, "embedding_model": EMBEDDING_MODEL,
        "feedback_contract": "investigator_provided_exogenous_future_turns",
        "G0": "NOT_PASSED",
        "q1_probability_or_internal_absence_proven": False,
        "q2_later_investigability_proven": False,
        "independent_human_review_completed": False,
        "confirmatory_trial": False,
        "research_adapter_context_revision": "t0_original_case_visible_to_host_and_current_pair_detector_v2",
        "cases": [],
    }
    for case in cases:
        result["cases"].append(run_case(case, provider))
    result["provider_audit"] = {
        "model_calls": provider.model_calls,
        "embedding_calls": provider.embedding_calls,
        "token_total": provider.total_tokens,
        "model_call_cap": provider.model_call_cap,
        "embedding_call_cap": provider.embedding_call_cap,
        "all_token_cap": provider.all_token_cap,
        "output_token_cap": provider.output_token_cap,
        "events": list(provider.events),
    }
    return result


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--fixture", required=True)
    cli.add_argument("--output", required=True)
    args = cli.parse_args()
    doc = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    validate_fixture(doc)
    key = os.environ.get("OPENAI_API_KEY", "")
    provider = BoundedProvider(key)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(doc, provider)
    except Exception as exc:
        # No provider text, exception body or secret is echoed to artifacts.
        destination.write_text(json.dumps({
            "schema": OUTPUT_SCHEMA,
            "status": "exploratory_run_incomplete",
            "failure_type": type(exc).__name__,
            "model_calls_attempted": provider.model_calls,
            "embedding_calls_attempted": provider.embedding_calls,
            "tokens_recorded": provider.total_tokens,
            "G0": "NOT_PASSED",
            "q1_or_q2_effect_established": False,
        }, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(
            f"exploratory live stage-1 stopped: {type(exc).__name__}"
        ) from None
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "model_calls": provider.model_calls,
        "embedding_calls": provider.embedding_calls,
        "recorded_tokens": provider.total_tokens,
        "cases": len(result["cases"]),
        "g0": result["G0"],
    }), flush=True)


if __name__ == "__main__":
    main()
