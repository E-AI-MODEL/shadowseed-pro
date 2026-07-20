"""Canonical English verdict aliases (issue #16)."""
from shadowseed.benchmark.dialectic_falsification import (
    VERDICT_HOUDT_STAND, VERDICT_ONBESLIST, VERDICT_REFUTED,
    VERDICT_SURVIVES, VERDICT_UNDECIDED, VERDICT_WEERLEGD,
)


def test_english_verdict_aliases_map_to_legacy_dutch_tokens():
    assert VERDICT_REFUTED == VERDICT_WEERLEGD == "WEERLEGD"
    assert VERDICT_SURVIVES == VERDICT_HOUDT_STAND == "HOUDT_STAND"
    assert VERDICT_UNDECIDED == VERDICT_ONBESLIST == "ONBESLIST"
