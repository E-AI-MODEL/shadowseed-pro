"""Append-only candidate-observation records for Shadow Seed Learning.

Observations are audit data, never authority. Recording a detector candidate here
must not change seed trace, occurrence count, evidence, Gate state, or weight.
SSL-exposed candidates are retained for audit but are never recurrence-eligible.
A later clean observation may be linked to an earlier contaminated observation
by appending a separate link record; the original observation stays immutable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable


OBSERVATION_SCHEMA_VERSION = 1


def normalize_observation_text(text: str) -> str:
    """Return a conservative comparison form without inventing semantics."""

    return " ".join(str(text).strip().lower().split())


@dataclass(frozen=True)
class CandidateObservation:
    observation_id: str
    raw_text: str
    normalized_text: str
    context_ref: str
    detector_backend: str
    detector_prompt_provenance: str | None
    candidate_type: str
    ssl_exposed: bool
    surfaced_seed_ids: tuple[str, ...]
    recurrence_eligible: bool
    created_at: str
    legacy_projection: bool = False
    schema_version: int = OBSERVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["surfaced_seed_ids"] = list(self.surfaced_seed_ids)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CandidateObservation":
        return cls(
            observation_id=str(payload["observation_id"]),
            raw_text=str(payload["raw_text"]),
            normalized_text=str(payload.get("normalized_text") or normalize_observation_text(payload["raw_text"])),
            context_ref=str(payload["context_ref"]),
            detector_backend=str(payload.get("detector_backend", "unknown")),
            detector_prompt_provenance=(
                None
                if payload.get("detector_prompt_provenance") is None
                else str(payload["detector_prompt_provenance"])
            ),
            candidate_type=str(payload.get("candidate_type", "possible_completion")),
            ssl_exposed=bool(payload.get("ssl_exposed", False)),
            surfaced_seed_ids=tuple(str(item) for item in payload.get("surfaced_seed_ids", [])),
            recurrence_eligible=bool(payload.get("recurrence_eligible", False)),
            created_at=str(payload.get("created_at", "")),
            legacy_projection=bool(payload.get("legacy_projection", False)),
            schema_version=int(payload.get("schema_version", OBSERVATION_SCHEMA_VERSION)),
        )


@dataclass(frozen=True)
class ObservationLink:
    link_id: str
    contaminated_observation_id: str
    clean_observation_id: str
    link_type: str = "later_clean_exact_match"
    schema_version: int = OBSERVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ObservationLink":
        return cls(
            link_id=str(payload["link_id"]),
            contaminated_observation_id=str(payload["contaminated_observation_id"]),
            clean_observation_id=str(payload["clean_observation_id"]),
            link_type=str(payload.get("link_type", "later_clean_exact_match")),
            schema_version=int(payload.get("schema_version", OBSERVATION_SCHEMA_VERSION)),
        )


class CandidateObservationLedger:
    """In-memory append-only ledger with deterministic record identities."""

    def __init__(
        self,
        observations: Iterable[CandidateObservation] | None = None,
        links: Iterable[ObservationLink] | None = None,
    ) -> None:
        self._observations: list[CandidateObservation] = list(observations or ())
        self._links: list[ObservationLink] = list(links or ())
        self._observation_ids = {item.observation_id for item in self._observations}
        self._link_ids = {item.link_id for item in self._links}

    @property
    def observations(self) -> tuple[CandidateObservation, ...]:
        return tuple(self._observations)

    @property
    def links(self) -> tuple[ObservationLink, ...]:
        return tuple(self._links)

    @staticmethod
    def _observation_id(context_ref: str, index: int, raw_text: str) -> str:
        digest = sha256(
            f"candidate-observation-v1\0{context_ref}\0{index}\0{raw_text}".encode("utf-8")
        ).hexdigest()
        return f"obs_{digest[:24]}"

    @staticmethod
    def _link_id(contaminated_id: str, clean_id: str) -> str:
        digest = sha256(
            f"candidate-observation-link-v1\0{contaminated_id}\0{clean_id}".encode("utf-8")
        ).hexdigest()
        return f"obslink_{digest[:24]}"

    def record_batch(
        self,
        candidates: Iterable[str],
        *,
        context_ref: str,
        detector_backend: str,
        detector_prompt_provenance: str | None,
        candidate_type: str,
        ssl_exposed: bool,
        surfaced_seed_ids: Iterable[str] = (),
        created_at: str,
        legacy_projection: bool = False,
    ) -> list[CandidateObservation]:
        """Append detector observations and return the records for this batch.

        `ssl_exposed=True` always forces `recurrence_eligible=False`. Clean
        observations are recurrence-eligible, but this ledger itself never
        increments recurrence or calls the Gate.
        """

        surfaced = tuple(str(item) for item in surfaced_seed_ids)
        created: list[CandidateObservation] = []
        for index, candidate in enumerate(candidates):
            raw_text = str(candidate).strip()
            if not raw_text:
                continue
            observation = CandidateObservation(
                observation_id=self._observation_id(context_ref, index, raw_text),
                raw_text=raw_text,
                normalized_text=normalize_observation_text(raw_text),
                context_ref=context_ref,
                detector_backend=detector_backend,
                detector_prompt_provenance=detector_prompt_provenance,
                candidate_type=candidate_type,
                ssl_exposed=ssl_exposed,
                surfaced_seed_ids=surfaced,
                recurrence_eligible=not ssl_exposed,
                created_at=created_at,
                legacy_projection=legacy_projection,
            )
            if observation.observation_id in self._observation_ids:
                continue
            self._observations.append(observation)
            self._observation_ids.add(observation.observation_id)
            created.append(observation)
            if not observation.ssl_exposed:
                self._link_prior_contaminated_exact_matches(observation)
        return created

    def _link_prior_contaminated_exact_matches(
        self, clean_observation: CandidateObservation
    ) -> None:
        """Append exact-match recovery links without mutating old records."""

        for previous in self._observations:
            if previous.observation_id == clean_observation.observation_id:
                continue
            if not previous.ssl_exposed:
                continue
            if previous.normalized_text != clean_observation.normalized_text:
                continue
            link = ObservationLink(
                link_id=self._link_id(previous.observation_id, clean_observation.observation_id),
                contaminated_observation_id=previous.observation_id,
                clean_observation_id=clean_observation.observation_id,
            )
            if link.link_id in self._link_ids:
                continue
            self._links.append(link)
            self._link_ids.add(link.link_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "observations": [item.to_dict() for item in self._observations],
            "links": [item.to_dict() for item in self._links],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "CandidateObservationLedger":
        if not payload:
            return cls()
        schema_version = int(payload.get("schema_version", OBSERVATION_SCHEMA_VERSION))
        if schema_version != OBSERVATION_SCHEMA_VERSION:
            raise ValueError("unsupported candidate-observation ledger schema")
        return cls(
            observations=(
                CandidateObservation.from_dict(item)
                for item in payload.get("observations", [])
            ),
            links=(ObservationLink.from_dict(item) for item in payload.get("links", [])),
        )

    @classmethod
    def project_legacy_turn_reports(
        cls,
        turn_reports: Iterable[dict[str, Any]],
        *,
        detector_backend: str = "legacy-turn-report",
    ) -> "CandidateObservationLedger":
        """Project old suppressed-candidate reports without granting recurrence.

        Historical reports are not rewritten. The projection is explicit and
        marks each generated observation as legacy provenance.
        """

        ledger = cls()
        for report in turn_reports:
            turn = report.get("turn", "unknown")
            suppressed = report.get("suppressed_self_attributed_candidates", [])
            if not suppressed:
                continue
            ledger.record_batch(
                suppressed,
                context_ref=f"turn:{turn}:legacy_suppressed_candidate",
                detector_backend=detector_backend,
                detector_prompt_provenance=None,
                candidate_type="possible_completion",
                ssl_exposed=True,
                surfaced_seed_ids=report.get("surfaced_seed_ids", []),
                created_at="",
                legacy_projection=True,
            )
        return ledger
