"""Source-linked offline checks for the 48-call pilot. No paid model calls."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research.scripts import q1q2_two_point_48 as p

class TwoPointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("LOCAL_OBSERVED"):
            raise unittest.SkipTest("SHA-pinned original Actions archive not available in routine CI")
        cls.source=p.original(os.environ["LOCAL_OBSERVED"])
        cls.cases,cls.order=p.plan(cls.source)

    def test_source_and_factors(self):
        self.assertEqual(len(self.cases),2)
        self.assertEqual(len(self.order)*2,48)
        self.assertEqual(self.cases[0]["original_outcome"],"accepted")
        self.assertEqual(self.cases[1]["original_outcome"],"rejected")
        for c in self.cases:
            for arm in p.ARMS:
                self.assertEqual(sum(t["moment"]==c["moment"] and t["arm"]==arm
                                     for t in self.order),3)
            self.assertEqual(c["placebo_case"],"DM26-C03")
            self.assertNotEqual(c["target"],c["placebo"])

    def test_control_prompts_have_no_target_or_placebo(self):
        for c in self.cases:
            for arm in p.ARMS:
                first=p.prompt(c,arm,1,None)
                follow=p.prompt(c,arm,2,"Fictief antwoord 1")
                self.assertIn("Fictief antwoord 1",follow)
                self.assertLess(len(first),p.MAX_CHARS)
                if arm=="shadow_candidate":
                    self.assertIn(c["target"],first)
                    self.assertNotIn(c["placebo"],first)
                else:
                    self.assertNotIn(c["target"],first)
                if arm=="placebo":
                    self.assertIn(c["placebo"],first)
                else:
                    self.assertNotIn(c["placebo"],first)

    def test_dry_run_is_no_network_and_no_api_key(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("sys.argv",["runner","--observed",os.environ["LOCAL_OBSERVED"],
                                   "--output",d,"--dry-run"]):
                self.assertEqual(p.main(),0)
            manifest=json.loads((Path(d)/"plan.json").read_text())
            self.assertEqual(manifest["planned_calls"],48)
            self.assertEqual(manifest["independent_cases"],1)
            self.assertFalse(manifest["product_Gate_promotion_tested"])

    def test_mocked_48_without_real_provider(self):
        counter=[0]
        def fake_provider(model,prompt,key):
            counter[0]+=1
            i=counter[0]
            answer="Fictief toetsbaar antwoord "+str(i)
            return answer,dict(response_id="fake_"+str(i),model_requested=model,
                model_returned=model,prompt_sha256=p.sha(prompt),
                answer_sha256=p.sha(answer),input_tokens=600,output_tokens=80)
        with tempfile.TemporaryDirectory() as d:
            with patch("sys.argv",["runner","--observed",os.environ["LOCAL_OBSERVED"],
                                   "--output",d]),patch.dict(os.environ,{"OPENAI_API_KEY":"FAKE"}),patch.object(p,"provider",fake_provider):
                self.assertEqual(p.main(),0)
            self.assertEqual(counter[0],48)
            observed=json.loads((Path(d)/"observed-owner.json").read_text())
            self.assertEqual(observed["successful_calls"],48)
            self.assertEqual(len(observed["trajectories"]),24)
            self.assertTrue(all(len(x["turns"])==2 for x in observed["trajectories"]))
            blind=json.loads((Path(d)/"blind-human-review.json").read_text())
            owner=json.loads((Path(d)/"owner-unblind.json").read_text())
            self.assertEqual(len(blind["groups"]),6)
            self.assertEqual(len(owner["unblind"]),24)
            self.assertNotIn("shadow_candidate",json.dumps(blind))
            self.assertNotIn('"FAKE"',json.dumps(observed))

if __name__=="__main__":
    unittest.main()
