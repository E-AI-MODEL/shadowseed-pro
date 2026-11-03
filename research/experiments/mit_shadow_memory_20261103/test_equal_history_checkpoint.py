"""Protocol regressions for equal-history ShadowSeed / ordinary-model checkpoint trial."""
import numpy as np
from research.experiments.mit_shadow_memory_20261103.equal_history_checkpoint import (
    CHECKPOINTS, parse_response, nearest_cluster_before_observation,
)

def test_checkpoint_times_are_fixed_and_chronological():
    assert CHECKPOINTS==(26,60,100,121,142)
    assert len(set(CHECKPOINTS))==len(CHECKPOINTS)
    assert list(CHECKPOINTS)==sorted(CHECKPOINTS)

def test_only_existing_prior_turns_are_accepted():
    raw="PICK: 13\nRELATION: RELATED_DISTINCT\nREASON: The original MLP direction motivates a different test."
    parsed=parse_response(raw,{1,8,13})
    assert parsed["valid"] is True
    assert parsed["pick"]==13
    assert parsed["relation"]=="RELATED_DISTINCT"
    assert parse_response(raw,{1,8})["valid"] is False

def test_none_requires_no_link_or_uncertainty():
    a=parse_response("PICK: NONE\nRELATION: NO_CLEAR_DIRECT_LINK\nREASON: No specific mechanism shared.",{1})
    assert a["valid"] is True and a["pick"] is None
    b=parse_response("PICK: NONE\nRELATION: RELATED_DISTINCT\nREASON: Maybe.",{1})
    assert b["valid"] is False
    c=parse_response("PICK: 1\nRELATION: NO_CLEAR_DIRECT_LINK\nREASON: Maybe.",{1})
    assert c["valid"] is False

def test_unstructured_output_does_not_become_a_success():
    assert parse_response("Turn 13 seems similar.",{13})["valid"] is False
    assert parse_response("PICK: 13\nPICK: 15\nRELATION: SAME_CLAIM\nREASON: duplicated",{13,15})["valid"] is False

def test_cluster_nearest_uses_only_caller_supplied_history():
    class FakeClusters:
        members=[["An earlier specific hypothesis"],["A different earlier hypothesis"]]
        def nearest(self,vec,*,floor,limit):
            assert floor==0.6 and limit==4
            assert vec.shape==(2,)
            return [(0,0.92),(1,0.72)]
    actual=nearest_cluster_before_observation(
        FakeClusters(),np.array([0.9,0.1]),
        {"An earlier specific hypothesis":[5,7],"A different earlier hypothesis":[13]},
    )
    assert [a["earliest_prior_turn"] for a in actual]==[5,13]
    assert actual[0]["prior_turns"]==[5,7]
    # No matching source text does not silently create a made-up prior turn.
    assert nearest_cluster_before_observation(FakeClusters(),np.array([0.9,0.1]),{})==[]
