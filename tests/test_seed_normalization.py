import numpy as np

from shadowseed.benchmark.open_set_seed_review import detect_embedding
from shadowseed.manager import SSLManager
from shadowseed.seed_normalization import normalize_detection_candidates, split_broad_seed_text


def test_split_broad_seed_text_breaks_list_like_detection():
    parts = split_broad_seed_text("Security, privacy en schaalbaarheid ontbreken.")

    assert len(parts) == 3
    assert all(part.endswith("ontbreekt.") for part in parts)


def test_normalize_detection_candidates_expands_broad_candidate():
    normalized = normalize_detection_candidates([
        "Voeg een analysekader toe met aandacht voor security, privacy en schaalbaarheid"
    ])

    assert len(normalized) >= 3


def test_normalize_keeps_single_relational_seed_with_and_intact():
    normalized = normalize_detection_candidates([
        "Encryptie van medische data in rust en tijdens transport."
    ])

    assert normalized == ["Encryptie van medische data in rust en tijdens transport."]


def test_manager_ingest_detection_candidates_keeps_accept_reject_split():
    manager = SSLManager(embedding_fn=lambda _text: __import__("numpy").array([1.0, 0.0, 0.0]))
    result = manager.ingest_detection_candidates([
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
        "Security, privacy en schaalbaarheid ontbreken.",
    ])

    assert len(result["accepted"]) == 1
    assert result["accepted"][0]["seed_id"] == "ss_001"
    assert len(result["rejected"]) == 3


def test_expand_short_fragments_default_adds_ontbreekt_to_broad_categories():
    # legacy human-written categories still expand
    normalized = normalize_detection_candidates(["kolonialisme"])
    assert normalized == ["kolonialisme ontbreekt."]


def test_expand_short_fragments_disabled_keeps_model_fragments_as_is():
    # when output comes from a real taalmodel detector, short stubs are
    # left visible instead of being dressed up with "ontbreekt"
    normalized = normalize_detection_candidates(
        ["TORONTO", "FOAF", "Bloom Filters"],
        expand_short_fragments=False,
    )
    assert normalized == ["TORONTO.", "FOAF.", "Bloom Filters."]
    for seed in normalized:
        assert "ontbreekt" not in seed.lower()


def test_expand_short_fragments_disabled_still_keeps_full_sentence_seeds():
    sentence = "Motivatie van Sven Jaschan om de Netsky-worm te schrijven."
    normalized = normalize_detection_candidates([sentence], expand_short_fragments=False)
    assert normalized == [sentence]


def test_manager_ingest_passes_expand_flag_through():
    manager = SSLManager(embedding_fn=lambda _text: __import__("numpy").array([1.0, 0.0, 0.0]))
    result = manager.ingest_detection_candidates(
        ["TORONTO"],
        expand_short_fragments=False,
    )
    accepted_or_rejected = result["accepted"] + result["rejected"]
    assert any("TORONTO" in row["text"] for row in accepted_or_rejected)
    # without the flag the same input would have produced "TORONTO ontbreekt."
    legacy = manager.normalize_detection_candidates(["TORONTO"])
    assert legacy == ["TORONTO ontbreekt."]


def test_split_broad_disabled_keeps_comma_sentence_whole():
    # model output: a natural sentence with a comma must stay one seed instead
    # of being shredded into "Het aantal ..." + "wordt niet aangegeven."
    sentence = "Het aantal virusvarianten die kunnen ontstaan, wordt niet aangegeven."
    normalized = normalize_detection_candidates(
        [sentence], expand_short_fragments=False, split_broad=False
    )
    assert normalized == [sentence]


def test_split_broad_disabled_does_not_grow_candidate_count():
    raw = [
        "Er zijn andere virusontwikkelaars even belangrijk als Sven Jaschan, maar niet genoemd.",
        "Het aantal virusvarianten die kunnen ontstaan, wordt niet aangegeven.",
    ]
    normalized = normalize_detection_candidates(
        raw, expand_short_fragments=False, split_broad=False
    )
    assert len(normalized) == len(raw)
    assert not any(seed.strip().lower() == "wordt niet aangegeven." for seed in normalized)


def test_ingest_model_mode_keeps_unique_seed_ids_for_paraphrases():
    # a degenerate embedding makes every candidate look identical, which with
    # dedup ON would collapse distinct gaps onto one seed_id (the duplicate-id
    # bug). Model mode turns dedup OFF so each accepted gap keeps a unique id
    # and the human "duplicate" reject code decides real duplication.
    manager = SSLManager(embedding_fn=lambda _t: np.array([1.0, 0.0, 0.0]))
    result = manager.ingest_detection_candidates(
        [
            "Ontbreken van de reactie van Apple op de nieuwe service.",
            "Ontbreken van de reactie van andere retailers op de nieuwe service.",
            "Ontbreken van de prijsverdeling van de nieuwe downloadservice.",
        ],
        expand_short_fragments=False,
        split_broad=False,
        deduplicate=False,
        min_seed_words=4,
    )
    ids = [row["seed_id"] for row in result["accepted"]]
    assert len(result["accepted"]) == 3
    assert len(set(ids)) == 3


def test_ingest_model_mode_rejects_short_stub_and_exact_duplicate():
    manager = SSLManager(embedding_fn=detect_embedding)
    result = manager.ingest_detection_candidates(
        [
            "De #36;10 miljoen Ansari X Prize wordt niet genoemd.",
            "De naam van de tweede team is niet genoemd.",
            "De naam van de tweede team is niet genoemd.",
            "De #36",
        ],
        expand_short_fragments=False,
        split_broad=False,
        deduplicate=False,
        min_seed_words=4,
    )
    accepted_texts = [r["text"] for r in result["accepted"]]
    reject_reasons = sorted(r["reason"] for r in result["rejected"])
    # the mangled but whole "#36;10" sentence stays one seed, not two fragments
    assert "De #36;10 miljoen Ansari X Prize wordt niet genoemd." in accepted_texts
    assert "duplicate" in reject_reasons
    assert "too_vague" in reject_reasons
    ids = [r["seed_id"] for r in result["accepted"]]
    assert len(set(ids)) == len(ids)
