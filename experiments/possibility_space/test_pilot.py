"""Offline contract/negative control tests; never model-efficacy evidence."""
import unittest
from pathlib import Path

from pilot import (
    ARMS, _json_object, delta, extract_pairs, first_prompt, legal_bridge,
    read_cases, reachable_pairs, score_first, score_second, second_prompt, selftest,
)

CASES = read_cases(Path(__file__).with_name("first_pilot_cases.json"))


class TestPossibilityPilot(unittest.TestCase):
    def test_four_arms_and_no_truth_shortcut(self):
        self.assertEqual(len(ARMS), 4)
        for c in CASES:
            for arm in ARMS:
                p = first_prompt(c, arm)
                self.assertNotIn("positive_fixture_bridge", p)
                self.assertNotIn("invalid_fixture_bridge", p)
                self.assertIn('"bridges"', p)
            self.assertNotIn("positive_fixture_bridge", second_prompt(c, []))
            self.assertIn("Shared ordinary-generation reference", first_prompt(c, "D-shadow", "{\"bridges\": []}"))

    def test_positive_bridge_and_ablation(self):
        for c in CASES:
            bridge = c["positive_fixture_bridge"]
            if bridge is None:
                continue
            prior = reachable_pairs(c, c["existing_edges"])
            self.assertTrue(legal_bridge(c, tuple(bridge)))
            self.assertTrue(delta(c, tuple(bridge)))
            self.assertTrue(delta(c, tuple(bridge)).isdisjoint(prior))
            score = score_first(c, [tuple(bridge)])
            self.assertTrue(score["ablation_pass"])
            self.assertGreater(len(score["verified_new_terminal_pairs"]), 0)
            correctly_predicted = list(map(tuple, score["verified_new_terminal_pairs"]))
            follow = score_second(c, score, correctly_predicted)
            self.assertEqual(follow["false_positive_claims"], [])
            self.assertEqual(follow["missed_verified_relations"], [])

    def test_nontrivial_choice_set(self):
        from pilot import legal_candidates
        for c in CASES:
            if c["positive_fixture_bridge"]:
                candidates = legal_candidates(c)
                self.assertGreater(len(candidates), 1)
                self.assertTrue(any(not delta(c, pair) for pair in candidates))

    def test_wrong_zone_never_grants_new_relation(self):
        for c in CASES:
            invalid = tuple(c["invalid_fixture_bridge"])
            self.assertFalse(legal_bridge(c, invalid))
            self.assertFalse(delta(c, invalid))
            scored = score_first(c, [invalid])
            self.assertFalse(scored["verified_new_terminal_pairs"])
            self.assertEqual(scored["invalid"], [list(invalid)])

    def test_negative_world_has_no_valid_solution(self):
        c = next(c for c in CASES if c["id"] == "NEGATIVE")
        self.assertIsNone(c["positive_fixture_bridge"])
        self.assertEqual(selftest([c])["cases"][0]["positive_fixture_delta"], [])

    def test_model_false_prediction_is_detected(self):
        c = next(c for c in CASES if c["id"] == "ARCHIVE")
        invalid_score = score_first(c, [("dewarp_east", "tag_west")])
        bogus = score_second(c, invalid_score, [("scan_east_1", "catalog_east")])
        self.assertEqual(bogus["verified_correct_claims"], [])
        self.assertEqual(len(bogus["false_positive_claims"]), 1)

    def test_parsing_does_not_treat_prose_as_edge(self):
        self.assertEqual(_json_object("not JSON"), {})
        self.assertEqual(extract_pairs({"from": "x"}, 2), [])
        self.assertEqual(extract_pairs([["x", "y"], ["x", "y"], "injection"], 2), [("x", "y")])

    def test_fixture_selftest_is_explicitly_not_model_evidence(self):
        result = selftest(CASES)
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["this_is_not_model_evidence"])
        self.assertEqual(result["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
