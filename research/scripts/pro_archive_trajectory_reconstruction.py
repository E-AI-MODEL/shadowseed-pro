"""Reconstruct recorded Pro research trajectories from a private derived ZIP.

Offline and descriptive. No LLM, embeddings, Gate, semantic assessment or changes
in the Pro product. The public manifest contains counts and input hashes only.
Full historical rows are exported only with --owner-only-dir.

Input is the 28 Oct 2026 *derived* Shadowseed observation-register ZIP. Its
hash proves only the identity of this ZIP, not its correspondence with all
original GitHub Actions artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

STAGE_INDEX = "02_beurten_stage_220.csv"
FULL_STAGE = "09_alle_220_volledige_beurtrecords.csv"
CANDIDATES = "01_alle_kandidaten_1224.csv"
REQUIRED = (STAGE_INDEX, FULL_STAGE, CANDIDATES)


def _read_csv(raw: bytes, name: str) -> list[dict[str, str]]:
    source = io.StringIO(raw.decode("utf-8-sig"), newline="")
    reader = csv.DictReader(source)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError(f"missing or duplicate header: {name}")
    rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"malformed CSV row: {name}")
    return rows


def _stage_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return tuple(row[k] for k in ("dataset", "artifact_id", "model", "case_id", "turn"))


def _trajectory_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return tuple(row[k] for k in ("dataset", "artifact_id", "model", "case_id"))


def _candidate_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return tuple(row[k] for k in ("dataset", "artid", "model", "case_id", "turn"))


def _turn_number(turn: str) -> int:
    try:
        number = int(turn)
    except (ValueError, TypeError) as exc:
        raise ValueError("a recorded turn must be an integer") from exc
    if number < 0 or str(number) != turn:
        raise ValueError("a recorded turn must be a canonical nonnegative integer")
    return number


def load_register(zip_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return public count-only manifest and owner-only, source-preserving rows."""
    archive_hash = sha256(zip_path.read_bytes()).hexdigest()
    with ZipFile(zip_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member names are ambiguous")
        if not set(REQUIRED).issubset(names):
            raise ValueError("input is missing required observation register tables")
        inputs = {}
        for name in REQUIRED:
            info = archive.getinfo(name)
            if info.file_size > 30_000_000:
                raise ValueError("observation register member exceeds safety bound")
            blob = archive.read(name)
            inputs[name] = {"sha256": sha256(blob).hexdigest(), "rows": _read_csv(blob, name)}

    full = inputs[FULL_STAGE]["rows"]
    stage = inputs[STAGE_INDEX]["rows"]
    candidates = inputs[CANDIDATES]["rows"]
    if Counter(map(_stage_key, full)) != Counter(map(_stage_key, stage)):
        raise ValueError("full and stage-index turn keys diverge")
    stage_keys = [_stage_key(row) for row in full]
    if len(stage_keys) != len(set(stage_keys)):
        raise ValueError("duplicate full stage turn for the same source trajectory")

    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for source_index, row in enumerate(full, start=2):
        t = _turn_number(row["turn"])
        try:
            original = json.loads(row["originele_complete_beurt_json"])
        except (ValueError, TypeError) as exc:
            raise ValueError("non-JSON original turn object") from exc
        if not isinstance(original, dict):
            raise ValueError("original turn object is not a JSON object")
        orig_turn = original.get("turn", original.get("index"))
        if orig_turn is not None and orig_turn != t:
            raise ValueError("original turn index differs from derived register")
        groups[_trajectory_key(row)].append({"source_csv_line": source_index, "row": row})

    trajectories = []
    stage_to_trajectory = {}
    sizes = Counter()
    for group_key in sorted(groups):
        turns = sorted(groups[group_key], key=lambda a: _turn_number(a["row"]["turn"]))
        numbers = [_turn_number(entry["row"]["turn"]) for entry in turns]
        if numbers != list(range(len(numbers))):
            raise ValueError("trajectory turn sequence is not contiguous from zero")
        trajectory_id = "T-" + sha256(json.dumps(group_key, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
        record = {
            "trajectory_id": trajectory_id,
            "source_identity": dict(zip(("dataset", "artifact_id", "model", "case_id"), group_key)),
            "turns": turns,
            "read_only": True,
            "claim": "recorded_text_not_model_internal_evidence",
        }
        trajectories.append(record)
        sizes[len(turns)] += 1
        for entry in turns:
            stage_to_trajectory[_stage_key(entry["row"])] = trajectory_id

    # Literal source identity is necessary for exact joins. Do not silently map
    # model names (e.g. qwen-unspecified versus qwen2.5-7b).
    stage_without_model = defaultdict(set)
    for k, tid in stage_to_trajectory.items():
        stage_without_model[(k[0], k[1], k[3], k[4])].add(tid)
    match_counts = Counter()
    related_rows = []
    for source_index, row in enumerate(candidates, start=2):
        ck = _candidate_key(row)
        possible = stage_without_model.get((ck[0], ck[1], ck[3], ck[4]), set())
        exact = stage_to_trajectory.get(ck)
        if exact:
            status = "literal_source_key_match"
            related = exact
        elif len(possible) == 1:
            status = "model_label_differs_not_joined"
            related = None
        else:
            status = "no_literal_stage_match"
            related = None
        match_counts[status] += 1
        related_rows.append({
            "source_csv_line": source_index,
            "row": row,
            "literal_join_status": status,
            "stage_trajectory_id_only_if_exact": related,
        })

    by_dataset = Counter(row["dataset"] for row in full)
    candidate_by_dataset = Counter(row["dataset"] for row in candidates)
    public = {
        "format": "pro-derived-register-observation-coverage-v1",
        "status": "descriptive_offline_no_q1_q2_judgement",
        "input_kind": "derived_observation_register_not_original_action_archive",
        "input_zip_sha256": archive_hash,
        "member_sha256": {name: inputs[name]["sha256"] for name in REQUIRED},
        "stage_turn_records": len(full),
        "stage_trajectories": len(trajectories),
        "trajectory_length_distribution": dict(sorted(sizes.items())),
        "stage_turns_by_dataset": dict(sorted(by_dataset.items())),
        "candidate_occurrences_preserved": len(related_rows),
        "candidates_by_dataset": dict(sorted(candidate_by_dataset.items())),
        "candidate_to_stage_literal_join": dict(sorted(match_counts.items())),
        "source_identity_note": "Different model labels are not asserted equivalent; unmatched means no literal key, not lost data.",
        "semantic_assessments_performed": 0,
        "provider_model_calls": 0,
        "pro_runtime_or_gate_mutations": 0,
        "original_action_artifacts_individually_reverified": False,
        "complete_all_repository_history": False,
    }
    private = {"trajectories": trajectories, "candidate_occurrences": related_rows}
    return public, private


def write_owner_only(directory: Path, private: dict[str, Any], public: dict[str, Any]) -> None:
    """Write raw rows into a new, user-controlled directory; never log them."""
    if directory.exists():
        raise FileExistsError("owner-only output directory already exists")
    directory.mkdir(mode=0o700, parents=True)
    sub = directory / "trajectories"
    sub.mkdir(mode=0o700)
    for record in private["trajectories"]:
        path = sub / (record["trajectory_id"] + ".json")
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        path.chmod(0o600)
    path = directory / "all_candidate_occurrences.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in private["candidate_occurrences"]:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    path.chmod(0o600)
    summary = directory / "manifest.json"
    summary.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    summary.chmod(0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("register_zip", type=Path, help="Owner-held 28 October derived observation register ZIP")
    parser.add_argument("--owner-only-dir", type=Path, help="Explicit opt-in raw trajectory export")
    parser.add_argument("--public-manifest", type=Path, help="Optional count-only JSON file")
    args = parser.parse_args()
    public, private = load_register(args.register_zip)
    if args.owner_only_dir:
        write_owner_only(args.owner_only_dir, private, public)
    if args.public_manifest:
        args.public_manifest.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(public, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
