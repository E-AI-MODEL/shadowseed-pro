from __future__ import annotations

import json
from pathlib import Path

import pytest

from shadowseed.analysis.artifact_snapshot import build_artifact_snapshot, main


def test_build_artifact_snapshot_preserves_artifact_provenance(tmp_path: Path) -> None:
    source = tmp_path / "downloaded-artifacts"
    first = source / "02-gap-finder-results"
    second = source / "06-blind-benchmark-results"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    (first / "summary.json").write_text('{"suite":"gap"}\n', encoding="utf-8")
    (second / "summary.json").write_text('{"suite":"blind"}\n', encoding="utf-8")
    (second / "notes.txt").write_text("ignored\n", encoding="utf-8")

    target = tmp_path / "results"
    artifacts = target / "artifacts"
    manifest_path = target / "manifest.json"

    build_artifact_snapshot(
        source,
        target,
        artifacts_dir=artifacts,
        manifest_path=manifest_path,
        source_workflow="Checks en benchmark-resultaten",
        source_run_id="123",
        repository="E-AI-MODEL/shadowseed",
        published_via=["analysis-job"],
        path_key="results_path",
    )

    assert (target / "summary.json").exists()
    assert (target / "06-blind-benchmark-results__summary.json").exists()
    assert not (target / "notes.txt").exists()
    assert (artifacts / "02-gap-finder-results" / "summary.json").exists()
    assert (artifacts / "06-blind-benchmark-results" / "summary.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_workflow"] == "Checks en benchmark-resultaten"
    assert manifest["source_run_id"] == "123"
    assert manifest["repository"] == "E-AI-MODEL/shadowseed"
    assert manifest["published_via"] == ["analysis-job"]
    assert len(manifest["copied_files"]) == 2

    copied_names = {Path(item["results_path"]).name for item in manifest["copied_files"]}
    assert copied_names == {"summary.json", "06-blind-benchmark-results__summary.json"}
    assert {item["original_artifact_path"] for item in manifest["copied_files"]} == {
        "artifacts/02-gap-finder-results/summary.json",
        "artifacts/06-blind-benchmark-results/summary.json",
    }


def test_build_artifact_snapshot_requires_expected_files(tmp_path: Path) -> None:
    source = tmp_path / "downloaded-artifacts"
    artifact = source / "02-gap-finder-results"
    artifact.mkdir(parents=True)
    (artifact / "ssl45_gap_suite.json").write_text('{"ok": true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="ssl45_false_positive_suite.json"):
        build_artifact_snapshot(
            source,
            tmp_path / "latest",
            required_files=["ssl45_gap_suite.json", "ssl45_false_positive_suite.json"],
        )


def test_artifact_snapshot_cli_writes_manifest(tmp_path: Path) -> None:
    source = tmp_path / "downloaded-artifacts"
    artifact = source / "07-analysis-report"
    artifact.mkdir(parents=True)
    (artifact / "analysis_report.md").write_text("# Report\n", encoding="utf-8")

    manifest_path = tmp_path / "latest" / "manifest.json"
    exit_code = main(
        [
            "--source",
            str(source),
            "--target-dir",
            str(tmp_path / "latest"),
            "--manifest-path",
            str(manifest_path),
            "--source-workflow",
            "Checks en benchmark-resultaten",
            "--published-via",
            "wiki",
            "pages",
            "--path-key",
            "latest_path",
            "--committed-back-to-main",
            "false",
            "--require-files",
            "analysis_report.md",
        ]
    )

    assert exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["published_via"] == ["wiki", "pages"]
    assert manifest["committed_back_to_main"] is False
    assert manifest["copied_files"][0]["latest_path"] == "latest/analysis_report.md"
