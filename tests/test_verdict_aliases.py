"""Canonical English verdict aliases (issue #16)."""
from shadowseed.benchmark.dialectic_falsification import (
    VERDICT_HOUDT_STAND, VERDICT_ONBESLIST, VERDICT_REFUTED,
    VERDICT_SURVIVES, VERDICT_UNDECIDED, VERDICT_WEERLEGD,
)


def test_english_verdict_aliases_map_to_legacy_dutch_tokens():
    assert VERDICT_REFUTED == VERDICT_WEERLEGD == "WEERLEGD"
    assert VERDICT_SURVIVES == VERDICT_HOUDT_STAND == "HOUDT_STAND"
    assert VERDICT_UNDECIDED == VERDICT_ONBESLIST == "ONBESLIST"


def test_dialectic_verdict_enum_english_names_dutch_values():
    from shadowseed.benchmark.dialectic_falsification import (
        DialecticVerdict, normalize_verdict,
    )
    # Canonical English names, legacy Dutch serialization values.
    assert DialecticVerdict.REFUTED.name == "REFUTED"
    assert DialecticVerdict.REFUTED.value == "WEERLEGD"
    assert DialecticVerdict.SURVIVES.value == "HOUDT_STAND"
    assert DialecticVerdict.UNDECIDED.value == "ONBESLIST"
    # Normalization accepts both legacy Dutch and English tokens.
    assert normalize_verdict("weerlegd") is DialecticVerdict.REFUTED
    assert normalize_verdict("REFUTED") is DialecticVerdict.REFUTED
    assert normalize_verdict("HOUDT_STAND") is DialecticVerdict.SURVIVES
