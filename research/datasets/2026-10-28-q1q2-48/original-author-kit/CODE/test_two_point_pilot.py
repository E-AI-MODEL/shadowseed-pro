"""Offline checks; no provider requests or network needed."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import two_point_pilot as m

SOURCE = os.environ.get('LOCAL_OBSERVED', '/mnt/data/shadowseed_pilot_20261028/artifacts/observed_12754935105.json')

class DesignChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.sha = m.load_source(SOURCE)
        cls.cases, cls.order = m.make_plan(cls.source)

    def test_source_constraints_and_exact_budget(self):
        self.assertEqual(len(self.order),24)
        self.assertEqual(sum(2 for _ in self.order),48)
        for c in self.cases:
            subset=[x for x in self.order if x['moment']==c['moment']]
            for arm in m.ARMS:
                self.assertEqual(sum(x['arm']==arm for x in subset),3)
            self.assertEqual(c['placebo_case'],'DM26-C03')
            self.assertNotEqual(c['placebo'],c['target'])
        self.assertEqual(self.cases[0]['historical_intake'],'accepted')
        self.assertEqual(self.cases[1]['historical_intake'],'rejected')

    def test_blinding_and_zero_baseline_contamination(self):
        for c in self.cases:
            prompts={a:m.prompt_for(c,a,1,None) for a in m.ARMS}
            for arm in ('ordinary','deliberate_search','placebo'):
                self.assertNotIn(c['target'],prompts[arm])
            self.assertNotIn(c['placebo'],prompts['shadow_candidate'])
            self.assertIn(c['target'],prompts['shadow_candidate'])
            self.assertIn(c['placebo'],prompts['placebo'])
            self.assertNotIn('detector_raw',prompts['ordinary'])
            for arm in m.ARMS:
                p2=m.prompt_for(c,arm,2,'Unieke eerste antwoordtekst.')
                self.assertIn('Unieke eerste antwoordtekst.',p2)

    def test_dry_run_no_api_key(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict(os.environ,{'OPENAI_API_KEY':''}):
                self.assertEqual(m.run(self.source,self.sha,Path(d),True),0)
            out=json.loads((Path(d)/'plan.json').read_text())
            self.assertEqual(out['expected_model_calls'],48)
            self.assertFalse(out['actual_canonical_gate_promotion_by_experiment'])
            self.assertEqual(out['human_reviews_completed'],0)

    def test_real_mode_mocked_48_calls_separate_unblind_key(self):
        calls=[]
        def fake(model,prompt,key):
            calls.append((model,prompt)); i=len(calls)
            response=f'Fictief toetsbaar vervolg {i} met vraagteken?'
            return response,{'response_id':f'fake_{i}','requested_model':model,
                     'returned_model':model,'status':'completed','input_tokens':600,
                     'output_tokens':80,'prompt_sha256':m.digest(prompt.encode()),
                     'response_sha256':m.digest(response.encode())}
        with tempfile.TemporaryDirectory() as d:
            with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST-DO-NOT-USE'}):
                with patch.object(m,'provider_call',fake):
                    self.assertEqual(m.run(self.source,self.sha,Path(d),False),0)
            self.assertEqual(len(calls),48)
            r=json.loads((Path(d)/'observed-owner.json').read_text())
            self.assertEqual(r['successful_calls'],48)
            self.assertEqual(len(r['trajectories']),24)
            self.assertTrue(all(len(x['turns'])==2 for x in r['trajectories']))
            blind=json.loads((Path(d)/'blind-human-review.json').read_text())
            key=json.loads((Path(d)/'owner-unblind.json').read_text())
            self.assertEqual(len(blind['groups']),6)
            self.assertEqual(len(key['unblind']),24)
            self.assertNotIn('shadow_candidate',json.dumps(blind))
            self.assertNotIn('TEST-DO-NOT-USE',json.dumps(r))

if __name__=='__main__':
    unittest.main(verbosity=2)
