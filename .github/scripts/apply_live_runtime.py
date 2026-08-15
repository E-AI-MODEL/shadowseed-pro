from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count} for {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


path = "src/shadowseed/chat.py"
replace_once(
    path,
    "from shadowseed.models import ProbeFeedbackResult, SeedEvent, ValidationGateResult\n",
    "from shadowseed.models import (\n    CandidateType,\n    ProbeFeedbackResult,\n    SeedEvent,\n    SeedOrigin,\n    ValidationGateResult,\n)\n",
)
replace_once(
    path,
    "        probe_corpus: str | None = None,\n        probe_top_k: int = 3,\n    ) -> None:\n",
    "        probe_corpus: str | None = None,\n        probe_top_k: int = 3,\n        runtime_mode: str = \"evaluation\",\n        gate_policy_id: str | None = None,\n        allow_toy_embedder: bool = False,\n    ) -> None:\n",
)
replace_once(
    path,
    "        self.cluster_threshold = cluster_threshold\n        self.probe_corpus_path = probe_corpus\n\n        embed_fn, _dim = make_embedding_fn(embedding_backend, embedding_model)\n",
    "        self.cluster_threshold = cluster_threshold\n        self.probe_corpus_path = probe_corpus\n        if runtime_mode not in {\"evaluation\", \"live\"}:\n            raise ValueError(\"runtime_mode must be 'evaluation' or 'live'\")\n        self.runtime_mode = runtime_mode\n        self.gate_policy_id = gate_policy_id or (\n            \"evidence_backed\" if runtime_mode == \"live\" else \"exploratory\"\n        )\n        self.allow_toy_embedder = allow_toy_embedder\n        if (\n            runtime_mode == \"live\"\n            and backend != \"fixture\"\n            and embedding_backend == \"lexical\"\n            and not allow_toy_embedder\n        ):\n            raise ValueError(\n                \"live runtime requires a semantic embedding backend; \"\n                \"use sentence-transformers/openai or pass allow_toy_embedder=True \"\n                \"only for an explicit non-production experiment\"\n            )\n\n        embed_fn, _dim = make_embedding_fn(embedding_backend, embedding_model)\n",
)
old_turn_header = """    def turn(self, question: str) -> dict[str, Any]:
        \"\"\"Run one turn while keeping baseline history isolated from SSL output.\"\"\"
"""
new_turn_header = """    def turn(self, question: str) -> dict[str, Any]:
        \"\"\"Run one turn through the configured evaluation or live runtime.\"\"\"
        if self.runtime_mode == \"live\":
            return self._turn_live(question)
        return self._turn_evaluation(question)

    def _filter_ssl_attributed_candidates(
        self,
        candidates: list[str],
        surfaced_seed_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        \"\"\"Suppress candidates attributable to this turn's own SSL input.\"\"\"
        if not surfaced_seed_ids:
            return list(candidates), []
        threshold = self.manager.dedup_threshold
        if self.clusterer is not None:
            threshold = min(threshold, self.clusterer.threshold)
        source_embeddings = [
            self.manager.seeds[seed_id].embedding
            for seed_id in surfaced_seed_ids
            if seed_id in self.manager.seeds
        ]
        kept: list[str] = []
        suppressed: list[str] = []
        for candidate in candidates:
            candidate_embedding = self.manager.get_embedding(candidate)
            attributable = any(
                float(np.dot(candidate_embedding, source_embedding)) >= threshold
                for source_embedding in source_embeddings
            )
            (suppressed if attributable else kept).append(candidate)
        return kept, suppressed

    def _turn_live(self, question: str) -> dict[str, Any]:
        \"\"\"Production-oriented one-generation loop with visible-history continuity.\"\"\"
        turn = self._turn
        if turn > 0:
            self.manager.decay_traces(turns_passed=1)
        reactivated = self.manager.scan_trtl_triggers(question)

        def _is_cluster_representative(seed_id: str) -> bool:
            if self.clusterer is None:
                return True
            cluster_id = self.seed_to_cluster.get(seed_id)
            return cluster_id is None or self.cluster_rep.get(cluster_id) == seed_id

        eligible = collect_eligible_promoted_seeds(
            self.manager,
            question,
            turn=turn,
            born_turn=self.born_turn,
            last_surfaced=self.last_surfaced,
            policy=self.surfacing_policy,
            include_seed=_is_cluster_representative,
        )
        selected = select_cross_turn_seeds(eligible, self.surfacing_policy.surface_top_k)
        allowed = self._contract_filter(selected)
        surfaced = [text for _similarity, _seed_id, text in allowed]
        surfaced_seed_ids = [seed_id for _similarity, seed_id, _text in allowed]
        mark_surfaced(self.last_surfaced, allowed, turn)

        fixture_answer = f\"Fixture echo answer to: {question}\"
        final_answer = self.model.generate(
            build_chat_prompt(self.history, question, surfaced),
            {\"question\": question, \"turn\": turn, \"baseline_answer\": fixture_answer},
            \"ssl\" if surfaced else \"baseline\",
            surfaced,
        )

        raw_candidates = self.detector.detect_seeds(
            {\"text\": final_answer}, max_seeds=self.max_seeds_per_turn
        )
        candidates, suppressed_self = self._filter_ssl_attributed_candidates(
            raw_candidates, surfaced_seed_ids
        )
        occurrence_before = {
            seed_id: seed.occurrence_count for seed_id, seed in self.manager.seeds.items()
        }
        origin = SeedOrigin(
            candidate_type=CandidateType.POSSIBLE_COMPLETION,
            detection_basis=\"visible_answer_non_ssl_attributed\",
            context_ref=f\"turn:{turn}:visible_answer\",
        )
        ingest = self.manager.ingest_detection_candidates(candidates, origin=origin)
        born: list[str] = []
        for accepted in ingest.get(\"accepted\", []):
            self.born_turn.setdefault(accepted[\"seed_id\"], turn)
            born.append(accepted[\"seed_id\"])

        if self.clusterer is not None:
            for accepted in ingest.get(\"accepted\", []):
                seed_id = accepted[\"seed_id\"]
                seed = self.manager.seeds.get(seed_id)
                if seed is None:
                    continue
                if seed_id not in self.seed_to_cluster:
                    cluster_id = self.clusterer.add(seed.text, seed.embedding)
                    had_representative = cluster_id in self.cluster_rep
                    self.seed_to_cluster[seed_id] = cluster_id
                    self.cluster_rep.setdefault(cluster_id, seed_id)
                    representative_id = self.cluster_rep.get(cluster_id)
                    if had_representative and representative_id is not None and representative_id != seed_id:
                        representative = self.manager.seeds.get(representative_id)
                        if representative is not None:
                            refresh_cluster_representative(self.manager, representative, seed)
                else:
                    cluster_id = self.seed_to_cluster[seed_id]
                    self.clusterer.bump(cluster_id)
                    representative = self.manager.seeds.get(self.cluster_rep.get(cluster_id, \"\"))
                    if representative is not None and representative is not seed:
                        refresh_cluster_representative(self.manager, representative, seed)

            for cluster_id, representative_id in self.cluster_rep.items():
                if representative_id in self.manager.seeds:
                    representative = self.manager.seeds[representative_id]
                    representative.occurrence_count = max(
                        representative.occurrence_count, self.clusterer.recurrence(cluster_id)
                    )

        changed_seed_ids = {
            seed_id
            for seed_id, seed in self.manager.seeds.items()
            if occurrence_before.get(seed_id) != seed.occurrence_count
        }
        promoted_now: list[str] = []
        recurrence_threshold = self.manager.config.min_occurrences_for_gate
        for seed_id in sorted(changed_seed_ids):
            seed = self.manager.seeds[seed_id]
            if seed.status == SeedStatus.EXPIRED or seed.occurrence_count < recurrence_threshold:
                continue
            if self.clusterer is not None:
                cluster_id = self.seed_to_cluster.get(seed_id)
                if cluster_id is not None and self.cluster_rep.get(cluster_id) != seed_id:
                    continue
            event = self.manager.submit_signals(
                seed_id,
                [recurrence_signal(seed.occurrence_count, threshold=recurrence_threshold)],
                policy_id=self.gate_policy_id,
            )
            if event.decision is GateDecision.PROMOTED and seed.status == SeedStatus.PROMOTED:
                promoted_now.append(seed_id)

        self.history.append((question, final_answer))
        self._turn += 1
        report = {
            \"runtime_mode\": \"live\",
            \"turn\": turn,
            \"question\": question,
            \"answer\": final_answer,
            \"baseline_answer\": None,
            \"ssl_answer\": final_answer if surfaced else None,
            \"surfaced_seeds\": surfaced,
            \"surfaced_seed_ids\": surfaced_seed_ids,
            \"selected_seed_ids\": [seed_id for _sim, seed_id, _text in selected],
            \"influence_decisions\": (
                [record.__dict__.copy() for record in self.influence_records[-len(selected):]]
                if selected else []
            ),
            \"detected_candidates\": raw_candidates,
            \"suppressed_self_attributed_candidates\": suppressed_self,
            \"seeds_born_weightless\": born,
            \"prompt_boundary_markers\": apply_prompt_boundary(surfaced)[1] if surfaced else [],
            \"promoted_this_turn\": promoted_now,
            \"reactivated_trtl\": reactivated,
            \"shadow_size\": len(self.manager.seeds),
            \"retrieval_probe\": self._run_retrieval_probe(question),
        }
        self.turn_reports.append(report)
        return report

    def _turn_evaluation(self, question: str) -> dict[str, Any]:
        \"\"\"Run the research comparison loop with baseline history isolation.\"\"\"
"""
replace_once(path, old_turn_header, new_turn_header)
replace_once(
    path,
    "[recurrence_signal(seed.occurrence_count, threshold=2)],\n                policy_id=\"exploratory\",",
    "[recurrence_signal(\n                    seed.occurrence_count,\n                    threshold=self.manager.config.min_occurrences_for_gate,\n                )],\n                policy_id=\"exploratory\",",
)
replace_once(
    path,
    "            \"turn\": turn,\n            \"question\": question,\n",
    "            \"runtime_mode\": \"evaluation\",\n            \"turn\": turn,\n            \"question\": question,\n",
)
replace_once(
    path,
    "                \"probe_corpus\": self.probe_corpus_path,\n                \"probe_top_k\": self.probe_top_k,\n",
    "                \"probe_corpus\": self.probe_corpus_path,\n                \"probe_top_k\": self.probe_top_k,\n                \"runtime_mode\": self.runtime_mode,\n                \"gate_policy_id\": self.gate_policy_id,\n                \"allow_toy_embedder\": self.allow_toy_embedder,\n",
)
replace_once(
    path,
    "            \"history\": [\n                {\"question\": question, \"baseline_answer\": answer}\n                for question, answer in self.history\n            ],\n",
    "            \"history\": [\n                {\n                    \"question\": question,\n                    \"answer\": answer,\n                    \"baseline_answer\": answer if self.runtime_mode == \"evaluation\" else None,\n                }\n                for question, answer in self.history\n            ],\n",
)
replace_once(
    path,
    "            (str(item.get(\"question\", \"\")), str(item.get(\"baseline_answer\", \"\")))\n            if isinstance(item, dict)\n",
    "            (\n                str(item.get(\"question\", \"\")),\n                str(item.get(\"answer\", item.get(\"baseline_answer\", \"\"))),\n            )\n            if isinstance(item, dict)\n",
)
replace_once(
    path,
    "            \"turns\": self._turn,\n            \"seeds\": seeds,\n",
    "            \"runtime_mode\": self.runtime_mode,\n            \"turns\": self._turn,\n            \"seeds\": seeds,\n",
)
replace_once(
    path,
    "    probe_corpus: str | None = None,\n    probe_top_k: int = 3,\n) -> Path | None:\n",
    "    probe_corpus: str | None = None,\n    probe_top_k: int = 3,\n    runtime_mode: str = \"live\",\n    gate_policy_id: str | None = None,\n    allow_toy_embedder: bool = False,\n) -> Path | None:\n",
)
replace_once(
    path,
    "        probe_corpus=probe_corpus,\n        probe_top_k=probe_top_k,\n    )\n",
    "        probe_corpus=probe_corpus,\n        probe_top_k=probe_top_k,\n        runtime_mode=runtime_mode,\n        gate_policy_id=gate_policy_id,\n        allow_toy_embedder=allow_toy_embedder,\n    )\n",
)

replace_once(
    "src/shadowseed/application/models.py",
    "    probe_corpus: str | None = None\n    probe_top_k: int = 3\n",
    "    probe_corpus: str | None = None\n    probe_top_k: int = 3\n    runtime_mode: str = \"evaluation\"\n    gate_policy_id: str | None = None\n    allow_toy_embedder: bool = False\n",
)

path = "src/shadowseed/adapters/embedding.py"
replace_once(
    path,
    "SUPPORTED_EMBEDDING_BACKENDS: tuple[str, ...] = (\"lexical\", \"openai\")\n",
    "SUPPORTED_EMBEDDING_BACKENDS: tuple[str, ...] = (\n    \"lexical\",\n    \"sentence-transformers\",\n    \"openai\",\n)\n",
)
replace_once(
    path,
    "    if backend == \"openai\":\n",
    "    if backend == \"sentence-transformers\":\n        try:\n            from sentence_transformers import SentenceTransformer\n        except ImportError as exc:\n            raise RuntimeError(\n                \"Install shadowseed[models] to use sentence-transformers embeddings\"\n            ) from exc\n        model = model_id or \"sentence-transformers/all-MiniLM-L6-v2\"\n        encoder = SentenceTransformer(model)\n        dimension = int(encoder.get_sentence_embedding_dimension())\n\n        def sentence_transformer_embed(text: str) -> np.ndarray:\n            return np.asarray(encoder.encode(text, normalize_embeddings=True), dtype=float)\n\n        return sentence_transformer_embed, dimension\n\n    if backend == \"openai\":\n",
)

path = "src/shadowseed/cli.py"
replace_once(
    path,
    "        help=\"[demo] interactive SSL shadow layer (manager, Gate, TTL/TrTL, agent contract)\",\n",
    "        help=\"[live] SSL conversation runtime; use --runtime-mode evaluation for research A/B\",\n",
)
replace_once(
    path,
    "    chat.add_argument(\"--embedding-backend\", choices=[\"lexical\", \"openai\"], default=\"lexical\")\n",
    "    chat.add_argument(\n        \"--embedding-backend\",\n        choices=[\"lexical\", \"sentence-transformers\", \"openai\"],\n        default=\"lexical\",\n    )\n    chat.add_argument(\n        \"--runtime-mode\",\n        choices=[\"live\", \"evaluation\"],\n        default=\"live\",\n        help=\"live uses one visible generation; evaluation keeps the isolated A/B baseline arm.\",\n    )\n    chat.add_argument(\n        \"--gate-policy\",\n        choices=[\"exploratory\", \"evidence_backed\"],\n        default=None,\n        help=\"Override the runtime policy. live defaults to evidence_backed.\",\n    )\n    chat.add_argument(\n        \"--allow-toy-embedder\",\n        action=\"store_true\",\n        help=\"Explicitly allow lexical hash embeddings in live non-fixture sessions.\",\n    )\n",
)
path = "src/shadowseed/cli_dispatch.py"
replace_once(
    path,
    "        probe_corpus=getattr(args, \"probe_corpus\", None),\n        probe_top_k=getattr(args, \"probe_top_k\", 3),\n",
    "        probe_corpus=getattr(args, \"probe_corpus\", None),\n        probe_top_k=getattr(args, \"probe_top_k\", 3),\n        runtime_mode=getattr(args, \"runtime_mode\", \"live\"),\n        gate_policy_id=getattr(args, \"gate_policy\", None),\n        allow_toy_embedder=getattr(args, \"allow_toy_embedder\", False),\n",
)

path = "src/shadowseed/benchmark/ssl_session_suite.py"
replace_once(
    path,
    "    data = json.loads(Path(input_path).read_text(encoding=\"utf-8\"))\n    embed_fn, _dim = make_embedding_fn(embedding_backend, embedding_model)\n",
    "    data = json.loads(Path(input_path).read_text(encoding=\"utf-8\"))\n    if backend == \"fixture\":\n        missing = [\n            f\"{conv.get('id', 'conversation')}:{index}\"\n            for conv in data.get(\"conversations\", [])\n            for index, turn in enumerate(conv.get(\"turns\", []))\n            if not str(turn.get(\"baseline_answer\", \"\")).strip()\n        ]\n        if missing:\n            preview = \", \".join(missing[:5])\n            raise ValueError(\n                \"fixture backend requires authored baseline_answer text for every \"\n                f\"session turn; missing: {preview}. Use a real model backend for \"\n                \"question-only session suites.\"\n            )\n    embed_fn, _dim = make_embedding_fn(embedding_backend, embedding_model)\n",
)
replace_once(
    path,
    "[recurrence_signal(seed.occurrence_count, threshold=2)],\n                    policy_id=\"exploratory\",",
    "[recurrence_signal(\n                        seed.occurrence_count,\n                        threshold=manager.config.min_occurrences_for_gate,\n                    )],\n                    policy_id=\"exploratory\",",
)

replace_once(
    "src/shadowseed/lifecycle.py",
    "        seed.trace *= math.exp(-turns_passed / manager.half_life_turns)\n",
    "        seed.trace *= math.exp(\n            -math.log(2.0) * turns_passed / manager.half_life_turns\n        )\n",
)

path = "src/shadowseed/application/health.py"
replace_once(
    path,
    "    checks.append(_ollama_check())\n",
    "    checks.append(_ollama_check())\n    checks.append(\n        HealthCheck(\n            \"live_embedding\",\n            \"warning\",\n            \"lexical hashing is demo/CI-only for live non-fixture sessions\",\n            \"Use sentence-transformers locally or OpenAI embeddings for live sessions.\",\n        )\n    )\n",
)

path = "tests/test_ssl_session_suite.py"
replace_once(
    path,
    '''def test_transfer_suite_runs_through_pipeline(tmp_path: Path):
    # W10: the doctrine-transfer dataset (new domains) must run through the same
    # pipeline. Fixture backend -> deterministic, no model/secret needed.
    out = tmp_path / "t.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_transfer_suite.json", str(out), backend="fixture"
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["artifact"] == "ssl_session_suite"
    assert payload["summary"]["conversation_count"] == 3
    domains = {c["domain"] for c in payload["conversations"]}
    assert domains == {"onderwijs", "publieke gezondheid", "beleid"}
''',
    '''def test_transfer_suite_fixture_refuses_question_only_input(tmp_path: Path):
    out = tmp_path / "t.json"
    with pytest.raises(ValueError, match="requires authored baseline_answer"):
        run_ssl_session(
            "src/shadowseed/data/ssl_session_transfer_suite.json", str(out), backend="fixture"
        )
''',
)
replace_once(
    path,
    '''def test_fixture_smoke_runs(tmp_path: Path):
    out = tmp_path / "s.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_suite.json", str(out), backend="fixture"
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["artifact"] == "ssl_session_suite"
    assert payload["summary"]["conversation_count"] == 3
''',
    '''def test_fixture_refuses_dead_question_only_session_run(tmp_path: Path):
    out = tmp_path / "s.json"
    with pytest.raises(ValueError, match="requires authored baseline_answer"):
        run_ssl_session(
            "src/shadowseed/data/ssl_session_suite.json", str(out), backend="fixture"
        )
''',
)
replace_once(
    path,
    '''            {"id": "A", "domain": "d", "dedup_threshold": 0.55, "min_occurrences": 2,
             "turns": [{"question": "Q1?"}, {"question": "Q2?"}]},
            {"id": "B", "domain": "d", "turns": [{"question": "Q1?"}, {"question": "Q2?"}]},
''',
    '''            {"id": "A", "domain": "d", "dedup_threshold": 0.55, "min_occurrences": 2,
             "turns": [
                 {"question": "Q1?", "baseline_answer": "Fixture A1."},
                 {"question": "Q2?", "baseline_answer": "Fixture A2."},
             ]},
            {"id": "B", "domain": "d", "turns": [
                {"question": "Q1?", "baseline_answer": "Fixture B1."},
                {"question": "Q2?", "baseline_answer": "Fixture B2."},
            ]},
''',
)
replace_once(
    path,
    '''def test_surface_settings_recorded(tmp_path: Path):
    out = tmp_path / "s.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_suite.json", str(out), backend="fixture", surface_top_k=1
    )
    appl = json.loads(out.read_text(encoding="utf-8"))["conversations"][0]["applied_thresholds"]
    assert appl["surface_top_k"] == 1
    assert "surface_threshold" in appl
''',
    '''def test_surface_settings_recorded(tmp_path: Path):
    inp = tmp_path / "input.json"
    inp.write_text(
        json.dumps(
            {
                "version": "t",
                "conversations": [
                    {
                        "id": "C",
                        "domain": "d",
                        "turns": [
                            {"question": "Q1?", "baseline_answer": "Fixture baseline."}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="fixture", surface_top_k=1)
    appl = json.loads(out.read_text(encoding="utf-8"))["conversations"][0]["applied_thresholds"]
    assert appl["surface_top_k"] == 1
    assert "surface_threshold" in appl
''',
)

Path("tests/test_live_runtime.py").write_text('''from __future__ import annotations

import numpy as np
import pytest

import shadowseed.chat as chatmod
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import SignalKind, ValidationSignal
from shadowseed.manager import SeedStatus


class RecordingModel:
    name = "recording"

    def __init__(self, answer: str = "Visible answer.") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, prompt, scenario, mode, seeds):
        self.calls.append((prompt, mode, list(seeds)))
        return self.answer


class StaticDetector:
    name = "static"

    def __init__(self, seed: str | None) -> None:
        self.seed = seed

    def detect_seeds(self, item, max_seeds=5):
        return [] if self.seed is None else [self.seed]


def _emb_factory(backend, model_id=None, **kwargs):
    def embed(text: str) -> np.ndarray:
        low = text.lower()
        if "privacy" in low or "data" in low:
            return np.array([1.0, 0.0])
        return np.array([0.0, 1.0])
    return embed, 2


def _session(monkeypatch, *, detector_seed=None, answer="Visible answer.", **kwargs):
    model = RecordingModel(answer)
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: model)
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(detector_seed))
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    session = ShadowChatSession(
        backend="openai",
        embedding_backend="openai",
        runtime_mode="live",
        recurrence_mode="pairwise",
        **kwargs,
    )
    return session, model


def test_live_turn_uses_one_generation_and_stores_visible_answer(monkeypatch):
    session, model = _session(monkeypatch, detector_seed=None, answer="What the user read.")
    report = session.turn("Question?")
    assert len(model.calls) == 1
    assert report["runtime_mode"] == "live"
    assert report["answer"] == "What the user read."
    assert report["baseline_answer"] is None
    assert session.history == [("Question?", "What the user read.")]


def test_live_recurrence_alone_never_grants_authority(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed="Privacy as a missing decision boundary.",
        answer="Answer about data.",
    )
    for index in range(6):
        session.turn(f"Question about data {index}?")
    seed = next(iter(session.manager.seeds.values()))
    assert seed.occurrence_count >= session.manager.config.min_occurrences_for_gate
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED
    assert session.gate_policy_id == "evidence_backed"
    assert session.manager.gate_events
    assert all(event.decision.value == "blocked" for event in session.manager.gate_events)


def test_live_suppresses_self_attributed_recurrence(monkeypatch):
    seed_text = "Privacy as a missing decision boundary."
    session, _model = _session(
        monkeypatch,
        detector_seed=seed_text,
        answer="Privacy remains important for this data decision.",
    )
    seed_id = session.manager.add_or_update_seed(seed_text)
    for index in range(3):
        session.manager.submit_signals(
            seed_id,
            [ValidationSignal(kind=SignalKind.SSOT, verified=True, source_ref=f"source:{index}")],
            policy_id="evidence_backed",
        )
    seed = session.manager.seeds[seed_id]
    assert seed.status is SeedStatus.PROMOTED
    before = seed.occurrence_count
    report = session.turn("What about privacy and data?")
    assert seed_id in report["surfaced_seed_ids"]
    assert report["suppressed_self_attributed_candidates"] == [seed_text]
    assert session.manager.seeds[seed_id].occurrence_count == before


def test_live_non_fixture_rejects_lexical_embedder(monkeypatch):
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: RecordingModel())
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(None))
    with pytest.raises(ValueError, match="requires a semantic embedding backend"):
        ShadowChatSession(backend="openai", embedding_backend="lexical", runtime_mode="live")


def test_evaluation_mode_remains_available(monkeypatch):
    session, model = _session(monkeypatch, detector_seed=None)
    session.runtime_mode = "evaluation"
    session.gate_policy_id = "exploratory"
    report = session.turn("Question?")
    assert report["runtime_mode"] == "evaluation"
    assert len(model.calls) == 1


def test_half_life_turns_is_a_real_half_life(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    seed_id = session.manager.add_or_update_seed("Privacy as a lifecycle test case.")
    start = session.manager.seeds[seed_id].trace
    session.manager.decay_traces(turns_passed=session.manager.half_life_turns)
    assert session.manager.seeds[seed_id].trace == pytest.approx(start / 2.0)
''', encoding="utf-8")

print("live runtime patch applied")
