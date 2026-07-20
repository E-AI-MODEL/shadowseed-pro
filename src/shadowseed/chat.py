"""Living shadow layer: an interactive SSL chat session (vision item 5).

`docs/research/vision-generative-seeds.md` §6.5 names the missing piece: the
lifecycle is unit-tested and benchmark-harnessed (W9), but the "shadow" in
shadow seed never had an *operational* demonstration — a seed born in turn 1,
dormant in the shadow, revalidated in turn 3, steering only then. This module is
that demonstration: the same pipeline semantics as ``ssl_session_suite`` (W9e
cluster recurrence, W9f representative promotion, round-023 use-time
discipline), but driving a real conversation instead of a benchmark, with the
`shadowseed_agent` safety contract enforced at the influence boundary and a
replayable audit trail.

Doctrine, enforced in code rather than assumed:

- seeds are born weightless every turn (trace only);
- influence exists only after Validation Gate promotion, and the
  ``AgentSafetyContract`` re-checks that at use time (weight > 0, PROMOTED,
  logged promotion, no active contradiction);
- use-time discipline: a promoted seed is *potential, not must* — ranked, capped
  (``surface_top_k``) and woven only where it sharpens;
- falsification is user-driven (``/falsify``): a contradicted seed loses weight
  and the contract blocks it from then on;
- every attempted influence is recorded as an ``AgentInfluenceRecord``; audit
  replay (``/audit``) fails hard on any weightless influence.

This is an application demo on top of the validated mechanics, not a new
evidence layer. Claim boundaries in the research docs are unchanged.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.detection.model_detector import make_detector_backend
from shadowseed.recurrence_clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    RecurrenceClusterer,
)
from shadowseed.retrieval_probe import retrieval_probe_vs_question
from shadowseed.adapters.models import make_backend
from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import recurrence_signal
from shadowseed.recurrence import refresh_cluster_representative
from shadowseed.surfacing import (
    SurfacingCandidate,
    SurfacingPolicy,
    apply_prompt_boundary,
    build_chat_prompt,
    collect_eligible_promoted_seeds,
    mark_surfaced,
    select_cross_turn_seeds,
)
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.vectorstore.memory import InMemoryVectorStore
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    assert_influence_records_valid,
)


class ShadowChatSession:
    """One live conversation with a shadow layer of weightless seeds."""

    def __init__(
        self,
        *,
        backend: str = "fixture",
        model_id: str | None = None,
        max_new_tokens: int = 700,
        embedding_backend: str = "lexical",
        embedding_model: str | None = None,
        surface_threshold: float = 0.30,
        surface_top_k: int = 2,
        early_turn_margin: float = 0.10,
        early_turn_history: int = 5,
        resurface_margin: float = 0.15,
        max_seeds_per_turn: int = 5,
        recurrence_mode: str = "cluster",
        cluster_threshold: float | None = None,
        contract: AgentSafetyContract | None = None,
        probe_corpus: str | None = None,
        probe_top_k: int = 3,
    ) -> None:
        embed_fn, _dim = make_embedding_fn(embedding_backend, embedding_model)
        self.model = make_backend(backend=backend, model_id=model_id, max_new_tokens=max_new_tokens)
        self.detector = make_detector_backend(
            backend, model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant="generative"
        )
        self.manager = SSLManager(embedding_fn=embed_fn)
        self.contract = contract or AgentSafetyContract()
        self.surfacing_policy = SurfacingPolicy(
            surface_threshold=surface_threshold,
            surface_top_k=surface_top_k,
            early_turn_margin=early_turn_margin,
            early_turn_history=early_turn_history,
            resurface_margin=resurface_margin,
        )
        # Compatibility attributes for callers that inspect session settings.
        self.surface_threshold = self.surfacing_policy.surface_threshold
        self.surface_top_k = self.surfacing_policy.surface_top_k
        self.early_turn_margin = self.surfacing_policy.early_turn_margin
        self.early_turn_history = self.surfacing_policy.early_turn_history
        self.resurface_margin = self.surfacing_policy.resurface_margin
        self.max_seeds_per_turn = max_seeds_per_turn
        self.clusterer = (
            RecurrenceClusterer(threshold=cluster_threshold or DEFAULT_CLUSTER_THRESHOLD)
            if recurrence_mode == "cluster"
            else None
        )
        self.seed_to_cluster: dict[str, int] = {}
        self.cluster_rep: dict[int, str] = {}
        self.born_turn: dict[str, int] = {}
        self.last_surfaced: dict[str, int] = {}
        self.history: list[tuple[str, str]] = []
        self.influence_records: list[AgentInfluenceRecord] = []
        self.turn_reports: list[dict[str, Any]] = []
        self._turn = 0
        # SSL->RAG bridge (vision item 2): promoted seeds probe this corpus so
        # the report can show what the seed finds that the question does not.
        self.probe_top_k = probe_top_k
        self.probe_store = self._load_probe_corpus(probe_corpus) if probe_corpus else None

    # -- doctrine boundary ---------------------------------------------------

    def _contract_filter(
        self, candidates: list[SurfacingCandidate]
    ) -> list[SurfacingCandidate]:
        """Re-check each candidate at use time and retain allowed seed IDs."""

        allowed: list[SurfacingCandidate] = []
        for similarity, seed_id, text in candidates:
            seed = self.manager.seeds[seed_id]
            # Atomic point-of-use: decide and record in one step, linked to the
            # authorizing Gate event (#14). A decision cannot be used without
            # being recorded, because the record is produced here.
            record = self.contract.decide_and_record(
                seed,
                InfluenceAction.ANSWER_MODIFICATION,
                gate_events=self.manager.gate_events,
                ledger=self.influence_records,
                context_ref=f"turn:{self._turn}",
                now=self.manager._now_iso(),
                contradiction_blocking=self.manager.is_blocking_contradiction(seed_id),
            )
            if record.allowed:
                allowed.append((similarity, seed_id, text))
        return allowed

    def audit(self) -> int:
        """Replay every influence decision against all point-of-use invariants;
        raise on any allowed influence that is weightless, non-promoted,
        contradicted, or not linked to a valid Gate event."""
        assert_influence_records_valid(self.influence_records, self.manager.gate_events)
        return len(self.influence_records)


    # -- SSL->RAG bridge (retrieval = presence, never steering) ----------------

    def _load_probe_corpus(self, path: str) -> InMemoryVectorStore:
        """Load a corpus into an in-memory store, embedded like the seeds.

        Accepts the repo retrieval-corpus schema (``documents[].chunks`` with
        ``chunk_id``, as indexed by ``index_retrieval_corpus``), a flat JSON
        list of ``{"id"|"chunk_id": ..., "text": ...}`` chunks (also under a
        top-level ``"chunks"`` key), or plain text split on blank lines.
        Raises when nothing indexes: an empty store must fail loudly, not probe
        silently against nothing.
        """
        raw = Path(path).read_text(encoding="utf-8")
        chunks: list[tuple[str, str, str | None]] = []  # (chunk_id, text, doc_id)
        if path.endswith(".json"):
            data = json.loads(raw)
            if isinstance(data, dict) and "documents" in data:
                items = [
                    {**chunk, "doc_id": doc.get("doc_id")}
                    for doc in data["documents"]
                    for chunk in doc.get("chunks", [])
                ]
            elif isinstance(data, dict):
                items = data.get("chunks", [])
            else:
                items = data
            for i, item in enumerate(items):
                text = str(item.get("text", "")).strip()
                if text:
                    chunk_id = str(item.get("chunk_id") or item.get("id") or f"chunk_{i:03d}")
                    chunks.append((chunk_id, text, item.get("doc_id")))
        else:
            for i, block in enumerate(p.strip() for p in raw.split("\n\n")):
                if block:
                    chunks.append((f"chunk_{i:03d}", block, None))
        if not chunks:
            raise ValueError(
                f"Probe corpus '{path}' contains no indexable chunks "
                "(expected documents[].chunks, a JSON list with 'text', or plain text)."
            )
        store = InMemoryVectorStore()
        for chunk_id, text, doc_id in chunks:
            store.add(
                chunk_id,
                self.manager.get_embedding(text),
                {"text": text, "chunk_id": chunk_id, "doc_id": doc_id},
            )
        return store

    def _run_retrieval_probe(self, question: str) -> dict[str, Any] | None:
        """Probe the corpus with promoted seeds; report presence, change nothing.

        Doctrine: what a seed *finds* is never *true* or *steering* — the hits go
        into the report only, never into the answer prompt, and probing mutates
        no seed state. When the manager sees a retrieval-grade constellation,
        its centroid is the query (the manager-centroid finally consumed);
        otherwise each promoted seed (representative only, in cluster mode)
        probes on its own.
        """
        if self.probe_store is None:
            return None
        seed_texts: list[str] = []
        for sid, seed in self.manager.seeds.items():
            if seed.status != SeedStatus.PROMOTED:
                continue
            if self.clusterer is not None:
                cid = self.seed_to_cluster.get(sid)
                if cid is not None and self.cluster_rep.get(cid) != sid:
                    continue
            seed_texts.append(seed.text)
        if not seed_texts:
            return None
        retrieval_consts = [
            c for c in self.manager.find_constellations() if c.probe_type == "retrieval"
        ]
        use_centroid = bool(retrieval_consts)
        if use_centroid:
            members = set(retrieval_consts[0].members)
            seed_texts = [
                self.manager.seeds[sid].text for sid in members if sid in self.manager.seeds
            ] or seed_texts
        res = retrieval_probe_vs_question(
            self.probe_store,
            question,
            seed_texts,
            top_k=self.probe_top_k,
            use_centroid=use_centroid,
            embed_fn=self.manager.get_embedding,
        )
        seed_only = set(res["seed_only_chunk_ids"])
        return {
            "use_centroid": res["use_centroid"],
            "probe_seed_texts": res["seed_texts"],
            "question_chunk_ids": res["question_chunk_ids"],
            "probe_chunk_ids": res["probe_chunk_ids"],
            "shared_chunk_ids": res["shared_chunk_ids"],
            "seed_only_chunk_ids": res["seed_only_chunk_ids"],
            "seed_only_hits": [h for h in res["probe_hits"] if h["chunk_id"] in seed_only],
        }

    # -- one live turn ---------------------------------------------------------

    def turn(self, question: str) -> dict[str, Any]:
        """Run one turn while keeping baseline history isolated from SSL output."""

        turn = self._turn
        if turn > 0:
            self.manager.decay_traces(turns_passed=1)
        reactivated = self.manager.scan_trtl_triggers(question)

        # 1. Generate an uncontaminated baseline. The baseline is also the only
        # answer stored in history and the only answer inspected for new gaps.
        baseline_answer = self.model.generate(
            build_chat_prompt(self.history, question, []),
            {
                "question": question,
                "turn": turn,
                "baseline_answer": f"Fixture echo answer to: {question}",
            },
            "baseline",
            [],
        )

        # 2. Select promoted, earlier-born seeds through the shared policy.
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

        # 3. The safety contract is the final influence boundary. Only allowed
        # seeds count as surfaced for resurface damping.
        allowed = self._contract_filter(selected)
        surfaced = [text for _similarity, _seed_id, text in allowed]
        mark_surfaced(self.last_surfaced, allowed, turn)

        if surfaced:
            ssl_answer = self.model.generate(
                build_chat_prompt(self.history, question, surfaced),
                {
                    "question": question,
                    "turn": turn,
                    "baseline_answer": baseline_answer,
                },
                "ssl",
                surfaced,
            )
            final_answer = ssl_answer
        else:
            ssl_answer = baseline_answer
            final_answer = baseline_answer

        # 4. Detect gaps only in the baseline to avoid gap starvation and
        # self-reinforcing history contamination. Every accepted seed starts at
        # weight zero.
        candidates = self.detector.detect_seeds(
            {"text": baseline_answer}, max_seeds=self.max_seeds_per_turn
        )
        ingest = self.manager.ingest_detection_candidates(candidates)
        born: list[str] = []
        for accepted in ingest.get("accepted", []):
            self.born_turn.setdefault(accepted["seed_id"], turn)
            born.append(accepted["seed_id"])

        # 5. Credit semantic recurrence to one cluster representative.
        if self.clusterer is not None:
            for accepted in ingest.get("accepted", []):
                seed_id = accepted["seed_id"]
                seed = self.manager.seeds.get(seed_id)
                if seed is None:
                    continue
                if seed_id not in self.seed_to_cluster:
                    cluster_id = self.clusterer.add(seed.text, seed.embedding)
                    had_representative = cluster_id in self.cluster_rep
                    self.seed_to_cluster[seed_id] = cluster_id
                    self.cluster_rep.setdefault(cluster_id, seed_id)
                    representative_id = self.cluster_rep.get(cluster_id)
                    if (
                        had_representative
                        and representative_id is not None
                        and representative_id != seed_id
                    ):
                        representative = self.manager.seeds.get(representative_id)
                        if representative is not None:
                            refresh_cluster_representative(self.manager, representative, seed)
                else:
                    cluster_id = self.seed_to_cluster[seed_id]
                    self.clusterer.bump(cluster_id)
                    representative = self.manager.seeds.get(
                        self.cluster_rep.get(cluster_id, "")
                    )
                    if representative is not None and representative is not seed:
                        refresh_cluster_representative(self.manager, representative, seed)

            for cluster_id, representative_id in self.cluster_rep.items():
                if representative_id in self.manager.seeds:
                    representative = self.manager.seeds[representative_id]
                    representative.occurrence_count = max(
                        representative.occurrence_count,
                        self.clusterer.recurrence(cluster_id),
                    )

        # 6. Recurrence is a first-class SSL signal: under the exploratory policy
        # it may drive promotion on its own, and only the Validation Gate raises
        # weight. Recurrence is submitted as a recurrence signal, never relabeled
        # as external evidence. Non-representative cluster members remain
        # weightless.
        promoted_now: list[str] = []
        for seed_id, seed in list(self.manager.seeds.items()):
            if seed.status == SeedStatus.EXPIRED:
                continue
            if self.clusterer is not None:
                cluster_id = self.seed_to_cluster.get(seed_id)
                if cluster_id is not None and self.cluster_rep.get(cluster_id) != seed_id:
                    continue
            event = self.manager.submit_signals(
                seed_id,
                [recurrence_signal(seed.occurrence_count, threshold=2)],
                policy_id="exploratory",
            )
            if event.decision is GateDecision.PROMOTED and seed.status == SeedStatus.PROMOTED:
                promoted_now.append(seed_id)

        # 7. The baseline is the stable conversation history. SSL remains a
        # sidecar that may improve the visible answer without feeding itself.
        self.history.append((question, baseline_answer))
        self._turn += 1

        report = {
            "turn": turn,
            "question": question,
            "answer": final_answer,
            "baseline_answer": baseline_answer,
            "ssl_answer": ssl_answer,
            "surfaced_seeds": surfaced,
            "surfaced_seed_ids": [seed_id for _sim, seed_id, _text in allowed],
            "selected_seed_ids": [seed_id for _sim, seed_id, _text in selected],
            "influence_decisions": (
                [record.__dict__.copy() for record in self.influence_records[-len(selected):]]
                if selected
                else []
            ),
            "seeds_born_weightless": born,
            "prompt_boundary_markers": apply_prompt_boundary(surfaced)[1] if surfaced else [],
            "promoted_this_turn": promoted_now,
            "reactivated_trtl": reactivated,
            "shadow_size": len(self.manager.seeds),
            "retrieval_probe": self._run_retrieval_probe(question),
        }
        self.turn_reports.append(report)
        return report

    # -- user-driven falsification (the dialectic, made operable) -------------

    def falsify(self, seed_id: str) -> dict[str, Any]:
        """User contradicts a seed: weight drops, trace decays, contract blocks it."""
        if seed_id not in self.manager.seeds:
            raise KeyError(f"Unknown seed id: {seed_id}")
        self.manager.run_validation_gate(seed_id, contradiction=True)
        seed = self.manager.seeds[seed_id]
        blocked = not self.contract.can_influence(
            seed, InfluenceAction.ANSWER_MODIFICATION, self.manager.validation_log
        )
        return {
            "seed_id": seed_id,
            "weight_after": seed.weight,
            "status_after": seed.status.value,
            "blocked_from_influence": blocked,
        }

    # -- introspection ---------------------------------------------------------

    def shadow_report(self) -> dict[str, Any]:
        seeds = []
        for sid, seed in self.manager.seeds.items():
            seeds.append(
                {
                    "id": sid,
                    "text": seed.text,
                    "weight": seed.weight,
                    "trace": round(seed.trace, 3),
                    "status": seed.status.value,
                    "occurrence_count": seed.occurrence_count,
                    "born_turn": self.born_turn.get(sid),
                }
            )
        return {
            "turns": self._turn,
            "seeds": seeds,
            "influence_records": [asdict(r) for r in self.influence_records],
        }

    def transcript(self) -> dict[str, Any]:
        return {
            "artifact": "shadow_chat_transcript",
            "doctrine": (
                "seeds born weightless; influence only via Gate promotion, re-checked "
                "by AgentSafetyContract at use time; potential-not-must surfacing "
                "(top_k cap); user-driven falsification; audited influence trail."
            ),
            "turn_reports": self.turn_reports,
            "shadow": self.shadow_report(),
        }


def run_chat(
    *,
    backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 700,
    embedding_backend: str = "lexical",
    embedding_model: str | None = None,
    surface_threshold: float = 0.30,
    surface_top_k: int = 2,
    early_turn_margin: float = 0.10,
    early_turn_history: int = 5,
    resurface_margin: float = 0.15,
    recurrence_mode: str = "cluster",
    script_path: str | None = None,
    transcript_path: str | None = None,
    show_shadow: bool = False,
    probe_corpus: str | None = None,
    probe_top_k: int = 3,
) -> Path | None:
    """CLI entrypoint: interactive REPL, or scripted turns via --script."""
    session = ShadowChatSession(
        backend=backend,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
        embedding_backend=embedding_backend,
        embedding_model=embedding_model,
        surface_threshold=surface_threshold,
        surface_top_k=surface_top_k,
        early_turn_margin=early_turn_margin,
        early_turn_history=early_turn_history,
        resurface_margin=resurface_margin,
        recurrence_mode=recurrence_mode,
        probe_corpus=probe_corpus,
        probe_top_k=probe_top_k,
    )

    def _emit(report: dict[str, Any]) -> None:
        print(f"\n[answer]\n{report['answer']}\n")
        if report["surfaced_seeds"]:
            print("[shadow -> answer] validated perspectives supplied:")
            for s in report["surfaced_seeds"]:
                print(f"  • {s}")
        if show_shadow:
            print(
                f"[shadow] seeds: {report['shadow_size']} | born (weightless): "
                f"{len(report['seeds_born_weightless'])} | promotions: "
                f"{len(report['promoted_this_turn'])} | TrTL reactivations: "
                f"{len(report['reactivated_trtl'])}"
            )
        probe = report.get("retrieval_probe")
        if probe and probe["seed_only_chunk_ids"]:
            print(
                "[probe] seed retrieves what the question does not (presence, not steering): "
                + ", ".join(probe["seed_only_chunk_ids"])
            )

    if script_path:
        lines = [
            line.strip()
            for line in Path(script_path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        for line in lines:
            print(f"\n>>> {line}")
            _emit(session.turn(line))
    else:  # pragma: no cover - interactive path
        print(
            "shadowseed chat - live shadow layer. Commands: /shadow, /audit, "
            "/falsify <seed_id>, /quit"
        )
        while True:
            try:
                line = input("\nquestion> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                continue
            if line in {"/quit", "/exit"}:
                break
            if line == "/shadow":
                print(json.dumps(session.shadow_report(), indent=2, ensure_ascii=False))
                continue
            if line == "/audit":
                count = session.audit()
                print(f"audit OK: {count} influence decisions replayed; no weightless influence.")
                continue
            if line.startswith("/falsify "):
                try:
                    print(json.dumps(session.falsify(line.split(None, 1)[1]), indent=2))
                except KeyError as exc:
                    print(str(exc))
                continue
            _emit(session.turn(line))

    session.audit()  # hard doctrine check before the transcript is written
    if transcript_path:
        out = Path(transcript_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(session.transcript(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\ntranscript (including audit trail) -> {out}")
        return out
    return None
