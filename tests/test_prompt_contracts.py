from __future__ import annotations

from shadowseed.prompt_contracts import prompt_contract_metadata


def test_prompt_contract_hash_is_stable_for_same_template() -> None:
    first = prompt_contract_metadata(
        prompt_id="detector_test",
        prompt_version="1",
        component="chat_detection",
        template="  One contract.\r\nSecond line.  ",
        input_contract=("question", "draft"),
        output_contract="candidate_or_NONE",
    )
    second = prompt_contract_metadata(
        prompt_id="detector_test",
        prompt_version="1",
        component="chat_detection",
        template="One contract.\nSecond line.",
        input_contract=("question", "draft"),
        output_contract="candidate_or_NONE",
    )

    assert first["template_sha256"] == second["template_sha256"]
    assert first["input_contract"] == ["question", "draft"]
    assert first["output_contract"] == "candidate_or_NONE"


def test_prompt_contract_hash_changes_when_template_changes() -> None:
    first = prompt_contract_metadata(
        prompt_id="revision_test",
        prompt_version="1",
        component="same_turn_revision",
        template="Preserve the draft.",
    )
    changed = prompt_contract_metadata(
        prompt_id="revision_test",
        prompt_version="1",
        component="same_turn_revision",
        template="Preserve the draft unless evidence changes it.",
    )

    assert first["template_sha256"] != changed["template_sha256"]
