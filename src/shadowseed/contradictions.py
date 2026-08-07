"""Contradiction record collection, state derivation, and lifecycle workflows.

The record contract itself remains in :mod:`shadowseed.gate.contradictions`.
This module owns the mutable collection, identifier sequence, blocking-state
derivation, formal resolution, migration, and persistence helpers. The core
manager exposes compatibility facade methods and retains authority/Gate
orchestration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from shadowseed.gate.contradictions import ContradictionRecord, ContradictionStatus
from shadowseed.gate.events import ContradictionState
from shadowseed.models import ShadowSeed


class ContradictionDomain:
    """Canonical mutable state and workflows for seed contradictions."""

    def __init__(
        self,
        records: Iterable[ContradictionRecord] | None = None,
        *,
        sequence: int = 0,
    ) -> None:
        self.records: list[ContradictionRecord] = list(records or ())
        self._sequence = max(0, int(sequence))
        self._sync_sequence()

    @property
    def sequence(self) -> int:
        return self._sequence

    @sequence.setter
    def sequence(self, value: int) -> None:
        self._sequence = max(0, int(value))

    @staticmethod
    def _sequence_from_id(contradiction_id: str) -> int | None:
        try:
            return int(contradiction_id.rsplit("::", 1)[1])
        except (IndexError, ValueError):
            return None

    def _sync_sequence(self) -> None:
        known = (
            value
            for record in self.records
            if (value := self._sequence_from_id(record.contradiction_id)) is not None
        )
        self._sequence = max((self._sequence, *known))

    def replace_records(self, records: Iterable[ContradictionRecord]) -> None:
        """Install ``records`` as the canonical collection.

        A list is adopted as-is rather than copied, because the historical
        public attribute ``SSLManager.contradiction_records`` *was* the caller's
        list: code that assigned a list and then appended to its own reference
        expected those records to be visible to blocking queries and export.
        Copying would silently drop such appends, so only non-list iterables are
        materialized.
        """

        self.records = records if isinstance(records, list) else list(records)
        self._sync_sequence()

    def contradictions_for(self, seed_id: str) -> list[ContradictionRecord]:
        """Return all records for ``seed_id`` in creation order."""

        return [record for record in self.records if record.seed_id == seed_id]

    def open_for(self, seed_id: str) -> list[ContradictionRecord]:
        """Return unresolved records that currently block ``seed_id``."""

        return [
            record
            for record in self.records
            if record.seed_id == seed_id and record.is_blocking
        ]

    def state_for(self, seed: ShadowSeed) -> ContradictionState:
        """Derive canonical blocking state, including the legacy scalar fallback."""

        records = self.contradictions_for(seed.id)
        if records:
            open_count = sum(1 for record in records if record.is_blocking)
            return ContradictionState(
                blocking=open_count > 0,
                open_count=open_count,
                score=seed.contradiction_score,
            )
        legacy_blocking = seed.contradiction_score > 0.0
        return ContradictionState(
            blocking=legacy_blocking,
            open_count=1 if legacy_blocking else 0,
            score=seed.contradiction_score,
        )

    def open(
        self,
        seed: ShadowSeed,
        *,
        reason: str,
        source_ref: str | None,
        strength: float,
        created_at: str,
    ) -> ContradictionRecord:
        """Create and append one open contradiction record."""

        self._sequence += 1
        record = ContradictionRecord(
            contradiction_id=f"contra::{seed.id}::{self._sequence:06d}",
            seed_id=seed.id,
            reason=reason,
            source_ref=source_ref,
            strength=max(0.0, min(1.0, strength)),
            lifecycle_state=ContradictionStatus.OPEN,
            created_at=created_at,
        )
        self.records.append(record)
        return record

    def resolve(
        self,
        seed_id: str,
        *,
        basis: str,
        contradiction_id: str | None = None,
        superseded: bool = False,
        withdrawn: bool = False,
        resolved_at: Callable[[], str],
        open_records: Iterable[ContradictionRecord] | None = None,
    ) -> list[ContradictionRecord]:
        """Formally close selected open records and return the changed records."""

        selected = list(
            self.open_for(seed_id) if open_records is None else open_records
        )
        if contradiction_id is not None:
            selected = [
                record
                for record in selected
                if record.contradiction_id == contradiction_id
            ]
        if not selected:
            raise ValueError(f"no open contradiction to resolve for seed '{seed_id}'")
        for record in selected:
            record.resolve(
                basis,
                superseded=superseded,
                withdrawn=withdrawn,
                resolved_at=resolved_at(),
            )
        return selected

    def migrate_legacy(
        self,
        seeds: Iterable[ShadowSeed],
        *,
        open_record: Callable[..., ContradictionRecord],
    ) -> list[ContradictionRecord]:
        """Create records for positive legacy scalars that lack records.

        The manager supplies its historical ``_open_contradiction_record``
        facade so the extraction preserves the existing call path without
        introducing alternate migration or restore APIs.
        """

        created: list[ContradictionRecord] = []
        for seed in seeds:
            if seed.contradiction_score <= 0.0 or self.contradictions_for(seed.id):
                continue
            created.append(
                open_record(
                    seed,
                    reason="migrated from legacy contradiction_score",
                    source_ref="legacy_migration",
                    strength=min(1.0, seed.contradiction_score),
                )
            )
        return created


__all__ = [
    "ContradictionDomain",
    "ContradictionRecord",
    "ContradictionStatus",
]
