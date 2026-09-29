from __future__ import annotations

from pathlib import Path

import pytest

import shadowseed.application.ingest as ingest_module
from shadowseed.application.ingest import chunk_text, prepare_sources, read_source_file
from shadowseed.workbench.controller import WorkbenchController


def test_chunk_text_preserves_source_provenance() -> None:
    text = ("Alpha explains one perspective.\n\n" * 120).strip()
    chunks = chunk_text(text, source_name="notes.md", max_chars=800, overlap_chars=100)

    assert len(chunks) > 1
    assert chunks[0].source_name == "notes.md"
    assert chunks[0].context_ref.startswith("source:notes.md:instance:")
    assert chunks[0].context_ref.endswith(":chunk:00000")
    assert all(chunk.text.strip() for chunk in chunks)


def test_prepare_sources_supports_paste_and_markdown(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Research\n\nBeta introduces another frame.", encoding="utf-8")

    chunks = prepare_sources(
        pasted_text="Gamma appears in pasted material.",
        file_paths=[source],
    )

    assert {chunk.source_name for chunk in chunks} == {"pasted-text", "source.md"}


def test_json_upload_extracts_string_content(tmp_path: Path) -> None:
    source = tmp_path / "corpus.json"
    source.write_text(
        '{"title":"Delta study","items":[{"text":"Epsilon finding"}]}',
        encoding="utf-8",
    )

    name, text = read_source_file(source)

    assert name == "corpus.json"
    assert "Delta study" in text
    assert "Epsilon finding" in text


def test_source_ingest_builds_shadow_memory_without_chat_turns(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Corpus",
        profile_id="demo",
        authority_profile_id="strict",
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
    )

    result = controller.ingest_sources(
        session_id,
        pasted_text=(
            "Alpha introduces a perspective. Beta adds context. "
            "Gamma exposes another assumption."
        ),
    )

    assert result["chunks"] == 1
    assert result["new_seed_count"] > 0
    assert result["session"]["turn"] == 0
    assert result["session"]["turn_reports"] == []
    assert result["session"]["seeds"]



def test_read_source_file_supports_csv_and_rejects_empty_or_unknown(tmp_path: Path) -> None:
    csv_source = tmp_path / "rows.csv"
    csv_source.write_text("name,value\nAlpha,one\nBeta,two\n", encoding="utf-8")
    name, text = read_source_file(csv_source)
    assert name == "rows.csv"
    assert "Alpha | one" in text
    assert "Beta | two" in text

    empty = tmp_path / "empty.txt"
    empty.write_text("   \n", encoding="utf-8")
    try:
        read_source_file(empty)
    except ValueError as exc:
        assert "no usable text" in str(exc)
    else:
        raise AssertionError("empty uploads must be rejected")

    unknown = tmp_path / "notes.pdf"
    unknown.write_text("not actually a PDF", encoding="utf-8")
    try:
        read_source_file(unknown)
    except ValueError as exc:
        assert "unsupported upload type" in str(exc)
    else:
        raise AssertionError("unsupported uploads must be rejected")


def test_chunk_text_validates_input_and_handles_single_chunk() -> None:
    assert chunk_text("   ", source_name="empty.txt") == []

    try:
        chunk_text("Alpha", source_name="tiny.txt", max_chars=100)
    except ValueError as exc:
        assert "at least 500" in str(exc)
    else:
        raise AssertionError("unsafe tiny chunk sizes must be rejected")

    chunks = chunk_text(
        "Alpha. Beta. Gamma.",
        source_name="short.txt",
        max_chars=500,
        overlap_chars=999,
    )
    assert len(chunks) == 1
    assert chunks[0].text == "Alpha. Beta. Gamma."


def test_prepare_sources_requires_real_input() -> None:
    try:
        prepare_sources()
    except ValueError as exc:
        assert "paste text or upload" in str(exc)
    else:
        raise AssertionError("empty source preparation must fail")



def test_prepare_sources_gives_each_submission_unique_context_refs() -> None:
    first = prepare_sources(pasted_text="Repeated source material.")
    second = prepare_sources(pasted_text="Repeated source material.")

    assert first[0].source_name == second[0].source_name == "pasted-text"
    assert first[0].context_ref != second[0].context_ref
    assert ":instance:" in first[0].context_ref
    assert ":chunk:00000" in first[0].context_ref


def test_same_named_files_get_distinct_source_instances(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    first_file = left / "notes.md"
    second_file = right / "notes.md"
    first_file.write_text("Alpha perspective.", encoding="utf-8")
    second_file.write_text("Beta perspective.", encoding="utf-8")

    chunks = prepare_sources(file_paths=[first_file, second_file])

    assert [chunk.source_name for chunk in chunks] == ["notes.md", "notes.md"]
    assert chunks[0].context_ref != chunks[1].context_ref


def test_source_ingest_requires_external_provider_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Local seed",
        profile_id="demo",
        backend="fixture",
    )

    stored = controller.sessions.load(session_id)
    hosted = {
        **stored,
        "backend": "openai",
        "model_id": "gpt-test",
        "config": {
            **dict(stored.get("config", {})),
            "runtime_mode": "live",
            "embedding_backend": "sentence-transformers",
            "allow_toy_embedder": False,
        },
    }
    monkeypatch.setattr(controller.sessions, "load", lambda _session_id: hosted)

    called = {"ingest": False}

    def fake_ingest(_session_id: str, _payload: list[dict]) -> dict:
        called["ingest"] = True
        return {
            "sources": 1,
            "source_names": ["pasted-text"],
            "chunks": 1,
            "characters": 5,
            "seeds_before": 0,
            "seeds_after": 0,
            "new_seed_count": 0,
            "promoted_seed_ids": [],
            "authority_review_seed_ids": [],
            "authority_runtime": None,
            "reports": [],
        }

    monkeypatch.setattr(controller.sessions, "ingest_source_chunks", fake_ingest)
    monkeypatch.setattr(controller.inspection, "session_view", lambda _session_id: {})

    with pytest.raises(ValueError, match="external-provider confirmation"):
        controller.ingest_sources(session_id, pasted_text="Alpha")

    assert called["ingest"] is False

    result = controller.ingest_sources(
        session_id,
        pasted_text="Alpha",
        external_confirmed=True,
    )
    assert called["ingest"] is True
    assert result["session"] == {}



def test_repeated_independent_source_submissions_can_recur(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Repeated source",
        profile_id="demo",
        authority_profile_id="autonomous",
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
    )

    context_refs: list[str] = []
    for _ in range(6):
        result = controller.ingest_sources(
            session_id,
            pasted_text="Alpha provides a recurring explanatory perspective.",
        )
        context_refs.extend(
            report["context_ref"]
            for report in result["reports"]
            if report.get("context_ref")
        )

    view = controller.session_view(session_id)
    alpha = next(seed for seed in view["seeds"] if "Alpha" in seed["text"])

    assert len(context_refs) == len(set(context_refs))
    assert alpha["occurrence_count"] >= 3
    assert alpha["status"] == "PROMOTED"



def test_corpus_summary_counts_same_named_files_as_distinct_sources(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    first_file = left / "notes.md"
    second_file = right / "notes.md"
    first_file.write_text("Alpha perspective.", encoding="utf-8")
    second_file.write_text("Beta perspective.", encoding="utf-8")

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Same basename corpus",
        profile_id="demo",
        backend="fixture",
    )
    result = controller.ingest_sources(
        session_id,
        file_paths=[str(first_file), str(second_file)],
    )

    assert result["sources"] == 2
    assert result["source_instance_count"] == 2
    assert result["source_names"] == ["notes.md"]



def test_source_batch_byte_limit_blocks_before_session_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Bounded source batch",
        profile_id="demo",
        backend="fixture",
    )
    monkeypatch.setattr(ingest_module, "MAX_SOURCE_BATCH_BYTES", 16)
    called = {"ingest": False}

    def _unexpected_ingest(*_args, **_kwargs):
        called["ingest"] = True
        raise AssertionError("session inference must not start for an oversized batch")

    monkeypatch.setattr(controller.sessions, "ingest_source_chunks", _unexpected_ingest)

    with pytest.raises(ValueError, match="source batch exceeds"):
        controller.ingest_sources(session_id, pasted_text="x" * 17)

    assert called["ingest"] is False


def test_source_batch_chunk_limit_blocks_before_session_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Bounded chunk batch",
        profile_id="demo",
        backend="fixture",
    )
    monkeypatch.setattr(ingest_module, "MAX_SOURCE_BATCH_CHUNKS", 1)
    called = {"ingest": False}

    def _unexpected_ingest(*_args, **_kwargs):
        called["ingest"] = True
        raise AssertionError("session inference must not start for too many chunks")

    monkeypatch.setattr(controller.sessions, "ingest_source_chunks", _unexpected_ingest)

    with pytest.raises(ValueError, match="maximum is 1 per ingest"):
        controller.ingest_sources(
            session_id,
            pasted_text=("Alpha explanatory perspective. " * 250),
        )

    assert called["ingest"] is False
