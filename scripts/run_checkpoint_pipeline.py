#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from context_extractor import extract_context


def append(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--input-file")
    ap.add_argument("--max-lines", type=int, default=250)
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    memory_dir = ws / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(memory_dir, 0o700)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = Path(args.input_file).expanduser() if args.input_file else memory_dir / f"{today}.md"
    if daily.exists():
        lines = daily.read_text(encoding="utf-8", errors="replace").splitlines()
        context = "\n".join(lines[-args.max_lines :])
    else:
        context = ""

    result = extract_context(context)
    ts = result["timestamp"]

    checkpoints = memory_dir / "checkpoints.jsonl"
    append(checkpoints, json.dumps(result, ensure_ascii=False) + "\n")
    os.chmod(checkpoints, 0o600)

    extracted = result.get("extracted") or {}

    decisions_path = memory_dir / "decisions.jsonl"
    for item in extracted.get("decisions", [])[:20]:
        row = {
            "ts": ts,
            "type": "decision",
            "decision": item,
            "source": result.get("source", "unknown"),
        }
        append(decisions_path, json.dumps(row, ensure_ascii=False) + "\n")
    if decisions_path.exists():
        os.chmod(decisions_path, 0o600)

    index_path = memory_dir / "MEMORY_INDEX.md"
    if not index_path.exists():
        index_path.write_text("# MEMORY_INDEX\n\n", encoding="utf-8")
        os.chmod(index_path, 0o600)

    summary_keys = ["achievements", "decisions", "issues", "next_steps"]
    for k in summary_keys:
        for item in extracted.get(k, [])[:3]:
            append(index_path, f"- [{today}] {k}: {str(item)[:180]}\n")

    task_queue = ws / "TASK_QUEUE.md"
    if not task_queue.exists():
        task_queue.write_text("# TASK_QUEUE\n\n> 由 checkpoint 与 nightly analysis 自动维护\n\n", encoding="utf-8")

    if extracted.get("next_steps"):
        append(task_queue, f"\n## {today} checkpoint\n")
        for task in extracted["next_steps"][:10]:
            append(task_queue, f"- [ ] {task}\n")

    print("ok")


if __name__ == "__main__":
    main()
