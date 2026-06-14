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

    def record_evidence(self, verdict: str = "pass"):
        (self.project / "run.log").write_text("runtime evidence\n", encoding="utf-8")
        self.run_state(
            "evidence", str(self.project), "--criterion", "c1",
            "--actor", "godot-qa-playtester", "--kind", "runtime",
            "--path", "run.log", "--verdict", verdict,
            "--summary", "Movement observed",
        )

    def test_inconclusive_evidence_cannot_pass(self):
        self.start_valid_milestone()
        self.record_evidence("inconclusive")
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result["status"], "needs_revision")
        self.assertTrue(result["failures"])

    def test_complete_reviewed_and_verified_milestone_passes(self):
        self.start_valid_milestone()
        self.record_evidence()
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result, {"status": "passed", "failures": []})

    def test_changed_evidence_cannot_pass(self):
        self.start_valid_milestone()
        self.record_evidence()
        (self.project / "run.log").write_text("tampered\n", encoding="utf-8")
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result["status"], "needs_revision")
        self.assertTrue(any("changed after recording" in item for item in result["failures"]))

    def test_artifact_change_invalidates_prior_approval(self):
        self.start_valid_milestone()
        self.run_state("complete-deliverable", str(self.project), "--id", "player")
        self.record_evidence()
        result = self.run_state("assess", str(self.project))
        self.assertTrue(any("changed after its final review" in item for item in result["failures"]))

    def test_reviewer_brief_is_scoped_and_independent(self):
        self.start_valid_milestone()
        result = self.run_state("brief", str(self.project), "--phase", "reviewer", "--deliverable", "player")
        self.assertEqual(result["role"], "godot-code-reviewer")
        self.assertEqual(result["deliverable"]["paths"], ["scripts/player.gd"])
        self.assertIn("Do not edit files or use maker reasoning", result["instruction"])
        self.assertNotIn("reviews", result)

    def test_revision_exhaustion_blocks(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Map", "--request", "build a map", "--criterion", "Map is traversable")
        self.run_state("revision", str(self.project))
        self.run_state("revision", str(self.project))
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result["status"], "blocked")

    def test_resolved_blocker_no_longer_blocks_pass(self):
        self.start_valid_milestone()
        self.run_state("block", str(self.project), "--reason", "Awaiting a decision")
        self.run_state("resolve-blocker", str(self.project), "--id", "b1", "--resolution", "Decision received")
        self.record_evidence()
        result = self.run_state("assess", str(self.project))
        self.assertEqual(result, {"status": "passed", "failures": []})

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

    def test_unsafe_owned_path_is_rejected(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Path", "--request", "implement scripts", "--criterion", "Scripts work")
        result = subprocess.run(
            [sys.executable, str(STATE), "add-deliverable", str(self.project), "--id", "escape", "--owner", "godot-gameplay-engineer", "--reviewer", "godot-code-reviewer", "--path", "../outside.gd"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("project-relative", result.stderr)

    def test_wrong_reviewer_pairing_is_rejected(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Pair", "--request", "implement scripts", "--criterion", "Scripts work")
        result = subprocess.run(
            [sys.executable, str(STATE), "add-deliverable", str(self.project), "--id", "bad", "--owner", "godot-gameplay-engineer", "--reviewer", "godot-systems-critic", "--path", "scripts/player.gd"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected reviewer godot-code-reviewer", result.stderr)

    def test_schema_one_state_migrates_without_losing_milestone(self):
        self.run_state("init", str(self.project))
        self.run_state("start", str(self.project), "--title", "Legacy", "--request", "implement scripts", "--criterion", "Scripts work")
        path = self.project / ".godot-gamestudio" / "studio.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["schema_version"] = 1
        state["current_milestone"]["blockers"] = ["Legacy blocker"]
        path.write_text(json.dumps(state), encoding="utf-8")
        self.run_state("set-constraint", str(self.project), "--key", "platform", "--value", "desktop")
        migrated = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["current_milestone"]["title"], "Legacy")
        self.assertEqual(migrated["current_milestone"]["blockers"][0]["reason"], "Legacy blocker")


if __name__ == "__main__":
    unittest.main()
