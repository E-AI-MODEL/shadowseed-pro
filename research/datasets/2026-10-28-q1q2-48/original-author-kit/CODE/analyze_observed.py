"""Descriptive audit only; does not estimate semantic new possibilities.

Reads author-only observed-owner.json. Records call completeness, input/output
usage, and simple visible-text echo diagnostics. No AI rater is used. Never
turns lexical novelty into a Q1/Q2 effect claim.
"""
from __future__ import annotations
import argparse,csv,json,re,statistics
from pathlib import Path

WORDS=re.compile(r"\b[\w-]{3,}\b",re.UNICODE)
def terms(s):
    return set(WORDS.findall(s.casefold()))
def overlap(a,b):
    t1,t2=terms(a),terms(b)
    return round(len(t1 & t2)/max(1,len(t1|t2)),4)
def assess(doc):
    records=[]
    for track in doc.get('trajectories',[]):
        if not track.get('turns'):
            records.append(dict(moment=track['moment'],model=track['model'],arm=track['arm'],
                replicate=track['replicate'],complete_pair=False,calls=0,
                input_tokens=0,output_tokens=0,first_chars=0,second_chars=0,first_second_jaccard=None))
            continue
        turns=track['turns'];r=track.copy();
        records.append(dict(moment=track['moment'],model=track['model'],arm=track['arm'],
            replicate=track['replicate'],complete_pair=len(turns)==2,calls=len(turns),
            input_tokens=sum(x['receipt'].get('input_tokens',0) for x in turns),
            output_tokens=sum(x['receipt'].get('output_tokens',0) for x in turns),
            first_chars=len(turns[0]['answer']),
            second_chars=len(turns[1]['answer']) if len(turns)>1 else 0,
            first_second_jaccard=overlap(turns[0]['answer'],turns[1]['answer']) if len(turns)>1 else None))
    buckets={}
    for r in records:
        k=(r['moment'],r['arm']); a=buckets.setdefault(k,[]);a.append(r)
    out=[]
    for (moment,arm),entries in sorted(buckets.items()):
        full=[x for x in entries if x['complete_pair']]
        out.append(dict(moment=moment,arm=arm,tracks_attempted=len(entries),complete_pairs=len(full),
            calls=sum(x['calls'] for x in entries),
            input_tokens=sum(x['input_tokens'] for x in entries),
            output_tokens=sum(x['output_tokens'] for x in entries),
            mean_visible_chars_first=round(statistics.mean(x['first_chars'] for x in full),1) if full else None,
            mean_first_second_jaccard=round(statistics.mean(x['first_second_jaccard'] for x in full),4) if full else None))
    return records,out

def main():
    p=argparse.ArgumentParser();p.add_argument('observed');p.add_argument('--out',required=True);args=p.parse_args()
    source=Path(args.observed);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    doc=json.loads(source.read_text(encoding='utf-8'))
    detail,arms=assess(doc)
    for filename,rows in [('mechanical_per_track.csv',detail),('mechanical_per_arm.csv',arms)]:
        with (out/filename).open('w',encoding='utf-8',newline='') as f:
            if rows:
                wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
    summary=dict(status=doc.get('status'),attempted_calls=doc.get('attempted_calls'),
        successful_calls=doc.get('successful_calls'),
        provider_reported_tokens=doc.get('reported_tokens'),
        independent_case_count=1,human_reviews_completed=0,
        new_relations_established=None,causal_Q2_effect_established=False,
        note='Mechanics and surface-form only. Do not infer value from word overlap.',arm_summary=arms)
    (out/'mechanical_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=summary['status'],calls=summary['successful_calls'],arms=len(arms),
        human_reviews_completed=0),ensure_ascii=False))
if __name__=='__main__':main()
