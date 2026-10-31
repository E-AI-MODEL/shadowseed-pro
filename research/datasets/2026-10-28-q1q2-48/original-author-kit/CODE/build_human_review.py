"""Produce two independent context-aware, seed/model/arm-blind review packets.

Call only after decrypting completed owner artifact. Never disclose owner key
before both reviews are signed. Reviews have 0 filled labels at creation.
"""
import argparse,hashlib,json,secrets
from pathlib import Path

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('observed')
    p.add_argument('--original',required=True)
    p.add_argument('--out',required=True)
    args=p.parse_args()
    output=Path(args.out);output.mkdir(parents=True,exist_ok=True)
    d=json.loads(Path(args.observed).read_text(encoding='utf-8'))
    raw=Path(args.original).read_bytes()
    if hashlib.sha256(raw).hexdigest()!='0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf':
        raise RuntimeError('Source mismatch')
    src=json.loads(raw)
    mapping={}
    moments={'horizon_after_T2':('gpt-5-2025-08-07',2),'battery_after_T3':('gpt-6-luna',3)}
    for name,(model,t) in moments.items():
        c=next(z for z in src['cases'] if z['case_id']=='DM26-C02' and z['model_id']==model)
        mapping[name]=dict(context_history=[dict(turn=x['turn'],user=x['user_input'],ordinary_host=x['host_answer']) for x in c['turns'][:t+1]], model_source='withheld', new_question_one='Welke onderscheidende onderzoeksvraag kan nog geformuleerd worden?', new_question_two='Welke andere afhankelijkheid of voorwaarde wordt onderzoekbaar?')
    owner_keys={}
    for reviewer in ('A','B'):
        packet=dict(review_id='Q1Q2-20261028-'+reviewer,human_review_complete=False,groups=[])
        owner=[]
        for name in moments:
            for rep in (1,2,3):
                tracks=[]
                for tr in d.get('trajectories',[]):
                    if tr['moment']!=name or tr['replicate']!=rep or len(tr['turns'])!=2:continue
                    uid=secrets.token_hex(12)
                    tracks.append(dict(track=uid,first_answer=tr['turns'][0]['answer'],second_answer=tr['turns'][1]['answer'],
                        label=dict(relation_found_without_stated_note=None,distinct_second_relation=None,
                        falsifiable_test=None,not_in_original_history=None,only_paraphrase_or_echo=None,
                        unsupported_fact_claim=None,reason='')))
                    owner.append(dict(track=uid,arm=tr['arm'],model=tr['model'],moment=name,replicate=rep))
                secrets.SystemRandom().shuffle(tracks)
                packet['groups'].append(dict(group=name+'-'+str(rep), original_context=mapping[name],tracks=tracks))
        secrets.SystemRandom().shuffle(packet['groups'])
        (output/f'REVIEW_{reviewer}_blind.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding='utf-8')
        owner_keys[reviewer]=owner
    (output/'OWNER_REVIEW_IDENTITY_KEY.json').write_text(json.dumps(dict(owner_only=True,reviewer_tracks=owner_keys),indent=2),encoding='utf-8')
    print(json.dumps(dict(groups_per_reviewer=len(packet['groups']),complete=False,reviewers=2, model_calls=d.get('successful_calls'))))
if __name__=='__main__':main()
