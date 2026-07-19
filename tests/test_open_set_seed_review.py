from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.open_set_candidate_adapter import (
    _extract_first_entity,
    detect_open_set_candidates,
)
from shadowseed.benchmark.open_set_seed_review import detect_embedding, run_open_set_seed_review


DATA = "src/shadowseed/data/open_set_seed_review_sample.json"


def _seed_key(packet: dict) -> tuple[str, str]:
    return (str(packet["item_id"]), str(packet["seed_text"]))


def test_open_set_seed_review_outputs_packets(tmp_path: Path) -> None:
    output = tmp_path / "open_set.json"
    packets = tmp_path / "open_set_packets.json"
    run_open_set_seed_review(DATA, str(output), review_packet_path=str(packets))

    payload = json.loads(output.read_text(encoding="utf-8"))
    review_payload = json.loads(packets.read_text(encoding="utf-8"))

    assert payload["summary"]["evidence_layer"] == "open_set_seed_quality"
    assert payload["summary"]["artifact_contract_version"] == "open-review-0.2"
    assert payload["summary"]["item_count"] == 3
    assert payload["summary"]["accepted_count"] > 0
    assert payload["summary"]["rejected_count"] > 0
    assert payload["summary"]["reviewer_ids"] == ["reviewer_a", "reviewer_b"]
    assert payload["summary"]["reviewer_count"] == 2
    assert payload["summary"]["review_packet_count"] == review_payload["summary"]["packet_count"]
    assert payload["summary"]["review_packet_count"] == payload["summary"]["accepted_count"] * 2
    assert payload["summary"]["artifacts"]["seed_output"] == str(output)
    assert payload["summary"]["artifacts"]["review_packets"] == str(packets)
    assert payload["summary"]["fixed_scenario_priors_used"] is False
    assert payload["summary"]["expected_gaps_used"] is False
    assert payload["summary"]["ground_truth_seeds_used"] is False
    assert payload["summary"]["regression_gap_detector_used"] is False
    assert review_payload["summary"]["reject_codes"]
    assert review_payload["summary"]["seed_count"] == payload["summary"]["accepted_count"]
    assert review_payload["summary"]["reviewer_ids"] == ["reviewer_a", "reviewer_b"]
    assert review_payload["summary"]["reviewer_count"] == 2
    assert review_payload["summary"]["fixed_scenario_priors_used"] is False
    assert review_payload["summary"]["expected_gaps_used"] is False
    assert review_payload["summary"]["ground_truth_seeds_used"] is False
    assert review_payload["summary"]["regression_gap_detector_used"] is False
    assert review_payload["summary"]["expected_summary_artifacts"] == [
        "open_set_seed_review_summary.json",
        "open_set_disagreements.json",
        "open_set_review_report.md",
    ]
    assert review_payload["packets"][0]["review_status"] == "pending"
    assert "reviewer_id" in review_payload["packets"][0]
    assert "reviewer_slot" in review_payload["packets"][0]
    assert "reject_reason" in review_payload["packets"][0]

    reviewers_by_seed: dict[tuple[str, str], set[str]] = {}
    slots_by_seed: dict[tuple[str, str], set[int]] = {}
    for packet in review_payload["packets"]:
        key = _seed_key(packet)
        reviewers_by_seed.setdefault(key, set()).add(packet["reviewer_id"])
        slots_by_seed.setdefault(key, set()).add(packet["reviewer_slot"])

    assert reviewers_by_seed
    assert all(reviewers == {"reviewer_a", "reviewer_b"} for reviewers in reviewers_by_seed.values())
    assert all(slots == {1, 2} for slots in slots_by_seed.values())


def test_open_set_seed_review_accepts_custom_reviewer_ids(tmp_path: Path) -> None:
    output = tmp_path / "open_set.json"
    packets = tmp_path / "open_set_packets.json"
    run_open_set_seed_review(
        DATA,
        str(output),
        review_packet_path=str(packets),
        reviewer_ids=["alpha", "beta", "alpha", ""],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    review_payload = json.loads(packets.read_text(encoding="utf-8"))

    assert payload["summary"]["reviewer_ids"] == ["alpha", "beta"]
    assert payload["summary"]["reviewer_count"] == 2
    assert review_payload["summary"]["reviewer_ids"] == ["alpha", "beta"]
    assert review_payload["summary"]["packet_count"] == payload["summary"]["accepted_count"] * 2

    reviewers_by_seed: dict[tuple[str, str], set[str]] = {}
    for packet in review_payload["packets"]:
        reviewers_by_seed.setdefault(_seed_key(packet), set()).add(packet["reviewer_id"])

    assert all(reviewers == {"alpha", "beta"} for reviewers in reviewers_by_seed.values())


def test_open_set_candidate_adapter_produces_atomic_candidates_for_unknown_domain() -> None:
    item = {
        "id": "HF_AG_NEWS_001",
        "title": "Company announces new chip plan",
        "domain": "nieuws - Sci/Tech",
        "text": "Acme said it will launch a new chip after talks with customers and investors.",
    }

    candidates = detect_open_set_candidates(item)

    assert candidates
    assert len(candidates) <= 5
    assert all(len(candidate.split()) <= 18 for candidate in candidates)
    assert any("Acme" in candidate for candidate in candidates)
    assert any("Source" in candidate or "Evidence" in candidate for candidate in candidates)


def test_detect_open_set_candidates_ignores_generated_ag_news_title() -> None:
    item = {
        "id": "AG_NEWS_TEST_0",
        "title": "AG News Business #0",
        "domain": "nieuws - Business",
        "text": "Fears for pension after talks with unions at Turner Newall and Federal Mogul.",
    }

    candidates = detect_open_set_candidates(item)

    assert candidates
    assert all("News" not in candidate for candidate in candidates)
    assert all("Business" not in candidate for candidate in candidates)
    assert all("AG" not in candidate for candidate in candidates)


def test_detect_open_set_candidates_returns_empty_on_empty_input() -> None:
    assert detect_open_set_candidates({"title": "", "text": ""}) == []
    assert detect_open_set_candidates({"title": "   ", "text": "  "}) == []
    assert detect_open_set_candidates({}) == []


def test_extract_first_entity_finds_proper_noun_over_generic() -> None:
    assert _extract_first_entity("Acme said it will launch a new chip.") == "Acme"


def test_extract_first_entity_skips_generic_company_word() -> None:
    assert _extract_first_entity("Company announces new chip plan") is None


def test_extract_first_entity_handles_mixed_capitalized_tokens() -> None:
    combined = "Company announces new chip plan. Acme said it will launch."
    assert _extract_first_entity(combined) == "Acme"


def test_extract_first_entity_returns_none_on_empty() -> None:
    assert _extract_first_entity("") is None
    assert _extract_first_entity("   ") is None


def test_detect_embedding_preserves_non_latin_tokens() -> None:
    latin = detect_embedding("hello world")
    chinese = detect_embedding("你好 世界")
    arabic = detect_embedding("مرحبا بالعالم")

    assert latin.any()
    assert chinese.any()
    assert arabic.any()


def test_open_set_review_handles_unknown_hf_domains_without_regression_priors(tmp_path: Path) -> None:
    input_file = tmp_path / "hf_batch.json"
    output = tmp_path / "open_set.json"
    packets = tmp_path / "open_set_packets.json"
    input_file.write_text(
        json.dumps(
            {
                "version": "hf-open-set-test",
                "items": [
                    {
                        "id": "HF_AG_NEWS_001",
                        "title": "Company announces new chip plan",
                        "domain": "nieuws - Sci/Tech",
                        "text": "Acme said it will launch a new chip after talks with customers and investors.",
                    },
                    {
                        "id": "HF_AG_NEWS_002",
                        "title": "Market rises after rate decision",
                        "domain": "nieuws - Business",
                        "text": "Markets rose after the central bank announced a decision that affected investors.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    run_open_set_seed_review(str(input_file), str(output), review_packet_path=str(packets))
    payload = json.loads(output.read_text(encoding="utf-8"))
    review_payload = json.loads(packets.read_text(encoding="utf-8"))

    assert payload["summary"]["item_count"] == 2
    assert payload["summary"]["raw_candidate_count"] > 0
    assert payload["summary"]["accepted_count"] > 0
    assert payload["summary"]["review_packet_count"] == payload["summary"]["accepted_count"] * 2
    assert payload["summary"]["candidate_source_counts"] == {"open_set_candidate_adapter": 2}
    assert payload["summary"]["fixed_scenario_priors_used"] is False
    assert payload["summary"]["expected_gaps_used"] is False
    assert payload["summary"]["ground_truth_seeds_used"] is False
    assert payload["summary"]["regression_gap_detector_used"] is False
    assert review_payload["summary"]["packet_count"] > 0
    assert review_payload["summary"]["candidate_source_counts"] == {"open_set_candidate_adapter": 2}
    assert review_payload["packets"]
    assert all(packet["review_status"] == "pending" for packet in review_payload["packets"])

    reviewers_by_seed: dict[tuple[str, str], set[str]] = {}
    for packet in review_payload["packets"]:
        reviewers_by_seed.setdefault(_seed_key(packet), set()).add(packet["reviewer_id"])
    assert all(reviewers == {"reviewer_a", "reviewer_b"} for reviewers in reviewers_by_seed.values())
