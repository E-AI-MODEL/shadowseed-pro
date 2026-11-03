"""Acceptance checks for the MIT-specific method-fit screen."""
from research.experiments.mit_shadow_memory_20261103.run_replay_v3 import quality_reasons, normalize_research_numbered_output

def test_control_with_measurable_outcome_can_enter_weightless_intake():
    candidate = (
        "Compare the layer 19 MLP directional edit versus the unchanged weights "
        "and measure the repeated-token log probabilities across held-out math examples."
    )
    assert quality_reasons(candidate) == []

def test_learning_rate_and_training_are_out_of_scope():
    for candidate in (
        "Compare the learning rate against baseline and measure accuracy after tuning.",
        "Compare training with repetitive sentences versus original and measure accuracy.",
        "Compare dropout with original weights and measure repeated token likelihood.",
    ):
        assert "outside_frozen_weight_edit" in quality_reasons(candidate)

def test_recurrent_connections_misreading_is_flagged():
    candidate = "Compare recurrent connections versus the baseline and measure repetition rate."
    assert "incorrect_architecture_assumption" in quality_reasons(candidate)

def test_generic_questions_are_not_accepted():
    candidate = "What mechanisms underlie the correlation between neurons and correct answers?"
    assert "missing_explicit_comparison" in quality_reasons(candidate)
    candidate = "Compare two architectures versus baseline for generalization to diverse tasks."
    assert "generic_transfer_question" in quality_reasons(candidate)
    assert "missing_measurable_outcome" in quality_reasons(candidate)

def test_scope_rejection_does_not_mark_good_control_invalid():
    candidate = "Compare sparse top64 weight suppression versus the unchanged model and measure whitespace cutoff errors."
    assert quality_reasons(candidate) == []


def test_recovery_preserves_real_qwen_labeled_outcome():
    raw = (
        "1. **Compare** the performance of the original unedited weights with "
        "those after applying the specific weight edit across all 32 math tasks "
        "using an independent dataset for evaluation.\n"
        "   - **Specific Outcome**: Accuracy improvement or degradation on the "
        "held-out tasks compared to the tuned version.\n"
        "2. **Measure** the impact of the weight edit by comparing the perplexity "
        "scores before and after the edit when generating new sequences."
    )
    normalized = normalize_research_numbered_output(raw)
    assert len(normalized.splitlines()) == 2
    assert "Measured outcome: Accuracy" in normalized
    assert quality_reasons(normalized.splitlines()[0]) == []
    assert quality_reasons(normalized.splitlines()[1]) == []

def test_none_is_never_reinterpreted_as_a_candidate():
    mixed = "NONE\n1. Compare model versus baseline and measure accuracy on unseen math."
    assert normalize_research_numbered_output(mixed) == mixed

def test_orphan_metric_is_never_promoted_as_candidate():
    raw = "- Specific Outcome: Accuracy improved\n1. Compare directions versus baseline and measure token errors."
    normalized = normalize_research_numbered_output(raw)
    assert "Accuracy improved" not in normalized
    assert len(normalized.splitlines()) == 1
