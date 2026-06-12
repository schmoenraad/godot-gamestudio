import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from select_team import select_team  # noqa: E402


class SmokeEvaluationTests(unittest.TestCase):
    def test_expected_role_routing(self):
        suite = json.loads((ROOT / "evals" / "smoke" / "evals.json").read_text(encoding="utf-8"))
        for case in suite["cases"]:
            with self.subTest(case=case["id"]):
                result = select_team(case["prompt"])
                makers = {item["maker"] for item in result["assignments"]}
                reviewers = {item["reviewer"] for item in result["assignments"]}
                self.assertTrue(set(case.get("expected_makers", [])) <= makers)
                self.assertTrue(set(case.get("expected_reviewers", [])) <= reviewers)
                self.assertTrue(set(case.get("expected_coordinators", [])) <= set(result["coordinators"]))


if __name__ == "__main__":
    unittest.main()
