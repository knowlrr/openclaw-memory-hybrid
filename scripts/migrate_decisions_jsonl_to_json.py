#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


def safe_name(text: str, n: int = 36) -> str:
    # force ASCII-safe slug for cross-platform compatibility
    raw = (text or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "_", raw)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:n] or "decision"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--src", default="memory/decisions.jsonl")
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    src = ws / args.src
    decisions_dir = ws / ".memory_hub" / "life" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print("no_source")
        return

    created = 0
    for idx, line in enumerate(src.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        ts = obj.get("ts") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamp = ts.replace("-", "").replace(":", "").replace(" ", "_")[:15]
        name = safe_name(str(obj.get("decision", "decision")))
        out = {
            "ts": ts,
            "type": obj.get("type", "decision"),
            "decision": obj.get("decision", ""),
            "source": obj.get("source", "migrated_jsonl"),
            "status": "open",
            "feedback": [],
            "migrated_from": str(src),
        }
        p = decisions_dir / f"dec_{stamp}_{idx:03d}_{name}.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created += 1

    print(f"ok migrated={created}")


if __name__ == "__main__":
    main()
