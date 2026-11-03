"""Real-source extraction, chronology and exact/lexical control regressions."""
from research.experiments.mit_shadow_memory_20261103.replay_85_source_hypotheses import (
    extract_hypotheses, normalized_literal, source_records,
    build_lexical_baseline, verify_replay_source,
)
from shadowseed.detection.model_detector import parse_numbered_seeds_with_diagnostics


def test_ignore_tool_json_and_nonhypothesis_program_lines():
    raw = (
        "\n" + chr(96) * 3 + "forward\n"
        + '{"type":"generate","model":"original","output":"hypothesis"}'
        + "\n" + chr(96) * 3 + "\n"
        + chr(96) * 3 + "python\n"
        + "# Hypothesis: Repeated tails may correlate with a specific MLP direction.\n"
        + "print(42)\n" + chr(96) * 3
    )
    assert extract_hypotheses(raw) == [
        "Repeated tails may correlate with a specific MLP direction."
    ]


def test_ordered_turn_identity_preserved_without_duplicate_credit():
    turns = [
        (1, "# Hypothesis: A repeated proposed mechanism."),
        (2, "# Hypothesis: A repeated proposed mechanism."),
        (3, "# Hypothesis: A different proposed mechanism."),
    ]
    rows = source_records(turns)
    assert [x["mit_turn"] for x in rows] == [1, 2, 3]
    assert normalized_literal(rows[0]["text"]) == normalized_literal(rows[1]["text"])
    baseline = build_lexical_baseline(rows)
    exact = [x for x in baseline if x["kind"] == "exact"]
    assert len(exact) == 1
    assert exact[0]["mit_turn"] == 2
    assert exact[0]["earlier_turn"] == 1


def test_known_literal_cases_and_absence():
    assert normalized_literal("  The same idea. ") == "the same idea"
    assert extract_hypotheses(chr(96)*3 + "forward\n{}" + chr(96)*3) == []
    assert extract_hypotheses("An assistant might say hypothesis in prose") == []


def test_refuse_nonpinned_or_partial_trajectory():
    try:
        verify_replay_source("## t001\n### astra\n# Hypothesis: A test.")
        assert False, "A partial log should fail instead of returning incomplete evidence"
    except ValueError:
        pass
