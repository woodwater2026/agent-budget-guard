# 🌊🌲 Agent Budget Guard

**Autonomous AI agent cost monitoring and budget enforcement tool.**

## 🎯 Overview
Agent Budget Guard is a lightweight, proactive tool designed to prevent "Inference Bill Shock" in AI agentic workflows. It monitors token usage, estimates costs based on 2026 model pricing, and enforces strict budget thresholds.

## ✨ Key Features
- **Proactive Cost Estimation**: Calculate costs *before* the API call happens.
- **Context-Aware Thresholds**: Set different limits for "routine", "experiment", and "high-roi" tasks.
- **Multi-Model Support**: Integrated pricing for Gemini-Flash, DeepSeek-V3, and Claude-3.5-Sonnet.
- **Dynamic Routing (Coming Soon)**: Automatically switch models to stay within budget.

## 🚀 Quick Start
```python
from cost_calculator import BudgetGuard

guard = BudgetGuard(default_threshold=0.05)
cost = guard.estimate_cost("claude-3-5-sonnet", 100_000, 10_000)
ok, msg = guard.check_budget(cost, "routine")

if not ok:
    print(msg) # ALERT: Estimated cost $0.4500 exceeds routine limit of $0.0500.
```

## 📜 License
MIT
