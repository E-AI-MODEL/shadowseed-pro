from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.open_set_hf import fetch_open_set_hf_batch


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_fetch_open_set_hf_batch_normalizes_rows(tmp_path: Path, monkeypatch) -> None:
    registry = {
        "sources": [
            {
                "id": "ag_news_test",
                "dataset": "szhuggingface/ag_news",
                "config": "default",
                "split": "test",
                "revision": "main",
                "license": "apache-2.0",
                "text_field": "text",
                "label_field": "label",
                "label_names": {
                    "0": "World",
                    "1": "Sports",
                    "2": "Business",
                    "3": "Sci/Tech",
                },
                "domain_template": "nieuws - {label_name}",
                "title_template": "AG News {label_name} #{row_idx}",
                "min_text_length": 40,
            }
        ]
    }
    registry_path = tmp_path / "sources.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    payload = {
        "rows": [
            {
                "row_idx": 11,
                "row": {
                    "text": "Markets rallied after stronger than expected earnings and investors revised their outlook for major industrial companies.",
                    "label": 2,
                },
            },
            {
                "row_idx": 12,
                "row": {
                    "text": "Space agencies expanded cooperation on satellite launches and lunar planning after months of technical talks.",
                    "label": 3,
                },
            },
        ]
    }

    monkeypatch.setattr(
        "shadowseed.benchmark.open_set_hf.urlopen",
        lambda *_args, **_kwargs: _FakeResponse(payload),
    )

    output = tmp_path / "hf_batch.json"
    fetch_open_set_hf_batch(
        str(output),
        source_id="ag_news_test",
        registry_path=str(registry_path),
        limit=2,
        offset=10,
    )

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["source"]["dataset"] == "szhuggingface/ag_news"
    assert result["source"]["returned_count"] == 2
    assert [item["id"] for item in result["items"]] == ["AG_NEWS_TEST_11", "AG_NEWS_TEST_12"]
    assert result["items"][0]["domain"] == "nieuws - Business"
    assert result["items"][0]["title"] == "AG News Business #11"
    assert result["items"][1]["source_metadata"]["label_name"] == "Sci/Tech"


def test_fetch_open_set_hf_batch_skips_short_rows(tmp_path: Path, monkeypatch) -> None:
    registry = {
        "sources": [
            {
                "id": "ag_news_test",
                "dataset": "szhuggingface/ag_news",
                "config": "default",
                "split": "test",
                "text_field": "text",
                "default_domain": "nieuws",
                "min_text_length": 50,
            }
        ]
    }
    registry_path = tmp_path / "sources.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    payload = {
        "rows": [
            {"row_idx": 1, "row": {"text": "Te kort."}},
            {
                "row_idx": 2,
                "row": {
                    "text": "A longer article body that comfortably passes the minimum length threshold for the review batch.",
                },
            },
        ]
    }

    monkeypatch.setattr(
        "shadowseed.benchmark.open_set_hf.urlopen",
        lambda *_args, **_kwargs: _FakeResponse(payload),
    )

    output = tmp_path / "hf_batch.json"
    fetch_open_set_hf_batch(
        str(output),
        source_id="ag_news_test",
        registry_path=str(registry_path),
        limit=2,
        offset=0,
    )

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["source"]["returned_count"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "AG_NEWS_TEST_2"


def test_arxiv_abstracts_source_maps_fields_from_real_registry(tmp_path: Path, monkeypatch) -> None:
    """Drift guard for the committed arxiv_abstracts registry entry (Layer F).

    Feeds a fake Datasets Server row in the gfissore/arxiv-abstracts-2021
    shape through the REAL registry file, so a silent registry edit that
    breaks the field mapping fails here instead of in a live dispatch.
    """
    payload = {
        "rows": [
            {
                "row_idx": 7,
                "row": {
                    "title": "Topological order in quantum spin liquids",
                    "abstract": (
                        "We study the emergence of topological order in frustrated "
                        "quantum magnets using a combination of exact diagonalization "
                        "and tensor-network methods. We identify a gapped spin-liquid "
                        "phase characterized by anyonic excitations and a fourfold "
                        "topological ground-state degeneracy on the torus, and we map "
                        "the phase boundary to neighboring magnetically ordered states."
                    ),
                    "categories": "cond-mat.str-el",
                },
            }
        ]
    }
    monkeypatch.setattr(
        "shadowseed.benchmark.open_set_hf.urlopen",
        lambda *_args, **_kwargs: _FakeResponse(payload),
    )

    output = tmp_path / "hf_batch.json"
    fetch_open_set_hf_batch(str(output), source_id="arxiv_abstracts", limit=1, offset=0)

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["source"]["dataset"] == "gfissore/arxiv-abstracts-2021"
    assert result["source"]["license"] == "cc0-1.0"
    item = result["items"][0]
    assert item["id"] == "ARXIV_ABSTRACTS_7"
    assert item["title"] == "Topological order in quantum spin liquids"
    assert item["domain"] == "wetenschap - arXiv abstract"
    assert item["text"].startswith("We study the emergence")
