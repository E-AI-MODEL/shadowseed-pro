"""Regression tests for the isolated MIT research replay adapter."""
import pytest

from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import (
    extract_observation, parse_turns,
)
from shadowseed.detection.model_detector import parse_numbered_seeds_with_diagnostics

def test_only_actual_hypothesis_not_code_is_read():
    reply = "\n" + chr(96) * 3 + "python\n# Hypothesis: Compare independent repairs after selective ablation.\nprint(1)\n" + chr(96) * 3
    assert extract_observation(reply) == "Compare independent repairs after selective ablation."
    request = "\n" + chr(96) * 3 + "forward\n" + '{"type":"generate","model":"original"}' + "\n" + chr(96) * 3
    assert extract_observation(request) is None

def test_extraction_does_not_invent_or_paraphrase():
    reply = "Observed alternative mechanism in layer 19; results require independent testing."
    assert extract_observation(reply) is None
    assert extract_observation("We attempted to separate repetition from useful mathematical reasoning. Our observations were inconclusive, and we proposed comparing independent held-out cases.").startswith("We attempted to separate repetition from useful mathematical reasoning.")

def test_parser_keeps_fail_closed_none_mixed():
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics("NONE\n1. Additional speculative angle",max_seeds=2)
    assert seeds == []
    assert diagnostics["mixed_none_output"] is True
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics("1. Independent held-out accuracy comparison",max_seeds=2)
    assert len(seeds) == 1
    assert diagnostics["accepted_candidates"] == 1

def test_rejects_missing_mit_turns():
    minimal = "## t001\n### astra\nOne answer."
    with pytest.raises(ValueError, match="Expected exactly 158"):
        parse_turns(minimal)
