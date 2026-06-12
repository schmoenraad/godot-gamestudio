import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from select_team import select_team  # noqa: E402


class TeamSelectionTests(unittest.TestCase):
    def makers(self, request: str) -> set[str]:
        return {item["maker"] for item in select_team(request)["assignments"]}

    def test_routes_core_domains(self):
        cases = {
            "write a branching quest and dialogue": "godot-narrative-designer",
            "build a tilemap dungeon level": "godot-world-builder",
            "generate an animated player sprite sheet": "godot-sprite-studio",
            "implement a typed GDScript player controller": "godot-gameplay-engineer",
            "design a controller-friendly HUD": "godot-ui-ux-designer",
            "debug this crash": "godot-gameplay-engineer",
        }
        for request, expected in cases.items():
            with self.subTest(request=request):
                self.assertIn(expected, self.makers(request))

    def test_mixed_creative_work_adds_director_and_respects_limit(self):
        result = select_team("write a quest, build its map, create sprites, and implement the scripts")
        self.assertIn("godot-creative-director", result["coordinators"])
        makers = {item["maker"] for item in result["assignments"]}
        self.assertIn("godot-gameplay-engineer", makers)
        self.assertTrue(all(len(wave["agents"]) <= 4 for wave in result["execution_waves"]))

    def test_animation_uses_animation_reviewer(self):
        result = select_team("create an animated sprite sheet")
        assignment = next(item for item in result["assignments"] if item["maker"] == "godot-sprite-studio")
        self.assertEqual(assignment["reviewer"], "godot-animation-reviewer")


if __name__ == "__main__":
    unittest.main()
