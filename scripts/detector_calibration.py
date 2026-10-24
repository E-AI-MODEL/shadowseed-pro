"""Compare the product detector prompt with a candidate prompt on live turns.

Each conversation of the suite runs through a live ``ShadowChatSession`` with
the product detector (``current_pair`` v0.6). At every detection call the same
item (question, draft answer, bounded context) is also sent to the candidate
prompt, so both prompts see identical input. Neither the candidate output nor
its seeds enter the session. Per turn and per prompt the script records the
raw output, the parsed candidates, which of them pass intake, and whether the
turn produced no admitted candidate at all.

``sample`` merges the run outputs of all shards and draws, per prompt, a
seeded random sample of at most ``--cap`` admitted candidates. The mixed sample
is written with the prompt hidden behind an id; the id-to-prompt key goes to a
separate file, so usefulness can be labelled without knowing the prompt.

Usage:
    python scripts/detector_calibration.py run --suite benchmarks/evidence_efficacy/study-1-suite.json \\
        --model qwen2.5:7b-instruct-q4_K_M --output calibration.json [--conversation EE01 ...]
    python scripts/detector_calibration.py sample --input shard-*.json \\
        --items review_items.json --key review_key.json [--cap 60] [--seed 20261024]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from shadowseed.chat import ShadowChatSession
from shadowseed.detection.model_detector import (
    _looks_like_fewshot_leak,
    _token_set,
    build_detection_prompt,
    parse_numbered_seeds_with_diagnostics,
)
from shadowseed.intake import is_atomic_seed

CANDIDATE_ID = "detector_current_pair_candidate_v0.7"

CANDIDATE_EXAMPLES = (
    "Whether the deadline already includes the review period.",
    "Which budget limit the user is working within.",
)

CANDIDATE_PROMPT = """
You read one user question and the draft answer to it. Note what is still open:
points the answer depends on but does not settle.

Look for:
- an assumption the answer makes without checking it;
- a case or condition the answer does not cover;
- a number, threshold or choice it leaves unspecified;
- information about the user's situation that the answer needs but was not given;
- a distinction the answer blurs.

Most practical answers leave at least one such point open. Answer NONE only
when the answer fully settles the question.

Write at most {max_seeds} open points, one short sentence per numbered line, in
the same language as the question. One open point per line. Do not answer it,
do not explain why it matters, and do not invent facts, names or numbers. Do
not repeat a point that the earlier conversation already settled.

Format example (different topic):
1. {example_1}
2. {example_2}

Earlier conversation (reference only):
{conversation_context}

Question:
{question}

Draft answer:
{answer}

Open points:
""".strip()

_EXAMPLE_TOKENS = tuple(_token_set(example) for example in CANDIDATE_EXAMPLES)


def build_candidate_prompt(item: dict[str, Any], max_seeds: int) -> str:
    return CANDIDATE_PROMPT.format(
        max_seeds=max_seeds,
        example_1=CANDIDATE_EXAMPLES[0],
        example_2=CANDIDATE_EXAMPLES[1],
        conversation_context=(
            str(item.get("conversation_context") or "").strip() or "NONE"
        ),
        question=str(item.get("question") or "").strip(),
        answer=str(item.get("text") or "").strip(),
    )


def _candidate_leak(seed: str) -> bool:
    tokens = _token_set(seed)
    if not tokens:
        return False
    return any(
        len(tokens & ex) / len(tokens | ex) >= 0.7 for ex in _EXAMPLE_TOKENS if ex
    )


def evaluate(raw: str, text: str, max_seeds: int, *, candidate: bool) -> dict[str, Any]:
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        raw, max_seeds=max_seeds, source_text=text
    )
    leaks = [seed for seed in seeds if candidate and _candidate_leak(seed)]
    seeds = [seed for seed in seeds if seed not in leaks]
    admitted = [seed for seed in seeds if is_atomic_seed(seed)]
    return {
        "raw": raw[:2000],
        "diagnostics": diagnostics,
        "parsed": seeds,
        "example_leaks": leaks,
        "admitted": admitted,
        "empty": not admitted,
    }


def run_conversation(
    conversation: dict[str, Any], session: ShadowChatSession, max_new_tokens: int
) -> dict[str, Any]:
    detector = session.detector
    original = detector.detect_seeds
    records: list[dict[str, Any]] = []

    def paired(item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        seeds = original(item, max_seeds=max_seeds)
        text = str(item.get("text") or "").strip()
        product_raw = str(getattr(detector, "last_raw_output", "") or "")
        candidate_raw = detector.client.generate(
            build_candidate_prompt(item, max_seeds), max_new_tokens=max_new_tokens
        )
        records.append(
            {
                "question": str(item.get("question") or ""),
                "answer": text[:3000],
                "product": evaluate(product_raw, text, max_seeds, candidate=False),
                "candidate": evaluate(candidate_raw, text, max_seeds, candidate=True),
            }
        )
        return seeds

    detector.detect_seeds = paired  # type: ignore[method-assign]
    turns = []
    for index, turn in enumerate(conversation["turns"]):
        before = len(records)
        session.turn(str(turn["question"]))
        for record in records[before:]:
            turns.append({"turn": index, **record})
    return {"conversation_id": conversation["id"], "turns": turns}


def summarize(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    turns = [t for c in conversations for t in c["turns"]]
    for arm in ("product", "candidate"):
        summary[arm] = {
            "detections": len(turns),
            "empty_detections": sum(t[arm]["empty"] for t in turns),
            "explicit_none": sum(
                bool(t[arm]["diagnostics"]["explicit_none"]) for t in turns
            ),
            "parsed": sum(len(t[arm]["parsed"]) for t in turns),
            "admitted": sum(len(t[arm]["admitted"]) for t in turns),
            "example_leaks": sum(len(t[arm]["example_leaks"]) for t in turns),
        }
    return summary


def review_sample(
    conversations: list[dict[str, Any]], *, cap: int, seed: int
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Draw at most ``cap`` admitted candidates per prompt and mix them blind."""

    rng = random.Random(seed)
    items, key = [], {}
    for arm in ("product", "candidate"):
        pool = []
        for conversation in conversations:
            for turn in conversation["turns"]:
                for seed_text in turn[arm]["admitted"]:
                    item_id = hashlib.sha256(
                        f"{conversation['conversation_id']}|{turn['turn']}|{arm}|{seed_text}".encode()
                    ).hexdigest()[:16]
                    pool.append(
                        {
                            "id": item_id,
                            "conversation_id": conversation["conversation_id"],
                            "turn": turn["turn"],
                            "question": turn["question"],
                            "answer": turn["answer"],
                            "candidate": seed_text,
                        }
                    )
        pool.sort(key=lambda item: item["id"])
        chosen = rng.sample(pool, cap) if len(pool) > cap else pool
        for item in chosen:
            key[item["id"]] = arm
        items.extend(chosen)
    items.sort(key=lambda item: hashlib.sha256(item["id"].encode()).hexdigest())
    return items, key


def _run(args: argparse.Namespace) -> int:
    suite = json.loads(args.suite.read_text(encoding="utf-8"))
    conversations = [
        c
        for c in suite["conversations"]
        if not args.conversation or c["id"] in args.conversation
    ]
    results = []
    for conversation in conversations:
        session = ShadowChatSession(
            backend="ollama",
            model_id=args.model,
            runtime_mode="live",
            recurrence_recognizer="embedding",
            # Only recurrence uses the embedder; this run measures detection.
            allow_toy_embedder=True,
        )
        # CPU runners can need longer than the product default per generation.
        for backend in (session.model, session.detector):
            client = getattr(backend, "client", None)
            if client is not None and hasattr(client, "timeout"):
                client.timeout = 900.0
        results.append(run_conversation(conversation, session, args.max_new_tokens))
        print(f"{conversation['id']}: {summarize(results[-1:])}", flush=True)

    payload = {
        "schema": "ssl-detector-calibration-v1",
        "model": args.model,
        "suite": str(args.suite),
        "candidate_prompt_id": CANDIDATE_ID,
        "candidate_prompt_sha256": hashlib.sha256(
            CANDIDATE_PROMPT.encode()
        ).hexdigest(),
        "product_prompt_sha256": hashlib.sha256(
            build_detection_prompt("", variant="current_pair", question="q").encode()
        ).hexdigest(),
        "summary": summarize(results),
        "conversations": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"]))
    return 0


def _sample(args: argparse.Namespace) -> int:
    conversations = []
    for path in args.input:
        conversations.extend(
            json.loads(path.read_text(encoding="utf-8"))["conversations"]
        )
    items, key = review_sample(conversations, cap=args.cap, seed=args.seed)
    args.items.write_text(
        json.dumps({"items": items}, indent=2) + "\n", encoding="utf-8"
    )
    args.key.write_text(json.dumps({"key": key}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summarize(conversations), "review_items": len(items)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--suite", required=True, type=Path)
    run.add_argument("--model", required=True)
    run.add_argument("--conversation", action="append", default=[])
    run.add_argument("--max-new-tokens", type=int, default=400)
    run.add_argument("--output", required=True, type=Path)
    sample = commands.add_parser("sample")
    sample.add_argument("--input", required=True, type=Path, nargs="+")
    sample.add_argument("--items", required=True, type=Path)
    sample.add_argument("--key", required=True, type=Path)
    sample.add_argument("--cap", type=int, default=60)
    sample.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args(argv)
    return _run(args) if args.command == "run" else _sample(args)


if __name__ == "__main__":
    raise SystemExit(main())
