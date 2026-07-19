"""Aggregate completed open-set review packets into usable evaluation summaries."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from shadowseed.benchmark.open_set_seed_review import (
    EVIDENCE_LAYER,
    REJECT_CODES,
    REVIEW_CRITERIA,
)


ACCEPT_STATES = {"accept", "accepted", "approved", "pass", "passed"}
REJECT_STATES = {"reject", "rejected", "failed", "fail"}
TRUE_VALUES = {"true", "yes", "y", "1", "pass", "passed", "accept", "accepted"}
FALSE_VALUES = {"false", "no", "n", "0", "fail", "failed", "reject", "rejected"}
VALID_COMPLETED_DECISIONS = {"accepted", "rejected"}


def _normalize_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in TRUE_VALUES:
            return True
        if lowered in FALSE_VALUES:
            return False
    return None


def _normalized_fields(packet: dict[str, Any]) -> list[bool | None]:
    fields = packet.get("review_fields", {})
    return [_normalize_bool(fields.get(criterion)) for criterion in REVIEW_CRITERIA]


def _packet_decision(packet: dict[str, Any]) -> str:
    review_status = str(packet.get("review_status") or "").strip().lower()
    reject_reason = str(packet.get("reject_reason") or "").strip()
    normalized = _normalized_fields(packet)

    if review_status == "pending" or (
        not review_status and all(value is None for value in normalized) and not reject_reason
    ):
        return "pending"

    accepted_by_status = review_status in ACCEPT_STATES
    accepted_by_fields = bool(normalized) and all(value is True for value in normalized) and not reject_reason
    rejected_by_status = review_status in REJECT_STATES
    rejected_by_fields = any(value is False for value in normalized) or bool(reject_reason)

    if accepted_by_status or accepted_by_fields:
        if all(value is True for value in normalized) and not reject_reason:
            return "accepted"
        return "invalid"

    if rejected_by_status or rejected_by_fields:
        if (
            any(value is False for value in normalized)
            and all(value is not None for value in normalized)
            and reject_reason in REJECT_CODES
        ):
            return "rejected"
        return "invalid"

    return "invalid"


def _pairwise_agreement_ratio(values: list[str]) -> float | None:
    if len(values) < 2:
        return None
    total_pairs = 0
    matching_pairs = 0
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            total_pairs += 1
            if left == right:
                matching_pairs += 1
    return (matching_pairs / total_pairs) if total_pairs else None


def _render_report(summary: dict[str, Any], disagreements_path: Path) -> str:
    reject_counts = summary.get("reject_reason_counts", {})
    reject_lines = "\n".join(
        f"- `{reason}`: {count}" for reason, count in sorted(reject_counts.items())
    ) or "- none"
    criterion_lines = "\n".join(
        f"- `{criterion}`: {summary['criterion_pass_rates'][criterion]:.2f}"
        for criterion in REVIEW_CRITERIA
    )
    domain_lines = "\n".join(
        f"- `{domain}`: {count}"
        for domain, count in sorted(summary.get("domain_seed_counts", {}).items())
    ) or "- none"

    return "\n".join(
        [
            "# Open-set Seed Review Report",
            "",
            f"Evidence layer: `{summary['evidence_layer']}`",
            f"Status: `{summary['status']}`",
            "",
            "## Overview",
            "",
            f"- packets: {summary['packet_count']}",
            f"- completed packets: {summary['completed_packet_count']}",
            f"- invalid packets: {summary['invalid_packet_count']}",
            f"- unique seeds: {summary['unique_seed_count']}",
            f"- fully reviewed seeds: {summary['completed_seed_count']}",
            f"- accepted seeds: {summary['accepted_seed_count']}",
            f"- rejected seeds: {summary['rejected_seed_count']}",
            f"- mixed seeds: {summary['mixed_seed_count']}",
            f"- pending seeds: {summary['pending_seed_count']}",
            f"- invalid seeds: {summary['invalid_seed_count']}",
            "",
            "## Core Rates",
            "",
            f"- packet acceptance rate: {summary['packet_acceptance_rate']:.2f}",
            f"- seed acceptance rate: {summary['seed_acceptance_rate']:.2f}",
            f"- seed rejection rate: {summary['seed_rejection_rate']:.2f}",
            f"- unanimous verdict rate: {summary['unanimous_verdict_rate']:.2f}",
            f"- pairwise decision agreement rate: {summary['pairwise_decision_agreement_rate']:.2f}",
            "",
            "## Criterion Pass Rates",
            "",
            criterion_lines,
            "",
            "## Reject Reasons",
            "",
            reject_lines,
            "",
            "## Domain Coverage",
            "",
            domain_lines,
            "",
            "## Follow-up",
            "",
            f"- disagreements artifact: `{disagreements_path}`",
            "- invalid packet rows must be fixed before this layer is treated as completed evidence",
            "- partial reviewer completion does not count as a seed-level acceptance or rejection",
            "- do not collapse this layer into the standard regression score",
        ]
    ) + "\n"


def summarize_open_set_seed_review(
    review_packet_path: str,
    output_path: str,
    disagreements_output_path: str | None = None,
    report_output_path: str | None = None,
) -> Path:
    payload = json.loads(Path(review_packet_path).read_text(encoding="utf-8"))
    packets = payload.get("packets", [])

    by_seed: dict[tuple[str, str], dict[str, Any]] = {}
    reviewer_ids: set[str] = set()
    reject_reason_counter: Counter[str] = Counter()
    criterion_completed_counts: Counter[str] = Counter()
    criterion_true_counts: Counter[str] = Counter()
    domain_seed_counts: Counter[str] = Counter()

    packet_count = len(packets)
    completed_packet_count = 0
    invalid_packet_count = 0
    accepted_packet_count = 0
    rejected_packet_count = 0

    for packet in packets:
        key = (str(packet.get("item_id") or "unknown"), str(packet.get("seed_text") or ""))
        entry = by_seed.setdefault(
            key,
            {
                "item_id": packet.get("item_id"),
                "title": packet.get("title"),
                "domain": packet.get("domain"),
                "seed_id": packet.get("seed_id"),
                "seed_text": packet.get("seed_text"),
                "reviewers": [],
                "criterion_true_counts": {criterion: 0 for criterion in REVIEW_CRITERIA},
                "criterion_false_counts": {criterion: 0 for criterion in REVIEW_CRITERIA},
                "criterion_pending_counts": {criterion: 0 for criterion in REVIEW_CRITERIA},
                "reject_reason_counts": {},
            },
        )
        reviewer_id = str(packet.get("reviewer_id") or "unknown")
        reviewer_ids.add(reviewer_id)
        decision = _packet_decision(packet)
        fields = packet.get("review_fields", {})
        reject_reason = packet.get("reject_reason")

        reviewer_row = {
            "reviewer_id": reviewer_id,
            "review_status": packet.get("review_status", "pending"),
            "decision": decision,
            "review_fields": fields,
            "reject_reason": reject_reason,
            "reviewer_notes": packet.get("reviewer_notes", ""),
        }
        entry["reviewers"].append(reviewer_row)

        if decision in VALID_COMPLETED_DECISIONS:
            completed_packet_count += 1
        elif decision == "invalid":
            invalid_packet_count += 1
        if decision == "accepted":
            accepted_packet_count += 1
        elif decision == "rejected":
            rejected_packet_count += 1

        for criterion in REVIEW_CRITERIA:
            normalized = _normalize_bool(fields.get(criterion))
            if normalized is True:
                entry["criterion_true_counts"][criterion] += 1
                criterion_true_counts[criterion] += 1
                criterion_completed_counts[criterion] += 1
            elif normalized is False:
                entry["criterion_false_counts"][criterion] += 1
                criterion_completed_counts[criterion] += 1
            else:
                entry["criterion_pending_counts"][criterion] += 1

        if reject_reason:
            reject_reason_counter[str(reject_reason)] += 1
            local_counter = Counter(entry["reject_reason_counts"])
            local_counter[str(reject_reason)] += 1
            entry["reject_reason_counts"] = dict(local_counter)

    accepted_seed_count = 0
    rejected_seed_count = 0
    mixed_seed_count = 0
    pending_seed_count = 0
    invalid_seed_count = 0
    unanimous_seed_count = 0
    agreement_eligible_seed_count = 0
    pairwise_decision_agreement_sum = 0.0
    disagreements: list[dict[str, Any]] = []
    aggregated_results: list[dict[str, Any]] = []

    for entry in by_seed.values():
        valid_completed = [
            reviewer["decision"]
            for reviewer in entry["reviewers"]
            if reviewer["decision"] in VALID_COMPLETED_DECISIONS
        ]
        invalid_rows = [
            reviewer for reviewer in entry["reviewers"] if reviewer["decision"] == "invalid"
        ]
        expected_reviewer_count = len(entry["reviewers"])
        domain = str(entry.get("domain") or "unknown")
        domain_seed_counts[domain] += 1

        if invalid_rows:
            verdict = "invalid"
            invalid_seed_count += 1
            pairwise_decision_agreement = None
        elif len(valid_completed) < expected_reviewer_count:
            verdict = "pending"
            pending_seed_count += 1
            pairwise_decision_agreement = None
        elif all(decision == "accepted" for decision in valid_completed):
            verdict = "accepted"
            accepted_seed_count += 1
            pairwise_decision_agreement = _pairwise_agreement_ratio(valid_completed)
        elif all(decision == "rejected" for decision in valid_completed):
            verdict = "rejected"
            rejected_seed_count += 1
            pairwise_decision_agreement = _pairwise_agreement_ratio(valid_completed)
        else:
            verdict = "mixed"
            mixed_seed_count += 1
            pairwise_decision_agreement = _pairwise_agreement_ratio(valid_completed)

        if len(valid_completed) >= 2:
            agreement_eligible_seed_count += 1
            if len(set(valid_completed)) == 1:
                unanimous_seed_count += 1
            if pairwise_decision_agreement is not None:
                pairwise_decision_agreement_sum += pairwise_decision_agreement
            if len(set(valid_completed)) != 1:
                disagreements.append(
                    {
                        "item_id": entry["item_id"],
                        "title": entry["title"],
                        "domain": entry["domain"],
                        "seed_id": entry["seed_id"],
                        "seed_text": entry["seed_text"],
                        "decisions": valid_completed,
                        "pairwise_decision_agreement": pairwise_decision_agreement,
                        "reviewers": entry["reviewers"],
                    }
                )

        entry["completed_reviewer_count"] = len(valid_completed)
        entry["reviewer_count"] = expected_reviewer_count
        entry["aggregate_verdict"] = verdict
        entry["pairwise_decision_agreement"] = pairwise_decision_agreement
        aggregated_results.append(entry)

    completed_seed_count = accepted_seed_count + rejected_seed_count + mixed_seed_count
    summary = {
        "evidence_layer": EVIDENCE_LAYER,
        "packet_count": packet_count,
        "completed_packet_count": completed_packet_count,
        "pending_packet_count": packet_count - completed_packet_count - invalid_packet_count,
        "invalid_packet_count": invalid_packet_count,
        "accepted_packet_count": accepted_packet_count,
        "rejected_packet_count": rejected_packet_count,
        "packet_acceptance_rate": (accepted_packet_count / completed_packet_count) if completed_packet_count else 0.0,
        "unique_seed_count": len(aggregated_results),
        "completed_seed_count": completed_seed_count,
        "accepted_seed_count": accepted_seed_count,
        "rejected_seed_count": rejected_seed_count,
        "mixed_seed_count": mixed_seed_count,
        "pending_seed_count": pending_seed_count,
        "invalid_seed_count": invalid_seed_count,
        "agreement_eligible_seed_count": agreement_eligible_seed_count,
        "unanimous_seed_count": unanimous_seed_count,
        "seed_acceptance_rate": (accepted_seed_count / len(aggregated_results)) if aggregated_results else 0.0,
        "seed_rejection_rate": (rejected_seed_count / len(aggregated_results)) if aggregated_results else 0.0,
        "unanimous_verdict_rate": (unanimous_seed_count / agreement_eligible_seed_count) if agreement_eligible_seed_count else 0.0,
        "pairwise_decision_agreement_rate": (
            pairwise_decision_agreement_sum / agreement_eligible_seed_count
        ) if agreement_eligible_seed_count else 0.0,
        "criteria": REVIEW_CRITERIA,
        "criterion_pass_rates": {
            criterion: (criterion_true_counts[criterion] / criterion_completed_counts[criterion])
            if criterion_completed_counts[criterion]
            else 0.0
            for criterion in REVIEW_CRITERIA
        },
        "reject_reason_counts": dict(reject_reason_counter),
        "reviewer_ids": sorted(reviewer_ids),
        "domain_seed_counts": dict(domain_seed_counts),
        "status": (
            "review_invalid"
            if invalid_packet_count
            else "review_complete"
            if packet_count and completed_packet_count == packet_count
            else "review_in_progress"
        ),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    disagreements_output = Path(disagreements_output_path) if disagreements_output_path else output.with_name(output.stem + "_disagreements.json")
    disagreements_output.parent.mkdir(parents=True, exist_ok=True)
    report_output = Path(report_output_path) if report_output_path else output.with_name(output.stem + "_report.md")
    report_output.parent.mkdir(parents=True, exist_ok=True)

    summary["artifacts"] = {
        "summary": str(output),
        "disagreements": str(disagreements_output),
        "report": str(report_output),
    }

    output.write_text(
        json.dumps({"summary": summary, "results": aggregated_results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    disagreements_output.write_text(
        json.dumps(
            {
                "summary": {
                    "evidence_layer": EVIDENCE_LAYER,
                    "disagreement_count": len(disagreements),
                    "agreement_eligible_seed_count": agreement_eligible_seed_count,
                    "unanimous_verdict_rate": summary["unanimous_verdict_rate"],
                    "pairwise_decision_agreement_rate": summary["pairwise_decision_agreement_rate"],
                },
                "disagreements": disagreements,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report_output.write_text(_render_report(summary, disagreements_output), encoding="utf-8")

    return output
