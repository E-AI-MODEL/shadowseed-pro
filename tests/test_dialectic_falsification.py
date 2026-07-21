"""Tests for Layer G dialectical falsification.

Dialectical review may remove influence or apply bounded feedback, but it may
never promote a seed. Unparseable output fails safely to ONBESLIST.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shadowseed.benchmark.dialectic_falsification import (
    VERDICT_HOUDT_STAND,
    VERDICT_ONBESLIST,
    VERDICT_WEERLEGD,
    FixtureDialecticBackend,
    apply_dialectic_outcome,
    build_dialectic_prompt,
    parse_dialectic_verdict,
    run_dialectic_falsification,
)
from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed_agent import AgentSafetyContract, InfluenceAction

FIXTURE = Path("src/shadowseed/data/dialectic_falsification_fixture.json")


def _promoted_seed(manager: SSLManager, text: str) -> str:
    sid = manager.ingest_detection_candidates([text])["accepted"][0]["seed_id"]
    seed = manager.seeds[sid]
    for _ in range(8):
        if seed.status == SeedStatus.PROMOTED:
            return sid
        seed.occurrence_count += 1
        manager.run_validation_gate(sid, external_evidence=True)
    raise AssertionError("seed promoveerde niet")


def test_prompt_contains_source_and_seed():
    prompt = build_dialectic_prompt("De stelling.", "De brontekst.")
    assert "De stelling." in prompt and "De brontekst." in prompt
    assert "VERDICT:" in prompt


@pytest.mark.parametrize(
    ("raw", "verdict"),
    [
        ("VERDICT: WEERLEGD\nREDEN: gedekt door de bron.", VERDICT_WEERLEGD),
        ("verdict: houdt_stand\nreden: echt gat.", VERDICT_HOUDT_STAND),
        ("VERDICT: HOUDT STAND\nREDEN: spatievariant.", VERDICT_HOUDT_STAND),
        ("VERDICT: ONBESLIST\nREDEN: te weinig bron.", VERDICT_ONBESLIST),
        ("blabla zonder format", VERDICT_ONBESLIST),  # fail-safe
        ("", VERDICT_ONBESLIST),
        # echoed format line / hedging: never a contradiction that was not asserted
        ("VERDICT: WEERLEGD | HOUDT_STAND | ONBESLIST\nREDEN: echo.", VERDICT_ONBESLIST),
        ("VERDICT: WEERLEGD of HOUDT_STAND\nREDEN: twijfel.", VERDICT_ONBESLIST),
        # a verdict word in the REDEN line must not make the verdict ambiguous
        ("VERDICT: WEERLEGD\nREDEN: de stelling houdt geen stand.", VERDICT_WEERLEGD),
    ],
)
def test_parse_verdict(raw, verdict):
    assert parse_dialectic_verdict(raw)["verdict"] == verdict


def test_weerlegd_drops_weight_and_contract_blocks():
    manager = SSLManager(embedding_fn=lexical_embedding)
    sid = _promoted_seed(manager, "Een toetsbaar ontbrekend punt over subsidies.")
    seed = manager.seeds[sid]
    contract = AgentSafetyContract()
    assert not contract.inspect(
        seed, InfluenceAction.ANSWER_MODIFICATION, manager.gate_events,
        contradiction_blocking=manager.is_blocking_contradiction(sid),
    ).is_blocked

    record = apply_dialectic_outcome(manager, sid, VERDICT_WEERLEGD)
    assert record["channel"] == "gate_contradiction"
    assert record["weight_after"] < record["weight_before"]
    assert contract.inspect(
        seed, InfluenceAction.ANSWER_MODIFICATION, manager.gate_events,
        contradiction_blocking=manager.is_blocking_contradiction(sid),
    ).is_blocked


def test_houdt_stand_is_bounded_and_never_promotes():
    manager = SSLManager(embedding_fn=lexical_embedding)
    sid = manager.ingest_detection_candidates(["Een actief, niet gepromoveerd punt."])[
        "accepted"
    ][0]["seed_id"]
    seed = manager.seeds[sid]
    seed.unsafe_set_authority(status=SeedStatus.ACTIVE)
    for _ in range(30):  # hammer the reward channel: promotion must never happen
        apply_dialectic_outcome(manager, sid, VERDICT_HOUDT_STAND)
    assert seed.status != SeedStatus.PROMOTED
    assert seed.weight <= 1.0


def test_onbeslist_changes_nothing():
    manager = SSLManager(embedding_fn=lexical_embedding)
    sid = _promoted_seed(manager, "Een punt waarover de bron zwijgt.")
    before = manager.seeds[sid].weight
    record = apply_dialectic_outcome(manager, sid, VERDICT_ONBESLIST)
    assert record["weight_after"] == before


def test_unknown_verdict_raises():
    manager = SSLManager(embedding_fn=lexical_embedding)
    sid = _promoted_seed(manager, "Nog een toetsbaar punt over isolatie.")
    with pytest.raises(ValueError):
        apply_dialectic_outcome(manager, sid, "MISSCHIEN")


def test_fixture_run_end_to_end(tmp_path: Path):
    out = tmp_path / "dialectic.json"
    result = run_dialectic_falsification(str(FIXTURE), output_path=str(out))
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["artifact"] == "dialectic_falsification"
    assert result["summary"]["cases"] == 3
    # every case was attacked as a *promoted* seed and matches the expectation
    for record in result["records"]:
        assert record.get("matches_expected") is True
    assert result["summary"]["weerlegd"] == 1
    assert result["summary"]["houdt_stand"] == 2
    # the refuted seed ends blocked-from-influence territory: weight dropped
    refuted = next(r for r in result["records"] if r["verdict"] == VERDICT_WEERLEGD)
    assert refuted["weight_after"] < refuted["weight_before"]


def test_fixture_backend_is_deterministic():
    backend = FixtureDialecticBackend()
    scenario = {"seed_text": "Iets over kosmologie.", "source_text": "Een rapport over isolatie."}
    first = backend.generate("p", scenario, "dialectic", [])
    assert first == backend.generate("p", scenario, "dialectic", [])
    assert "WEERLEGD" in first


def test_transfer_v3_cases_survive_ingest_atomically():
    # round-033-preregistratie-guard (codex-P2-les): elke case moet exact
    # één geaccepteerde, tekst-intacte seed opleveren via de échte
    # ingest-route — anders beoordeelt de dialectiek een fragment (of
    # niets) terwijl het verdict onder de volle stelling wordt opgeslagen
    data = json.loads(
        Path("src/shadowseed/data/dialectic_falsification_transfer_v3.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(data["cases"]) == 24
    for case in data["cases"]:
        manager = SSLManager(embedding_fn=lexical_embedding)
        ingest = manager.ingest_detection_candidates([case["seed_text"]])
        accepted = ingest.get("accepted", [])
        assert len(accepted) == 1, f"niet-atomisch door ingest: {case['seed_text']!r}"
        got = (accepted[0].get("seed_text") or accepted[0].get("text", "")).rstrip(".")
        assert got == case["seed_text"].rstrip("."), f"tekst gewijzigd: {case['seed_text']!r}"
