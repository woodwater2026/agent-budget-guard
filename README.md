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

```bash
pip install agent-budget-guard
```

```python
from agent_budget_guard import BudgetGuard

# Set a budget for your agent run
guard = BudgetGuard(budget_usd=1.0)

# After each LLM call, record the token usage
guard.record(model="gpt-4o", input_tokens=500, output_tokens=200)
guard.record(model="claude-3-5-sonnet", input_tokens=800, output_tokens=400)

# Gate further calls on budget status
if guard.is_over_budget():
    raise RuntimeError("Budget exceeded — halting agent.")

# Print a summary dashboard
guard.status()
```

See `examples/quickstart.py` for a full simulated agent demo (no API key required).

### Advanced: Orchestrator
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

## 🛠 Project Components
- `cost_calculator.py`: Core logic for pricing metadata and estimation.
- `orchestrator.py`: The "Brain" coordinating optimization and routing.
- `model_degrader.py`: Automated logic for model switching.
- `cli.py`: Command-line interface for human-agent collaboration.
- `notifier.py`: Integrated email alert system (Gmail IMAP/SMTP).

## 📜 License
MIT

---

## 🏛 2026 AI Agent Financial Security Whitepaper (Preview)
*By Water Woods & ZQ*

As of Q1 2026, the rise of **Agentic Wallets** (supported by Stripe/Coinbase) has shifted the AI risk landscape from "Token Overuse" to "Unauthorized Transactional Authority." 

**Core Principles for Agent Financial Safety:**
1. **Dynamic Model Degradation**: Proactively switch to SLMs (Small Language Models) when task ROI is low.
2. **Circuit Breaking**: Instant kill-switch on spending velocity anomalies.
3. **Decoupled Vaults**: Keep financial keys in isolated, encrypted environments outside of the agent's immediate workspace.

Agent Budget Guard implements these principles to ensure your agents remain profitable, not just productive.
