"""Mechanical prescreen for open-set model-detector output (triage aid).

This script reads an ``open_set_seed_output.json`` produced by
``shadowseed run-open-set-seed-review --detector model`` and flags candidate
gaps ("candidate gaps") against the v0.3g prompt's own form contract:
the canonical candidate is a gap-label noun phrase (or an absence sentence);
asserting a fact is the failure mode.

IMPORTANT — what this is and is NOT:

- It is a *deterministic* triage aid. It only flags failure modes that can be
  detected without reading for meaning (absence-phrasing, truncated clauses,
  parse leaks, HTML entities, English echo, few-shot copying, non-atomic
  shape, and redundant near-duplicate restatements within an item).
- ``truncated`` and ``claim_vs_gap`` are mutually exclusive diagnoses for a
  missing absence marker. A candidate that opens a subordinate clause
  ("Of ...") but never reaches its "wordt niet vermeld" scaffold was cut off
  by the decoding budget or the line parser — that is a truncation artifact,
  not a claim-form regression of the prompt. Conflating the two (as the
  round 005 offset-12 batch showed: all nine "claim_vs_gap" flags there were
  unfinished clauses, human-rejected as ``not_testable``) points the next
  prompt iteration at the wrong root cause.
- ``near_duplicate`` flags only near-identical rewordings of the SAME gap (high
  content-overlap). Distinct-but-related gaps are deliberately spared: in SSL a
  cluster of related gaps is potential Constellation material (4.5 §9.1), not
  noise.
- It is NOT human review. It does NOT count as ``reviewer_a``/``reviewer_b``
  and NOT as ``open_set_seed_quality`` (Layer C) evidence.
- It is NOT even the AI-judgment prescreen used in round 004: it makes no
  accept/borderline/reject verdict, because that needs reading.
- ``false_gap`` (naming something absent that is actually in the text),
  ``mistranslation`` and ``grammar`` are explicitly NOT checked here; they
  require a human or AI reader. They are listed so a reader knows to look.

Consistent with merge #109: detector output is candidate-only. Status (seed,
evidence, Round) is granted later by review/manager/gate/core, never here.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from shadowseed.detection.model_detector import (
    _HTML_ENTITY,
    _looks_like_citation_fragment,
    _looks_like_fewshot_leak,
)
from shadowseed.manager import SSLManager

# Absence markers that match the v0.3e prompt's required forms
# ("... wordt niet genoemd", "... is niet aangegeven", "... ontbreekt").
_ABSENCE_MARKERS: tuple[str, ...] = (
    "ontbreek",  # ontbreekt / ontbreken
    "wordt niet",
    "worden niet",
    "word niet",
    "is niet vermeld",
    "niet vermeld",
    "niet genoemd",
    "niet benoemd",
    "niet aangegeven",
    "niet gespecificeerd",
    "niet beschreven",
    "niet toegelicht",
    "niet uitgelegd",
    "niet gegeven",
    "niet bekend",
    "niet duidelijk",
    "niet gemaakt",  # "... wordt niet duidelijk gemaakt"
    "onduidelijk",
    "onbekend",
    "onvermeld",
)

# A short list of English function words. Two or more as whole words inside a
# nominally-Dutch gap signals an untranslated echo from the source text.
# Dutch/English homographs ("of", "in", "is", "was", "her") are deliberately
# EXCLUDED: every v0.3e gap is phrased "Of ... wordt niet vermeld", so counting
# "Of"/"in"/"is" as English would false-flag well-formed Dutch output.
_ENGLISH_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "and", "for", "with", "are", "were", "to", "on", "at", "by",
        "from", "that", "this", "their", "his", "has", "have", "been", "will",
        "would", "after", "about", "into",
    }
)

# An embedded "<n>. " mid-sentence indicates a parser/numbering leak: a second
# numbered item bled into one candidate.
_EMBEDDED_NUMBER = re.compile(r"\S\s+\d+[.)]\s+[A-Z]")

# --- claim detection (v0.3g form contract) -----------------------------------
# Since v0.3g the canonical candidate form is the gap-label noun phrase
# ("De prijs van de bundle.", "Koloniaal kapitaal als financieringsbron ...");
# the absence sentence ("... wordt niet vermeld.") stays allowed. What is
# forbidden is ASSERTING a fact. A noun phrase has no main-clause finite verb,
# so `claim_vs_gap` now means: a finite verb occurs in the MAIN clause (before
# any relative/subordinating word) and no absence marker is present. Finite
# verbs inside relative clauses ("... die zijn voorspeld voor LHC") are fine.
# The verb list covers auxiliaries, copulas and common finite verbs; rare main
# verbs can slip through — this stays a triage heuristic, not a verdict.
_FINITE_VERBS = re.compile(
    r"\b(is|zijn|was|waren|wordt|worden|werd|werden|heeft|hebben|had|hadden|"
    r"kan|kunnen|mag|mogen|moet|moeten|wil|willen|zal|zullen|zou|zouden|"
    r"blijkt|blijken|lijkt|lijken|gaat|gaan|doet|doen|maakt|maken|geeft|geven|"
    r"staat|staan|komt|komen|ligt|liggen|valt|vallen|vormt|vormen|biedt|bieden|"
    r"speelt|spelen|leidt|leiden|zorgt|zorgen|betekent|betekenen|toont|tonen|"
    r"bevat|bevatten|weet|weten|ontbreekt|ontbreken)\b"
)
_SUBORDINATOR = re.compile(
    r"\b(die|dat|waar|waarin|waarmee|waarop|waarvan|waarbij|waardoor|waarvoor|"
    r"waaraan|waaruit|waarover|wat|wie|welke|hoe|hoeveel|waarom|wanneer|"
    r"zoals|omdat|doordat|terwijl|hoewel|of)\b"
)


def _asserts_a_fact(lowered: str) -> bool:
    """True when a finite verb appears in the main clause (pre-subordinator)."""
    cut = _SUBORDINATOR.search(lowered)
    main_clause = lowered[: cut.start()] if cut else lowered
    # "ontbreekt/ontbreken" as the main verb is the legitimate absence form,
    # not an assertion ("Kapitaalvorming ontbreekt.").
    match = _FINITE_VERBS.search(main_clause)
    if not match:
        return False
    return match.group(1) not in ("ontbreekt", "ontbreken")

# Subordinate-clause openers of the v0.3e scaffold ("Of X ..., wordt niet
# vermeld."). A candidate that starts with one of these but never reaches an
# absence marker is an unfinished clause: the generation or the parser cut it
# off before the scaffold could close. That is `truncated`, not `claim_vs_gap`.
_SUBORDINATE_OPENERS: tuple[str, ...] = (
    "of ",
    "wat ",
    "wie ",
    "waar ",
    "waarom ",
    "wanneer ",
    "hoe ",
    "hoeveel ",
    "welke ",
    "in hoeverre ",
)

# Dutch function words that cannot end a complete sentence. A candidate whose
# last word is one of these was cut off mid-clause, even if an absence marker
# appears earlier in the sentence. Verbs are deliberately NOT in this list:
# Dutch subordinate clauses legitimately end in a verb ("... waar de
# wildfires voorspeld worden.", "... wat ze mogen."), so a bare verb tail is
# not evidence of truncation. Truncated clauses that end in a verb without a
# marker (round 005: "... die mensen mogen.") are caught by the
# opener-without-marker rule above; marker-bearing cutoffs at a dangling
# auxiliary ("... wordt niet vermeld en zal") are caught by the
# conjunction+auxiliary tail rule below.
_TRUNCATION_TAIL: frozenset[str] = frozenset(
    {
        "de", "het", "een", "te", "dat", "die", "of", "en", "met", "in", "op",
        "aan", "van", "tot", "naar", "voor", "om", "per", "bij", "onder",
        "over", "tussen", "door", "uit", "als", "dan", "maar", "want", "dus",
        "er", "deze", "dit", "hun", "haar",
    }
)

# A modal/auxiliary as the very last word is legitimate in a subordinate
# clause ("... wat ze mogen.") but is a dangling clause start when it
# directly follows a conjunction or determiner ("... en zal", "... of een
# wordt"). Only that combination counts as truncation evidence.
_AUX_TAILS: frozenset[str] = frozenset(
    {
        "zal", "zullen", "kan", "kunnen", "mag", "mogen", "moet", "moeten",
        "wil", "willen", "zou", "zouden", "wordt", "worden", "werd", "werden",
        "heeft", "hebben", "had", "hadden", "is", "was", "waren",
    }
)
_DANGLING_BEFORE_AUX: frozenset[str] = frozenset(
    {
        "en", "maar", "of", "want", "dus", "die", "dat", "deze", "dit",
        "de", "het", "een", "te", "ook", "nog", "niet",
    }
)

# Scaffold words shared by almost every v0.3e gap ("Of ... wordt niet vermeld").
# They are stripped before measuring overlap so similarity reflects the *gap
# content*, not the absence scaffold every seed shares.
_SCAFFOLD_WORDS: frozenset[str] = frozenset(
    {
        "een", "het", "wordt", "worden", "word", "niet", "vermeld", "vermeldt",
        "aangegeven", "genoemd", "benoemd", "beschreven", "gespecificeerd",
        "toegelicht", "uitgelegd", "gegeven", "bekend", "duidelijk", "gemaakt",
        "ontbreekt", "ontbreken", "onduidelijk", "onbekend", "onvermeld",
        "sprake", "heeft", "hebben", "was", "zijn", "naar", "voor", "van",
        "door", "dat", "met", "deze", "die", "hun", "ook", "wat", "hoeveel",
    }
)

# Jaccard threshold for flagging a candidate as a redundant restatement of an
# EARLIER candidate in the same item. Set high on purpose (aligned with SSL's
# own dedup at cosine 0.85, 4.5 §12.4): we flag near-identical rewordings of the
# SAME gap, NOT distinct-but-related gaps — those are Constellation material
# (4.5 §9.1) and must survive.
_NEAR_DUPLICATE_THRESHOLD = 0.7

# Mechanically detectable codes.
MECHANICAL_CODES: tuple[str, ...] = (
    "claim_vs_gap",
    "truncated",
    "parse_leak",
    "language_leak",
    "entity_bleed",
    "citation_fragment",
    "fewshot_leak",
    "not_atomic",
    "near_duplicate",
)

# Codes that need a reader; surfaced for transparency but never auto-assigned.
NON_MECHANICAL_CODES: tuple[str, ...] = ("false_gap", "mistranslation", "grammar")


def prescreen_seed(seed: str, source_text: str = "") -> list[str]:
    """Return the mechanical failure codes for one candidate gap."""
    codes: list[str] = []
    lowered = seed.lower()

    has_marker = any(marker in lowered for marker in _ABSENCE_MARKERS)
    words = re.findall(r"[a-zà-ÿ0-9]+", lowered)
    tail_truncated = bool(words) and words[-1] in _TRUNCATION_TAIL
    if (
        not tail_truncated
        and len(words) >= 2
        and words[-1] in _AUX_TAILS
        and words[-2] in _DANGLING_BEFORE_AUX
    ):
        tail_truncated = True
    opener_truncated = lowered.startswith(_SUBORDINATE_OPENERS) and not has_marker
    if opener_truncated or tail_truncated:
        codes.append("truncated")
    elif not has_marker and _asserts_a_fact(lowered):
        codes.append("claim_vs_gap")

    if _EMBEDDED_NUMBER.search(seed):
        codes.append("parse_leak")

    english_hits = sum(1 for tok in re.findall(r"[a-zA-Z]+", lowered) if tok in _ENGLISH_STOPWORDS)
    if english_hits >= 2:
        codes.append("language_leak")

    if _HTML_ENTITY.search(seed):
        codes.append("entity_bleed")

    if _looks_like_citation_fragment(seed, source_text):
        codes.append("citation_fragment")

    if _looks_like_fewshot_leak(seed):
        codes.append("fewshot_leak")

    if not SSLManager.is_atomic_seed(seed):
        codes.append("not_atomic")

    return codes


def _content_tokens(text: str) -> set[str]:
    """Content tokens of a gap: words >2 chars, minus the absence scaffold."""
    return {
        tok
        for tok in re.findall(r"[a-zà-ÿ0-9]+", text.lower())
        if len(tok) > 2 and tok not in _SCAFFOLD_WORDS
    }


def _near_duplicate_indices(
    candidates: list[str], threshold: float = _NEAR_DUPLICATE_THRESHOLD
) -> set[int]:
    """Indices of candidates that restate an EARLIER candidate in the same item.

    Compares Jaccard overlap of content tokens. Keeps the first occurrence
    clean and flags later near-identical rewordings only. Distinct-but-related
    gaps stay below the threshold and are NOT flagged: in SSL they are potential
    Constellation members (4.5 §9.1), not noise.
    """
    token_sets = [_content_tokens(c) for c in candidates]
    flagged: set[int] = set()
    for i in range(len(candidates)):
        for j in range(i):
            a, b = token_sets[i], token_sets[j]
            if not a or not b:
                continue
            jaccard = len(a & b) / len(a | b)
            if jaccard >= threshold:
                flagged.add(i)
                break
    return flagged


def _source_text_index(input_batch: dict[str, Any] | None) -> dict[str, str]:
    if not input_batch:
        return {}
    index: dict[str, str] = {}
    for item in input_batch.get("items", []):
        item_id = str(item.get("id") or item.get("item_id") or "")
        text = str(item.get("text") or item.get("input") or "")
        if item_id:
            index[item_id] = text
    return index


def prescreen_output(
    seed_output: dict[str, Any],
    input_batch: dict[str, Any] | None = None,
    round_label: str = "unknown",
) -> dict[str, Any]:
    """Build a mechanical prescreen report over a seed_output payload."""
    summary = seed_output.get("summary", {})
    source_index = _source_text_index(input_batch)

    verdicts: list[dict[str, Any]] = []
    failure_code_counts: dict[str, int] = {code: 0 for code in MECHANICAL_CODES}
    flagged = 0

    results = seed_output.get("results", [])
    item_count = len(results)
    items_empty = 0

    for result in results:
        item_id = str(result.get("item_id", ""))
        source_text = source_index.get(item_id, "")
        candidates = result.get("normalized_candidates") or result.get("raw_candidates") or []
        if not candidates:
            items_empty += 1
        dup_indices = _near_duplicate_indices(candidates)
        for position, seed in enumerate(candidates, start=1):
            codes = prescreen_seed(seed, source_text)
            if (position - 1) in dup_indices:
                codes.append("near_duplicate")
            for code in codes:
                failure_code_counts[code] += 1
            if codes:
                flagged += 1
            verdicts.append(
                {
                    "item_id": item_id,
                    "position": position,
                    "seed": seed,
                    "codes": codes,
                    "clean": not codes,
                }
            )

    seed_count = len(verdicts)
    return {
        "artifact": "mechanical_prescreen",
        "disclaimer": (
            "Deterministic prescreen, NOT human review. It does NOT count as "
            "reviewer_a/reviewer_b or open_set_seed_quality (Layer C) "
            "evidence and gives NO accept/reject verdict. It is intended to focus "
            "attention and test the v0.3e prompt against its own rules."
        ),
        "round": round_label,
        "detector": summary.get("detector"),
        "model_backend": summary.get("model_backend"),
        "yield": {
            "item_count": item_count,
            "items_with_candidates": item_count - items_empty,
            "items_empty": items_empty,
            "empty_rate": round(items_empty / item_count, 3) if item_count else 0.0,
            "mean_candidates_per_item": round(seed_count / item_count, 3) if item_count else 0.0,
        },
        "mechanical_codes": list(MECHANICAL_CODES),
        "not_mechanically_checkable": list(NON_MECHANICAL_CODES),
        "seed_count": seed_count,
        "flagged_count": flagged,
        "clean_count": seed_count - flagged,
        "clean_rate": round((seed_count - flagged) / seed_count, 3) if seed_count else 0.0,
        "near_duplicate_rate": round(failure_code_counts["near_duplicate"] / seed_count, 3)
        if seed_count
        else 0.0,
        "failure_code_counts": failure_code_counts,
        "verdicts": verdicts,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Mechanical prescreen - {report['round']} (NOT human review)")
    lines.append("")
    lines.append(f"> **Status: deterministic aid, not evidence.** {report['disclaimer']}")
    lines.append("")
    lines.append(
        f"Detector: `{report.get('detector')}` · backend: `{report.get('model_backend')}`"
    )
    lines.append("")
    y = report["yield"]
    lines.append("## Yield (does the model produce candidates?)")
    lines.append("")
    lines.append(
        f"- items: **{y['item_count']}** · with candidates: **{y['items_with_candidates']}** "
        f"· empty: **{y['items_empty']}** (empty-rate **{y['empty_rate']}**)"
    )
    lines.append(f"- mean candidates per item: **{y['mean_candidates_per_item']}**")
    lines.append("")
    lines.append(
        f"## Quality of produced candidates ({report['seed_count']} candidate gaps)"
    )
    lines.append("")
    lines.append(f"- clean (no mechanical flag): **{report['clean_count']}**")
    lines.append(f"- flagged: **{report['flagged_count']}**")
    lines.append(f"- clean-rate: **{report['clean_rate']}**")
    lines.append(f"- near-duplicate-rate: **{report['near_duplicate_rate']}**")
    lines.append("")
    lines.append("## Mechanical failure codes")
    lines.append("")
    for code, count in sorted(
        report["failure_code_counts"].items(), key=lambda kv: (-kv[1], kv[0])
    ):
        lines.append(f"- `{code}`: {count}")
    lines.append("")
    lines.append("## Not mechanically checkable (requires a reviewer)")
    lines.append("")
    lines.append("- " + ", ".join(f"`{c}`" for c in report["not_mechanically_checkable"]))
    lines.append("")
    return "\n".join(lines) + "\n"


def _load_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "seed_output",
        help="Path to open_set_seed_output.json ({summary, results}).",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional HF input batch (items with id+text) for quotation and context checks.",
    )
    parser.add_argument(
        "--round",
        default="unknown",
        help="Round label, for example round_005.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the prescreen JSON; a Markdown report is written next to it. "
        "Empty means stdout.",
    )
    args = parser.parse_args(argv)

    seed_output = _load_json(args.seed_output)
    assert seed_output is not None
    input_batch = _load_json(args.input)
    report = prescreen_output(seed_output, input_batch, round_label=args.round)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote {out} and {out.with_suffix('.md')}")
    else:
        print(render_markdown(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
