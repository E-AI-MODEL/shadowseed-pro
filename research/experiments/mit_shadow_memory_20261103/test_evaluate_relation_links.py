"""Regression tests for interpreting MIT relation links without conflating evidence."""
from research.experiments.mit_shadow_memory_20261103.evaluate_relation_links import (
    LABELS, CHALLENGES, build_cases, pair_cluster_links, parse_model_judgment,
)

def test_known_broad_thematic_links_remain_positive():
    assert pair_cluster_links(13,60) == [6]  # MLP edit related to head intervention
    assert pair_cluster_links(88,100) == [10] # random control related to sparse edit
    assert pair_cluster_links(27,84) == [12] # preserving state related to experiment
    assert pair_cluster_links(1,64) == [0]   # early mechanism / transfer

def test_no_link_is_not_a_claim_of_no_relationship():
    assert pair_cluster_links(81,82) == []   # identical text deduped by Engine
    assert pair_cluster_links(44,62) == []   # no recurrent cluster link
    assert pair_cluster_links(16,131) == []

def test_parser_preserves_distinct_related_label():
    raw = "LABEL: RELATED_DISTINCT\nREASON: The second mechanism tests a different component."
    x = parse_model_judgment(raw)
    assert x["valid"] is True
    assert x["label"] == "RELATED_DISTINCT"
    assert "different component" in x["reason"]

def test_parser_fails_closed_on_ambiguous_or_broken_format():
    for raw in (
        "I would say related.",
        "LABEL: SAME_CLAIM\nLABEL: RELATED_DISTINCT\nREASON: unclear",
        "LABEL: NO_CLEAR_DIRECT_LINK",
    ):
        assert parse_model_judgment(raw)["valid"] is False

def test_same_claim_not_independent_validation():
    x = parse_model_judgment("LABEL: SAME_CLAIM\nREASON: Exact repeated wording.")
    assert x["valid"] and x["label"] == "SAME_CLAIM"
    assert "independent" not in x

def test_case_generation_is_chronological_and_deduplicated():
    source = {
        "cases": [
            {"id": "a", "turn_a": 13,"turn_b": 60,"same_specific_test":"different_or_uncertain"},
            {"id": "b", "turn_a": 81,"turn_b": 82,"same_specific_test":"candidate_same"},
        ],
    }
    available = {i:"placeholder" for i in (13,60,81,82,44,62,16,131,154,34,27,123,74,98)}
    pairs = build_cases(source,available)
    assert len({(r["a"],r["b"]) for r in pairs}) == len(pairs)
    assert all(r["a"] < r["b"] for r in pairs)
    assert all(r["prior_label_is_ground_truth"] is False for r in pairs)
    assert any(r["a"]==44 and r["b"]==62 for r in pairs)

def test_label_vocabulary_mutually_exclusive():
    assert len(LABELS)==len(set(LABELS))==4
    assert len(CHALLENGES)==8
