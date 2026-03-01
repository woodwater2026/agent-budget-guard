# 🌊🌲 Agent Budget Guard

**AI agent 的 API 成本追踪与预算控制工具。**

你的 agent 24/7 在运行。你知道它每天烧多少钱吗？

---

## 安装

### 方式一：Python 包（集成到 agent 代码）

```bash
pip install agent-budget-guard
```

### 方式二：OpenClaw Skill（自动 heartbeat 追踪）

```bash
# 在 OpenClaw workspace 添加 skill 后，每次 heartbeat 自动记录花费
python3 budget.py track --model "anthropic/claude-sonnet-4-6" --in 3000 --out 400 --task "heartbeat"
python3 budget.py summary --days 7
```

---

## 快速开始

### Python 包用法

```python
from agent_budget_guard import BudgetGuard

# 初始化，设置单次任务预算上限
guard = BudgetGuard(budget_usd=2.0)

# 每次 LLM 调用后记录
guard.record(model="claude-sonnet-4-6", input_tokens=3000, output_tokens=400)
guard.record(model="gpt-4o", input_tokens=500, output_tokens=200)

# 检查是否超预算
if guard.is_over_budget():
    raise RuntimeError("预算超限，停止执行")

# 打印汇总
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

### CLI 用法（OpenClaw Skill）

```bash
# 记录一次调用
python3 budget.py track --model "anthropic/claude-sonnet-4-6" --in 5000 --out 800 --task "product-dev"

# 执行前预估（返回 approve/warn/block）
python3 budget.py check --model "anthropic/claude-sonnet-4-6" --tokens 50000 --task "big-task"

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
| 高峰时段模型价格不同 | 预算失控 |

**Agent Budget Guard 的做法：**
- `budget.track` — 每次调用后立即记录到 JSONL 日志
- `budget.check` — 执行前预估，返回 `approve/warn/block`，block 时硬性停止
- `budget.summary` — 按模型和任务类型汇总花费

---

## 真实数据

这个工具的第一个用户是它的 AI co-founder（Water Woods），在 2026-03-01 的实际追踪数据：

```
12 次 heartbeat 调用
总花费：$0.2016
平均每次：$0.0168
全部模型：claude-sonnet-4-6
异常检测：11:03 那次 $0.0321（output tokens 异常高）
```

详见：[BLOG_POST.md](./BLOG_POST.md)

---

## 支持的模型定价

| 模型 | Input (per 1M) | Output (per 1M) |
|------|---------------|----------------|
| claude-sonnet-4-6 | $3.00 | $15.00 |
| claude-haiku-4-5 | $0.80 | $4.00 |
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gemini-1.5-flash | $0.075 | $0.30 |
| deepseek-v3 | $0.14 | $0.28 |

添加新模型：更新 `agent_budget_guard/__init__.py` 中的 `_PRICING` 字典。

---

## 项目结构

```
agent_budget_guard/
├── __init__.py          # BudgetGuard 类 + 定价数据（单一来源）
├── circuit_breaker.py   # 消费速度熔断器
├── model_degrader.py    # 自动降级到更便宜的模型
├── orchestrator.py      # 完整编排（预估 + 熔断 + 路由）
└── cli.py               # 命令行接口

skills/agent-budget-guard/
└── scripts/budget.py    # OpenClaw skill CLI（从包导入定价逻辑）
```

---

## 日志格式

`~/.openclaw/workspace/projects/agent_budget_guard/data/usage_log.jsonl`

```json
{"ts": "2026-03-01T17:50:53+00:00", "model": "anthropic/claude-sonnet-4-6", "in": 5000, "out": 800, "usd": 0.027, "task": "heartbeat"}
```

---

## License

MIT

---

*由 Water Woods（沐）和 ZQ 构建 — 2026*
