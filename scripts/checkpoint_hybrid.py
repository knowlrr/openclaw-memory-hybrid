#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

try:
    import fcntl
except Exception:  # pragma: no cover
    fcntl = None


def ensure_file(path: Path, init_text: str, mode: int = 0o600):
    if not path.exists():
        path.write_text(init_text, encoding="utf-8")
        os.chmod(path, mode)


def append_line_locked(path: Path, line: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as f:
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def has_idempotency_key(path: Path, key: str) -> bool:
    if not path.exists():
        return False
    marker = f'"idempotency_key": "{key}"'
    with path.open("r", encoding="utf-8") as f:
        for row in f:
            if marker in row:
                return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Run a safe hybrid memory checkpoint")
    ap.add_argument("--workspace", required=True)
    ap.add_argument(
        "--window",
        choices=["hour", "day"],
        default="hour",
        help="Idempotency window for checkpoint writes",
    )
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser().resolve()
    memory_dir = ws / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(memory_dir, 0o700)

    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    day = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")

    daily = memory_dir / f"{day}.md"
    decisions = memory_dir / "decisions.jsonl"
    index = memory_dir / "MEMORY_INDEX.md"

    ensure_file(index, "# MEMORY_INDEX\n\n", mode=0o600)
    ensure_file(decisions, "", mode=0o600)

    idem_key = f"checkpoint:{day}:{hour}" if args.window == "hour" else f"checkpoint:{day}"

    if has_idempotency_key(decisions, idem_key):
        print("skipped (idempotent)")
        return

    if daily.exists():
        append_line_locked(daily, f"\n[hybrid] checkpoint at {ts}\n")
    else:
        daily.write_text(f"# Memory Log - {day}\n\n[hybrid] checkpoint at {ts}\n", encoding="utf-8")
        os.chmod(daily, 0o600)

    event = {
        "ts": ts,
        "type": "checkpoint",
        "status": "ok",
        "source": "daily memory",
        "idempotency_key": idem_key,
        "version": "v2",
    }
    append_line_locked(decisions, json.dumps(event, ensure_ascii=False) + "\n")
    append_line_locked(index, f"- [{day}] checkpoint executed ({hour}:00 window)\n")

    print("ok")


if __name__ == "__main__":
    main()
