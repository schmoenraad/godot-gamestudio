import os
import json
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from grade_visual_fixture import png_details  # noqa: E402
from build_release import validate_archive  # noqa: E402
from run_benchmarks import classify_failure, extract_json, grade_routing, harness_command, run_one  # noqa: E402


def write_rgb_png(path: Path, width: int, height: int) -> None:
    rows = []
    colors = [(20, 30, 40), (200, 50, 60), (50, 200, 90), (240, 210, 70), (80, 120, 220)]
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(colors[(x + y) % len(colors)])
        rows.append(bytes(row))
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows)))
    data += chunk(b"IEND", b"")
    path.write_bytes(data)


class BenchmarkToolTests(unittest.TestCase):
    def test_extracts_fenced_json(self):
        self.assertEqual(extract_json('text\n```json\n{"makers": []}\n```')["makers"], [])

    def test_auth_failures_are_inconclusive(self):
        self.assertEqual(classify_failure("401 Invalid Authentication", 1, False), "unavailable_auth")
        self.assertEqual(classify_failure("getaddrinfo ENOTFOUND example.test", None, True), "unavailable_network")
        self.assertEqual(classify_failure("No such file or directory: claude", None, False), "unavailable_harness")
        self.assertEqual(classify_failure("", 0, False), "completed")

    def test_routing_grader_requires_expected_roles_and_qa(self):
        case = {"expected_makers": ["godot-gameplay-engineer"], "expected_reviewers": ["godot-code-reviewer"]}
        response = json.dumps({"makers": ["godot-gameplay-engineer"], "reviewers": ["godot-code-reviewer"], "coordinators": [], "qa": "godot-qa-playtester"})
        self.assertEqual(grade_routing(case, response)["status"], "pass")

    def test_png_decoder_counts_colors(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.png"
            write_rgb_png(path, 8, 4)
            details = png_details(path)
            self.assertEqual((details["width"], details["height"]), (8, 4))
            self.assertEqual(details["unique_colors"], 5)

    def test_claude_plugin_option_does_not_swallow_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            command, _ = harness_command("claude", "PROMPT", root, root, "community", "routing")
            self.assertEqual(command[2], "PROMPT")
            self.assertIn("--tools", command)

    def test_godot_guard_times_out(self):
        env = os.environ.copy()
        env["REAL_GODOT_BIN"] = "/bin/sleep"
        env["GODOT_GUARD_TIMEOUT"] = "1"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "godot_guard.py"), "5"],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 124)

    def test_benchmark_removes_isolated_home(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            def fake_command(*_args):
                home = run_dir / "home"
                home.mkdir(parents=True)
                (home / "temporary-credential").write_text("secret", encoding="utf-8")
                response = '{"makers": [], "reviewers": [], "coordinators": [], "qa": "godot-qa-playtester"}'
                return [sys.executable, "-c", f"print({response!r})"], os.environ.copy()

            with patch("run_benchmarks.harness_command", side_effect=fake_command):
                result = run_one(
                    "codex",
                    "baseline",
                    "routing",
                    {"id": "cleanup", "prompt": "plan", "expected_makers": []},
                    run_dir,
                    10,
                )
            self.assertEqual(result["status"], "completed")
            self.assertFalse((run_dir / "home").exists())

    def test_release_validator_rejects_raw_results(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as value:
                value.writestr("godot-gamestudio/evals/results/run/stdout.log", "raw")
            with self.assertRaises(SystemExit):
                validate_archive(archive)


if __name__ == "__main__":
    unittest.main()
