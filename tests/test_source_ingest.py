from __future__ import annotations

from pathlib import Path

from shadowseed.application.ingest import chunk_text, prepare_sources, read_source_file
from shadowseed.workbench.controller import WorkbenchController


def test_chunk_text_preserves_source_provenance() -> None:
    text = ("Alpha explains one perspective.\n\n" * 120).strip()
    chunks = chunk_text(text, source_name="notes.md", max_chars=800, overlap_chars=100)

    assert len(chunks) > 1
    assert chunks[0].source_name == "notes.md"
    assert chunks[0].context_ref == "source:notes.md:chunk:00000"
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
