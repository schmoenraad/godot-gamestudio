import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from inspect_project import inspect  # noqa: E402


class ProjectInspectionTests(unittest.TestCase):
    def test_collects_orchestration_context(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "project.godot").write_text(
                '[application]\nconfig/name="Fixture"\nrun/main_scene="res://main.tscn"\n'
                '[display]\nwindow/size/viewport_width=320\n'
                'window/size/viewport_height=180\n'
                '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
                '[input]\nmove_left={\n"deadzone": 0.5\n}\n',
                encoding="utf-8",
            )
            (project / "main.tscn").write_text("[gd_scene]\n", encoding="utf-8")
            (project / "scripts").mkdir()
            (project / "scripts" / "player.gd").write_text("extends Node\n", encoding="utf-8")
            (project / "addons" / "godotiq").mkdir(parents=True)
            result = inspect(project)
            self.assertEqual(result["name"], "Fixture")
            self.assertEqual(result["viewport"]["width"], 320)
            self.assertEqual(result["input_actions"], ["move_left"])
            self.assertEqual(result["file_counts"]["scenes"], 1)
            self.assertEqual(result["languages"], ["GDScript"])
            self.assertTrue(result["godotiq"]["detected"])


if __name__ == "__main__":
    unittest.main()
