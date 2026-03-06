# OpenClaw Memory Hybrid

中文说明见：[`README.zh-CN.md`](./README.zh-CN.md)

Hybrid memory architecture for OpenClaw:

- **Base layer**: OpenClaw native memory (`memory-core` + `QMD` backend)
- **Process layer**: decision/task/checkpoint workflow inspired by `openclaw-memory-hub`
- **Goal**: enhancement without replacing native memory stack

## Why Hybrid

Native QMD is better at retrieval/indexing and OpenClaw integration.
Memory-hub style is better at process discipline (decision JSON, task feedback, checkpoint templates).

This project combines both:

1. Keep `memory.backend = qmd`
2. Add lightweight process scripts that write into workspace memory files
3. Keep all writes compatible with OpenClaw defaults (`MEMORY.md`, `memory/YYYY-MM-DD.md`)

## Architecture

```txt
[OpenClaw + QMD]
  - semantic retrieval
  - citations
  - scope controls
  - Obsidian vault indexing

[Hybrid Process Layer]
  - checkpoint runner
  - decisions log (JSONL)
  - task feedback append
  - memory index note (token-efficient context)
```

## Quick Start

1. Put this folder in your OpenClaw workspace
2. Review `docs/qmd-config-template.jsonc`
3. Run:

```bash
python3 scripts/checkpoint_hybrid.py --workspace ~/.openclaw/workspace
```

4. Optional cron (every 6h):

```bash
0 */6 * * * /opt/homebrew/opt/python@3.10/bin/python3.10 /path/to/openclaw-memory-hybrid/scripts/checkpoint_hybrid.py --workspace /Users/you/.openclaw/workspace >> /Users/you/.openclaw/workspace/memory/hybrid-checkpoint.log 2>&1
```

## Safety/Robustness (v2)

- Idempotency window (`--window hour|day`, default `hour`) prevents duplicate checkpoint writes in the same window.
- Appends are lock-protected (`flock`) and `fsync` flushed for safer concurrent runs.
- Checkpoints no longer append into `MEMORY.md` directly (reduces long-term memory pollution).
- Memory file permissions default to restricted mode (`600`, memory dir `700`).

## Non-goals

- No replacement of OpenClaw memory plugin
- No direct mutation of vector internals
- No bypass of QMD/update scope policies

## License

MIT
