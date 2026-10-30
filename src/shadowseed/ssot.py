"""Single Source of Truth manager for SSL 4.5.

The SSOT manager indexes documents in a separate vectorstore. It can inspect
open weightless seeds and retain operator-asserted source/seed relationships
without granting authority. An authorized product service may separately
submit evidence. The SSOT store
is separate from the seed vectorstore:

- seed vectorstore: uncertain regions and shadow seeds;
- SSOT vectorstore: trusted document chunks supplied by the user or a pipeline.

SSLManager.seeds remains the source of truth for trace, weight, status and
Validation Gate decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any
import re

from shadowseed.gate.signals import SignalDirection, SignalKind
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.vectorstore.base import VectorStore


def _text_digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


class SSOTRelation(str, Enum):
    """Operator-asserted relationship; never inferred from retrieval similarity."""

    SUPPORTS = "supports"
    OPPOSES = "opposes"
    TOPICAL = "topical"
    UNDETERMINED = "undetermined"
    NOT_TESTABLE = "not_testable"


@dataclass(frozen=True)
class SSOTRelationReview:
    """Exact seed/document-version review; verifier identity is caller-asserted."""

    seed_id: str
    seed_digest: str
    doc_id: str
    document_digest: str
    relation: SSOTRelation
    evidence_unit_id: str
    reviewer: str
    rationale: str
    reviewed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "relation": self.relation.value}


@dataclass
class SSOTDocument:
    doc_id: str
    source: str
    trust_level: str = "user_verified"
    content_digest: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SSOTManager:
    def __init__(self, vector_store: VectorStore, ssl_manager: SSLManager):
        self.store = vector_store
        self.ssl = ssl_manager
        self.documents: dict[str, SSOTDocument] = {}
        # An operator-asserted relationship is separate from source trust and
        # never inferred from an embedding hit. Rehydrate only after review.
        self.relation_reviews: dict[tuple[str, str], SSOTRelationReview] = {}

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return []
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]

    @staticmethod
    def sentence_chunks(text: str, max_words: int = 80, overlap_sentences: int = 1) -> list[str]:
        """Split text into sentence-aware chunks without adding NLP dependencies."""
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_words = 0

        for paragraph in paragraphs or [text]:
            for sentence in SSOTManager.split_sentences(paragraph):
                sentence_words = len(re.findall(r"\S+", sentence))
                if current and current_words + sentence_words > max_words:
                    chunks.append(" ".join(current).strip())
                    current = current[-overlap_sentences:] if overlap_sentences > 0 else []
                    current_words = sum(len(re.findall(r"\S+", item)) for item in current)
                current.append(sentence)
                current_words += sentence_words

        if current:
            chunks.append(" ".join(current).strip())
        return chunks

    @staticmethod
    def chunk_text(text: str, max_words: int = 80) -> list[str]:
        """Split trusted text into coherent searchable chunks."""
        chunks = SSOTManager.sentence_chunks(text, max_words=max_words)
        if chunks:
            return chunks
        words = re.findall(r"\S+", text.strip())
        return [" ".join(words[start : start + max_words]).strip() for start in range(0, len(words), max_words)]

    def _add_chunk(
        self,
        chunk_id: str,
        chunk: str,
        doc_id: str,
        chunk_index: int,
        source: str,
        trust_level: str,
        status: str,
        created_at: str,
    ) -> None:
        embedding = self.ssl.get_embedding(chunk)
        self.store.add(
            chunk_id,
            embedding,
            {
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "text": chunk,
                "text_digest": _text_digest(chunk),
                "document_digest": self.documents[doc_id].content_digest,
                "source": source,
                "trust_level": trust_level,
                "status": status,
                "created_at": created_at,
                "verified_at": None,
            },
        )

    def ingest_document(
        self,
        doc_text: str,
        doc_id: str,
        source: str = "user_upload",
        trust_level: str = "user_verified",
        chunk_words: int = 80,
    ) -> list[str]:
        """Index a trusted document in the SSOT vectorstore.

        Returns the inserted chunk ids. The method only stores SSOT facts. Seed
        validation is done explicitly through validate_open_seeds_against_ssot().
        """
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError("doc_id must be a nonempty string")
        # Re-ingesting a document replaces its stale chunks and voids relation
        # attestations, even if the caller accidentally reuses the same ID.
        if doc_id in self.documents:
            for old_id in tuple(self.store.get_all_ids()):
                if self.store.get_metadata(old_id).get("doc_id") == doc_id:
                    self.store.delete(old_id)
            self.relation_reviews = {
                key: review for key, review in self.relation_reviews.items()
                if key[1] != doc_id
            }
        document = SSOTDocument(
            doc_id=doc_id,
            source=source,
            trust_level=trust_level,
            content_digest=_text_digest(doc_text),
        )
        self.documents[doc_id] = document
        status = "verified" if trust_level == "user_verified" else "proposed"
        chunk_ids: list[str] = []
        for index, chunk in enumerate(self.chunk_text(doc_text, max_words=chunk_words), start=1):
            chunk_id = f"{doc_id}::chunk_{index:03d}"
            self._add_chunk(
                chunk_id,
                chunk,
                doc_id=doc_id,
                chunk_index=index,
                source=source,
                trust_level=trust_level,
                status=status,
                created_at=document.created_at,
            )
            chunk_ids.append(chunk_id)
        return chunk_ids

    def ingest_from_llm_output(
        self,
        llm_output: str,
        doc_id: str,
        source: str = "llm_output",
        chunk_words: int = 40,
    ) -> list[str]:
        """Store LLM factual claims as unverified SSOT proposals.

        These chunks are searchable, but validate_open_seeds_against_ssot ignores
        them until verify_chunk() marks them as trusted.
        """
        return self.ingest_document(
            llm_output,
            doc_id=doc_id,
            source=source,
            trust_level="llm_proposed",
            chunk_words=chunk_words,
        )

    def verify_chunk(self, chunk_id: str, verifier: str = "human") -> None:
        metadata = self.store.get_metadata(chunk_id)
        metadata.update(
            {
                "trust_level": "user_verified",
                "status": "verified",
                "verified_by": verifier,
                "verified_at": datetime.now().isoformat(),
            }
        )
        self.store.update_metadata(chunk_id, metadata)

    def reject_chunk(self, chunk_id: str, verifier: str = "human") -> None:
        metadata = self.store.get_metadata(chunk_id)
        metadata.update(
            {
                "status": "rejected",
                "verified_by": verifier,
                "verified_at": datetime.now().isoformat(),
            }
        )
        self.store.update_metadata(chunk_id, metadata)

    def search(self, query_text: str, top_k: int = 5) -> list[tuple[str, float, dict[str, Any]]]:
        query_embedding = self.ssl.get_embedding(query_text)
        return self.store.search(query_embedding, top_k=top_k)

    def retrieve_context(self, query_text: str, top_k: int = 3, threshold: float = 0.20) -> list[dict[str, Any]]:
        hits = self.search(query_text, top_k=top_k)
        return [
            {"chunk_id": chunk_id, "similarity": score, "metadata": metadata}
            for chunk_id, score, metadata in hits
            if score >= threshold and metadata.get("status") == "verified"
        ]

    def attest_document_relation(
        self,
        seed_id: str,
        doc_id: str,
        *,
        relation: SSOTRelation | str,
        reviewer: str,
        rationale: str,
        evidence_unit_id: str | None = None,
    ) -> SSOTRelationReview:
        """Record an explicit *operator claim* about a specific seed and document.

        The caller MUST be a trusted, authenticated operator. This method cannot
        authenticate the person, verify source truth or establish independence.
        It does not call the Gate. A model's output is not a legitimate reviewer.
        The full document must be examined, including possible contrary passages.
        """
        if seed_id not in self.ssl.seeds:
            raise KeyError(f"Unknown seed: {seed_id}")
        if doc_id not in self.documents:
            raise KeyError(f"Unknown SSOT document: {doc_id}")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("reviewer must be nonempty")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("rationale must be nonempty")
        unit = doc_id if evidence_unit_id is None else evidence_unit_id
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("evidence_unit_id must be nonempty")
        decision = SSOTRelation(relation)
        seed = self.ssl.get_seed(seed_id)
        review = SSOTRelationReview(
            seed_id=seed_id,
            seed_digest=_text_digest(seed.text),
            doc_id=doc_id,
            document_digest=self.documents[doc_id].content_digest,
            relation=decision,
            evidence_unit_id=unit.strip(),
            reviewer=reviewer.strip(),
            rationale=rationale.strip(),
            reviewed_at=datetime.now(timezone.utc).isoformat(),
        )
        self.relation_reviews[(seed_id, doc_id)] = review
        return review

    def _all_document_chunks_verified(self, doc_id: str) -> bool:
        """Require trusted status AND unchanged text of every indexed chunk.

        Unknown older metadata is rejected until the source is re-ingested and
        reviewed. A digest is an integrity check, not an authenticity proof.
        """
        document = self.documents.get(doc_id)
        if document is None:
            return False
        chunks = [
            metadata
            for chunk_id in self.store.get_all_ids()
            if (metadata := self.store.get_metadata(chunk_id)).get("doc_id") == doc_id
        ]
        return bool(chunks) and all(
            metadata.get("status") == "verified"
            and metadata.get("document_digest") == document.content_digest
            and isinstance(metadata.get("text"), str)
            and metadata.get("text_digest") == _text_digest(metadata["text"])
            for metadata in chunks
        )

    def _has_unaudited_legacy_ssot_evidence(self, seed_id: str) -> bool:
        """Do not silently recertify historical similarity-only Gate support."""
        return any(
            event.seed_id == seed_id
            and any(
                signal.kind is SignalKind.SSOT
                and signal.direction is SignalDirection.SUPPORT
                and not (signal.reason or "").startswith("relation-attested:ssot:")
                for signal in event.signals
            )
            for event in self.ssl.gate_events
        )

    def validate_open_seeds_against_ssot(
        self,
        threshold: float = 0.20,
        top_k: int = 3,
        max_evidence_per_seed: int = 2,
    ) -> list[dict[str, Any]]:
        """READ ONLY: inspect explicit source relations for weightless seeds.

        Kept under the old method name for callers inspecting search results;
        this no longer performs any Gate operation. A reviewer string and
        source-status metadata cannot prove authorization or source truth.
        The product's authorized evidence.verify service is the only supported
        handoff to authority, with atomic workspace persistence. Opposing and
        unresolved observations remain searchable, never auto-contradicted.
        """
        validations: list[dict[str, Any]] = []
        for seed_id, seed in self.ssl.seeds.items():
            if seed.status in {SeedStatus.PROMOTED, SeedStatus.EXPIRED}:
                continue
            if seed.weight != 0.0:
                continue
            if self._has_unaudited_legacy_ssot_evidence(seed_id):
                # Old immutable Gate events need an explicit audit/migration;
                # a new source_ref must not double-count pre-fix support.
                continue
            hits = self.store.search(seed.embedding, top_k=top_k)
            # Opposing or mixed declared relations for one asserted source
            # unit are not resolved by majority vote or a similarity score.
            declared: dict[str, set[SSOTRelation]] = {}
            for (review_seed_id, review_doc_id), review in self.relation_reviews.items():
                if review_seed_id != seed_id:
                    continue
                current_doc = self.documents.get(review_doc_id)
                if (
                    current_doc is None
                    or review.seed_digest != _text_digest(seed.text)
                    or review.document_digest != current_doc.content_digest
                ):
                    continue
                declared.setdefault(review.evidence_unit_id, set()).add(review.relation)
            conflicting_units = {
                unit for unit, relations in declared.items() if len(relations) > 1
            }

            candidates: dict[str, tuple[str, float, dict[str, Any], SSOTRelationReview]] = {}
            for chunk_id, score, metadata in hits:
                if score < threshold or metadata.get("status") != "verified":
                    continue
                doc_id = metadata.get("doc_id")
                review = self.relation_reviews.get((seed_id, doc_id))
                current_doc = self.documents.get(doc_id)
                if review is None or current_doc is None:
                    continue
                if (
                    review.relation is not SSOTRelation.SUPPORTS
                    or review.seed_digest != _text_digest(seed.text)
                    or review.document_digest != current_doc.content_digest
                    or review.evidence_unit_id in conflicting_units
                    or not self._all_document_chunks_verified(doc_id)
                ):
                    continue
                candidates.setdefault(
                    review.evidence_unit_id, (chunk_id, score, metadata, review)
                )

            # This is a READ-ONLY handoff. A caller-written reviewer string,
            # source status or relationship label cannot authenticate an actor,
            # authorize a Gate event, or persist an atomic production ledger.
            # The existing Workbench evidence.verify path handles the separate
            # operator decision. A source identity must be preserved there.
            review_candidates = [
                {
                    "chunk_id": chunk_id,
                    "similarity": score,
                    "doc_id": metadata.get("doc_id"),
                    "source": metadata.get("source"),
                    "evidence_unit_id": unit,
                    "relation_review": review.to_dict(),
                    "gate_authorized": False,
                    "requires_authorized_submission": True,
                }
                for unit, (chunk_id, score, metadata, review) in list(candidates.items())[
                    :max_evidence_per_seed
                ]
            ]
            if review_candidates:
                validations.append(
                    {
                        "seed_id": seed_id,
                        "seed_text": seed.text,
                        "review_candidates": review_candidates,
                        "gate_authorized": False,
                        "seed_after_inspection": self.ssl.get_seed(seed_id).to_dict(),
                    }
                )
        return validations

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": [document.to_dict() for document in self.documents.values()],
            "chunk_ids": self.store.get_all_ids(),
            # Export for inspection, not automatic trust restoration on reload.
            "relation_reviews": [
                review.to_dict() for review in self.relation_reviews.values()
            ],
        }
