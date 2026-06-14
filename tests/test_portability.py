import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install_agents.py"


class PortabilityTests(unittest.TestCase):
    def test_registry_and_generated_agents_match(self):
        roles = json.loads((ROOT / "roles" / "roles.json").read_text(encoding="utf-8"))["roles"]
        self.assertEqual({item["id"] for item in roles}, {path.stem for path in (ROOT / "agents").glob("*.md")})
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_adapters.py"), "--check"], check=True)

    def test_every_maker_has_a_read_only_reviewer(self):
        roles = json.loads((ROOT / "roles" / "roles.json").read_text(encoding="utf-8"))["roles"]
        by_id = {item["id"]: item for item in roles}
        for maker in (item for item in roles if item["kind"] == "maker"):
            reviewer = by_id[maker["reviewer"]]
            self.assertEqual(reviewer["kind"], "reviewer")
            self.assertTrue(reviewer["read_only"])

    def test_all_manifests_agree(self):
        paths = [
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / "gemini-extension.json",
            ROOT / "kimi.plugin.json",
        ]
        manifests = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        self.assertEqual({item["name"] for item in manifests}, {"godot-gamestudio"})
        self.assertEqual(len({item["version"] for item in manifests}), 1)

    def test_project_profiles_for_markdown_harnesses(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "project.godot").write_text("[application]\n", encoding="utf-8")
            for harness in ("claude", "gemini"):
                subprocess.run(
                    [sys.executable, str(INSTALL), str(project), "--harness", harness, "--role", "godot-code-reviewer"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                profile = project / f".{harness}" / "agents" / "godot-code-reviewer.md"
                self.assertIn("name: godot-code-reviewer", profile.read_text(encoding="utf-8"))


class GodotVisualFixtureTests(unittest.TestCase):
    def find_godot(self) -> str | None:
        candidates = [
            os.environ.get("GODOT_BIN"),
            shutil.which("godot4"),
            shutil.which("godot"),
            "/Applications/Godot.app/Contents/MacOS/Godot",
        ]
        return next((value for value in candidates if value and Path(value).is_file()), None)

    def test_headless_fixture_creates_nonempty_png(self):
        godot = self.find_godot()
        if not godot:
            self.skipTest("Godot executable not available")
        fixture = ROOT / "tests" / "fixtures" / "2d-visual"
        output = fixture / "artifacts" / "smoke.png"
        output.unlink(missing_ok=True)
        result = subprocess.run(
            [godot, "--headless", "--path", str(fixture), "--editor", "--quit-after", "3"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run(
            [godot, "--headless", "--path", str(fixture)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = output.read_bytes()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (320, 180))
        self.assertGreater(len(data), 500)


if __name__ == "__main__":
    unittest.main()
