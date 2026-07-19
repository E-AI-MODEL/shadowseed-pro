"""Blind model-vs-baseline control for open-set seed review.

This implements the control condition for open-set Layer C: reviewers judge
detector candidates and template-baseline candidates *blind and interleaved*,
so the seed-quality claim is "the model arm beats the baseline arm under blind
review" rather than a bare acceptance rate (a forking-paths risk; cf. Gelman &
Loken 2013, and SSL 4.5 §20/H1/H8 "boven baseline").

Two modes:

  build    model_seed_output + baseline_seed_output (+ input) -> blind packets
           and a separate hidden key (arm + original text per blind_id).

  unblind  filled blind packets + key -> per-arm accept/atomic rates + delta.

The blind packet carries no arm label. The key is written separately and must
NOT be shown to reviewers. Shuffling is deterministic (seeded by item id) so a
run is reproducible.

Consistent with merge #109: candidates are candidate-only; this script grants
no seed/evidence/Round status. Reviewer judgment is the only Layer C evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

# Review fields a reviewer fills per blinded candidate.
JUDGMENT_FIELDS: tuple[str, ...] = (
    "atomic",
    "relevant",
    "testable",
    "non_trivial",
    "useful_for_followup",
    "accept",
    "reject_reason",
)

REJECT_CODES: tuple[str, ...] = (
    "too_broad",
    "too_vague",
    "trivial",
    "not_relevant",
    "not_testable",
    "duplicate",
    "style_not_gap",
)


def _candidates(result: dict[str, Any]) -> list[str]:
    return result.get("normalized_candidates") or result.get("raw_candidates") or []


def _index_by_item(seed_output: dict[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for result in seed_output.get("results", []):
        index[str(result.get("item_id", ""))] = _candidates(result)
    return index


def _blind_id(item_id: str, arm: str, position: int) -> str:
    raw = f"{item_id}|{arm}|{position}"
    return "b_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _seeded_rng(item_id: str) -> random.Random:
    seed = int(hashlib.sha1(item_id.encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(seed)


def build_blind_packets(
    model_output: dict[str, Any],
    baseline_output: dict[str, Any],
    reviewer_ids: tuple[str, ...] = ("reviewer_a", "reviewer_b"),
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return (blind packets, hidden key)."""
    model_index = _index_by_item(model_output)
    baseline_index = _index_by_item(baseline_output)
    item_ids = sorted(set(model_index) | set(baseline_index))

    packets: list[dict[str, Any]] = []
    key: dict[str, dict[str, Any]] = {}

    for item_id in item_ids:
        entries: list[tuple[str, str]] = []  # (arm, text)
        for position, text in enumerate(model_index.get(item_id, []), start=1):
            entries.append(("model", text))
        for position, text in enumerate(baseline_index.get(item_id, []), start=1):
            entries.append(("baseline", text))

        rng = _seeded_rng(item_id)
        rng.shuffle(entries)

        for shown_position, (arm, text) in enumerate(entries, start=1):
            blind_id = _blind_id(item_id, arm, shown_position)
            key[blind_id] = {"item_id": item_id, "arm": arm, "text": text}
            for reviewer_id in reviewer_ids:
                packets.append(
                    {
                        "blind_id": blind_id,
                        "item_id": item_id,
                        "shown_position": shown_position,
                        "candidate": text,
                        "reviewer_id": reviewer_id,
                        "judgment": {field: None for field in JUDGMENT_FIELDS},
                        "review_status": "pending",
                    }
                )

    return packets, key


def _is_accept(judgment: dict[str, Any]) -> bool | None:
    value = judgment.get("accept")
    if isinstance(value, bool):
        return value
    return None


def unblind(
    filled_packets: list[dict[str, Any]],
    key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate filled blind packets per arm using the hidden key."""
    arms = ("model", "baseline")
    stats: dict[str, dict[str, int]] = {
        arm: {"judged": 0, "accepted": 0, "accepted_atomic": 0} for arm in arms
    }

    reviewer_ids: set[str] = set()
    for packet in filled_packets:
        arm = key.get(packet.get("blind_id", ""), {}).get("arm")
        if arm not in stats:
            continue
        judgment = packet.get("judgment", {})
        accept = _is_accept(judgment)
        if accept is None:
            continue  # not yet reviewed
        reviewer_id = str(packet.get("reviewer_id") or "").strip()
        if reviewer_id:
            reviewer_ids.add(reviewer_id)
        stats[arm]["judged"] += 1
        if accept:
            stats[arm]["accepted"] += 1
            if judgment.get("atomic") is True:
                stats[arm]["accepted_atomic"] += 1

    def rate(num: int, den: int) -> float:
        return round(num / den, 3) if den else 0.0

    per_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        s = stats[arm]
        per_arm[arm] = {
            "judged": s["judged"],
            "accepted": s["accepted"],
            "accept_rate": rate(s["accepted"], s["judged"]),
            "atomic_rate_of_accepted": rate(s["accepted_atomic"], s["accepted"]),
        }

    return {
        "artifact": "blind_control_summary",
        "disclaimer": (
            "Per-arm aggregation of blind review. Model versus "
            "adapter_v1 baseline on identical items. No combined score; layers "
            "remain separate. See reviewer_ids for the source of the "
            "judgments (human or delegated AI)."
        ),
        "reviewer_ids": sorted(reviewer_ids),
        "per_arm": per_arm,
        "accept_rate_delta_model_minus_baseline": round(
            per_arm["model"]["accept_rate"] - per_arm["baseline"]["accept_rate"], 3
        ),
        "reject_codes": list(REJECT_CODES),
    }


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    build = sub.add_parser("build", help="Build blind interleaved review packets.")
    build.add_argument("--model", required=True, help="model_seed_output.json")
    build.add_argument("--baseline", required=True, help="baseline_seed_output.json")
    build.add_argument("--input", default=None, help="optional input batch; not required")
    build.add_argument("--packets", required=True, help="output: blind_review_packets.json")
    build.add_argument("--key", required=True, help="output: blind_key.json (DO NOT share with reviewers)")
    build.add_argument(
        "--reviewer-id",
        dest="reviewer_ids",
        action="append",
        default=None,
        help="Reviewer ID; may be repeated. Default: reviewer_a and reviewer_b.",
    )

    unb = sub.add_parser("unblind", help="Aggregate completed packets by arm.")
    unb.add_argument("--packets", required=True, help="completed blind_review_packets.json")
    unb.add_argument("--key", required=True, help="blind_key.json")
    unb.add_argument("--output", default=None, help="output: blind_control_summary.json")

    args = parser.parse_args(argv)

    if args.mode == "build":
        reviewer_ids = tuple(args.reviewer_ids) if args.reviewer_ids else ("reviewer_a", "reviewer_b")
        packets, key = build_blind_packets(_load(args.model), _load(args.baseline), reviewer_ids)
        _write(args.packets, packets)
        _write(args.key, key)
        print(f"Wrote {len(packets)} blind packets to {args.packets} and key to {args.key}")
        return 0

    if args.mode == "unblind":
        summary = unblind(_load(args.packets), _load(args.key))
        if args.output:
            _write(args.output, summary)
            print(f"Wrote {args.output}")
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
