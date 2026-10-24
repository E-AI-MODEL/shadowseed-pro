"""Bounded LIVE model feasibility pilot: retention of model-originated candidates.

EXPLORATORY ONLY. A real model writes a first answer, alternate hypotheses,
ordinary notes, a compressed summary and six follow-up replies. New evidence
is withheld from *all* T0 prompts. Existing SSLManager and VectorStore supply
weightless candidate birth and embedding-based retrieval. This is not Q1/Q2
validation, a sealed holdout, or a matched-token causal comparison.

All inputs are fictional. Secrets are only read from the GitHub Environment
by the action; no secret, token or provider exception body is written to output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

import numpy as np

from shadowseed.manager import CandidateType, SSLManager, SeedOrigin
from shadowseed.vectorstore import create_vector_store


SCHEMA = "shadowseed-live-compression-exploratory-v0"
RESULT_SCHEMA = "shadowseed-live-compression-pilot-v0"
MAX_CASES = 3
MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_MODEL_CALLS = 30
MAX_EMBEDDING_CALLS = 3
MAX_COMBINED_TOKENS = 110000
OUTPUT_LIMIT = 2200
MEMORY_SLOTS = 2
MEMORY_WORDS = 22
TOP_K = 1
THRESHOLD = 0.30
ARMS = (
    "compressed_only", "ordinary_notes", "shadowseeds",
    "candidate_ablation", "deliberate_recall", "full_history",
)
SYSTEM = (
    "You are analyzing a fictional research scenario. Distinguish proposals "
    "from evidence; do not claim certainty. Follow the user's task. "
    "Return only a valid JSON object, without markdown."
)
NEUTRAL = (
    "Administrative placeholder: check the document version and update "
    "the meeting agenda before publishing."
)


def validate_cases(data: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unsupported case schema")
    if data.get("model") != MODEL or data.get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("model pins do not match the approved pilot constants")
    cases = data.get("items")
    if not isinstance(cases, list) or len(cases) != MAX_CASES:
        raise ValueError("exactly three synthetic cases are required")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        cid = case.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Z_]{3,40}", cid) or cid in ids:
            raise ValueError("case ids must be unique uppercase identifiers")
        ids.add(cid)
        for field in ("initial_question", "initial_context", "late_event", "followup_question"):
            text = case.get(field)
            if not isinstance(text, str) or len(text.strip()) < 30 or len(text) > 5000:
                raise ValueError(f"{cid}: invalid {field}")
        if not isinstance(case.get("no_opportunity"), bool):
            raise ValueError(f"{cid}: no_opportunity must be boolean")
        if not isinstance(case.get("target_terms"), list) or any(
            not isinstance(t, str) or not 2 <= len(t) <= 35
            for t in case["target_terms"]
        ):
            raise ValueError(f"{cid}: invalid keyword scoring hints")
        if case["no_opportunity"] and case["target_terms"]:
            raise ValueError(f"{cid}: negative controls must have no target terms")
    return cases


def _json(text: str) -> dict[str, Any]:
    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else {}
    except (ValueError, TypeError):
        return {}


def _field(parsed: dict[str, Any], name: str, max_words: int = 200) -> str | None:
    value = parsed.get(name)
    if not isinstance(value, str) or not value.strip():
        return None
    words = value.strip().split()
    return " ".join(words[:max_words])


def _memory_list(parsed: dict[str, Any], name: str) -> list[str]:
    value = parsed.get(name)
    if not isinstance(value, list) or len(value) != MEMORY_SLOTS:
        return []
    if any(not isinstance(v, str) or not v.strip() for v in value):
        return []
    return [" ".join(v.strip().split()[:MEMORY_WORDS]) for v in value]


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _save(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.with_suffix(path.suffix + ".tmp")
    target.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    target.replace(path)


class Provider:
    """No retries. Hard call caps and per-response usage recording."""

    def __init__(self, key: str, *, transport: Callable | None = None):
        if not key.strip():
            raise ValueError("missing GitHub Environment API credential")
        self.key = key
        self.transport = transport or urllib.request.urlopen
        self.model_calls = 0
        self.embedding_calls = 0
        self.token_count = 0
        self.events: list[dict[str, Any]] = []

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            "https://api.openai.com/v1/" + endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.transport(request, timeout=105) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code} at {endpoint}") from None
        except Exception as exc:
            raise RuntimeError(f"provider {type(exc).__name__} at {endpoint}") from None
        if not isinstance(data, dict):
            raise RuntimeError("invalid provider response envelope")
        return data

    def generate(self, stage: str, case_id: str, prompt: str) -> dict[str, Any]:
        if self.model_calls >= MAX_MODEL_CALLS:
            raise RuntimeError("model call cap reached")
        if self.token_count >= MAX_COMBINED_TOKENS - (OUTPUT_LIMIT + 6000):
            raise RuntimeError("combined token budget nearly exhausted")
        if len(prompt) > 16000:
            raise ValueError("prompt length bound exceeded")
        self.model_calls += 1
        result = self._post("responses", {
            "model": MODEL, "instructions": SYSTEM, "input": prompt,
            "max_output_tokens": OUTPUT_LIMIT,
            "reasoning": {"effort": "low"}, "store": False,
        })
        usage = result.get("usage") or {}
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        if inp < 0 or out < 0:
            raise RuntimeError("invalid token counters")
        self.token_count += inp + out
        text = "\n".join(
            part.get("text", "")
            for item in result.get("output", []) if isinstance(item, dict)
            for part in item.get("content", []) if isinstance(part, dict)
            if part.get("type") == "output_text" and isinstance(part.get("text"), str)
        )
        event = {"stage": stage, "case": case_id,
                 "model": result.get("model", MODEL),
                 "status": result.get("status"),
                 "usage": {"input_tokens": inp, "output_tokens": out},
                 "text": text,
                 "parsed_json": bool(_json(text)),
                 "incomplete_details": result.get("incomplete_details")}
        self.events.append(event)
        print(json.dumps({
            "case": case_id, "stage": stage, "status": event["status"],
            "in": inp, "out": out, "parsed": event["parsed_json"],
            "calls": self.model_calls,
        }), flush=True)
        if self.token_count > MAX_COMBINED_TOKENS:
            raise RuntimeError("combined token cap exceeded; stop immediately")
        return event

    def embed(self, case_id: str, texts: list[str]) -> dict[str, np.ndarray]:
        if self.embedding_calls >= MAX_EMBEDDING_CALLS:
            raise RuntimeError("embedding call cap reached")
        if not texts or len(texts) > 20 or any(not t or len(t) > 1800 for t in texts):
            raise ValueError("invalid embedding batch")
        self.embedding_calls += 1
        result = self._post("embeddings", {
            "model": EMBEDDING_MODEL, "input": texts,
        })
        data = result.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise RuntimeError("embedding response cardinality mismatch")
        vectors: dict[str, np.ndarray] = {}
        for item in data:
            i = item.get("index")
            if type(i) is not int or i < 0 or i >= len(texts) or texts[i] in vectors:
                raise RuntimeError("embedding response invalid index")
            vec = np.asarray(item.get("embedding"), dtype=float)
            if vec.ndim != 1 or vec.size != 1536 or not np.all(np.isfinite(vec)):
                raise RuntimeError("embedding response invalid vector")
            norm = float(np.linalg.norm(vec))
            if norm <= 0:
                raise RuntimeError("embedding response zero norm")
            vectors[texts[i]] = vec / norm
        if len(vectors) != len(set(texts)):
            raise RuntimeError("embedding response missing vectors")
        usage = result.get("usage") or {}
        self.token_count += int(usage.get("total_tokens") or 0)
        self.events.append({"stage": "embeddings", "case": case_id,
                            "model": EMBEDDING_MODEL,
                            "usage": {"total_tokens": int(usage.get("total_tokens") or 0)},
                            "texts_count": len(texts)})
        return vectors


def _initial_prompt(case: dict[str, Any]) -> str:
    return (
        "Beantwoord de vraag voorlopig, zonder een definitieve oorzaak te claimen. "
        'Antwoord als JSON: {"answer":"maximaal 100 woorden"}.\n'
        "BEGIN FICTIEVE CASUS\n" + case["initial_context"]
        + "\nVRAAG: " + case["initial_question"] + "\nEND CASUS"
    )


def _preupdate_prompt(case: dict[str, Any], draft: str, stage: str) -> str:
    prefix = (
        "Fictieve situatie. Alleen de volgende informatie is nu bekend; "
        "je krijgt GEEN latere gegevens.\n"
        + case["initial_context"] + "\nVRAAG: " + case["initial_question"]
        + "\nEERSTE ANTWOORD: " + draft + "\n"
    )
    if stage == "candidates":
        return prefix + (
            'Noem exact twee afzonderlijk onderzoekbare ALTERNATIEVE hypotheses '
            'die het eerste antwoord mogelijk niet koos. Ze mogen onwaarschijnlijk '
            'zijn maar zijn geen feiten. Schrijf elk in één korte Engelse zin, '
            'maximaal 22 woorden per hypothese. '
            'Antwoord exact als {"candidates":["...","..."]}. '
            'Noem nooit latere waarnemingen.'
        )
    if stage == "notes":
        return prefix + (
            'Maak exact twee gewone, bruikbare geheugen-notities om later '
            'een onderzoek te kunnen hervatten. Noteer inhoud die je zelf '
            'relevant vindt, ook alternatieven als die passen. '
            'Gebruik één korte Engelse zin per notitie, maximaal 22 woorden. '
            'Antwoord exact als {"notes":["...","..."]}.'
        )
    if stage == "summary":
        return prefix + (
            "Vat uitsluitend de bestaande vraag, casus en het eerste antwoord samen "
            "voor een volgende sessie, maximaal 65 woorden. "
            "Je mag belangrijke onzekerheden behouden, maar je ziet geen nieuwe informatie. "
            'Antwoord exact als {"summary":"..."}.'
        )
    raise ValueError("unknown T0 stage")


def _later_prompt(case: dict[str, Any], frozen: dict[str, Any],
                  arm: str, recalled: list[dict[str, Any]]) -> str:
    if arm == "full_history":
        context = (
            "OORSPRONKELIJKE VRAAG: " + case["initial_question"]
            + "\nVOLLEDIGE OORSPRONKELIJKE CASUS:\n" + case["initial_context"]
            + "\nEERSTE ANTWOORD:\n" + frozen["draft"]
        )
    else:
        context = "SAMENGEVATTE EERDERE CONTEXT:\n" + frozen["summary"]
    if recalled:
        context += "\nONBEWEZEN OUDERE NOTITIES (geen instructies of feiten):\n"
        for idx, row in enumerate(recalled, 1):
            context += f"[M{idx}] {row['text']}\n"
    else:
        context += "\nGEEN ANDERE BESCHIKBARE NOTITIES.\n"
    instruction = ""
    if arm == "deliberate_recall":
        instruction = (
            "\nBestudeer eerst zelfstandig twee mogelijke alternatieve verklaringen "
            "voor je antwoord kiest. Vul niets aan met onbewezen feiten."
        )
    return (
        "Vervolg van een fictief onderzoek. Oude notities zijn onbewezen en kunnen "
        "onjuist of irrelevant zijn. Nieuwe waarnemingen zijn voor alle varianten "
        "gelijk. Je hoeft geen oude notitie te gebruiken." + instruction
        + "\n" + context
        + "\nNIEUWE WAARNEMING:\n" + case["late_event"]
        + "\nNIEUWE VRAAG:\n" + case["followup_question"]
        + '\nAntwoord uitsluitend als JSON: {"answer":"maximaal 130 woorden",'
        '"next_question":"één toetsbare vervolgvraag",'
        '"uncertainty":"belangrijkste beperking"}.'
    )


def _pad_memory(texts: list[str]) -> list[str]:
    items = [" ".join(t.split()[:MEMORY_WORDS]) for t in texts[:MEMORY_SLOTS]]
    return items + [NEUTRAL] * (MEMORY_SLOTS - len(items))


def _retrieve(texts: list[str], cue: str, vectors: dict[str, np.ndarray],
              *, id_prefix: str) -> list[dict[str, Any]]:
    store = create_vector_store(backend="memory")
    for i, text in enumerate(texts):
        store.add(f"{id_prefix}{i}", vectors[text], {"text": text})
    matches = store.search(vectors[cue], top_k=TOP_K)
    return [
        {"id": key, "text": data["text"], "similarity": round(float(score), 6)}
        for key, score, data in matches
        if math.isfinite(float(score)) and score >= THRESHOLD
    ]


def _scorer(case: dict[str, Any], text: str) -> dict[str, Any]:
    lower = text.lower()
    if case["no_opportunity"]:
        forbidden = ("warehouse", "supplier", "magazijn", "leverancier",
                     "vrachtwagen", "customs")
        hits = [term for term in forbidden if term in lower]
        return {"negative_context_intrusions": hits}
    hints = case["target_terms"]
    return {"exploratory_keyword_matches": [x for x in hints if x.lower() in lower],
            "not_an_independent_quality_score": True}


def _t0(case: dict[str, Any], provider: Provider) -> dict[str, Any]:
    draft_event = provider.generate("T0_draft", case["id"], _initial_prompt(case))
    draft = _field(_json(draft_event["text"]), "answer", 135)
    if draft is None:
        raise RuntimeError(f"{case['id']}: unparseable draft; no fabricated baseline")
    candidates_event = provider.generate(
        "T0_candidates", case["id"], _preupdate_prompt(case, draft, "candidates")
    )
    notes_event = provider.generate(
        "T0_notes", case["id"], _preupdate_prompt(case, draft, "notes")
    )
    summary_event = provider.generate(
        "T0_compression", case["id"], _preupdate_prompt(case, draft, "summary")
    )
    candidate_texts = _memory_list(_json(candidates_event["text"]), "candidates")
    note_texts = _memory_list(_json(notes_event["text"]), "notes")
    summary = _field(_json(summary_event["text"]), "summary", 65)
    return {
        "case_id": case["id"], "draft": draft, "candidates": candidate_texts,
        "ordinary_notes": note_texts, "summary": summary,
        "candidate_valid": len(candidate_texts) == MEMORY_SLOTS,
        "notes_valid": len(note_texts) == MEMORY_SLOTS,
        "compression_valid": summary is not None,
        "candidate_sha256": _sha(candidate_texts),
        "t0_events": [e["stage"] for e in (
            draft_event, candidates_event, notes_event, summary_event
        )],
        "is_investigator_created_case": True,
        "late_evidence_in_t0": False,
    }


def _t2(case: dict[str, Any], frozen: dict[str, Any],
        provider: Provider) -> dict[str, Any]:
    if not frozen["compression_valid"]:
        return {"case_id": case["id"], "status": "skipped_invalid_compression"}
    candidate_texts = _pad_memory(frozen["candidates"])
    note_texts = _pad_memory(frozen["ordinary_notes"])
    sham_texts = [
        "Check the meeting agenda and archive location before the next session.",
        "Review the font size and meeting room booking administrative paperwork.",
    ]
    # Ablate the FIRST candidate, chosen at T0, before any T2 search or outcomes.
    ablated_texts = list(candidate_texts)
    ablated_texts[0] = NEUTRAL
    cue = case["late_event"] + "\n" + case["followup_question"]
    unique_texts = list(dict.fromkeys(
        [cue, NEUTRAL] + candidate_texts + note_texts + sham_texts + ablated_texts
    ))
    vectors = provider.embed(case["id"], unique_texts)
    manager = SSLManager(embedding_fn=lambda s: vectors[s])
    canonical_ids = []
    for text in frozen["candidates"]:
        seed_id = manager.add_or_update_seed(
            text, deduplicate=False,
            origin=SeedOrigin(
                candidate_type=CandidateType.ALTERNATIVE_HYPOTHESIS,
                detection_basis="model_generated_T0_pre_update",
                context_ref="synthetic:" + case["id"] + ":T0",
            )
        )
        seed = manager.get_seed(seed_id)
        if seed.weight != 0.0 or seed.evidence_count != 0:
            raise RuntimeError("candidate was assigned evidence or weight")
        canonical_ids.append(seed_id)
    if manager.gate_events:
        raise RuntimeError("no Gate call permitted in feasibility pilot")

    recovered = {
        "ordinary_notes": _retrieve(note_texts, cue, vectors, id_prefix="N"),
        "shadowseeds": _retrieve(candidate_texts, cue, vectors, id_prefix="S"),
        "candidate_ablation": _retrieve(ablated_texts, cue, vectors, id_prefix="E"),
        "sham_notes": _retrieve(sham_texts, cue, vectors, id_prefix="X"),
    }
    observations: dict[str, Any] = {}
    for arm in ARMS:
        # Neutral memory fills the two available slots for compressed/no-memory
        # and deliberate-recall arms, but not the unmatched full-history control.
        if arm == "ordinary_notes":
            recalled = recovered["ordinary_notes"]
        elif arm == "shadowseeds":
            recalled = recovered["shadowseeds"]
        elif arm == "candidate_ablation":
            recalled = recovered["candidate_ablation"]
        else:
            recalled = []
        prompt = _later_prompt(case, frozen, arm, recalled)
        event = provider.generate("T2_" + arm, case["id"], prompt)
        parsed = _json(event["text"])
        answer = _field(parsed, "answer", 160)
        question = _field(parsed, "next_question", 100)
        observations[arm] = {
            "status": event["status"], "parsed_json": answer is not None,
            "recalled": recalled, "prompt_sha256": hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(), "prompt_characters": len(prompt),
            "model_text": event["text"], "answer": answer,
            "next_question": question,
            "uncertainty": _field(parsed, "uncertainty", 100),
            "exploratory_surface_metric": _scorer(case, answer or ""),
            "usage": event["usage"],
        }
    return {
        "case_id": case["id"], "status": "completed_exploratory_followup",
        "no_opportunity": case["no_opportunity"],
        "canonical_seed_ids": canonical_ids,
        "candidate_weightless": all(x.weight == 0.0 for x in manager.seeds.values()),
        "gate_events": len(manager.gate_events),
        "embedding_model": EMBEDDING_MODEL, "retrieval_threshold": THRESHOLD,
        "top_k": TOP_K, "mechanical_memory_slots": MEMORY_SLOTS,
        "memory_word_cap": MEMORY_WORDS,
        "ablation_precommitted": "first T0 candidate, replaced by neutral text",
        "the_ablation_is_not_blind_independent_efficacy": True,
        "retrieval": recovered, "arms": observations,
    }


def run(document: dict[str, Any], *, provider: Provider,
        out_dir: Path, fixture_sha: str) -> dict[str, Any]:
    cases = validate_cases(document)
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA, "status": "running",
        "claim": "engineering pilot only; Q1 and Q2 NOT measured or established",
        "fixture_sha256": fixture_sha, "model": MODEL,
        "embedding_model": EMBEDDING_MODEL, "caps": {
            "model_calls": MAX_MODEL_CALLS, "embedding_calls": MAX_EMBEDDING_CALLS,
            "max_combined_tokens": MAX_COMBINED_TOKENS,
            "max_output_tokens_per_call": OUTPUT_LIMIT,
        },
        "limitations": [
            "3 investigator-authored, visible, synthetic cases, not independent holdouts",
            "candidate generator and ordinary notes are additional model calls",
            "memory slots/word caps NOT matched total tokens or information",
            "semantic retrieval uses precommitted threshold but has no proven calibration",
            "simple keyword mention is not correctness, causal benefit, or novel inquiry",
            "no human blinded meaningfulness review and no controlled context-window pressure",
            "the independent G0 review ledger remains unfilled",
        ],
        "t0": [], "t2": [], "errors": [],
    }
    def checkpoint() -> None:
        result["usage"] = {
            "model_calls": provider.model_calls,
            "embedding_calls": provider.embedding_calls,
            "combined_tokens": provider.token_count,
        }
        result["event_log"] = provider.events
        _save(out_dir / "result.json", result)

    checkpoint()
    try:
        # First freeze ALL baseline/alternative/note/summary artifacts, without
        # revealing any later evidence to model prompts. Then open the T2 phase.
        for case in cases:
            frozen = _t0(case, provider)
            result["t0"].append(frozen)
            checkpoint()
        _save(out_dir / "frozen-t0.json", {
            "schema": RESULT_SCHEMA, "stage": "all_T0_complete_before_T2",
            "fixture_sha256": fixture_sha,
            "frozen": result["t0"], "sha256": _sha(result["t0"]),
        })
        for case, frozen in zip(cases, result["t0"]):
            result["t2"].append(_t2(case, frozen, provider))
            checkpoint()
        result["status"] = (
            "completed_exploratory_not_efficacy"
            if all(x.get("status") == "completed_exploratory_followup"
                   for x in result["t2"])
            else "partial_invalid_compression"
        )
    except Exception as exc:
        # Never write exception message: provider exceptions could include
        # request metadata. Only a safe class and fixed note are retained.
        result["status"] = "incomplete_stop"
        result["errors"].append({
            "type": type(exc).__name__,
            "note": "stopped without retry; inspect step-level status and provider usage",
        })
    finally:
        checkpoint()
    print(json.dumps({
        "final_status": result["status"], "cases_frozen": len(result["t0"]),
        "cases_followup": len(result["t2"]),
        "model_calls": provider.model_calls,
        "embedding_calls": provider.embedding_calls,
        "token_count": provider.token_count,
    }), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded live synthetic research pilot")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.cases.read_bytes()
    document = json.loads(raw)
    validate_cases(document)
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("Live model run blocked: configured environment credential absent")
    provider = Provider(key)
    result = run(
        document, provider=provider, out_dir=args.out_dir,
        fixture_sha=hashlib.sha256(raw).hexdigest(),
    )
    if result["status"] != "completed_exploratory_not_efficacy":
        raise SystemExit("Pilot incomplete. See preserved artifacts; no efficacy claim.")


if __name__ == "__main__":
    main()
