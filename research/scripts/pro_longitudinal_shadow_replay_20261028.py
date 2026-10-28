"""Source-frozen, zero-provider-call chronological Shadowseed Pro replay.

Read an archived 27 October source, not a new LLM run. The *real* Pro engine
receives original user inputs and host answers; the detector is replayed
byte-for-byte at the candidate-list boundary. The deterministic embedding is
a deliberately *toy* instrument, unsuitable for semantic novelty claims.

Output is aggregate only: never publish host answers or candidate contents.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
from shadowseed import ShadowseedEngine

SOURCE_ARTIFACT_ID = 12754935105
ORIGINAL_SHA = "0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf"
DIM = 128


def toy_embedding(text: str) -> np.ndarray:
    """Deterministic lexical sign-hash; not a semantic embedding or neural probe."""
    import re
    vec = np.zeros(DIM, dtype=float)
    for word in re.findall(r"\w+", text.lower(), flags=re.UNICODE):
        h = sha256(word.encode()).digest()
        vec[int.from_bytes(h[:2], "big") % DIM] += (
            1.0 if h[2] % 2 else -1.0
        )
    norm = np.linalg.norm(vec)
    return vec / norm if norm else np.eye(1, DIM, 0, dtype=float)[0]


class FrozenDetector:
    """No model calls: exact archived post-generation candidate lists."""

    name = "archived-detector-output-replay"
    prompt_variant = "current_pair"

    def __init__(self, turn_candidates: list[list[str]]) -> None:
        self._turn_candidates = turn_candidates
        self.calls = 0
        self.last_raw_output = None
        self.last_parse_diagnostics = None
        self.last_prompt_metadata = None

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        if self.calls >= len(self._turn_candidates):
            raise RuntimeError("Unexpected extra detector invocation")
        result = self._turn_candidates[self.calls]
        self.calls += 1
        if len(result) > max_seeds:
            raise RuntimeError("archived candidate count exceeds current cap")
        return list(result)


def from_github() -> bytes:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN absent: no source may be downloaded")
    api = (
        "https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/"
        f"actions/artifacts/{SOURCE_ARTIFACT_ID}/zip"
    )
    req = urllib.request.Request(api, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "pro-source-frozen-replay",
    })
    with urllib.request.urlopen(req, timeout=75) as response:
        payload = response.read(3_500_000)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return archive.read("observed.json")


def load_source(blob: bytes) -> dict:
    if sha256(blob).hexdigest() != ORIGINAL_SHA:
        raise ValueError("SOURCE SHA mismatch; fail closed")
    value = json.loads(blob)
    if len(value.get("cases", [])) != 12 or any(
        len(case.get("turns", [])) != 4 for case in value["cases"]
    ):
        raise ValueError("Source design mismatch; fail closed")
    return value


def replay(source: dict) -> dict:
    aggregate = Counter()
    by_model = defaultdict(Counter)
    by_turn = defaultdict(Counter)
    by_case = []
    seen_original = set()
    for case in source["cases"]:
        label = (case["case_id"], case["model_id"])
        if label in seen_original:
            raise ValueError("duplicate source case/model trajectory")
        seen_original.add(label)
        # Engine lives for *four* original turns, not a fresh object per turn.
        candidates_by_turn = [
            list(turn["canonical_report"].get("detected_candidates", []))
            for turn in case["turns"]
        ]
        detector = FrozenDetector(candidates_by_turn)
        engine = ShadowseedEngine(
            detector_backend=detector,
            embedding_fn=toy_embedding,
            recurrence_mode="pairwise",
            gate_policy_id="evidence_backed",
            max_seeds_per_turn=5,
        )
        case_total = Counter()
        before_ids = set()
        prior_unresolved = set()
        for index, turn in enumerate(case["turns"]):
            if int(turn.get("turn", -1)) != index:
                raise ValueError("out-of-order original source turn")
            prepared = engine.prepare_turn(turn["user_input"])
            if prepared.model_context or prepared.surfaced_seed_ids:
                raise AssertionError("host steering in no-evidence weightless replay")
            report = engine.observe_turn(prepared, turn["host_answer"])
            if report["detected_candidates"] != candidates_by_turn[index]:
                raise AssertionError("detector replay was not source-exact")
            intake = report["intake_diagnostics"]
            scope = intake.get("unresolved", [])
            if len(scope) + len(intake["accepted"]) + len(intake["rejected"]) != len(
                candidates_by_turn[index]
            ):
                raise AssertionError("source candidate lost in intake")
            expected = turn["canonical_report"]["intake_diagnostics"]["item_lineage"]
            historically_rejected = sum(
                x.get("outcome") == "rejected" and x.get("reason") == "not_atomic"
                for x in expected
            )
            recorded_scope = sum(
                x.get("outcome") in ("born_unresolved", "reobserved_unresolved")
                for x in intake["item_lineage"]
            )
            if recorded_scope != historically_rejected:
                raise AssertionError("unresolved count differs from historical form rejects")
            current = engine.inspect()["seeds"]
            if any(seed["weight"] != 0 for seed in current):
                raise AssertionError("unverified source changed Gate authority")
            ids_now = {seed["id"] for seed in current}
            if not before_ids.issubset(ids_now):
                raise AssertionError("seed vanished from short live replay")
            before_ids = ids_now
            unresolved_now = {
                seed["id"] for seed in current if seed["scope_status"] == "unresolved"
            }
            if not prior_unresolved.issubset(unresolved_now):
                raise AssertionError("unresolved source memory disappeared")
            prior_unresolved = unresolved_now
            part = Counter({
                "turns": 1,
                "archived_candidates": len(candidates_by_turn[index]),
                "historical_not_atomic": historically_rejected,
                "observed_unresolved": len(scope),
                "unresolved_created": sum(
                    x["transition"] == "created_unresolved" for x in scope
                ),
                "unresolved_reobserved": sum(
                    x["transition"] == "reobserved_unresolved" for x in scope
                ),
                "accepted": len(intake["accepted"]),
                "rejected_now": len(intake["rejected"]),
                "new_seed_ids": len(
                    ids_now - (set() if index == 0 else previous_ids)
                ),
                "reactivated_trtl": len(prepared.reactivated_trtl),
                "host_seed_exposures": len(prepared.surfaced_seed_ids),
                "nonzero_weight_seeds": sum(seed["weight"] != 0 for seed in current),
            })
            previous_ids = ids_now
            aggregate.update(part)
            case_total.update(part)
            by_model[case["model_id"]].update(part)
            by_turn[index].update(part)
        if detector.calls != 4 or engine.turn != 4:
            raise AssertionError("failed to replay all four original host turns")
        restored = ShadowseedEngine.from_state(
            engine.export_state(),
            detector_backend=FrozenDetector([]),
            embedding_fn=toy_embedding,
        )
        final_orig = {s["id"]: s for s in engine.inspect()["seeds"]}
        final_copy = {s["id"]: s for s in restored.inspect()["seeds"]}
        if set(final_orig) != set(final_copy) or any(
            final_orig[sid]["text"] != final_copy[sid]["text"]
            or final_orig[sid]["scope_status"] != final_copy[sid]["scope_status"]
            or final_orig[sid]["weight"] != final_copy[sid]["weight"]
            for sid in final_orig
        ):
            raise AssertionError("seed identity/scope lost on state round-trip")
        case_total["persisted_final_seeds"] = len(final_orig)
        case_total["persisted_unresolved"] = sum(
            s["scope_status"] == "unresolved" for s in final_orig.values()
        )
        aggregate["persisted_final_seeds"] += case_total["persisted_final_seeds"]
        aggregate["persisted_unresolved"] += case_total["persisted_unresolved"]
        by_model[case["model_id"]]["persisted_final_seeds"] += case_total["persisted_final_seeds"]
        by_model[case["model_id"]]["persisted_unresolved"] += case_total["persisted_unresolved"]
        by_case.append({
            "case": case["case_id"], "model": case["model_id"],
            "counts": dict(case_total),
        })
    if aggregate["turns"] != 48 or aggregate["archived_candidates"] != 94:
        raise AssertionError("source event count unexpected")
    if aggregate["historical_not_atomic"] != 46:
        raise AssertionError("historical count unexpected")
    if aggregate["nonzero_weight_seeds"] or aggregate["host_seed_exposures"]:
        raise AssertionError("unauthorized influence detected")
    return {
        "status": "completed_mechanical_replay_unreviewed",
        "source_sha256": ORIGINAL_SHA,
        "feature": "pro-unresolved-weightless-birth",
        "scope": "12 dependent case/model sessions x 4 real archived host turns",
        "embedding": "toy deterministic lexical; semantic matches NOT validated",
        "source_generation": "frozen existing outputs; no model calls, no new evidence",
        "turn_mechanics": "actual ShadowseedEngine prepare_turn/observe_turn",
        "counts": dict(aggregate),
        "by_model": {m: dict(v) for m, v in sorted(by_model.items())},
        "by_turn": {str(k): dict(v) for k, v in sorted(by_turn.items())},
        "by_case": by_case,
        "independent_human_reviews": 0,
        "q1_q2_efficacy": "NOT TESTED: no independent new model-generation trajectories",
        "unresolved_note": "post-rejection retention is not pre-generation discovery",
        "candidate_text_in_public_output": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, help="private original observed.json")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    blob = args.source.read_bytes() if args.source else from_github()
    summary = replay(load_source(blob))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": summary["status"],
        "counts": summary["counts"],
        "source_sha256": summary["source_sha256"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
