#!/usr/bin/env python3
"""Build a blind A/B review pack from an ssl_session_suite.json artifact.

The SSL session runner may still carry legacy embedded blind fields for debug
compatibility. This script is the canonical review-pack generator: it extracts
only cross-turn payoff events, balances whether baseline or SSL is shown as
answer A, and writes one answer key that matches the review items.

Default output names are neutral so W9/W10/etc. rounds do not inherit stale
labels:

- ssl_session_blind_ab_review_items.json
- ssl_session_blind_ab_answer_key.json
- ssl_session_blind_ab_review_form.md
- ssl_session_blind_ab_scoring_template.csv
- ssl_session_blind_ab_summary.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ssl-session-blind-ab.v2"
DEFAULT_PREFIX = "ssl_session_blind_ab"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_prefix(prefix: str) -> str:
    """Treat prefix as a filename prefix, never as a path.

    The workflow exposes this as a free-form input, so reject separators rather
    than silently writing outside the review artifact directory.
    """
    value = (prefix or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX
    if value in {".", ".."} or value.startswith("."):
        raise ValueError("--prefix must be a plain filename prefix, not a hidden or relative path")
    if "/" in value or "\\" in value:
        raise ValueError("--prefix must be a filename prefix and may not contain path separators")
    if Path(value).is_absolute() or Path(value).name != value:
        raise ValueError("--prefix must be a filename prefix inside --output-dir")
    return value


def _turn_number(turn: dict[str, Any]) -> int:
    raw = turn.get("turn") or turn.get("turn_index") or 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _item_id(conversation_id: str, turn: dict[str, Any], index: int) -> str:
    turn_no = _turn_number(turn)
    return f"{conversation_id}-t{turn_no:02d}-{index:02d}"


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text or ""))


def _answer_diagnostics(text: str) -> dict[str, Any]:
    stripped = (text or "").strip()
    if not stripped:
        return {
            "word_count": 0,
            "char_count": 0,
            "ends_with_sentence_punctuation": False,
            "likely_truncated": False,
        }

    ends_cleanly = stripped.endswith((".", "!", "?", "…", ")", "]", '"', "'", "”", "’"))
    last_line = stripped.splitlines()[-1].strip()
    dangling_marker = bool(re.match(r"^(\d+\.|[-*•])\s*$", last_line))
    likely_truncated = (not ends_cleanly) or dangling_marker

    return {
        "word_count": _word_count(stripped),
        "char_count": len(stripped),
        "ends_with_sentence_punctuation": ends_cleanly,
        "likely_truncated": likely_truncated,
    }


def _balanced_ssl_a_assignments(count: int, *, seed: int) -> list[bool]:
    """Return a reproducible, near-balanced SSL-as-A assignment list.

    A plain stream of random bits can accidentally put most SSL answers on one
    side for small review packs. Build a balanced bag first, then shuffle it
    reproducibly.
    """
    if count <= 0:
        return []

    rng = random.Random(seed)
    ssl_a_count = count // 2
    if count % 2:
        ssl_a_count += rng.randrange(2)
    assignments = [True] * ssl_a_count + [False] * (count - ssl_a_count)
    rng.shuffle(assignments)
    return assignments


def _cross_turn_candidates(payload: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    candidates: list[tuple[str, str, dict[str, Any]]] = []
    for conv in payload.get("conversations", []):
        conversation_id = _safe_text(conv.get("conversation_id") or conv.get("id") or "conversation")
        domain = _safe_text(conv.get("domain"))
        for turn in conv.get("turns", []):
            if not turn.get("is_cross_turn_payoff"):
                continue
            baseline_answer = _safe_text(turn.get("baseline_answer"))
            ssl_answer = _safe_text(turn.get("ssl_answer"))
            if not baseline_answer or not ssl_answer:
                continue
            candidates.append((conversation_id, domain, turn))
    return candidates


def build_review_pack(payload: dict[str, Any], *, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    review_items: list[dict[str, Any]] = []
    answer_key: list[dict[str, Any]] = []

    candidates = _cross_turn_candidates(payload)
    assignments = _balanced_ssl_a_assignments(len(candidates), seed=seed)

    for global_index, ((conversation_id, domain, turn), ssl_is_a) in enumerate(
        zip(candidates, assignments),
        start=1,
    ):
        baseline_answer = _safe_text(turn.get("baseline_answer"))
        ssl_answer = _safe_text(turn.get("ssl_answer"))
        answer_a = ssl_answer if ssl_is_a else baseline_answer
        answer_b = baseline_answer if ssl_is_a else ssl_answer
        item_id = _item_id(conversation_id, turn, global_index)

        surfaced_seeds = list(turn.get("surfaced_cross_turn_seeds") or [])
        promoted_seeds = list(turn.get("promoted_seeds") or turn.get("promoted_this_turn") or [])

        review_items.append(
            {
                "schema_version": SCHEMA_VERSION,
                "item_id": item_id,
                "conversation_id": conversation_id,
                "domain": domain,
                "turn": _turn_number(turn),
                "question": _safe_text(turn.get("question")),
                "answer_A": answer_a,
                "answer_B": answer_b,
                "answer_diagnostics": {
                    "A": _answer_diagnostics(answer_a),
                    "B": _answer_diagnostics(answer_b),
                },
                "post_choice_seed_context": {
                    "surfaced_cross_turn_seeds": surfaced_seeds,
                    "promoted_seeds_this_turn": promoted_seeds,
                },
                "review": {
                    "winner": "",  # A, B, or tie
                    "scores": {
                        "content_completeness": {"A": "", "B": ""},
                        "question_relevance": {"A": "", "B": ""},
                        "specificity_sharpness": {"A": "", "B": ""},
                        "no_noise_or_hallucinated_relevance": {"A": "", "B": ""},
                        "usefulness": {"A": "", "B": ""},
                    },
                    "motivation": "",
                    "seed_effect_after_choice": "",  # clear_help, some_help, no_difference, noise
                    "noise_or_hallucinated_relevance": "",  # yes/no
                    "exclude_from_winrate": "",  # yes/no; use yes for truncated or otherwise invalid items
                },
            }
        )
        answer_key.append(
            {
                "schema_version": SCHEMA_VERSION,
                "item_id": item_id,
                "conversation_id": conversation_id,
                "turn": _turn_number(turn),
                "A": "ssl" if ssl_is_a else "baseline",
                "B": "baseline" if ssl_is_a else "ssl",
                "ssl_answer_key": "A" if ssl_is_a else "B",
                "baseline_answer_key": "B" if ssl_is_a else "A",
                "answer_A_sha256": _sha256_text(answer_a),
                "answer_B_sha256": _sha256_text(answer_b),
                "surfaced_cross_turn_seeds": surfaced_seeds,
            }
        )

    return review_items, answer_key


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_form(path: Path, review_items: list[dict[str, Any]], *, title: str) -> None:
    parts: list[str] = [
        f"# {title}",
        "",
        "Blind A/B review of cross-turn payoff events.",
        "",
        "Procedure:",
        "",
        "1. Choose A, B, or tie before looking at seed context.",
        "2. Score both answers on the criteria.",
        "3. Only then inspect seed context and assess the seed effect.",
        "4. Mark an item invalid for win rate when an answer is clearly truncated.",
        "",
        "Scores: 1 = weak, 5 = strong.",
        "",
    ]
    for item in review_items:
        diag_a = item["answer_diagnostics"]["A"]
        diag_b = item["answer_diagnostics"]["B"]
        trunc_note = ""
        if diag_a["likely_truncated"] or diag_b["likely_truncated"]:
            trunc_note = (
                "\n\n> Note: this item has a truncation flag. Review its content, "
                "but consider excluding it from win rate if truncation affects the judgment."
            )
        parts.extend(
            [
                f"## Item {item['item_id']}",
                "",
                f"- Conversation: `{item['conversation_id']}`",
                f"- Domain: `{item['domain']}`",
                f"- Turn: `{item['turn']}`",
                f"- Diagnostics A: `{diag_a['word_count']} words`, likely_truncated=`{diag_a['likely_truncated']}`",
                f"- Diagnostics B: `{diag_b['word_count']} words`, likely_truncated=`{diag_b['likely_truncated']}`",
                trunc_note.strip(),
                "",
                "### Question/context",
                "",
                item["question"],
                "",
                "### Answer A",
                "",
                item["answer_A"],
                "",
                "### Answer B",
                "",
                item["answer_B"],
                "",
                "### Choice",
                "",
                "- [ ] A is better",
                "- [ ] B is better",
                "- [ ] Tie / no clear winner",
                "- [ ] Invalid for win rate due to truncation or artifact problem",
                "",
                "### Scores",
                "",
                "| Criterion | A | B |",
                "|---|---:|---:|",
                "| Content completeness |  |  |",
                "| Relevance to the question |  |  |",
                "| Specificity / precision |  |  |",
                "| No noise or hallucinated relevance |  |  |",
                "| Usefulness as an answer |  |  |",
                "",
                "### Short rationale",
                "",
                "",
                "### Seed context, inspect only after choosing",
                "",
                "Surfaced cross-turn seeds:",
                "",
            ]
        )
        seeds = item["post_choice_seed_context"].get("surfaced_cross_turn_seeds") or []
        if seeds:
            parts.extend([f"- {seed}" for seed in seeds])
        else:
            parts.append("- n/a")
        parts.extend(
            [
                "",
                "Seed effect:",
                "",
                "- [ ] promoted seed clearly helps",
                "- [ ] promoted seed helps slightly",
                "- [ ] promoted seed makes no difference",
                "- [ ] promoted seed adds noise",
                "- [ ] promoted seed narrows the answer",
                "",
            ]
        )
    path.write_text("\n".join(part for part in parts if part is not None).rstrip() + "\n", encoding="utf-8")


def write_scoring_csv(path: Path, review_items: list[dict[str, Any]]) -> None:
    fields = [
        "item_id",
        "conversation_id",
        "domain",
        "turn",
        "winner",
        "content_completeness_A",
        "content_completeness_B",
        "question_relevance_A",
        "question_relevance_B",
        "specificity_sharpness_A",
        "specificity_sharpness_B",
        "no_noise_A",
        "no_noise_B",
        "usefulness_A",
        "usefulness_B",
        "seed_effect_after_choice",
        "noise_or_hallucinated_relevance",
        "exclude_from_winrate",
        "motivation",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in review_items:
            writer.writerow(
                {
                    "item_id": item["item_id"],
                    "conversation_id": item["conversation_id"],
                    "domain": item["domain"],
                    "turn": item["turn"],
                    "exclude_from_winrate": (
                        "suggest_review"
                        if item["answer_diagnostics"]["A"]["likely_truncated"]
                        or item["answer_diagnostics"]["B"]["likely_truncated"]
                        else ""
                    ),
                }
            )


def write_summary(
    path: Path,
    payload: dict[str, Any],
    review_items: list[dict[str, Any]],
    answer_key: list[dict[str, Any]],
    *,
    input_path: Path,
    review_items_path: Path,
    answer_key_path: Path,
    seed: int,
    prefix: str,
) -> None:
    by_conv: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    truncation_flags = 0

    for item in review_items:
        by_conv[item["conversation_id"]] = by_conv.get(item["conversation_id"], 0) + 1
        domain = item.get("domain") or ""
        by_domain[domain] = by_domain.get(domain, 0) + 1
        if item["answer_diagnostics"]["A"]["likely_truncated"] or item["answer_diagnostics"]["B"]["likely_truncated"]:
            truncation_flags += 1

    legacy_embedded_key_present = bool(payload.get("blind_answer_key") or payload.get("legacy_internal_blind_answer_key"))

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source_summary": payload.get("summary", {}),
        "source_artifact_path": str(input_path),
        "source_artifact_sha256": _sha256_file(input_path),
        "review_pack_prefix": prefix,
        "shuffle_seed": seed,
        "blind_review_item_count": len(review_items),
        "items_by_conversation": by_conv,
        "items_by_domain": by_domain,
        "ssl_answer_distribution": {
            "A": sum(1 for key in answer_key if key["ssl_answer_key"] == "A"),
            "B": sum(1 for key in answer_key if key["ssl_answer_key"] == "B"),
        },
        "truncation": {
            "items_with_likely_truncated_answer": truncation_flags,
            "policy": "Review inhoudelijk, maar sluit duidelijk afgekapte items uit van win-rate.",
        },
        "integrity": {
            "review_items_sha256": _sha256_file(review_items_path),
            "answer_key_sha256": _sha256_file(answer_key_path),
            "hash_basis": "actual UTF-8 artifact bytes as written to disk",
            "answer_key_is_canonical": True,
            "legacy_embedded_blind_key_present": legacy_embedded_key_present,
            "note": (
                "Use this generated answer key for unblinding. Any embedded SSL-session "
                "blind fields are legacy/debug only and must not be used for scoring."
            ),
        },
    }
    write_json(path, summary)


def _prefix_path(output_dir: Path, prefix: str, suffix: str) -> Path:
    safe_prefix = _safe_prefix(prefix)
    return output_dir / f"{safe_prefix}_{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to ssl_session_suite.json")
    parser.add_argument("--output-dir", required=True, help="Directory for generated review files")
    parser.add_argument("--seed", type=int, default=45, help="Randomization seed for balanced A/B assignment")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Filename prefix for generated review files")
    parser.add_argument("--title", default="SSL session blind A/B review", help="Review form title")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = _safe_prefix(args.prefix)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    review_items, answer_key = build_review_pack(payload, seed=args.seed)

    review_items_path = _prefix_path(output_dir, prefix, "review_items.json")
    answer_key_path = _prefix_path(output_dir, prefix, "answer_key.json")
    review_form_path = _prefix_path(output_dir, prefix, "review_form.md")
    scoring_template_path = _prefix_path(output_dir, prefix, "scoring_template.csv")
    summary_path = _prefix_path(output_dir, prefix, "summary.json")

    write_json(review_items_path, review_items)
    write_json(answer_key_path, answer_key)
    write_form(review_form_path, review_items, title=args.title)
    write_scoring_csv(scoring_template_path, review_items)
    write_summary(
        summary_path,
        payload,
        review_items,
        answer_key,
        input_path=input_path,
        review_items_path=review_items_path,
        answer_key_path=answer_key_path,
        seed=args.seed,
        prefix=prefix,
    )

    print(f"Generated {len(review_items)} blind A/B review items in {output_dir} with prefix {prefix!r}")


if __name__ == "__main__":
    main()
