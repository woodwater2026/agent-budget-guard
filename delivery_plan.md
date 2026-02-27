# Agent Budget Guard - Delivery & CI Plan (2026-02-27)

## 🎯 Goal
Automate the delivery of features and patches for the Budget Guard project while maintaining security and cost-efficiency.

## 🛠 Prerequisites (Action Items)
- [ ] **Install GitHub CLI (`gh`)**: Currently missing on MBP 2015. Need `brew install gh`.
- [ ] **Configure Git**: Ensure `woodwater` user has git identity set up.
- [ ] **Auth**: Link to ZQ's GitHub or a dedicated project account.

## 🔄 Delivery Loop Workflow
1. **Local Dev**: Water Woods implements features in `projects/agent_budget_guard/`.
2. **Pre-flight Check**: Run `cost_calculator.py` to ensure the agent's own work didn't exceed budget.
3. **Branching**: Create a feature branch `feat/guard-v1.x`.
4. **Pull Request**: Use `gh pr create` with an AI-generated summary of changes.
5. **Approval**: ZQ reviews the PR (Human-in-the-loop).

## 🛡 Security Guardrails
- **No-Merge Policy**: Water Woods cannot self-merge PRs without ZQ's approval.
- **Sensitive Data**: Use a `.gitignore` to ensure API keys never leave the machine.
