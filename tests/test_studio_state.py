import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "scripts" / "studio_state.py"
INSTALL = ROOT / "scripts" / "install_agents.py"


class StudioStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        (self.project / "project.godot").write_text("[application]\nconfig/name=\"Fixture\"\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_state(self, *args: str) -> dict | None:
        result = subprocess.run([sys.executable, str(STATE), *args], check=True, capture_output=True, text=True)
        return json.loads(result.stdout) if result.stdout.strip().startswith("{") else None

    def start_valid_milestone(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Player movement", "--request", "implement player movement", "--criterion", "Player moves after input")
        self.run_state("add-deliverable", str(self.project), "--id", "player", "--owner", "godot-gameplay-engineer", "--reviewer", "godot-code-reviewer", "--path", "scripts/player.gd")
        self.run_state("complete-deliverable", str(self.project), "--id", "player")
        self.run_state("review", str(self.project), "--deliverable", "player", "--reviewer", "godot-code-reviewer", "--verdict", "approved", "--summary", "No blocking findings")

    def test_inconclusive_evidence_cannot_pass(self):
        self.start_valid_milestone()
        self.run_state("evidence", str(self.project), "--criterion", "c1", "--kind", "runtime", "--path", "run.log", "--verdict", "inconclusive", "--summary", "Runner unavailable")
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result["status"], "needs_revision")
        self.assertTrue(result["failures"])

    def test_complete_reviewed_and_verified_milestone_passes(self):
        self.start_valid_milestone()
        self.run_state("evidence", str(self.project), "--criterion", "c1", "--kind", "runtime", "--path", "run.log", "--verdict", "pass", "--summary", "Movement observed")
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result, {"status": "passed", "failures": []})

    def test_revision_exhaustion_blocks(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Map", "--request", "build a map", "--criterion", "Map is traversable")
        self.run_state("revision", str(self.project))
        self.run_state("revision", str(self.project))
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result["status"], "blocked")

    def test_agent_installer_refuses_overwrite(self):
        subprocess.run([sys.executable, str(INSTALL), str(self.project), "--role", "godot-game-designer"], check=True, capture_output=True, text=True)
        second = subprocess.run([sys.executable, str(INSTALL), str(self.project), "--role", "godot-game-designer"], capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        profile = (self.project / ".codex" / "agents" / "godot-game-designer.toml").read_text(encoding="utf-8")
        self.assertIn("[[skills.config]]", profile)

    def test_overlapping_deliverable_paths_are_rejected(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Overlap", "--request", "implement scripts", "--criterion", "Scripts work")
        self.run_state("add-deliverable", str(self.project), "--id", "one", "--owner", "godot-gameplay-engineer", "--reviewer", "godot-code-reviewer", "--path", "scripts/player")
        result = subprocess.run(
            [sys.executable, str(STATE), "add-deliverable", str(self.project), "--id", "two", "--owner", "godot-gameplay-engineer", "--reviewer", "godot-code-reviewer", "--path", "scripts/player/controller.gd"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Path ownership conflict", result.stderr)


if __name__ == "__main__":
    unittest.main()
