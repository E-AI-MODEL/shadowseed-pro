from shadowseed.authority_profiles import (
    AUTHORITY_PROFILES,
    AuthorityProfileId,
    STRICT_PROFILE,
    get_authority_profile,
)


def test_default_authority_profile_preserves_current_controlled_contract():
    profile = get_authority_profile(None)

    assert profile is STRICT_PROFILE
    assert profile.id is AuthorityProfileId.STRICT
    assert profile.detect_mode == "auto"
    assert profile.validate_mode == "manual"
    assert profile.require_operator_verified_evidence is True
    assert profile.auto_validate_recurrence is False
    assert profile.auto_validate_system_evidence is False
    assert profile.auto_promote_when_gate_allows is True
    assert profile.auto_surface_when_relevant is True
    assert profile.contradiction_mode == "block_and_manual_resolution"


def test_all_public_profiles_keep_gate_and_audit_semantics_explicit():
    assert set(AUTHORITY_PROFILES) == {
        AuthorityProfileId.STRICT,
        AuthorityProfileId.ASSISTED,
        AuthorityProfileId.AUTONOMOUS,
        AuthorityProfileId.OPEN,
    }

    for profile in AUTHORITY_PROFILES.values():
        assert profile.promote_mode in {"gate", "gate_after_manual_validation"}
        assert profile.surface_mode == "gate_and_relevance"


def test_open_profile_is_explicitly_opt_in():
    profile = get_authority_profile("open")

    assert profile.id is AuthorityProfileId.OPEN
    assert profile.allow_unreviewed_system_evidence is True
    assert get_authority_profile(None).allow_unreviewed_system_evidence is False


def test_unknown_profile_is_rejected():
    try:
        get_authority_profile("anything-goes")
    except ValueError as exc:
        assert "unknown authority profile" in str(exc)
    else:
        raise AssertionError("unknown profile must be rejected")
