"""Vectorstore hardening tests (coverage assessment 2026-07-02).

The maintainer's test-layer assessment flagged the vectorstore as the weak spot
(~48% line / ~23% branch): the FAISS/Chroma adapters never run in CI because the
optional extras are not installed. These tests exercise the adapter logic behind
lightweight fakes (no faiss/chromadb needed), the edge branches of the in-memory
store, the smoke runner, and — most importantly — the doctrine guard:

    "gevonden" mag nooit automatisch "waar" of "sturend" worden

Retrieval from the vectorstore must never change seed weight, status, trace or
occurrence_count. Only the Validation Gate may grant influence.
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore, create_vector_store
from shadowseed.vectorstore.base import VectorStore


# ---------------------------------------------------------------------------
# Doctrine: retrieval never steers
# ---------------------------------------------------------------------------


def test_retrieval_is_never_steering():
    """Found != true/steering: searching the store must not mutate SSL state."""
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(embedding_fn=lexical_embedding, vector_constellation=constellation)
    seed_id = manager.add_or_update_seed(
        "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
        trigger_keywords=["toepasselijk", "recht"],
    )
    before = manager.get_seed(seed_id).to_dict()
    assert before["weight"] == 0.0  # weightless until the Gate says otherwise

    # retrieve repeatedly, via both the manager route and the store route
    for _ in range(5):
        manager.find_uncertain_region(
            "Consument koopt bij buitenlandse webwinkel en wil garantie afdwingen.",
            threshold=0.05,
        )
        constellation.search_similar_seeds(
            manager.get_embedding("toepasselijk recht consumentencontract"),
            threshold=0.0,
        )

    after = manager.get_seed(seed_id).to_dict()
    for field in ("weight", "status", "trace", "occurrence_count", "evidence_count"):
        assert after[field] == before[field], f"retrieval mutated {field}"


# ---------------------------------------------------------------------------
# InMemoryVectorStore edge branches
# ---------------------------------------------------------------------------


def test_memory_store_edge_branches():
    store = InMemoryVectorStore()
    # zero vector: normalize returns it unchanged instead of dividing by 0
    store.add("zero", np.zeros(4), {"text": "zero"})
    # shape mismatch entries are skipped, not crashed on
    store.add("odd", np.ones(3), {"text": "odd"})
    store.add("fit", np.ones(4), {"text": "fit"})

    hits = store.search(np.ones(4), top_k=5)
    ids = [h[0] for h in hits]
    assert "fit" in ids and "odd" not in ids  # mismatching dim skipped
    assert store.search(np.ones(4), top_k=0) == []

    with pytest.raises(KeyError):
        store.update_metadata("nope", {"a": 1})
    with pytest.raises(KeyError):
        store.get_metadata("nope")

    store.delete("nope")  # deleting unknown id is a no-op
    store.delete("fit")
    assert "fit" not in store.get_all_ids()


def test_factory_rejects_unknown_backend():
    with pytest.raises(ValueError):
        create_vector_store(backend="does-not-exist")


# ---------------------------------------------------------------------------
# FAISS adapter behind a fake faiss module (no faiss-cpu needed)
# ---------------------------------------------------------------------------


class _FakeIndexFlatIP:
    def __init__(self, dim: int) -> None:
        self.dim = dim
        self._matrix = np.zeros((0, dim), dtype="float32")

    def add(self, matrix):
        self._matrix = np.vstack([self._matrix, np.asarray(matrix, dtype="float32")])

    def search(self, query, k):
        scores = self._matrix @ np.asarray(query, dtype="float32")[0]
        order = np.argsort(-scores)[:k]
        return scores[order].reshape(1, -1), order.reshape(1, -1)


@pytest.fixture
def faiss_store(monkeypatch):
    fake = types.ModuleType("faiss")
    fake.IndexFlatIP = _FakeIndexFlatIP
    monkeypatch.setitem(sys.modules, "faiss", fake)
    from shadowseed.vectorstore.faiss_store import FaissVectorStore

    return FaissVectorStore(dimensions=4)


def test_faiss_adapter_contract(faiss_store):
    store = faiss_store
    store.add("a", np.array([1.0, 0.0, 0.0, 0.0]), {"text": "a"})
    store.add("b", np.array([0.0, 1.0, 0.0, 0.0]), {"text": "b"})

    with pytest.raises(ValueError):
        store.add("bad", np.ones(3), {})  # dim mismatch on add is an error

    hits = store.search(np.array([1.0, 0.1, 0.0, 0.0]), top_k=2)
    assert [h[0] for h in hits] == ["a", "b"]  # sorted by inner product
    assert store.search(np.ones(3), top_k=2) == []  # dim mismatch on query
    assert store.search(np.ones(4), top_k=0) == []

    store.update_metadata("a", {"extra": 1})
    assert store.get_metadata("a")["extra"] == 1
    with pytest.raises(KeyError):
        store.update_metadata("nope", {})
    with pytest.raises(KeyError):
        store.get_metadata("nope")

    store.delete("a")  # delete rebuilds the index
    assert store.get_all_ids() == ["b"]
    assert [h[0] for h in store.search(np.ones(4), top_k=2)] == ["b"]
    store.delete("b")
    assert store.search(np.ones(4), top_k=2) == []  # empty store


# ---------------------------------------------------------------------------
# Chroma adapter behind a fake chromadb module (no chromadb needed)
# ---------------------------------------------------------------------------


class _FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self._ids: list[str] = []
        self._embeddings: list[list[float]] = []
        self._metadatas: list[dict] = []
        self.raise_on_delete = False

    def count(self):
        return len(self._ids)

    def add(self, ids, embeddings, metadatas, documents):
        for id, emb, meta in zip(ids, embeddings, metadatas):
            self._ids.append(id)
            self._embeddings.append(list(emb))
            self._metadatas.append(dict(meta))

    def get(self, include=None):
        # Recent Chroma versions return numpy arrays; reproduce that shape so the
        # historical "truth value of an empty array is ambiguous" regression stays
        # covered (see _as_list in chroma_store.py).
        return {
            "ids": np.array(self._ids),
            "metadatas": list(self._metadatas),
            "embeddings": np.array(self._embeddings) if self._embeddings else None,
        }

    def query(self, query_embeddings, n_results, include):
        q = np.asarray(query_embeddings[0], dtype=float)
        dists = [float(np.linalg.norm(q - np.asarray(e, dtype=float))) for e in self._embeddings]
        order = np.argsort(dists)[:n_results]
        return {
            "ids": [[self._ids[i] for i in order]],
            "distances": [[dists[i] for i in order]],
            "metadatas": [[self._metadatas[i] for i in order]],
        }

    def update(self, ids, metadatas):
        for id, meta in zip(ids, metadatas):
            self._metadatas[self._ids.index(id)] = dict(meta)

    def delete(self, ids):
        if self.raise_on_delete:
            raise RuntimeError("backend hiccup")
        for id in ids:
            if id in self._ids:
                i = self._ids.index(id)
                del self._ids[i], self._embeddings[i], self._metadatas[i]


class _FakeClient:
    def __init__(self, path: str | None = None) -> None:
        self.path = path
        self.collections: dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name):
        return self.collections.setdefault(name, _FakeCollection(name))


@pytest.fixture
def chroma_env(monkeypatch):
    fake = types.ModuleType("chromadb")
    clients: list[_FakeClient] = []

    def _client():
        c = _FakeClient()
        clients.append(c)
        return c

    def _persistent(path):
        c = _FakeClient(path=path)
        clients.append(c)
        return c

    fake.Client = _client
    fake.PersistentClient = _persistent
    monkeypatch.setitem(sys.modules, "chromadb", fake)
    from shadowseed.vectorstore.chroma_store import ChromaVectorStore

    return ChromaVectorStore, clients


def test_chroma_adapter_contract(chroma_env):
    ChromaVectorStore, clients = chroma_env
    store = ChromaVectorStore(collection_name="t")
    # ephemeral collections get a unique suffix so parallel runs never collide
    assert store.collection.name.startswith("t_") and store.collection.name != "t"

    store.add("a", np.array([1.0, 0.0]), {"text": "a", "tags": ["x", "y"]})
    store.add("b", np.array([0.0, 1.0]), {"text": "b"})
    # non-primitive metadata is stringified for the chroma payload, but the
    # adapter cache keeps the original value
    assert store.get_metadata("a")["tags"] == ["x", "y"]

    hits = store.search(np.array([1.0, 0.1]), top_k=2)
    assert [h[0] for h in hits] == ["a", "b"]  # closest distance -> highest score
    assert hits[0][1] > hits[1][1]
    assert store.search(np.array([1.0, 0.0]), top_k=0) == []

    store.update_metadata("a", {"seen": 1})
    assert store.get_metadata("a")["seen"] == 1
    with pytest.raises(KeyError):
        store.get_metadata("nope")

    # delete tolerates backend errors (best effort) and drops the local cache...
    store.collection.raise_on_delete = True
    store.delete("a")
    assert "a" not in store._metadata
    # ...but the entry resurrects from the still-populated backing collection on
    # the next full read. Documented behavior: the store is an index, not the
    # source of truth — SSLManager stays leading, so a resurrected index entry
    # can never grant weight or status by itself.
    assert "a" in store.get_all_ids()


def test_chroma_hydration_from_persisted_collection(chroma_env):
    ChromaVectorStore, clients = chroma_env
    first = ChromaVectorStore(collection_name="persist", persist_directory="/tmp/x")
    assert first.collection.name == "persist"  # exact name when persistent
    assert clients[-1].path == "/tmp/x"
    first.add("s1", np.array([1.0, 0.0]), {"text": "seed one"})

    # a new adapter over the same backing collection must hydrate ids/metadata,
    # including when the backend hands back numpy arrays (the old crash)
    second = ChromaVectorStore.__new__(ChromaVectorStore)
    second.collection_name = "persist"
    second.client = clients[-1]
    second.collection = clients[-1].get_or_create_collection("persist")
    second._metadata = {}
    second._embeddings = {}
    second._hydrate_cache_from_collection()
    assert second.get_all_ids() == ["s1"]
    assert second.get_metadata("s1")["text"] == "seed one"
    assert isinstance(second._embeddings["s1"], np.ndarray)


def test_as_list_handles_numpy_and_none():
    from shadowseed.vectorstore.chroma_store import _as_list

    assert _as_list(None) == []
    assert _as_list(np.array([])) == []  # the historical ambiguity crash
    assert _as_list(np.array([1, 2])) == [1, 2]


# ---------------------------------------------------------------------------
# VectorConstellation housekeeping + sync branches
# ---------------------------------------------------------------------------


def _stub_seed_metadata(created_at: str, status: str = "NEW", weight: float = 0.0):
    return {
        "text": "t",
        "weight": weight,
        "trace": 1.0,
        "status": status,
        "occurrence_count": 1,
        "evidence_count": 0,
        "created_at": created_at,
    }


def test_housekeeping_deletes_only_old_open_weightless_seeds():
    store = InMemoryVectorStore()
    constellation = VectorConstellation(store)
    old = (datetime.now() - timedelta(days=90)).isoformat()
    fresh = datetime.now().isoformat()

    store.add("old_open", np.ones(4), _stub_seed_metadata(old))
    store.add("fresh_open", np.ones(4), _stub_seed_metadata(fresh))
    store.add("old_promoted", np.ones(4), _stub_seed_metadata(old, status="PROMOTED", weight=0.6))
    store.add("bad_date", np.ones(4), _stub_seed_metadata("not-a-date"))

    deleted = constellation.housekeeping(max_age_days=30)
    assert deleted == ["old_open"]
    remaining = set(store.get_all_ids())
    # promoted evidence is never garbage-collected; unparsable dates are skipped
    assert remaining == {"fresh_open", "old_promoted", "bad_date"}


def test_sync_seed_updates_existing_and_adds_new():
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(embedding_fn=lexical_embedding)
    sid = manager.add_or_update_seed("Ontbrekende bronvermelding bij de kernclaim.")
    seed = manager.get_seed(sid)

    constellation.sync_seed(seed)  # not present yet -> add
    assert sid in constellation.store.get_all_ids()
    seed.trace = 2.5
    constellation.sync_seed(seed)  # present -> metadata update
    assert constellation.store.get_metadata(sid)["trace"] == 2.5


# ---------------------------------------------------------------------------
# Smoke runner end-to-end on the dependency-free backend
# ---------------------------------------------------------------------------


def test_vectorstore_smoke_runs_and_passes(tmp_path: Path):
    from shadowseed.benchmark.vectorstore_smoke import run_vectorstore_smoke

    out = run_vectorstore_smoke(str(tmp_path / "smoke.json"), backend="memory")
    import json

    payload = json.loads(Path(out).read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["passed"] is True
    assert summary["created_weight"] == 0.0  # weightless at birth
    assert summary["promoted_weight"] >= 0.5  # influence only via the Gate
    assert summary["contradicted_weight"] < summary["promoted_weight"]
