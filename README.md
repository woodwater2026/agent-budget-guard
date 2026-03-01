[![PyPI version](https://img.shields.io/pypi/v/agent-budget-guard.svg)](https://pypi.org/project/agent-budget-guard/)
[![Python](https://img.shields.io/pypi/pyversions/agent-budget-guard.svg)](https://pypi.org/project/agent-budget-guard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 🌊🌲 Agent Budget Guard

**AI agent 的 API 成本追踪与预算控制工具。**

你的 agent 24/7 在运行。你知道它每天烧多少钱吗？

---

## Real Usage — 这个工具由 AI agent 自主开发，并用于监控自己

**Water Woods（沐）** 是构建 agent-budget-guard 的 AI co-founder，也是第一个用户。它 24/7 运行在 OpenClaw 框架上，每 5 分钟 heartbeat 一次，用这个工具追踪自己每一笔 API 花费。

**2026-03-01 实际 usage_log 数据（部分）：**

```jsonl
{"ts":"2026-03-01T17:50:53+00:00","model":"anthropic/claude-sonnet-4-6","in":5000,"out":800,"usd":0.027,"task":"heartbeat"}
{"ts":"2026-03-01T19:03:51+00:00","model":"anthropic/claude-sonnet-4-6","in":4700,"out":1200,"usd":0.0321,"task":"heartbeat"}
{"ts":"2026-03-01T19:08:48+00:00","model":"anthropic/claude-sonnet-4-6","in":3500,"out":500,"usd":0.018,"task":"heartbeat"}
```

**当日汇总：**

```
调用次数：25 次
总花费：  $0.55
任务拆分：heartbeat $0.39 · product-dev $0.15 · 维护 $0.01
异常检测：11:03 那次 $0.032（output tokens 是平均的 3 倍）
```

没有 agent-budget-guard，这些数字只会在月底账单里出现。

> 完整技术文章：[BLOG_POST.md](./BLOG_POST.md)

---

## 安装

```bash
pip install agent-budget-guard
```

**或者作为 OpenClaw Skill：**

```bash
python3 budget.py track --model "anthropic/claude-sonnet-4-6" --in 3000 --out 400 --task "heartbeat"
python3 budget.py summary --days 7
```

---

## 快速开始

```python
from agent_budget_guard import BudgetGuard

guard = BudgetGuard(budget_usd=2.0)

# 每次 LLM 调用后记录
guard.record(model="claude-sonnet-4-6", input_tokens=3000, output_tokens=400)
guard.record(model="gpt-4o", input_tokens=500, output_tokens=200)

if guard.is_over_budget():
    raise RuntimeError("预算超限，停止执行")

guard.status()
```

输出：
```
============================================
  Agent Budget Guard  v0.1.1
============================================
  [██░░░░░░░░░░░░░░░░░░] 9.3%
  Calls:    2
  Spent:    $0.01800
  Budget:   $2.0000
  Status:   ✅ Within budget
============================================
```

**CLI（OpenClaw Skill）：**

```bash
# 记录一次调用
python3 budget.py track --model "anthropic/claude-sonnet-4-6" --in 5000 --out 800 --task "product-dev"

# 执行前预估，返回 approve / warn / block
python3 budget.py check --model "anthropic/claude-sonnet-4-6" --tokens 50000

# 查看花费汇总
python3 budget.py summary --days 7
```

---

## 为什么 AI Agent 需要这个

| 问题 | 后果 |
|------|------|
| Agent 24/7 运行，无人监控 | 月底账单惊喜 |
| 子 agent 调用子 agent | 指数级消耗 |
| 上下文越来越长 | 每次调用越来越贵 |
| 预算只在事后才知道 | 无法拦截 |

- `budget.track` — 每次调用后立即写入 JSONL 日志
- `budget.check` — 执行前预估，`block` 时硬性停止
- `budget.summary` — 按模型和任务类型汇总

---

## 支持的模型

| 模型 | Input (per 1M) | Output (per 1M) |
|------|---------------|----------------|
| claude-sonnet-4-6 | $3.00 | $15.00 |
| claude-haiku-4-5 | $0.80 | $4.00 |
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gemini-1.5-flash | $0.075 | $0.30 |
| deepseek-v3 | $0.14 | $0.28 |

添加新模型：更新 `agent_budget_guard/__init__.py` 的 `_PRICING`。

---

## 日志格式

`data/usage_log.jsonl`

```json
{"ts": "2026-03-01T17:50:53+00:00", "model": "anthropic/claude-sonnet-4-6", "in": 5000, "out": 800, "usd": 0.027, "task": "heartbeat"}
```

---

## License

MIT — 由 Water Woods（沐）和 ZQ 构建，2026
