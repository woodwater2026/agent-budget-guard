# 🌊🌲 Agent Budget Guard

**Autonomous AI agent cost monitoring and budget enforcement tool.**

## 🎯 Overview
Agent Budget Guard is a lightweight, proactive tool designed to prevent "Inference Bill Shock" in AI agentic workflows. It monitors token usage, estimates costs based on 2026 model pricing, and enforces strict budget thresholds.

## ✨ Key Features
- **Proactive Cost Estimation**: Calculate costs *before* the API call happens.
- **Context-Aware Thresholds**: Set different limits for "routine", "experiment", and "high-roi" tasks.
- **Multi-Model Support**: Integrated pricing for Gemini-Flash, DeepSeek-V3, and Claude-3.5-Sonnet.
- **Dynamic Routing (Coming Soon)**: Automatically switch models (e.g., to cost-effective SLMs) to stay within budget.
- **Context Compression**: Built-in `TokenOptimizer` to strip redundant data and summarize long histories.

## 📑 White Paper: AI Agent Financial Security (2026)

As we enter the era of **Agentic Commerce**, AI agents are transitioning from "tools that process data" to "economic actors that manage capital." This shift introduces unprecedented financial risks:
1. **Recursive Spending Loops**: Agents calling agents in a loop, exponentially draining API credits.
2. **Inference Bill Shock**: Frontier models (like Claude 3.5 Sonnet) providing high reasoning at high variable costs.
3. **Authorization Leakage**: Agents with access to financial wallets spending beyond their intent.

**Agent Budget Guard** provides the essential "Financial Control Plane" for this new economy, ensuring every token and every cent is governed by human-defined ROI thresholds.

## 📘 AI Agent Financial Security (2026 Perspective)
In the burgeoning "Agentic Economy," AI agents are transitioning from tools to economic actors. Managing their financial permissions and API costs is the new frontier of cybersecurity. Agent Budget Guard provides the essential "Control Plane" for:
- **Spending Velocity Control**: Preventing high-frequency billing loops.
- **Model Orchestration**: Balancing reasoning quality with fiscal responsibility.
- **Micro-transaction Auditing**: Real-time logging of every cent spent by autonomous sub-agents.

---

## 🚀 Quick Start
### As a Library
```python
from orchestrator import GuardOrchestrator

orchestrator = GuardOrchestrator()
messages = [{"role": "user", "content": "Help me rewrite this code."}]
result = orchestrator.process_request("claude-3-5-sonnet", messages)
```

### As a CLI Tool
```bash
python3 cli.py --model gemini-flash-1.5 --prompt "Check my budget" --context routine
```

## 📜 License
MIT
