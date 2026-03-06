#!/usr/bin/env python3
import argparse, json
from datetime import datetime
from pathlib import Path


def ensure(p: Path, text: str):
    if not p.exists():
        p.write_text(text, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', required=True)
    args = ap.parse_args()

    ws = Path(args.workspace).expanduser()
    mem = ws / 'MEMORY.md'
    daily = ws / 'memory' / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    decisions = ws / 'memory' / 'decisions.jsonl'
    index = ws / 'memory' / 'MEMORY_INDEX.md'

    daily.parent.mkdir(parents=True, exist_ok=True)
    ensure(mem, '# MEMORY.md\n\n')
    ensure(index, '# MEMORY_INDEX\n\n')

    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    checkpoint = f"\n## Hybrid Checkpoint {ts}\n- status: ok\n- source: daily memory\n"
    mem.write_text(mem.read_text(encoding='utf-8') + checkpoint, encoding='utf-8')

    event = {
        'ts': ts,
        'type': 'checkpoint',
        'note': 'hybrid memory checkpoint executed'
    }
    with decisions.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

    idx_line = f"- [{datetime.now().strftime('%Y-%m-%d')}] checkpoint executed"
    index.write_text(index.read_text(encoding='utf-8') + idx_line + '\n', encoding='utf-8')

    if daily.exists():
        daily.write_text(daily.read_text(encoding='utf-8') + f"\n\n[hybrid] checkpoint at {ts}\n", encoding='utf-8')
    else:
        daily.write_text(f"# Memory Log - {datetime.now().strftime('%Y-%m-%d')}\n\n[hybrid] checkpoint at {ts}\n", encoding='utf-8')

    print('ok')


if __name__ == '__main__':
    main()
