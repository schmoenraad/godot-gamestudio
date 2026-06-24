import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRADER = ROOT / "scripts" / "grade_sprite_sheet.py"


def write_rgba_png(path: Path, width: int, height: int, pixels: list[list[tuple[int, int, int, int]]]) -> None:
    rows = [bytes([0]) + b"".join(bytes(pixel) for pixel in row) for row in pixels]

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows)))
    data += chunk(b"IEND", b"")
    path.write_bytes(data)


def make_sheet(path: Path, drift: bool = False, edge_touch: bool = False) -> None:
    width, height = 64, 64
    pixels = [[(255, 0, 255, 255) for _x in range(width)] for _y in range(height)]
    for row in range(2):
        for col in range(2):
            left = col * 32 + (0 if edge_touch and row == 0 and col == 0 else 10)
            top = row * 32 + 10
            sprite_width = 12 if not (drift and row == 1 and col == 1) else 22
            sprite_height = 16
            for y in range(top, top + sprite_height):
                for x in range(left, left + sprite_width):
                    pixels[y][x] = (20 + row * 30, 30 + col * 40, 80, 255)
            pixels[top][left] = (240, 220, 90, 255)
    write_rgba_png(path, width, height, pixels)


class SpriteGraderTests(unittest.TestCase):
    def run_grader(self, path: Path) -> dict:
        result = subprocess.run(
            [sys.executable, str(GRADER), str(path), "--rows", "2", "--cols", "2"],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_accepts_consistent_sheet(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sheet.png"
            make_sheet(path)
            self.assertEqual(self.run_grader(path)["status"], "pass")

    def test_rejects_scale_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sheet.png"
            make_sheet(path, drift=True)
            result = self.run_grader(path)
            self.assertEqual(result["status"], "fail")
            self.assertFalse(next(check for check in result["checks"] if check["id"] == "scale-drift")["passed"])

    def test_rejects_edge_contact(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sheet.png"
            make_sheet(path, edge_touch=True)
            result = self.run_grader(path)
            self.assertEqual(result["status"], "fail")
            self.assertFalse(next(check for check in result["checks"] if check["id"] == "no-cell-edge-contact")["passed"])


if __name__ == "__main__":
    unittest.main()
