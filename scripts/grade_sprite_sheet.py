#!/usr/bin/env python3
"""Grade a generated sprite sheet for game-ready grid and anchor consistency."""

from __future__ import annotations

import argparse
import json
import statistics
import struct
import zlib
from pathlib import Path
from typing import Any


MAGENTA = (255, 0, 255)


def decode_png(path: Path) -> tuple[int, int, list[list[tuple[int, int, int, int]]]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    if depth != 8 or color_type not in {2, 6}:
        raise ValueError(f"unsupported PNG depth/type: {depth}/{color_type}")
    channels = 3 if color_type == 2 else 4
    chunks: list[bytes] = []
    position = 8
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        if kind == b"IDAT":
            chunks.append(payload)
        position += 12 + length
    raw = zlib.decompress(b"".join(chunks))
    stride = width * channels
    previous = bytearray(stride)
    rows: list[list[tuple[int, int, int, int]]] = []
    offset = 0
    for _y in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride
        for index in range(stride):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 255
            elif filter_type == 2:
                row[index] = (row[index] + up) & 255
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
                row[index] = (row[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
        pixels = []
        for index in range(0, stride, channels):
            if channels == 3:
                pixels.append((row[index], row[index + 1], row[index + 2], 255))
            else:
                pixels.append((row[index], row[index + 1], row[index + 2], row[index + 3]))
        rows.append(pixels)
        previous = row
    return width, height, rows


def is_background(pixel: tuple[int, int, int, int], tolerance: int) -> bool:
    red, green, blue, alpha = pixel
    if alpha <= 8:
        return True
    return (
        abs(red - MAGENTA[0]) <= tolerance
        and abs(green - MAGENTA[1]) <= tolerance
        and abs(blue - MAGENTA[2]) <= tolerance
    )


def cell_bounds(
    pixels: list[list[tuple[int, int, int, int]]],
    left: int,
    top: int,
    width: int,
    height: int,
    tolerance: int,
) -> dict[str, Any]:
    points = []
    colors = set()
    for y in range(top, top + height):
        for x in range(left, left + width):
            pixel = pixels[y][x]
            if not is_background(pixel, tolerance):
                points.append((x - left, y - top))
                colors.add(pixel[:3])
    if not points:
        return {"content_pixels": 0, "unique_colors": 0}
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "content_pixels": len(points),
        "unique_colors": len(colors),
        "x": min(xs),
        "y": min(ys),
        "w": max(xs) - min(xs) + 1,
        "h": max(ys) - min(ys) + 1,
        "center_x": (min(xs) + max(xs)) / 2,
        "foot_y": max(ys),
        "touches_edge": min(xs) == 0 or min(ys) == 0 or max(xs) == width - 1 or max(ys) == height - 1,
    }


def max_relative_drift(values: list[float]) -> float:
    median = statistics.median(values)
    if median == 0:
        return 0
    return max(abs(value - median) / median for value in values)


def max_absolute_drift(values: list[float]) -> float:
    median = statistics.median(values)
    return max(abs(value - median) for value in values)


def grade(path: Path, rows: int, cols: int, tolerance: int, max_scale_drift: float, max_anchor_drift: float) -> dict[str, Any]:
    width, height, pixels = decode_png(path)
    checks = []
    checks.append({"id": "grid-divides-image", "passed": width % cols == 0 and height % rows == 0, "width": width, "height": height})
    if width % cols or height % rows:
        return {"status": "fail", "checks": checks, "path": str(path)}
    cell_width = width // cols
    cell_height = height // rows
    corners = [pixels[0][0], pixels[0][-1], pixels[-1][0], pixels[-1][-1]]
    checks.append({"id": "magenta-corners", "passed": all(is_background(pixel, tolerance) for pixel in corners)})
    cells = []
    for row in range(rows):
        for col in range(cols):
            cells.append(cell_bounds(pixels, col * cell_width, row * cell_height, cell_width, cell_height, tolerance))
    missing = [index for index, cell in enumerate(cells) if not cell.get("content_pixels")]
    checks.append({"id": "all-cells-contain-sprites", "passed": not missing, "missing_cells": missing})
    populated = [cell for cell in cells if cell.get("content_pixels")]
    if populated:
        edge_cells = [index for index, cell in enumerate(cells) if cell.get("touches_edge")]
        checks.append({"id": "no-cell-edge-contact", "passed": not edge_cells, "edge_cells": edge_cells})
        scale_drift = max(max_relative_drift([cell["w"] for cell in populated]), max_relative_drift([cell["h"] for cell in populated]))
        checks.append({"id": "scale-drift", "passed": scale_drift <= max_scale_drift, "value": round(scale_drift, 3), "limit": max_scale_drift})
        center_drift = max_absolute_drift([cell["center_x"] for cell in populated])
        foot_drift = max_absolute_drift([cell["foot_y"] for cell in populated])
        checks.append({
            "id": "anchor-drift",
            "passed": center_drift <= max_anchor_drift and foot_drift <= max_anchor_drift,
            "center_drift_px": round(center_drift, 2),
            "foot_drift_px": round(foot_drift, 2),
            "limit_px": max_anchor_drift,
        })
        checks.append({"id": "minimum-color-range", "passed": max(cell["unique_colors"] for cell in populated) >= 2})
    else:
        checks.extend([
            {"id": "no-cell-edge-contact", "passed": False, "edge_cells": []},
            {"id": "scale-drift", "passed": False},
            {"id": "anchor-drift", "passed": False},
            {"id": "minimum-color-range", "passed": False},
        ])
    return {
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "path": str(path),
        "rows": rows,
        "cols": cols,
        "cell_width": cell_width,
        "cell_height": cell_height,
        "cells": cells,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sheet")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--background-tolerance", type=int, default=8)
    parser.add_argument("--max-scale-drift", type=float, default=0.2)
    parser.add_argument("--max-anchor-drift", type=float, default=3.0)
    args = parser.parse_args()
    print(json.dumps(grade(
        Path(args.sheet).resolve(),
        args.rows,
        args.cols,
        args.background_tolerance,
        args.max_scale_drift,
        args.max_anchor_drift,
    ), indent=2))


if __name__ == "__main__":
    main()
