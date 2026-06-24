import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "scripts" / "normalize_sprite_sheet.py"
GRADER = ROOT / "scripts" / "grade_sprite_sheet.py"


def write_rgba_png(path: Path, width: int, height: int, pixels: list[list[tuple[int, int, int, int]]]) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    rows = [bytes([0]) + b"".join(bytes(pixel) for pixel in row) for row in pixels]
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows)))
    data += chunk(b"IEND", b"")
    path.write_bytes(data)


def make_noisy_magenta_sheet(path: Path) -> None:
    width, height = 128, 128
    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append((255, (x + y) % 24, 248 + (x % 8), 255))
        pixels.append(row)

    for row in range(2):
        for col in range(2):
            left = col * 64 + 24
            top = row * 64 + 18
            for y in range(top, top + 32):
                for x in range(left, left + 16):
                    pixels[y][x] = (15, 25 + row * 20, 80 + col * 30, 255)
            pixels[top][left] = (245, 220, 90, 255)
    write_rgba_png(path, width, height, pixels)


class SpriteNormalizerTests(unittest.TestCase):
    def test_normalizes_noisy_magenta_background_to_gradeable_sheet(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.png"
            normalized = Path(temp) / "normalized.png"
            make_noisy_magenta_sheet(raw)

            normalize_result = subprocess.run(
                [
                    sys.executable,
                    str(NORMALIZER),
                    str(raw),
                    str(normalized),
                    "--rows",
                    "2",
                    "--cols",
                    "2",
                    "--cell-size",
                    "32",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(normalize_result.stdout)["status"], "pass")

            grade_result = subprocess.run(
                [sys.executable, str(GRADER), str(normalized), "--rows", "2", "--cols", "2"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(grade_result.stdout)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
