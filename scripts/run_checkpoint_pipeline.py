#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--input-file")
    ap.add_argument("--max-lines", type=int, default=250)
    ap.add_argument("--window", choices=["hour", "day"], default="hour")
    ap.add_argument("--audit-jsonl", action="store_true", help="append-only audit logs")
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    hub = ws / ".memory_hub"
    raw_memory_dir = hub / "memory"
    life_dir = hub / "life"
    decisions_dir = life_dir / "decisions"
    archives_dir = life_dir / "archives"
    state_file = hub / "state.json"

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

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")
    window_key = f"checkpoint:{today}:{hour}" if args.window == "hour" else f"checkpoint:{today}"

    state = load_state(state_file)
    if state.get("last_checkpoint_window") == window_key:
        print("skipped (idempotent)")
        return

    # v4 unified source: workspace/memory/YYYY-MM-DD.md
    default_daily = ws / "memory" / f"{today}.md"
    daily = Path(args.input_file).expanduser() if args.input_file else default_daily
    if daily.exists():
        lines = daily.read_text(encoding="utf-8", errors="replace").splitlines()
        context = "\n".join(lines[-args.max_lines :])
    else:
        context = ""

    result = extract_context(context)
    ts = result["timestamp"]
    extracted = result.get("extracted") or {}

    stamp = now.strftime("%Y%m%d_%H%M%S")
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
        audit = dict(result)
        audit["idempotency_key"] = window_key
        append(checkpoints, json.dumps(audit, ensure_ascii=False) + "\n")
        os.chmod(checkpoints, 0o600)

    summary_keys = ["achievements", "decisions", "issues", "next_steps"]
    seen_hashes = set(state.get("index_hashes", []))
    new_hashes = []
    for k in summary_keys:
        for item in extracted.get(k, [])[:3]:
            line = f"- [{today}] {k}: {str(item)[:180]}"
            h = hashlib.sha1(line.encode("utf-8")).hexdigest()
            if h in seen_hashes:
                continue
            append(index_path, line + "\n")
            new_hashes.append(h)

    existing_task_hashes = set(state.get("task_hashes", []))
    task_lines = []
    for task in extracted.get("next_steps", [])[:10]:
        t = str(task).strip()
        if not t:
            continue
        h = hashlib.sha1(t.encode("utf-8")).hexdigest()
        if h in existing_task_hashes:
            continue
        task_lines.append(t)
        existing_task_hashes.add(h)

    if task_lines:
        append(task_queue, f"\n## {today} checkpoint\n")
        for t in task_lines:
            append(task_queue, f"- [ ] {t}\n")

    state["last_checkpoint_window"] = window_key
    state["last_checkpoint_ts"] = ts
    state["index_hashes"] = (list(seen_hashes) + new_hashes)[-500:]
    state["task_hashes"] = list(existing_task_hashes)[-1000:]
    save_state(state_file, state)

    print("ok")


if __name__ == "__main__":
    main()
