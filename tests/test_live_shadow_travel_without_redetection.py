"""Characterization of the ALREADY-EXISTING shadow-following route.

Uses the public detached ShadowseedEngine over genuine successive turns. The
detector proposes one investigator-scripted seed ONCE; all later detections are
explicitly empty. The host supplies equal visible answers to a NONE control.
No model calls, new Gate, new memory, new probe or Q1/Q2 efficacy claim.

This test distinguishes weightless storage, context/TrTL reactivation, actual
detector recurrence and forbidden answer influence. It deliberately records
current behavior: a related turn while the seed is ACTIVE does NOT by itself
add an occurrence or refresh trace; only DORMANT seeds enter the TrTL scan.
That behavior is *not* asserted as correct research doctrine.
"""
from __future__ import annotations

import numpy as np

from shadowseed import ShadowseedEngine


SEED = "Hoe hangen oorzaken en gevolgen samen?"


class _OneCandidateThenNone:
    name = "investigator-scripted-detector"
    prompt_variant = "research-single-seed"

    def __init__(self, seed: str | None) -> None:
        self.seed = seed
        self.calls = 0

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        assert isinstance(item["question"], str)
        assert isinstance(item["text"], str)
        self.calls += 1
        return [self.seed] if self.calls == 1 and self.seed is not None else []


def _embed(text: str) -> np.ndarray:
    """Synthetic 2-D embedding only for a reproducible *mechanics* test."""
    return np.array(
        [1.0, 0.0] if "oorzaken" in text.lower() else [0.0, 1.0],
        dtype=float,
    )


def _engine(seed: str | None) -> tuple[ShadowseedEngine, _OneCandidateThenNone]:
    detector = _OneCandidateThenNone(seed)
    engine = ShadowseedEngine(
        detector_backend=detector,
        embedding_fn=_embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    return engine, detector


def _turn(engine: ShadowseedEngine, question: str, answer: str) -> tuple[object, dict]:
    prepared = engine.prepare_turn(question)
    # No weightless candidate is used to steer the host, even when similar.
    assert prepared.model_context == ""
    assert prepared.surfaced_seed_ids == ()
    report = engine.observe_turn(prepared, answer)
    assert report["answer"] == answer
    assert not report["surfaced_seed_ids"]
    assert not report["promoted_this_turn"]
    return prepared, report


def test_existing_shadow_travels_without_redetection_or_answer_influence() -> None:
    shadow, shadow_detector = _engine(SEED)
    none, none_detector = _engine(None)

    first = ("Welke metingen zijn beschikbaar?", "Het instrument toont één meting.")
    sp0, sr0 = _turn(shadow, *first)
    np0, nr0 = _turn(none, *first)
    assert len(sr0["seeds_born_weightless"]) == 1
    assert not nr0["seeds_born_weightless"]

    initial = shadow.inspect()["seeds"]
    assert len(initial) == 1
    seed_id = initial[0]["id"]
    assert initial[0]["text"] == SEED
    assert initial[0]["trace"] > 0
    assert initial[0]["weight"] == 0
    assert initial[0]["evidence_count"] == 0
    assert initial[0]["occurrence_count"] == 1

    # Related content during the ACTIVE stage is not detector recurrence.
    relevant = ("Hoe hangen oorzaken en gevolgen samen?", "We beschikken niet over extra bewijs.")
    sp1, sr1 = _turn(shadow, *relevant)
    np1, nr1 = _turn(none, *relevant)
    still_active = shadow.inspect()["seeds"][0]
    assert sp1.reactivated_trtl == ()
    assert still_active["trace"] < initial[0]["trace"]
    assert still_active["occurrence_count"] == 1
    assert still_active["weight"] == 0
    assert not sr1["seeds_born_weightless"]

    # Genuine later turns with no detector redetection or seed text in the answer.
    filler = "Het antwoord bevat geen nieuwe bevestiging."
    for index in range(1, 25):
        question = f"Welke losstaande instrumenten zijn beschikbaar in beurt {index}?"
        sp, sr = _turn(shadow, question, filler)
        np, nr = _turn(none, question, filler)
        assert not sp.reactivated_trtl
        assert not sr["seeds_born_weightless"]
        assert not nr["seeds_born_weightless"]
        state = shadow.inspect()["seeds"][0]
        assert state["weight"] == 0
        assert state["occurrence_count"] == 1
        assert not none.inspect()["seeds"]
        if state["status"] == "DORMANT":
            break
    else:
        raise AssertionError("existing TTL failed to produce a dormant seed")

    dormant = shadow.inspect()["seeds"][0]
    before_trace = dormant["trace"]
    # This existing, non-influence TrTL path uses the new incoming question.
    question = "Wat betekenen die oorzaken in dit geval?"
    sp_final = shadow.prepare_turn(question)
    np_final = none.prepare_turn(question)
    assert sp_final.reactivated_trtl == (seed_id,)
    assert np_final.reactivated_trtl == ()
    assert sp_final.model_context == np_final.model_context == ""
    assert sp_final.surfaced_seed_ids == np_final.surfaced_seed_ids == ()
    reawakened = shadow.inspect()["seeds"][0]
    assert reawakened["status"] == "NEW"
    assert reawakened["trace"] > before_trace
    assert reawakened["weight"] == 0
    assert reawakened["occurrence_count"] == 1
    assert reawakened["evidence_count"] == 0

    answer = "De gewone host blijft bij zijn zichtbare antwoord."
    sr_final = shadow.observe_turn(sp_final, answer)
    nr_final = none.observe_turn(np_final, answer)
    assert sr_final["answer"] == nr_final["answer"] == answer
    assert not sr_final["seeds_born_weightless"]
    assert not nr_final["seeds_born_weightless"]
    assert shadow_detector.calls == none_detector.calls == shadow.turn
    assert shadow.turn == none.turn
    assert not none.inspect()["seeds"]
    assert shadow.inspect()["influence_records"] == none.inspect()["influence_records"] == []
    assert shadow.audit() == none.audit() == 0

    # A reactivation records lifespan/observational relevance ONLY, NOT a new
    # model-generated question, independent evidence, authority or Q2 effect.
