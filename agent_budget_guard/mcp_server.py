"""
Agent Budget Guard — MCP Server

Exposes budget tracking tools via the Model Context Protocol (MCP).
Supports Claude Desktop, Cursor, Windsurf, and any MCP-compatible client.

Usage (stdio transport):
    agent-budget-guard-mcp

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "agent-budget-guard": {
          "command": "agent-budget-guard-mcp"
        }
      }
    }
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Pricing (per 1M tokens)
# ---------------------------------------------------------------------------
_PRICING = {
    "gpt-4o":                      {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":                 {"input": 0.15,  "output": 0.60},
    "claude-3-5-sonnet":           {"input": 3.00,  "output": 15.00},
    "claude-3-haiku":              {"input": 0.25,  "output": 1.25},
    "claude-sonnet-4-6":           {"input": 3.00,  "output": 15.00},
    "anthropic/claude-sonnet-4-6": {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5":            {"input": 0.80,  "output": 4.00},
    "anthropic/claude-haiku-4-5":  {"input": 0.80,  "output": 4.00},
    "gemini-1.5-flash":            {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":              {"input": 1.25,  "output": 5.00},
    "deepseek-v3":                 {"input": 0.14,  "output": 0.28},
}

TASK_CAP_USD = 2.00
DAILY_BUDGET_USD = 10.00
WARN_THRESHOLD_USD = 8.00

LOG_PATH = Path(os.environ.get(
    "ABG_LOG_PATH",
    Path.home() / ".agent_budget_guard" / "usage_log.jsonl"
))


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pricing = _PRICING.get(model, {"input": 1.0, "output": 3.0})
    return (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000


def _ensure_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _today_usd() -> float:
    if not LOG_PATH.exists():
        return 0.0
    today = datetime.now(timezone.utc).date().isoformat()
    total = 0.0
    with open(LOG_PATH) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("ts", "").startswith(today):
                    total += entry.get("usd", 0.0)
            except Exception:
                pass
    return total


def _append_log(entry: dict):
    _ensure_log()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "agent-budget-guard",
    instructions="Track and enforce LLM API spending for AI agents. Use budget_track after each LLM call, budget_check before expensive tasks, and budget_summary for cost reports.",
)


@mcp.tool()
def budget_track(model: str, tokens_in: int, tokens_out: int, task: str = "general") -> dict:
    """
    Log an LLM API call and return cost summary.

    Call this after every significant LLM call to track spending.
    Returns whether the per-task cap ($2) has been exceeded.
    """
    call_usd = _estimate_cost(model, tokens_in, tokens_out)
    today_before = _today_usd()

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "in": tokens_in,
        "out": tokens_out,
        "usd": call_usd,
        "task": task,
    }
    _append_log(entry)

    today_usd = today_before + call_usd
    budget_remaining = TASK_CAP_USD - call_usd

    return {
        "ok": True,
        "call_usd": round(call_usd, 6),
        "today_usd": round(today_usd, 4),
        "budget_remaining": round(budget_remaining, 4),
        "over_task_cap": call_usd > TASK_CAP_USD,
    }


@mcp.tool()
def budget_check(model: str, tokens: int, task: str = "planned-task") -> dict:
    """
    Pre-check whether a planned task fits within the $2 per-task cap.

    Call this before spawning expensive subagents or large LLM calls.
    Returns decision: 'approve', 'warn', or 'block'.
    """
    # Estimate assuming 80% input / 20% output split
    tokens_in = int(tokens * 0.8)
    tokens_out = int(tokens * 0.2)
    estimated_usd = _estimate_cost(model, tokens_in, tokens_out)
    today_usd = _today_usd()

    if estimated_usd > TASK_CAP_USD:
        decision = "block"
    elif today_usd + estimated_usd > WARN_THRESHOLD_USD:
        decision = "warn"
    else:
        decision = "approve"

    return {
        "decision": decision,
        "estimated_usd": round(estimated_usd, 6),
        "today_usd": round(today_usd, 4),
        "budget_remaining": round(TASK_CAP_USD - estimated_usd, 4),
        "task_cap_usd": TASK_CAP_USD,
        "daily_budget_usd": DAILY_BUDGET_USD,
    }


@mcp.tool()
def budget_summary(days: int = 7) -> dict:
    """
    Summarize LLM spending over the last N days.

    Returns total cost, call count, and breakdowns by model and task.
    Useful for daily reports and cost reviews.
    """
    if not LOG_PATH.exists():
        return {"days": days, "total_usd": 0.0, "calls": 0, "by_model": {}, "by_task": {}}

    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    total_usd = 0.0
    calls = 0
    by_model: dict = {}
    by_task: dict = {}

    with open(LOG_PATH) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("ts", "") < cutoff:
                    continue
                usd = entry.get("usd", 0.0)
                total_usd += usd
                calls += 1
                model = entry.get("model", "unknown")
                task = entry.get("task", "unknown")
                by_model[model] = round(by_model.get(model, 0.0) + usd, 6)
                by_task[task] = round(by_task.get(task, 0.0) + usd, 6)
            except Exception:
                pass

    return {
        "days": days,
        "total_usd": round(total_usd, 4),
        "calls": calls,
        "avg_per_call": round(total_usd / calls, 5) if calls else 0,
        "by_model": by_model,
        "by_task": by_task,
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
