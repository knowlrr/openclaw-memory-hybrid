#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--topk", type=int, default=5)
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    hub = ws / ".memory_hub"
    memory_md = hub / "MEMORY.md"
    decisions_dir = hub / "life" / "decisions"
    task_queue = hub / "TASK_QUEUE.md"

    text = memory_md.read_text(encoding="utf-8", errors="replace") if memory_md.exists() else ""

    decision_payloads = []
    if decisions_dir.exists():
        for p in sorted(decisions_dir.glob("dec_*.json")):
            try:
                decision_payloads.append(json.loads(p.read_text(encoding="utf-8", errors="replace")))
            except Exception:
                continue

    tasks = []
    if text.count("Hybrid Checkpoint") > 3:
        tasks.append("清理 MEMORY.md 中历史 checkpoint 噪音，只保留长期结论")
    if any("risk" in str(d).lower() or "风险" in str(d) for d in decision_payloads):
        tasks.append("为高风险决策增加 review 字段与回滚策略")
    if len(decision_payloads) > 200:
        tasks.append("按月归档 life/decisions/*.json，并维护 decision 索引")
    tasks.append("检查 QMD scope 是否仍为 direct-only + 最小路径白名单")
    tasks.append("审计 TASK_QUEUE 已完成项并清理过期任务")

    today = datetime.now().strftime("%Y-%m-%d")
    hub.mkdir(parents=True, exist_ok=True)
    if not task_queue.exists():
        task_queue.write_text("# TASK_QUEUE\n\n> 由 checkpoint 与 nightly analysis 自动维护\n\n", encoding="utf-8")

    with task_queue.open("a", encoding="utf-8") as f:
        f.write(f"\n## {today} nightly deep analysis\n")
        for t in tasks[: args.topk]:
            f.write(f"- [ ] {t}\n")

    print("ok")


if __name__ == "__main__":
    main()
