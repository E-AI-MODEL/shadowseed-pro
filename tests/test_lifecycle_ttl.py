"""Lifecycle TTL + EXPIRED-terminality tests (4.5 §10/§12.2 doctrine).

A degraded or unreactivated seed must run out its TTL to EXPIRED and not come
back: weight drops, the dormancy clock counts down, and EXPIRED is terminal
against decay, the Gate, dedup-resurrection and reactivation.
"""

from __future__ import annotations

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus


def _embedding(text: str) -> np.ndarray:
    v = np.array(
        [float((len(text) % 7) + 1), float((sum(map(ord, text)) % 11) + 1)],
        dtype=float,
    )
    return v / np.linalg.norm(v)


def _manager(**kw) -> SSLManager:
    return SSLManager(embedding_fn=_embedding, **kw)


def test_dormant_seed_expires_after_ttl():
    m = _manager()
    sid = m.add_or_update_seed("Encryptie van medische data tijdens transport.")
    # force it just below the dormant threshold with no weight
    m.seeds[sid].trace = 0.04
    m.seeds[sid].unsafe_set_authority(weight=0.0)

    for turn in range(1, m.dormant_ttl_turns + 1):
        m.decay_traces(turns_passed=1)
        if turn < m.dormant_ttl_turns:
            assert m.seeds[sid].status == SeedStatus.DORMANT
            assert m.seeds[sid].turns_dormant == turn
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    assert m.seeds[sid].weight == 0.0
    assert any(e.event_type == "expired" for e in m.event_log)


def test_expired_seed_is_not_reactivated_or_decayed():
    m = _manager()
    sid = m.add_or_update_seed("Rate-limiting op API's die gezondheidsdata verwerken.")
    m.seeds[sid].unsafe_set_authority(status=SeedStatus.EXPIRED)
    # decay must skip it; reactivation must not touch it
    m.decay_traces(turns_passed=3)
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    reactivated = m.reactivate_by_text("Rate-limiting op API's die gezondheidsdata verwerken.")
    assert sid not in reactivated
    assert m.seeds[sid].status == SeedStatus.EXPIRED


def test_expired_seed_gate_is_noop():
    m = _manager()
    sid = m.add_or_update_seed("Authenticatiestrategie voor toegang tot gezondheidsdata.")
    m.seeds[sid].unsafe_set_authority(status=SeedStatus.EXPIRED)
    for _ in range(5):
        m.run_validation_gate(sid, external_evidence=True)
    assert m.seeds[sid].status == SeedStatus.EXPIRED
    assert m.seeds[sid].weight == 0.0
    assert m.validation_log[-1].verdict == "expired"


def test_dedup_does_not_resurrect_expired_seed():
    m = _manager()
    text = "AVG-compliance bij verwerking van medische hartslagdata."
    sid = m.add_or_update_seed(text)
    m.seeds[sid].unsafe_set_authority(status=SeedStatus.EXPIRED)

    # same text would normally dedup onto sid; it must create a NEW seed instead
    new_id = m.add_or_update_seed(text)
    assert new_id != sid
    assert m.seeds[sid].status == SeedStatus.EXPIRED  # the dead one stays dead
    assert m.seeds[new_id].status == SeedStatus.NEW


def test_contradiction_lowers_trace_toward_disappearance():
    m = _manager()
    sid = m.add_or_update_seed("Forumkeuzebeding in internationale online koopvoorwaarden.")
    trace_before = m.seeds[sid].trace
    m.run_validation_gate(sid, contradiction=True)
    assert m.seeds[sid].status == SeedStatus.NEW  # doctrine: falsified -> NEW
    assert m.seeds[sid].trace == trace_before - m.contradiction_trace_penalty


def test_scan_trtl_triggers_is_reactivate_alias():
    m = _manager()
    text = "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    sid = m.add_or_update_seed(text)
    m.seeds[sid].unsafe_set_authority(status=SeedStatus.DORMANT)
    reactivated = m.scan_trtl_triggers(text)
    assert reactivated == [sid]
    assert m.seeds[sid].status == SeedStatus.NEW


def test_reactivation_resets_dormancy_clock():
    m = _manager()
    text = "Toepasselijk recht bij een grensoverschrijdend consumentencontract."
    sid = m.add_or_update_seed(text)
    m.seeds[sid].unsafe_set_authority(status=SeedStatus.DORMANT)
    m.seeds[sid].turns_dormant = 2
    m.reactivate_by_text(text)
    assert m.seeds[sid].status == SeedStatus.NEW
    assert m.seeds[sid].turns_dormant == 0
