from __future__ import annotations

from argparse import Namespace

from shadowseed import cli
from shadowseed.cli import build_parser


def test_absencebench_aliases_map_to_canonical_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["prepare-absencebench"]).command == "prepare-absencebench-bundle"
    assert parser.parse_args(["prepare-absencebench-bundle"]).command == "prepare-absencebench-bundle"

    assert parser.parse_args(["fetch-absencebench"]).command == "fetch-absencebench-sample"
    assert parser.parse_args(["fetch-absencebench-sample"]).command == "fetch-absencebench-sample"

    assert parser.parse_args(["run-local-absencebench", "--input", "sample.json"]).command == "run-absencebench-local"
    assert parser.parse_args(["run-absencebench-local", "--input", "sample.json"]).command == "run-absencebench-local"

    assert parser.parse_args(["run-nlp-smoke"]).command == "run-absencebench-smoke"
    assert parser.parse_args(["run-absencebench-smoke"]).command == "run-absencebench-smoke"


def test_open_set_detector_choices_track_the_canonical_enums() -> None:
    """Drift guard: the CLI --detector / --model-backend choices must come
    from the canonical enums, not a hardcoded copy. ADR 0001."""
    from shadowseed.benchmark.open_set_candidate_adapter import SUPPORTED_DETECTORS
    from shadowseed.detection.model_detector import SUPPORTED_MODEL_BACKENDS

    parser = build_parser()
    subparsers_action = next(
        a for a in parser._actions if hasattr(a, "choices") and a.choices
        and "run-open-set-seed-review" in a.choices
    )
    open_set = subparsers_action.choices["run-open-set-seed-review"]
    detector_action = next(
        a for a in open_set._actions if "--detector" in getattr(a, "option_strings", [])
    )
    backend_action = next(
        a for a in open_set._actions if "--model-backend" in getattr(a, "option_strings", [])
    )
    assert tuple(detector_action.choices) == tuple(SUPPORTED_DETECTORS)
    assert tuple(backend_action.choices) == tuple(SUPPORTED_MODEL_BACKENDS)


def test_execute_command_resolves_alias_before_dispatch(monkeypatch) -> None:
    calls: list[str] = []

    def fake_handler(args: Namespace) -> str:
        calls.append(args.command)
        return "prepared.json"

    monkeypatch.setitem(cli.execute_command.__globals__["COMMAND_HANDLERS"], "prepare-absencebench-bundle", fake_handler)

    result = cli.execute_command(Namespace(command="prepare-absencebench", output="ignored"))

    assert result == "prepared.json"
    assert calls == ["prepare-absencebench"]
