#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

from context_extractor import extract_context


def append(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def safe_name(text: str, n: int = 36) -> str:
    s = re.sub(r"[^\w\-\u4e00-\u9fff]+", "_", text.strip())
    return s[:n].strip("_") or "decision"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--input-file")
    ap.add_argument("--max-lines", type=int, default=250)
    ap.add_argument("--audit-jsonl", action="store_true", help="also append decisions/checkpoints jsonl logs")
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    hub = ws / ".memory_hub"
    raw_memory_dir = hub / "memory"
    life_dir = hub / "life"
    decisions_dir = life_dir / "decisions"
    archives_dir = life_dir / "archives"

    for d in (hub, raw_memory_dir, life_dir, decisions_dir, archives_dir):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(hub, 0o700)
    os.chmod(raw_memory_dir, 0o700)

    memory_md = hub / "MEMORY.md"
    if not memory_md.exists():
        memory_md.write_text("# MEMORY\n\n", encoding="utf-8")
        os.chmod(memory_md, 0o600)

    index_path = hub / "MEMORY_INDEX.md"
    if not index_path.exists():
        index_path.write_text("# MEMORY_INDEX\n\n", encoding="utf-8")
        os.chmod(index_path, 0o600)

    task_queue = hub / "TASK_QUEUE.md"
    if not task_queue.exists():
        task_queue.write_text("# TASK_QUEUE\n\n> 由 checkpoint 与 nightly analysis 自动维护\n\n", encoding="utf-8")
        os.chmod(task_queue, 0o600)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = Path(args.input_file).expanduser() if args.input_file else raw_memory_dir / f"{today}.md"
    if daily.exists():
        lines = daily.read_text(encoding="utf-8", errors="replace").splitlines()
        context = "\n".join(lines[-args.max_lines :])
    else:
        context = ""

    result = extract_context(context)
    ts = result["timestamp"]
    extracted = result.get("extracted") or {}

    # write per-decision JSON files (memory-hub aligned)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, item in enumerate(extracted.get("decisions", [])[:20], start=1):
        row = {
            "ts": ts,
            "type": "decision",
            "decision": item,
            "source": result.get("source", "unknown"),
            "status": "open",
            "feedback": [],
        }
        fname = f"dec_{stamp}_{i:02d}_{safe_name(str(item))}.json"
        p = decisions_dir / fname
        p.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(p, 0o600)

    if args.audit_jsonl:
        checkpoints = raw_memory_dir / "checkpoints.jsonl"
        append(checkpoints, json.dumps(result, ensure_ascii=False) + "\n")
        os.chmod(checkpoints, 0o600)

        decisions_jsonl = raw_memory_dir / "decisions.jsonl"
        for item in extracted.get("decisions", [])[:20]:
            row = {"ts": ts, "type": "decision", "decision": item, "source": result.get("source", "unknown")}
            append(decisions_jsonl, json.dumps(row, ensure_ascii=False) + "\n")
        if decisions_jsonl.exists():
            os.chmod(decisions_jsonl, 0o600)

    summary_keys = ["achievements", "decisions", "issues", "next_steps"]
    for k in summary_keys:
        for item in extracted.get(k, [])[:3]:
            append(index_path, f"- [{today}] {k}: {str(item)[:180]}\n")

    if extracted.get("next_steps"):
        append(task_queue, f"\n## {today} checkpoint\n")
        for task in extracted["next_steps"][:10]:
            append(task_queue, f"- [ ] {task}\n")

    print("ok")


if __name__ == "__main__":
    main()
