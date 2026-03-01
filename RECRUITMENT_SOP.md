# Sub-agent Recruitment SOP (V0.3)

## 📋 Objective
To standardize the process of spawning specialized sub-agents with built-in financial guardrails.

## 🛠 Recruitment Process (Internal Protocol)

### 1. Intent Analysis
Before spawning, the Lead Agent must classify the task:
- **CODER**: Code generation, bug fixing, test writing.
- **RESEARCHER**: Web search, documentation reading, market analysis.
- **AUDITOR**: Code review, security checking, budget auditing.

### 2. Financial Provisioning
Assign a specific budget cap based on the context:
- `routine`: $0.05
- `experiment`: $0.50
- `high_roi`: $5.00

### 3. Execution Pattern
Use the `sessions_spawn` tool with the following parameters:
- `mode`: "run" for one-off tasks; "session" for ongoing collaboration.
- `model`: 
    - Default to `gemini-flash-1.5` (use Google credits).
    - Use `claude-3-5-sonnet` only for high-complexity architectural tasks.
- `label`: `[TaskType]_[ProjectName]_[Timestamp]`

## 🛡 Mandatory Guardrails
1. **Reporting**: Sub-agents MUST write logs to `projects/agent_budget_guard/staff_logs/`.
2. **Termination**: Sub-agents are set to `cleanup="delete"` by default unless memory preservation is required.
3. **Budget Check**: The Lead Agent must run `cost_calculator.py` pre-spawn to ensure the mission is affordable.
