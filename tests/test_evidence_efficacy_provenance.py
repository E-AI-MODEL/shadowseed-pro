from __future__ import annotations

import pytest

from shadowseed.benchmark.evidence_efficacy import _validate_model_provenance


def test_hf_and_sentence_transformer_revisions_are_required() -> None:
    with pytest.raises(ValueError, match="hf-transformers efficacy runs require"):
        _validate_model_provenance(
            backend="hf-transformers",
            model_id="org/model",
            model_revision=None,
            model_digest=None,
            embedding_backend="sentence-transformers",
            embedding_model="org/embedder",
            embedding_revision="embed-sha",
        )

    with pytest.raises(ValueError, match="embedding-revision"):
        _validate_model_provenance(
            backend="fixture",
            model_id="fixture",
            model_revision=None,
            model_digest=None,
            embedding_backend="sentence-transformers",
            embedding_model="org/embedder",
            embedding_revision=None,
        )


def test_openai_snapshot_record_must_equal_applied_model_id() -> None:
    with pytest.raises(ValueError, match="must equal --model-id"):
        _validate_model_provenance(
            backend="openai",
            model_id="gpt-example-snapshot-a",
            model_revision="gpt-example-snapshot-b",
            model_digest=None,
            embedding_backend="lexical",
            embedding_model=None,
            embedding_revision=None,
        )


def test_non_sentence_embedding_revision_is_rejected() -> None:
    with pytest.raises(ValueError, match="only supported for sentence-transformers"):
        _validate_model_provenance(
            backend="fixture",
            model_id="fixture",
            model_revision=None,
            model_digest=None,
            embedding_backend="lexical",
            embedding_model=None,
            embedding_revision="not-applicable",
        )
