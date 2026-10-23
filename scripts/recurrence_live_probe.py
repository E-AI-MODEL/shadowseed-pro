"""Run live product sessions and measure whether recurrence builds up.

Each conversation of the suite runs through a live ``ShadowChatSession`` with the
product defaults (evidence_backed Gate, cluster recurrence) and the chosen
``recurrence_recognizer``. The probe records, per conversation, how many seeds
were born, how many clusters recurred in two or more and three or more turns,
the recognition decisions and failures, and the time spent per turn and per
recognition call. No evidence is submitted, so nothing can gain authority:
this measures memory over time, not answer quality.

Usage:
    python scripts/recurrence_live_probe.py --suite benchmarks/evidence_efficacy/study-1-suite.json \\
        --model qwen2.5:7b-instruct-q4_K_M --recognizer model --output probe.json \\
        [--conversation EE01 ...]
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

from shadowseed.chat import ShadowChatSession

RECOGNITION_PREFIX = "You keep track of open questions"


def _summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "median_s": None, "max_s": None}
    return {
        "count": len(values),
        "median_s": round(statistics.median(values), 2),
        "max_s": round(max(values), 2),
    }


def run_conversation(conversation: dict[str, Any], session: ShadowChatSession) -> dict[str, Any]:
    recognition_seconds: list[float] = []
    original = session.model.generate_messages

    def timed(messages: list[dict[str, str]]) -> str:
        started = time.perf_counter()
        try:
            return original(messages)
        finally:
            if str(messages[-1].get("content", "")).startswith(RECOGNITION_PREFIX):
                recognition_seconds.append(time.perf_counter() - started)

    session.model.generate_messages = timed  # type: ignore[method-assign]

    turns = []
    turn_seconds: list[float] = []
    for index, turn in enumerate(conversation["turns"]):
        events_before = len(session.manager.event_log)
        started = time.perf_counter()
        report = session.turn(str(turn["question"]))
        turn_seconds.append(time.perf_counter() - started)
        new_events = session.manager.event_log[events_before:]
        detector = session.detector
        turns.append(
            {
                "turn": index,
                "detector_raw": str(getattr(detector, "last_raw_output", "") or "")[:1200],
                "detector_diagnostics": getattr(detector, "last_parse_diagnostics", None),
                "born": len(report.get("seeds_born_weightless", [])),
                "surfaced": len(report.get("surfaced_seed_ids", [])),
                "events": dict(Counter(event.event_type for event in new_events)),
            }
        )

    clusterer = session.clusterer
    recurrence = (
        [clusterer.recurrence(i) for i in range(len(clusterer.centroids))] if clusterer else []
    )
    recurring = []
    if clusterer is not None:
        for cluster_id, count in enumerate(recurrence):
            if count >= 2:
                recurring.append({"recurrence": count, "members": clusterer.members[cluster_id]})
    recognized = [
        event.detail for event in session.manager.event_log if event.event_type == "recurrence_recognized"
    ]
    failures = [
        event.detail for event in session.manager.event_log
        if event.event_type == "recurrence_recognition_failed"
    ]
    return {
        "conversation_id": conversation["id"],
        "domain": conversation.get("domain"),
        "seeds": len(session.manager.seeds),
        "clusters": len(recurrence),
        "recurring_2plus": sum(count >= 2 for count in recurrence),
        "recurring_3plus": sum(count >= 3 for count in recurrence),
        "max_recurrence": max(recurrence, default=0),
        "weight_above_zero": sum(seed.weight > 0 for seed in session.manager.seeds.values()),
        "recognition": {
            "decisions": len(recognized),
            # A refused claim is logged with its cluster but starts a new one.
            "repeats": sum(
                d.get("repeats_cluster") is not None and not d.get("refused_below_floor")
                for d in recognized
            ),
            "refused_below_floor": sum(bool(d.get("refused_below_floor")) for d in recognized),
            "failures": len(failures),
            "failure_reasons": dict(Counter(str(d.get("reason")) for d in failures)),
        },
        "timing": {
            "turn": _summary(turn_seconds),
            "recognition_call": _summary(recognition_seconds),
        },
        "recurring_clusters": recurring,
        "turns": turns,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--recognizer", choices=("model", "embedding"), required=True)
    parser.add_argument("--embedding-backend", default="ollama")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--conversation", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    suite = json.loads(args.suite.read_text(encoding="utf-8"))
    conversations = [
        c for c in suite["conversations"] if not args.conversation or c["id"] in args.conversation
    ]
    results = []
    for conversation in conversations:
        session = ShadowChatSession(
            backend="ollama",
            model_id=args.model,
            embedding_backend=args.embedding_backend,
            embedding_model=args.embedding_model,
            runtime_mode="live",
            recurrence_recognizer=args.recognizer,
        )
        # CPU runners can need longer than the product default per generation.
        for backend in (session.model, session.detector):
            client = getattr(backend, "client", None)
            if client is not None and hasattr(client, "timeout"):
                client.timeout = 900.0
        results.append(run_conversation(conversation, session))
        print(
            f"{conversation['id']}: seeds={results[-1]['seeds']} "
            f"recurring2+={results[-1]['recurring_2plus']} 3+={results[-1]['recurring_3plus']} "
            f"recognition={results[-1]['recognition']}",
            flush=True,
        )
    totals = {
        key: sum(r[key] for r in results)
        for key in ("seeds", "clusters", "recurring_2plus", "recurring_3plus", "weight_above_zero")
    }
    payload = {
        "schema": "ssl-recurrence-live-probe-v1",
        "model": args.model,
        "recognizer": args.recognizer,
        "embedding": {"backend": args.embedding_backend, "model": args.embedding_model},
        "suite": str(args.suite),
        "totals": totals,
        "conversations": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"recognizer": args.recognizer, "totals": totals}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
