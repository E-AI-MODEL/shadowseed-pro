"""Tests for cluster-based recurrence (W9e) — no network."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shadowseed.recurrence_clustering import (
    RecurrenceClusterer,
    auto_calibrated_min_occurrences,
)
from shadowseed.benchmark.ssl_session_suite import run_ssl_session


def test_paraphrases_cluster_unrelated_split():
    c = RecurrenceClusterer(threshold=0.6)
    # three near-parallel vectors (paraphrases) + one orthogonal (unrelated)
    a1 = np.array([1.0, 0.0, 0.0])
    a2 = np.array([0.9, 0.1, 0.0])
    a3 = np.array([0.85, 0.15, 0.0])
    b1 = np.array([0.0, 0.0, 1.0])
    ca = c.add("privacy", a1)
    assert c.add("datagebruik", a2) == ca
    assert c.add("vertrouwen", a3) == ca
    assert c.recurrence(ca) == 3  # paraphrases accumulate recurrence
    cb = c.add("iets heel anders", b1)
    assert cb != ca and c.recurrence(cb) == 1  # unrelated stays a singleton


def test_bump_keeps_recurrence_separate_from_centroid_weight():
    c = RecurrenceClusterer(threshold=0.6)
    a = np.array([1.0, 0.0])
    b = np.array([0.8, 0.6])
    cid = c.add("A", a)
    assert c.add("B", b) == cid

    for _ in range(4):
        c.bump(cid)

    assert c.recurrence(cid) == 6
    assert c.centroid_counts[cid] == 2
    before = c.centroids[cid].copy()

    c_vec = np.array([1.0, 0.0])
    assert c.add("C", c_vec) == cid

    expected = (before * 2 + c_vec) / 3
    assert c.recurrence(cid) == 7
    assert c.centroid_counts[cid] == 3
    np.testing.assert_allclose(c.centroids[cid], expected)


def test_auto_calibrated_bar_clamped():
    assert auto_calibrated_min_occurrences(4) == 2
    assert auto_calibrated_min_occurrences(9) == 3
    assert auto_calibrated_min_occurrences(30) == 4  # clamped at hi


def test_cluster_mode_promotes_at_safe_bar(tmp_path: Path, monkeypatch):
    # 6-turn convo; detector emits paraphrases of ONE gap; strict dedup (0.85)
    # keeps them distinct, but cluster recurrence lets the SAFE bar (min_occ 3)
    # promote -> cross-turn event. Proves W9e works without loosening dedup/Gate.
    conv = {"version": "t", "conversations": [
        {"id": "C", "domain": "d", "turns": [{"question": f"Q{i}?"} for i in range(6)]}]}
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    paraphrases = [
        "Privacy van gebruikersdata als kernzorg.",
        "Bescherming van persoonlijke data van gebruikers.",
        "Datagebruik en vertrouwen van gebruikers op lange termijn.",
        "Verantwoord omgaan met gevoelige gebruikersgegevens.",
        "Transparantie over hoe gebruikersdata wordt benut.",
        "Waarborgen van dataprivacy voor gebruikers.",
    ]

    class _Model:
        name = "fake"
        def generate(self, prompt, scenario, mode, seeds):
            return "SSL." if mode == "ssl" else "Baseline."

    class _Det:
        name = "d"
        def __init__(self): self.i = 0
        def detect_seeds(self, item, max_seeds=5):
            t = paraphrases[self.i % len(paraphrases)]; self.i += 1
            return [t]

    def _emb(backend, model_id=None, **kw):
        # paraphrases -> near-identical vector (cluster together, but each is a
        # distinct string so strict 0.85 dedup keeps them as separate seeds only
        # if vectors differ slightly); make them cluster at 0.6 yet not all merge.
        def embed(text: str):
            base = np.ones(16) * 0.5
            # tiny per-text jitter so strict dedup may keep some distinct
            h = sum(map(ord, text)) % 16
            base[h] += 0.05
            return base / np.linalg.norm(base)
        return embed, 16

    monkeypatch.setattr(sessmod(), "make_backend", lambda **k: _Model())
    monkeypatch.setattr(sessmod(), "make_detector_backend", lambda *a, **k: _Det())
    monkeypatch.setattr(sessmod(), "make_embedding_fn", _emb)

    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="openai",
                    recurrence_mode="cluster", cluster_threshold=0.6)  # min_occ stays default 3
    payload = json.loads(out.read_text(encoding="utf-8"))
    c = payload["conversations"][0]
    assert c["applied_thresholds"]["recurrence_mode"] == "cluster"
    assert c["applied_thresholds"]["min_occurrences"] == "default(3)"  # SAFE bar
    assert any(tr["promoted_total"] for tr in c["turns"]), "cluster recurrence should promote at the safe bar"


def test_cluster_mode_promotes_one_representative_not_all_members(tmp_path: Path, monkeypatch):
    # W9f: six DISTINCT paraphrases that CLUSTER together (pairwise cosine ~0.7,
    # >= cluster bar 0.6) yet stay separate seeds under the strict 0.85 dedup.
    # Round-020 v1 credited the cluster size to every member -> all six promoted.
    # After W9f only the cluster representative is credited -> exactly one promotes,
    # while the six seeds remain distinct in storage.
    import math

    paraphrases = [
        "Privacy van gebruikersdata.",
        "Bescherming van persoonlijke data.",
        "Vertrouwen rond datagebruik.",
        "Verantwoord omgaan met gegevens.",
        "Transparantie over datagebruik.",
        "Waarborgen van dataprivacy.",
    ]
    # one unique keyword per paraphrase so the embedder is robust to normalization
    keywords = ["privacy", "bescherming", "vertrouwen", "verantwoord", "transparantie", "waarborgen"]

    conv = {"version": "t", "conversations": [
        {"id": "C", "domain": "d", "turns": [{"question": f"Q{i}?"} for i in range(6)]}]}
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"
        def generate(self, prompt, scenario, mode, seeds):
            return "SSL." if mode == "ssl" else "Baseline."

    class _Det:
        name = "d"
        def __init__(self): self.i = 0
        def detect_seeds(self, item, max_seeds=5):
            t = paraphrases[self.i % len(paraphrases)]; self.i += 1
            return [t]

    # shared e0 direction + a unique orthogonal axis per paraphrase, weighted so
    # pairwise cosine = 7/(7+3) = 0.7: clusters at 0.6 but stays distinct at 0.85.
    a, b = math.sqrt(7.0), math.sqrt(3.0)
    dim = len(keywords) + 2  # axis 0 shared; axes 1..n unique; last axis for non-gaps

    def _emb(backend, model_id=None, **kw):
        def embed(text: str):
            low = text.lower()
            v = np.zeros(dim)
            for idx, kw_ in enumerate(keywords):
                if kw_ in low:
                    v[0] = a
                    v[idx + 1] = b
                    return v / np.linalg.norm(v)
            v[-1] = 1.0  # questions / anything else -> own direction, won't cluster
            return v
        return embed, dim

    monkeypatch.setattr(sessmod(), "make_backend", lambda **k: _Model())
    monkeypatch.setattr(sessmod(), "make_detector_backend", lambda *a, **k: _Det())
    monkeypatch.setattr(sessmod(), "make_embedding_fn", _emb)

    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="openai",
                    recurrence_mode="cluster", cluster_threshold=0.6)
    payload = json.loads(out.read_text(encoding="utf-8"))
    diag = payload["conversations"][0]["diagnostics"]

    # the six paraphrases stayed distinct under strict 0.85 dedup ...
    assert diag["distinct_seeds_created"] >= 5
    # ... the cluster still accumulated recurrence to clear the SAFE bar ...
    assert diag["max_occurrence_count"] >= 3
    # ... but only the representative promoted, not the whole cluster.
    assert len(diag["promoted_ever"]) == 1, diag["promoted_ever"]


def test_redetected_nonrep_counts_in_cluster_and_only_rep_promotes(tmp_path: Path, monkeypatch):
    # W9f regression: A creates the cluster, B joins it, then B is RE-DETECTED
    # verbatim several times (deduping into the stored B, so B's own
    # occurrence_count climbs). The re-detections must accumulate in the CLUSTER so
    # the representative (A) promotes, and B must NOT promote as a non-rep on its
    # own occurrence_count. Exactly one promotion, and it is A.
    import math

    A = "Privacy van gebruikersdata."
    B = "Bescherming van persoonlijke data."
    emissions = [A, B, B, B, B, B]  # A once; B four+ times -> B dedups into itself

    conv = {"version": "t", "conversations": [
        {"id": "C", "domain": "d", "turns": [{"question": f"Q{i}?"} for i in range(len(emissions))]}]}
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"
        def generate(self, prompt, scenario, mode, seeds):
            return "SSL." if mode == "ssl" else "Baseline."

    class _Det:
        name = "d"
        def __init__(self): self.i = 0
        def detect_seeds(self, item, max_seeds=5):
            t = emissions[self.i]; self.i += 1
            return [t]

    a, b = math.sqrt(7.0), math.sqrt(3.0)  # A,B pairwise cosine 0.7 (cluster, not merge)

    def _emb(backend, model_id=None, **kw):
        def embed(text: str):
            low = text.lower()
            v = np.zeros(4)
            if "privacy" in low:          # A -> axis 1
                v[0] = a; v[1] = b
            elif "bescherming" in low:    # B -> axis 2 (verbatim repeats -> identical)
                v[0] = a; v[2] = b
            else:
                v[3] = 1.0
                return v
            return v / np.linalg.norm(v)
        return embed, 4

    monkeypatch.setattr(sessmod(), "make_backend", lambda **k: _Model())
    monkeypatch.setattr(sessmod(), "make_detector_backend", lambda *a, **k: _Det())
    monkeypatch.setattr(sessmod(), "make_embedding_fn", _emb)

    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="openai",
                    recurrence_mode="cluster", cluster_threshold=0.6)
    payload = json.loads(out.read_text(encoding="utf-8"))
    diag = payload["conversations"][0]["diagnostics"]

    # A and B stayed distinct (0.7 < 0.85 dedup)
    assert diag["distinct_seeds_created"] == 2
    # B's re-detections accumulated in the cluster -> recurrence cleared the bar
    assert diag["max_occurrence_count"] >= 3
    # exactly one promotion and it is the representative (A's cluster), not the
    # re-detected non-rep B (text is normalized, so match on the distinguishing word)
    assert len(diag["promoted_ever"]) == 1, diag["promoted_ever"]
    assert "privacy" in diag["promoted_ever"][0].lower(), diag["promoted_ever"]
    assert all("bescherming" not in p.lower() for p in diag["promoted_ever"]), diag["promoted_ever"]


def test_nonrep_recurrence_refreshes_decayed_representative(tmp_path: Path, monkeypatch):
    # W9f follow-up: A is the representative, B is a non-rep in the same cluster.
    # After several quiet turns A's trace falls below the Gate threshold. Later
    # B re-detections must count as cluster recurrence AND keep A live enough to
    # validate; otherwise B is skipped and A is too stale, so nothing promotes.
    import math

    A = "Privacy van gebruikersdata."
    B = "Bescherming van persoonlijke data."
    emissions = [[A], [B], [], [], [], [], [B], [B], [B], [B]]

    conv = {"version": "t", "conversations": [
        {"id": "C", "domain": "d", "turns": [{"question": f"Q{i}?"} for i in range(len(emissions))]}]}
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"
        def generate(self, prompt, scenario, mode, seeds):
            return "SSL." if mode == "ssl" else "Baseline."

    class _Det:
        name = "d"
        def __init__(self): self.i = 0
        def detect_seeds(self, item, max_seeds=5):
            out = emissions[self.i]
            self.i += 1
            return out

    a, b = math.sqrt(7.0), math.sqrt(3.0)

    def _emb(backend, model_id=None, **kw):
        def embed(text: str):
            low = text.lower()
            v = np.zeros(4)
            if "privacy" in low:
                v[0] = a; v[1] = b
            elif "bescherming" in low:
                v[0] = a; v[2] = b
            else:
                v[3] = 1.0
                return v
            return v / np.linalg.norm(v)
        return embed, 4

    monkeypatch.setattr(sessmod(), "make_backend", lambda **k: _Model())
    monkeypatch.setattr(sessmod(), "make_detector_backend", lambda *a, **k: _Det())
    monkeypatch.setattr(sessmod(), "make_embedding_fn", _emb)

    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="openai",
                    recurrence_mode="cluster", cluster_threshold=0.6)
    payload = json.loads(out.read_text(encoding="utf-8"))
    diag = payload["conversations"][0]["diagnostics"]

    assert diag["distinct_seeds_created"] == 2
    assert diag["max_occurrence_count"] >= 3
    assert len(diag["promoted_ever"]) == 1, diag["promoted_ever"]
    assert "privacy" in diag["promoted_ever"][0].lower(), diag["promoted_ever"]
    assert all("bescherming" not in p.lower() for p in diag["promoted_ever"]), diag["promoted_ever"]


def sessmod():
    import shadowseed.benchmark.ssl_session_suite as m
    return m
