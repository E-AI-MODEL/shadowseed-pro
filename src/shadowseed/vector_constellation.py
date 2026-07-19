"""Hybrid vector constellation for weightless Shadow Seeds.

The constellation indexes seeds in vector space and keeps a feedback log. It is
not the source of truth for SSL state. SSLManager.seeds remains authoritative.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from shadowseed.manager import ShadowSeed
from shadowseed.vectorstore.base import VectorStore


@dataclass
class FeedbackEvent:
    seed_id: str
    feedback: str
    is_correction: bool
    similarity: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VectorConstellation:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.feedback_log: list[FeedbackEvent] = []

    def metadata_from_seed(self, seed: ShadowSeed) -> dict[str, Any]:
        return {
            "text": seed.text,
            "weight": seed.weight,
            "trace": seed.trace,
            "status": seed.status.value,
            "occurrence_count": seed.occurrence_count,
            "evidence_count": seed.evidence_count,
            "trigger_keywords": list(seed.trigger_keywords),
            "created_at": seed.created_at,
            "updated_at": seed.updated_at,
        }

    def add_seed(self, seed: ShadowSeed) -> None:
        self.store.add(seed.id, seed.embedding, self.metadata_from_seed(seed))

    def sync_seed(self, seed: ShadowSeed) -> None:
        if seed.id in self.store.get_all_ids():
            self.store.update_metadata(seed.id, self.metadata_from_seed(seed))
        else:
            self.add_seed(seed)

    def search_similar_seeds(
        self,
        query_embedding: np.ndarray,
        threshold: float = 0.8,
        top_k: int = 5,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        results = self.store.search(query_embedding, top_k=top_k)
        return [item for item in results if item[1] >= threshold]

    def record_feedback(
        self,
        seed_id: str,
        feedback: str,
        is_correction: bool,
        similarity: float,
    ) -> None:
        self.feedback_log.append(
            FeedbackEvent(
                seed_id=seed_id,
                feedback=feedback,
                is_correction=is_correction,
                similarity=similarity,
            )
        )

    def housekeeping(self, max_age_days: int = 30) -> list[str]:
        threshold_date = datetime.now() - timedelta(days=max_age_days)
        deleted: list[str] = []
        for seed_id in self.store.get_all_ids():
            metadata = self.store.get_metadata(seed_id)
            try:
                created_at = datetime.fromisoformat(str(metadata.get("created_at")))
            except ValueError:
                continue
            is_old_open_seed = (
                metadata.get("status") in {"NEW", "ACTIVE", "DORMANT"}
                and float(metadata.get("weight", 0.0)) == 0.0
                and int(metadata.get("evidence_count", 0)) == 0
                and created_at < threshold_date
            )
            if is_old_open_seed:
                self.store.delete(seed_id)
                deleted.append(seed_id)
        return deleted

    def to_dict(self) -> dict[str, Any]:
        return {
            "ids": self.store.get_all_ids(),
            "feedback_log": [item.to_dict() for item in self.feedback_log],
        }
