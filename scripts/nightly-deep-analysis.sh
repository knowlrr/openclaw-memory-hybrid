#!/usr/bin/env bash
# 每天夜间运行：分析 MEMORY/decisions 并生成优化任务
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

python3 "$SCRIPT_DIR/nightly_deep_analysis.py" --workspace "$WORKSPACE"
