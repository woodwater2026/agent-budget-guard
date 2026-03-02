"""Tests for MCP server tools."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Point log to a temp file for tests
_TMP = tempfile.mktemp(suffix=".jsonl")


@pytest.fixture(autouse=True)
def isolate_log(monkeypatch, tmp_path):
    log = tmp_path / "usage_log.jsonl"
    import agent_budget_guard.mcp_server as srv
    monkeypatch.setattr(srv, "LOG_PATH", log)
    yield log


def test_budget_track_basic():
    from agent_budget_guard.mcp_server import budget_track
    result = budget_track(model="anthropic/claude-sonnet-4-6", tokens_in=1000, tokens_out=200, task="test")
    assert result["ok"] is True
    assert result["call_usd"] > 0
    assert result["over_task_cap"] is False


def test_budget_track_writes_log(isolate_log):
    from agent_budget_guard.mcp_server import budget_track
    budget_track(model="anthropic/claude-sonnet-4-6", tokens_in=500, tokens_out=100, task="test")
    assert isolate_log.exists()
    entry = json.loads(isolate_log.read_text().strip())
    assert entry["task"] == "test"
    assert entry["usd"] > 0


def test_budget_track_over_cap():
    from agent_budget_guard.mcp_server import budget_track
    # 10M tokens should exceed $2 cap
    result = budget_track(model="anthropic/claude-sonnet-4-6", tokens_in=10_000_000, tokens_out=0, task="huge")
    assert result["over_task_cap"] is True


def test_budget_check_approve():
    from agent_budget_guard.mcp_server import budget_check
    result = budget_check(model="anthropic/claude-haiku-4-5", tokens=1000, task="small")
    assert result["decision"] == "approve"
    assert result["estimated_usd"] > 0
    assert "task_cap_usd" in result


def test_budget_check_block():
    from agent_budget_guard.mcp_server import budget_check
    # 100M tokens will exceed $2 cap
    result = budget_check(model="anthropic/claude-sonnet-4-6", tokens=100_000_000, task="huge")
    assert result["decision"] == "block"


def test_budget_summary_empty():
    from agent_budget_guard.mcp_server import budget_summary
    result = budget_summary(days=7)
    assert result["total_usd"] == 0.0
    assert result["calls"] == 0


def test_budget_summary_after_track(isolate_log):
    from agent_budget_guard.mcp_server import budget_track, budget_summary
    budget_track(model="gpt-4o-mini", tokens_in=1000, tokens_out=200, task="chat")
    budget_track(model="gpt-4o-mini", tokens_in=500, tokens_out=100, task="chat")
    result = budget_summary(days=1)
    assert result["calls"] == 2
    assert result["total_usd"] > 0
    assert "gpt-4o-mini" in result["by_model"]
    assert "chat" in result["by_task"]


def test_budget_summary_avg_per_call(isolate_log):
    from agent_budget_guard.mcp_server import budget_track, budget_summary
    budget_track(model="gpt-4o", tokens_in=1000, tokens_out=200, task="t")
    result = budget_summary(days=1)
    assert result["avg_per_call"] == result["total_usd"]
