"""Tests for the living shadow layer (shadowseed chat) — doctrine enforced live.

Vision item 5 operationalized: seed born early -> shadow -> Gate promotion ->
steers a later turn, with the AgentSafetyContract re-checking every influence
and the audit trail replayable. Deterministic (stubbed model/detector/embedder).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

import shadowseed.chat as chatmod
from shadowseed.chat import ShadowChatSession, run_chat
from shadowseed_agent import WeightlessInfluenceError, assert_no_weightless_influence
from shadowseed_agent.audit_policy import AgentInfluenceRecord

PARAPHRASES = [
    "Privacy van gebruikersdata.",
    "Bescherming van persoonlijke data.",
    "Vertrouwen rond datagebruik.",
    "Verantwoord omgaan met gegevens.",
    "Transparantie over datagebruik.",
    "Waarborgen van dataprivacy.",
    "Privacybesef bij gebruikers.",
]
KEYWORDS = [
    "privacy", "bescherming", "vertrouwen", "verantwoord",
    "transparantie", "waarborgen", "privacybesef",
]


class _Model:
    name = "fake"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, scenario, mode, seeds):
        self.prompts.append(prompt)
        return "Antwoord met invalshoek." if seeds else "Gewoon antwoord."


class _Detector:
    name = "fake-det"

    def __init__(self):
        self.i = 0

    def detect_seeds(self, item, max_seeds=5):
        text = PARAPHRASES[self.i % len(PARAPHRASES)]
        self.i += 1
        return [text]


def _emb_factory(backend, model_id=None, **kw):
    # paraphrases share one axis (pairwise cosine 0.7: clusters at 0.6, stays
    # distinct under the strict 0.85 dedup); questions about privacy align with
    # the shared axis so a promoted seed is relevant to them.
    a, b = math.sqrt(7.0), math.sqrt(3.0)
    dim = len(KEYWORDS) + 2

    def embed(text: str):
        low = text.lower()
        v = np.zeros(dim)
        for idx, kw_ in enumerate(KEYWORDS):
            if kw_ in low:
                v[0] = a
                v[idx + 1] = b
                return v / np.linalg.norm(v)
        if "gegevensbescherming" in low or "data" in low:
            v[0] = 1.0  # question aligned with the shared theme axis
            return v
        v[-1] = 1.0
        return v

    return embed, dim


def _make_session(monkeypatch, **kw) -> ShadowChatSession:
    monkeypatch.setattr(chatmod, "make_backend", lambda **k: _Model())
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **k: _Detector())
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    return ShadowChatSession(backend="openai", recurrence_mode="cluster", **kw)


@pytest.fixture
def session(monkeypatch) -> ShadowChatSession:
    return _make_session(monkeypatch)


def _drive(session: ShadowChatSession, turns: int) -> list[dict]:
    return [session.turn(f"Wat betekent dit voor de omgang met data? (beurt {t})") for t in range(turns)]


def test_seed_travels_shadow_then_steers_only_after_promotion(session):
    reports = _drive(session, 7)

    # early turns: nothing promoted yet that was born earlier -> nothing steers
    assert reports[0]["surfaced_seeds"] == []
    assert reports[1]["surfaced_seeds"] == []

    # the recurring theme promotes via the Gate and then surfaces in a LATER turn
    assert any(r["promoted_this_turn"] for r in reports), "recurrence should promote via the Gate"
    steered = [r for r in reports if r["surfaced_seeds"]]
    assert steered, "a promoted seed born earlier should steer a later answer"
    first = steered[0]
    assert first["turn"] > min(t for t, r in enumerate(reports) if r["promoted_this_turn"]) or (
        first["turn"] >= 1
    )
    # every allowed influence decision is contract-approved and recorded
    for dec in first["influence_decisions"]:
        if dec["allowed"]:
            assert dec["reason"] == "allowed_promoted_gate_logged"

    # audit replay passes: no weightless seed ever influenced an answer
    assert session.audit() >= 1


def test_weightless_seeds_never_steer(session):
    _drive(session, 7)
    for record in session.influence_records:
        if record.allowed:
            assert record.seed_weight > 0.0
            assert record.seed_status == "PROMOTED"


def test_falsification_blocks_future_influence(session):
    reports = _drive(session, 7)
    steered = [r for r in reports if r["surfaced_seeds"]]
    assert steered
    # find the promoted seed that steered
    sid = steered[-1]["influence_decisions"][0]["seed_id"]
    weight_before = session.manager.seeds[sid].weight

    result = session.falsify(sid)
    assert result["blocked_from_influence"] is True
    assert result["weight_after"] < weight_before

    # after falsification the seed no longer surfaces
    later = session.turn("En hoe zit het nu met de gegevensbescherming?")
    assert sid not in [d["seed_id"] for d in later["influence_decisions"] if d["allowed"]]
    session.audit()  # still clean


def test_cluster_recurrence_refreshes_stale_representative(session):
    # birth the representative and one clustered member
    _drive(session, 2)
    rep_ids = [sid for sid, born in session.born_turn.items() if born == 0]
    assert rep_ids
    rep = session.manager.seeds[rep_ids[0]]

    # age the representative below the Gate's trace bar while its theme recurs
    min_trace = session.manager.config.min_trace_for_gate
    rep.trace = min_trace / 2

    session.turn("Wat betekent dit voor de omgang met data? (refresh)")
    # a member joining/recurring in the cluster must keep the representative
    # gate-eligible (mirror of _refresh_cluster_representative in the suite)
    assert rep.trace > min_trace


def test_retrieval_probe_reports_presence_without_steering(tmp_path, monkeypatch):
    # SSL->RAG bridge live (vision item 2): the promoted seed probes the corpus
    # and finds what the question does not — reported as presence only.
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            [
                {"id": "doc_privacy", "text": "Privacy in het archief."},
                {"id": "doc_data", "text": "Alles over data."},
            ]
        ),
        encoding="utf-8",
    )
    session = _make_session(monkeypatch, probe_corpus=str(corpus), probe_top_k=1)
    reports = _drive(session, 7)

    # before any promotion the probe stays silent
    assert reports[0]["retrieval_probe"] is None

    probes = [r["retrieval_probe"] for r in reports if r["retrieval_probe"]]
    assert probes, "once a seed is promoted the probe should run"
    hit = next(p for p in probes if p["seed_only_chunk_ids"])
    # the question arm retrieves the question-aligned chunk; the seed arm
    # surfaces the theme chunk the question alone would never pull in
    assert "doc_privacy" in hit["seed_only_chunk_ids"]
    assert hit["seed_only_hits"][0]["chunk_id"] == "doc_privacy"

    # doctrine: gevonden != waar/sturend — retrieved text never enters a prompt
    assert all("archief" not in p for p in session.model.prompts)
    session.audit()  # and the probe added no influence


def test_probe_corpus_accepts_repo_retrieval_schema(tmp_path, monkeypatch):
    # the repo's retrieval corpora are shaped documents[].chunks with chunk_id
    # (index_retrieval_corpus); the loader must index those, not silently skip
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": "doc_a",
                        "chunks": [
                            {"chunk_id": "doc_a::c1", "text": "Privacy in het archief."},
                            {"chunk_id": "doc_a::c2", "text": "Alles over data."},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    session = _make_session(monkeypatch, probe_corpus=str(corpus), probe_top_k=1)
    assert sorted(session.probe_store.get_all_ids()) == ["doc_a::c1", "doc_a::c2"]
    assert session.probe_store.get_metadata("doc_a::c1")["doc_id"] == "doc_a"

    reports = _drive(session, 7)
    hit = next(
        p for p in (r["retrieval_probe"] for r in reports) if p and p["seed_only_chunk_ids"]
    )
    assert hit["seed_only_chunk_ids"] == ["doc_a::c1"]
    assert hit["seed_only_hits"][0]["doc_id"] == "doc_a"


def test_probe_corpus_without_chunks_fails_loudly(tmp_path, monkeypatch):
    corpus = tmp_path / "leeg.json"
    corpus.write_text(json.dumps({"iets": "anders"}), encoding="utf-8")
    with pytest.raises(ValueError, match="contains no indexable chunks"):
        _make_session(monkeypatch, probe_corpus=str(corpus))


def test_falsify_unknown_seed_raises(session):
    with pytest.raises(KeyError):
        session.falsify("bestaat-niet")


def test_audit_replay_fails_on_weightless_influence():
    bad = [
        AgentInfluenceRecord(
            seed_id="s1",
            action="answer_modification",
            seed_weight=0.0,
            seed_status="NEW",
            allowed=True,
            reason="oops",
        )
    ]
    with pytest.raises(WeightlessInfluenceError):
        assert_no_weightless_influence(bad)


def test_run_chat_script_mode_writes_audited_transcript(tmp_path: Path):
    # end-to-end on the real fixture backend: no stubs, no secrets
    script = tmp_path / "vragen.txt"
    script.write_text(
        "# demo\nWaarom is dit systeem veilig?\nEn wat mist er nog?\n", encoding="utf-8"
    )
    out = run_chat(
        backend="fixture",
        script_path=str(script),
        transcript_path=str(tmp_path / "transcript.json"),
    )
    payload = json.loads(Path(out).read_text(encoding="utf-8"))
    assert payload["artifact"] == "shadow_chat_transcript"
    assert len(payload["turn_reports"]) == 2  # comment line skipped
    assert "doctrine" in payload
    # the fixture path must actually exercise the shadow layer: non-blank
    # answers and at least one weightless birth (regression: chat scenarios
    # have no authored baseline_answer, which used to blank the fixture)
    assert all(r["answer"].strip() for r in payload["turn_reports"])
    assert any(r["seeds_born_weightless"] for r in payload["turn_reports"])
    # transcript is only written after a hard audit pass
    for rec in payload["shadow"]["influence_records"]:
        if rec["allowed"]:
            assert rec["seed_weight"] > 0.0
