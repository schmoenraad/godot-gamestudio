#!/usr/bin/env python3
"""Run Godot with a hard timeout so benchmark agents cannot leave it hanging."""

from __future__ import annotations

import os
import signal
import subprocess
import sys


def main() -> None:
    executable = os.environ.get("REAL_GODOT_BIN")
    if not executable:
        raise SystemExit("REAL_GODOT_BIN is not set")
    timeout = int(os.environ.get("GODOT_GUARD_TIMEOUT", "45"))
    process = subprocess.Popen([executable, *sys.argv[1:]], start_new_session=True)
    try:
        return_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        print(f"Godot guard: command exceeded {timeout} seconds", file=sys.stderr)
        raise SystemExit(124)
    raise SystemExit(return_code)


if __name__ == "__main__":
    main()
