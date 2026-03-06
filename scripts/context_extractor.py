#!/usr/bin/env python3
"""Context extractor for hybrid memory flow.

Extracts achievements / learnings / decisions / issues / next_steps from recent context.
Uses OpenClaw agent when available, with deterministic fallback.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ExtractConfig:
    openclaw_bin: str = "openclaw"
    session_id: str = "main"
    timeout_sec: int = 35
    min_context_chars: int = 80


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    out = {
        "achievements": [],
        "learnings": [],
        "decisions": [],
        "issues": [],
        "next_steps": [],
        "task_feedback": [],
    }
    for k in out.keys():
        v = payload.get(k)
        if isinstance(v, list):
            out[k] = [str(x).strip()[:300] for x in v if str(x).strip()]
    return out


def _fallback_extract(context: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in context.splitlines() if ln.strip()]
    data = {
        "achievements": [],
        "learnings": [],
        "decisions": [],
        "issues": [],
        "next_steps": [],
        "task_feedback": [],
    }
    for ln in lines:
        low = ln.lower()
        if re.search(r"完成|done|发布|上线|已实现|success", ln, re.I):
            data["achievements"].append(ln)
        if re.search(r"学习|learn|lesson|复盘|insight", ln, re.I):
            data["learnings"].append(ln)
        if re.search(r"决策|决定|decision", ln, re.I):
            data["decisions"].append(ln)
        if re.search(r"问题|失败|error|bug|risk|阻塞|告警", ln, re.I):
            data["issues"].append(ln)
        if re.search(r"下一步|next|todo|待办|计划", ln, re.I):
            data["next_steps"].append(ln)
        if "反馈" in ln or "feedback" in low:
            data["task_feedback"].append(ln)

    if not any(data.values()):
        data["task_feedback"].append(context[:400])
    return data


def _extract_via_openclaw(context: str, cfg: ExtractConfig) -> dict[str, Any] | None:
    prompt = (
        "只输出 JSON，不要 markdown。\n"
        "从上下文提取字段：achievements, learnings, decisions, issues, next_steps, task_feedback。\n"
        "每个字段都是字符串数组。没有就空数组。\n\n"
        + context[:10000]
    )
    try:
        cp = subprocess.run(
            [
                cfg.openclaw_bin,
                "agent",
                "--local",
                "--session-id",
                cfg.session_id,
                "--prompt",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=cfg.timeout_sec,
        )
        raw = (cp.stdout or "").strip().replace("```json", "").replace("```", "").strip()
        if not raw:
            return None
        m = re.search(r"\{[\s\S]*\}", raw)
        payload = json.loads(m.group(0) if m else raw)
        if isinstance(payload, dict):
            return _normalize(payload)
    except Exception:
        return None
    return None


def extract_context(context: str, cfg: ExtractConfig | None = None) -> dict[str, Any]:
    cfg = cfg or ExtractConfig()
    context = (context or "").strip()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if len(context) < cfg.min_context_chars:
        return {
            "timestamp": ts,
            "status": "empty",
            "extracted": {},
            "reason": "context_too_short",
        }

    llm_data = _extract_via_openclaw(context, cfg)
    if llm_data is not None:
        return {"timestamp": ts, "status": "success", "extracted": llm_data, "source": "openclaw"}

    return {
        "timestamp": ts,
        "status": "fallback",
        "extracted": _fallback_extract(context),
        "source": "local_rules",
    }
