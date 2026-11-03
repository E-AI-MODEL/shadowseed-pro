"""Research adapter prompt ablation regression tests."""
import pytest
from shadowseed.recurrence_recognition import build_prompt, OpenQuestion
from research.experiments.mit_shadow_memory_20261103.run_identity_strict_pilot import (
    strip_fewshot_and_require_single_answer
)

def test_remove_wrong_reference_examples_but_preserve_inputs():
    original = build_prompt(
        [OpenQuestion(1, 0, "Which experimental outcome would prove a targeted edit?")],
        ["Does a random control change the same outcome?"],
    )
    assert "a: 3" in original
    rewritten = strip_fewshot_and_require_single_answer(original)
    assert "a: 3" not in rewritten
    assert "b: NONE" not in rewritten
    assert "open question 1" in rewritten
    assert "Which experimental outcome" in rewritten
    assert "Does a random control" in rewritten
    assert "a: 1" in rewritten and "a: NONE" in rewritten
    assert "different intervention" in rewritten

def test_unknown_prompt_structure_fails_closed():
    with pytest.raises(ValueError, match="Unexpected canonical prompt"):
        strip_fewshot_and_require_single_answer("Unrelated changed prompt")
