#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--topk", type=int, default=5)
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    memory_md = ws / "MEMORY.md"
    decisions = ws / "memory" / "decisions.jsonl"
    task_queue = ws / "TASK_QUEUE.md"

    text = memory_md.read_text(encoding="utf-8", errors="replace") if memory_md.exists() else ""
    decision_text = decisions.read_text(encoding="utf-8", errors="replace") if decisions.exists() else ""

    tasks = []
    if text.count("Hybrid Checkpoint") > 3:
        tasks.append("清理 MEMORY.md 中历史 checkpoint 噪音，只保留长期结论")
    if "risk" in decision_text.lower() or "风险" in decision_text:
        tasks.append("为高风险决策增加 review 字段与回滚策略")
    if len(decision_text.splitlines()) > 200:
        tasks.append("按月归档 decisions.jsonl，并维护索引文件")
    tasks.append("检查 QMD scope 是否仍为 direct-only + 最小路径白名单")
    tasks.append("审计 TASK_QUEUE 已完成项并清理过期任务")

    today = datetime.now().strftime("%Y-%m-%d")
    if not task_queue.exists():
        task_queue.write_text("# TASK_QUEUE\n\n> 由 checkpoint 与 nightly analysis 自动维护\n\n", encoding="utf-8")

    with task_queue.open("a", encoding="utf-8") as f:
        f.write(f"\n## {today} nightly deep analysis\n")
        for t in tasks[: args.topk]:
            f.write(f"- [ ] {t}\n")

    print("ok")


if __name__ == "__main__":
    main()
