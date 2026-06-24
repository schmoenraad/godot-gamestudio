#!/usr/bin/env python3
"""Normalize a generated sprite sheet into fixed Godot-ready cells."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

from grade_sprite_sheet import MAGENTA, decode_png, is_background


Pixel = tuple[int, int, int, int]


def encode_rgba_png(path: Path, width: int, height: int, pixels: list[list[Pixel]]) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    rows = [bytes([0]) + b"".join(bytes(pixel) for pixel in row) for row in pixels]
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows)))
    data += chunk(b"IEND", b"")
    path.write_bytes(data)


def crop_bounds(
    pixels: list[list[Pixel]],
    left: int,
    top: int,
    width: int,
    height: int,
    tolerance: int,
) -> tuple[int, int, int, int] | None:
    points: list[tuple[int, int]] = []
    for y in range(top, top + height):
        for x in range(left, left + width):
            if not is_background(pixels[y][x], tolerance):
                points.append((x, y))
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def copy_crop(pixels: list[list[Pixel]], bounds: tuple[int, int, int, int], tolerance: int) -> list[list[Pixel]]:
    left, top, right, bottom = bounds
    cropped: list[list[Pixel]] = []
    for y in range(top, bottom + 1):
        row: list[Pixel] = []
        for x in range(left, right + 1):
            pixel = pixels[y][x]
            row.append((*MAGENTA, 255) if is_background(pixel, tolerance) else pixel)
        cropped.append(row)
    return cropped


def resize_nearest(source: list[list[Pixel]], width: int, height: int) -> list[list[Pixel]]:
    source_height = len(source)
    source_width = len(source[0])
    resized: list[list[Pixel]] = []
    for y in range(height):
        source_y = min(source_height - 1, int(y * source_height / height))
        row: list[Pixel] = []
        for x in range(width):
            source_x = min(source_width - 1, int(x * source_width / width))
            row.append(source[source_y][source_x])
        resized.append(row)
    return resized


def normalize(
    input_path: Path,
    output_path: Path,
    rows: int,
    cols: int,
    cell_size: int,
    margin: int,
    tolerance: int,
) -> dict[str, Any]:
    width, height, pixels = decode_png(input_path)
    if width % cols or height % rows:
        raise ValueError(f"image size {width}x{height} is not divisible by grid {cols}x{rows}")

    source_cell_width = width // cols
    source_cell_height = height // rows
    output_width = cols * cell_size
    output_height = rows * cell_size
    canvas: list[list[Pixel]] = [[(*MAGENTA, 255) for _x in range(output_width)] for _y in range(output_height)]
    cells: list[dict[str, Any]] = []

    for row_index in range(rows):
        for col_index in range(cols):
            left = col_index * source_cell_width
            top = row_index * source_cell_height
            bounds = crop_bounds(pixels, left, top, source_cell_width, source_cell_height, tolerance)
            cell_record: dict[str, Any] = {"row": row_index, "col": col_index, "found_content": bounds is not None}
            if bounds is None:
                cells.append(cell_record)
                continue

            crop = copy_crop(pixels, bounds, tolerance)
            crop_width = len(crop[0])
            crop_height = len(crop)
            max_width = cell_size - margin * 2
            max_height = cell_size - margin * 2
            scale = min(max_width / crop_width, max_height / crop_height, 1.0)
            target_width = max(1, round(crop_width * scale))
            target_height = max(1, round(crop_height * scale))
            resized = resize_nearest(crop, target_width, target_height)
            paste_x = col_index * cell_size + (cell_size - target_width) // 2
            paste_y = row_index * cell_size + cell_size - margin - target_height
            for y in range(target_height):
                for x in range(target_width):
                    canvas[paste_y + y][paste_x + x] = resized[y][x]

            cell_record.update({
                "source_bounds": {"x": bounds[0] - left, "y": bounds[1] - top, "w": crop_width, "h": crop_height},
                "output_bounds": {"x": paste_x - col_index * cell_size, "y": paste_y - row_index * cell_size, "w": target_width, "h": target_height},
                "scale": round(scale, 4),
            })
            cells.append(cell_record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    encode_rgba_png(output_path, output_width, output_height, canvas)
    return {
        "status": "pass" if all(cell["found_content"] for cell in cells) else "fail",
        "input": str(input_path),
        "output": str(output_path),
        "rows": rows,
        "cols": cols,
        "source_cell_width": source_cell_width,
        "source_cell_height": source_cell_height,
        "cell_size": cell_size,
        "margin": margin,
        "background_tolerance": tolerance,
        "cells": cells,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--cell-size", type=int, default=32)
    parser.add_argument("--margin", type=int, default=2)
    parser.add_argument("--background-tolerance", type=int, default=64)
    args = parser.parse_args()
    try:
        report = normalize(
            Path(args.input).resolve(),
            Path(args.output).resolve(),
            args.rows,
            args.cols,
            args.cell_size,
            args.margin,
            args.background_tolerance,
        )
    except Exception as error:
        print(json.dumps({"status": "fail", "error": str(error)}, indent=2))
        sys.exit(1)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
