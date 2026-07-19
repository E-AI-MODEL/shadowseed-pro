"""End-to-end: a bad/irrelevant seed dies out and cannot come back.

This closes the round-014 loop across the whole lifecycle: detection → scoring →
Gate (contradiction) → TTL decay → terminal EXPIRED. The doctrinal claim is that
the *lifecycle* (not the revision step) is the safety layer: a seed like the
round-014 "emperor-penguin" distractor never survives to influence an answer.
"""

from __future__ import annotations

import numpy as np

from shadowseed.benchmark.ssl45_gap_suite import apply_ssl45_validation, score_seed
from shadowseed.manager import SSLManager, SeedStatus


def _embedding(text: str) -> np.ndarray:
    v = np.array(
        [float((len(text) % 7) + 1), float((sum(map(ord, text)) % 11) + 1)],
        dtype=float,
    )
    return v / np.linalg.norm(v)


def test_irrelevant_seed_dies_out_and_stays_dead():
    m = SSLManager(embedding_fn=_embedding)
    bad = "De broedgewoonten van de keizerspinguin op Antarctica."

    # 1. detection: the irrelevant seed enters shadow memory at birth (weight 0)
    sid = m.add_or_update_seed(bad)
    assert m.seeds[sid].status == SeedStatus.NEW
    assert m.seeds[sid].weight == 0.0

    # 2. scoring against the scenario's real gaps -> no relevant match (score 0)
    ground_truth = [
        {"text": "Volgorde-risico van rendementen rond de pensioneringsdatum."},
        {"text": "Concentratierisico in marktgewogen indexfondsen."},
    ]
    scored = score_seed(bad, ground_truth)
    assert scored.score == 0

    # 3. Gate contradicts it: weight stays 0, back to NEW, trace knocked down so
    #    the disappearance clock starts (the same path the suites use for score-0)
    trace_before = m.seeds[sid].trace
    apply_ssl45_validation(m, sid, scored)
    assert m.seeds[sid].weight == 0.0
    assert m.seeds[sid].status == SeedStatus.NEW
    assert m.seeds[sid].trace < trace_before

    # 4. it is never re-recognised -> TTL: decays to DORMANT then EXPIRED
    saw_dormant = False
    for _ in range(60):
        m.decay_traces(turns_passed=1)
        if m.seeds[sid].status == SeedStatus.DORMANT:
            saw_dormant = True
        if m.seeds[sid].status == SeedStatus.EXPIRED:
            break
    assert saw_dormant, "seed should pass through DORMANT before expiring"
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    assert any(
        e.event_type == "expired" and e.detail.get("reason") == "dormant_ttl"
        for e in m.event_log
    )

    # 5. terminal: it cannot come back by any route
    # 5a. TrTL trigger (even an exact-text match) does not revive an EXPIRED seed
    assert m.scan_trtl_triggers(bad) == []
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    # 5b. the Gate is a no-op on an EXPIRED seed
    m.run_validation_gate(sid, external_evidence=True)
    m.run_validation_gate(sid, external_evidence=True)
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    assert m.seeds[sid].weight == 0.0
    # 5c. re-detection of the same gap creates a NEW seed, not a resurrection
    new_id = m.add_or_update_seed(bad)
    assert new_id != sid
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    assert m.seeds[new_id].status == SeedStatus.NEW


def test_recurring_relevant_seed_survives_the_same_pressure():
    """Control: a genuinely recurring (TrTL-recognised) seed does NOT die out
    under the same decay pressure — the lifecycle removes noise, not signal."""
    m = SSLManager(embedding_fn=_embedding)
    good = "Concentratierisico in marktgewogen indexfondsen."
    sid = m.add_or_update_seed(good)
    m.seeds[sid].status = SeedStatus.DORMANT  # drifted toward sleep

    for _ in range(20):
        m.decay_traces(turns_passed=1)
        # the conversation keeps recognising it (TrTL) before the TTL expires it
        m.scan_trtl_triggers(good)
        assert m.seeds[sid].status != SeedStatus.EXPIRED

    assert m.seeds[sid].status != SeedStatus.EXPIRED
