#!/usr/bin/env python3
"""Compatibility wrapper.

v4 converged architecture uses run_checkpoint_pipeline.py as the only checkpoint entry.
This wrapper is kept for backward compatibility and delegates to v4 pipeline.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Compatibility wrapper for v4 checkpoint pipeline")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--window", choices=["hour", "day"], default="hour")
    ap.add_argument("--audit-jsonl", action="store_true")
    args = ap.parse_args()

    script = Path(__file__).with_name("run_checkpoint_pipeline.py")
    cmd = [
        "python3",
        str(script),
        "--workspace",
        args.workspace,
        "--window",
        args.window,
    ]
    if args.audit_jsonl:
        cmd.append("--audit-jsonl")

    subprocess.run(cmd, check=True)
    print("ok (delegated to v4 pipeline)")


if __name__ == "__main__":
    main()
