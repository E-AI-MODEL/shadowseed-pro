"""Tests for the blind model-vs-baseline control for open-set review."""

import importlib.util
from pathlib import Path

_SCRIPT = Path("scripts/build_blind_control_packets.py").resolve()
_spec = importlib.util.spec_from_file_location("build_blind_control_packets", _SCRIPT)
assert _spec and _spec.loader
ctrl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ctrl)


def _output(item_id: str, candidates: list[str]) -> dict:
    return {"summary": {}, "results": [{"item_id": item_id, "normalized_candidates": candidates}]}


def test_build_hides_arm_and_key_maps_every_blind_id() -> None:
    model = _output("a", ["Of de prijs vermeld is, wordt niet genoemd."])
    baseline = _output("a", ["Rol van X.", "Tijdlijn van Y."])
    packets, key = ctrl.build_blind_packets(model, baseline)

    # one candidate per arm-entry, times two default reviewers
    assert len(packets) == (1 + 2) * 2
    for packet in packets:
        assert "arm" not in packet
        assert "arm" not in packet["judgment"]
        assert packet["blind_id"] in key
    arms = sorted(v["arm"] for v in key.values())
    assert arms == ["baseline", "baseline", "model"]


def test_build_is_deterministic() -> None:
    model = _output("a", ["m1", "m2"])
    baseline = _output("a", ["b1", "b2"])
    _, key1 = ctrl.build_blind_packets(model, baseline)
    _, key2 = ctrl.build_blind_packets(model, baseline)
    assert key1 == key2


def test_unblind_recovers_per_arm_rates() -> None:
    model = _output("a", ["m1", "m2"])
    baseline = _output("a", ["b1"])
    packets, key = ctrl.build_blind_packets(model, baseline, reviewer_ids=("reviewer_a",))

    # Accept both model candidates (one atomic), reject the baseline one.
    for packet in packets:
        arm = key[packet["blind_id"]]["arm"]
        if arm == "model":
            packet["judgment"]["accept"] = True
            packet["judgment"]["atomic"] = packet["candidate"] == "m1"
        else:
            packet["judgment"]["accept"] = False
            packet["judgment"]["reject_reason"] = "too_vague"

    summary = ctrl.unblind(packets, key)
    assert summary["per_arm"]["model"]["judged"] == 2
    assert summary["per_arm"]["model"]["accept_rate"] == 1.0
    assert summary["per_arm"]["model"]["atomic_rate_of_accepted"] == 0.5
    assert summary["per_arm"]["baseline"]["accept_rate"] == 0.0
    assert summary["accept_rate_delta_model_minus_baseline"] == 1.0


def test_unblind_ignores_unreviewed_rows() -> None:
    model = _output("a", ["m1"])
    baseline = _output("a", ["b1"])
    packets, key = ctrl.build_blind_packets(model, baseline, reviewer_ids=("reviewer_a",))
    # leave accept as None (pending)
    summary = ctrl.unblind(packets, key)
    assert summary["per_arm"]["model"]["judged"] == 0
    assert summary["per_arm"]["baseline"]["judged"] == 0
