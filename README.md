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
  - context extractor (LLM + fallback)
  - checkpoint runner (6h)
  - decisions log (JSONL)
  - task feedback append
  - nightly deep analysis -> TASK_QUEUE
  - memory index note (token-efficient context)
```

## Quick Start

1. Put this folder in your OpenClaw workspace
2. Review `docs/qmd-config-template.jsonc`
3. Run:

```bash
python3 scripts/checkpoint_hybrid.py --workspace ~/.openclaw/workspace
```

4. Optional cron:

```bash
# base checkpoint (safe append + idempotency)
0 */6 * * * /opt/homebrew/opt/python@3.10/bin/python3.10 /path/to/openclaw-memory-hybrid/scripts/checkpoint_hybrid.py --workspace /Users/you/.openclaw/workspace >> /Users/you/.openclaw/workspace/memory/hybrid-checkpoint.log 2>&1

# process-layer checkpoint extraction (context -> structured memory)
5 */6 * * * /bin/bash /path/to/openclaw-memory-hybrid/scripts/checkpoint-memory-llm.sh >> /Users/you/.openclaw/workspace/memory/hybrid-process.log 2>&1

# nightly deep analysis (generate optimization tasks)
30 2 * * * /bin/bash /path/to/openclaw-memory-hybrid/scripts/nightly-deep-analysis.sh >> /Users/you/.openclaw/workspace/memory/hybrid-nightly.log 2>&1
```

## Process-layer Additions (from memory-hub strengths)

- `scripts/context_extractor.py`
  - extracts `achievements/learnings/decisions/issues/next_steps/task_feedback`
  - prefers OpenClaw Agent JSON extraction, with local fallback rules
- `scripts/run_checkpoint_pipeline.py`
  - transforms recent memory context into structured outputs (`.memory_hub/life/decisions/*.json`, `MEMORY_INDEX.md`, `TASK_QUEUE.md`)
  - optional `--audit-jsonl` for append-only logs
- `scripts/checkpoint-memory-llm.sh`
  - 6-hour checkpoint trigger entry
- `scripts/nightly_deep_analysis.py` + `scripts/nightly-deep-analysis.sh`
  - nightly MEMORY/decsions analysis, auto-write optimization tasks to `TASK_QUEUE.md`

### Memory-hub alignment

Default process-layer output now aligns with memory-hub directory layout:

```txt
.workspace/.memory_hub/
├── MEMORY.md
├── MEMORY_INDEX.md
├── TASK_QUEUE.md
├── life/
│   ├── decisions/       # dec_*.json (traceable per decision)
│   └── archives/
└── memory/              # raw daily logs and optional audit jsonl
```

Migration from old `memory/decisions.jsonl`:

```bash
python3 scripts/migrate_decisions_jsonl_to_json.py --workspace ~/.openclaw/workspace
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

## Security

See [`SECURITY.md`](./SECURITY.md) for threat model and hardening checklist.

## License

MIT
