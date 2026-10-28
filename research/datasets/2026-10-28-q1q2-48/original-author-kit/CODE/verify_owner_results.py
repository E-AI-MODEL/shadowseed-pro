"""Verify original run data and raw responses without labeling semantic meaning."""
import json,hashlib,collections,sys
from pathlib import Path
p=Path(sys.argv[1]); o=json.loads((p/'observed-owner.json').read_text())
plan=json.loads((p/'plan.json').read_text())
assert o['status']=='complete_exploratory_unreviewed'
assert o['attempted_calls']==o['successful_calls']==plan['planned_calls']==48
assert o['human_reviews_completed']==plan['human_reviews_completed']==0
assert len(o['trajectories'])==24 and len(plan['call_order'])==24
assert plan['independent_cases']==1 and plan['research_moments']==2
assert o['source_sha256']==plan['source_sha256']=='0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf'
receipts=[]; tokens=0
for item,tr in zip(plan['call_order'],o['trajectories']):
    assert all(item[k]==tr[k] for k in ('moment','arm','replicate'))
    assert len(tr['turns'])==2
    assert tr['canonical_product_seed_surfaced'] is False
    assert tr['research_note_exposed']==(tr['arm'] in ('shadow_candidate','placebo'))
    for phase,turn in enumerate(tr['turns'],1):
        assert turn['phase']==phase and turn['answer']
        r=turn['receipt']
        assert r['model_requested']==r['model_returned']==tr['model'] or r['model_returned'].startswith(tr['model']+'-')
        assert r['answer_sha256']==hashlib.sha256(turn['answer'].encode()).hexdigest()
        assert r['input_tokens']>0 and r['output_tokens']>0
        tokens+=r['input_tokens']+r['output_tokens']
        receipts.append(r['response_id'])
assert tokens==o['reported_tokens']==187255
assert len(receipts)==len(set(receipts))==48
bucket=collections.Counter((t['moment'],t['arm']) for t in o['trajectories'])
assert len(bucket)==8 and set(bucket.values())=={3}
print(json.dumps(dict(verified=True,attempted=48,complete_calls=48,complete_trajectories=24,source_checksum=plan['source_sha256'],reported_tokens=tokens,unique_provider_response_ids=48,product_gate_seed_exposures=0,reviewed_human=0,group_counts={str(k):v for k,v in sorted(bucket.items())}),indent=2))
