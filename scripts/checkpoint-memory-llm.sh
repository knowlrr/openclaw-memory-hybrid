#!/usr/bin/env bash
# 每 6 小时运行：将最近上下文提取为结构化记忆
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

python3 "$SCRIPT_DIR/run_checkpoint_pipeline.py" --workspace "$WORKSPACE"
