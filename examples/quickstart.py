"""
Agent Budget Guard — Quickstart Example
========================================

This script demonstrates cost tracking without needing any real API keys.
It simulates a multi-step AI agent making several LLM calls and shows how
BudgetGuard keeps a running tally, warns you when you're close to budget,
and blocks execution when the budget is exceeded.

Run it:
    pip install agent-budget-guard
    python examples/quickstart.py
"""

import time
from agent_budget_guard import BudgetGuard

# ── 1. Create a guard with a $0.01 budget (low, so we hit the limit) ──────────
guard = BudgetGuard(budget_usd=0.01, verbose=True)

print("\n🤖 Simulating a multi-step AI agent...\n")

# ── 2. Simulate a few LLM calls ───────────────────────────────────────────────

steps = [
    ("Step 1: Summarize document",     "gpt-4o-mini",       800,  300),
    ("Step 2: Extract key entities",   "gpt-4o-mini",       400,  150),
    ("Step 3: Draft response email",   "claude-3-5-sonnet", 600,  800),
    ("Step 4: Translate to French",    "gemini-1.5-flash",  900,  900),
    ("Step 5: Final quality check",    "gpt-4o",           1200,  400),
]

for label, model, input_tok, output_tok in steps:
    print(f"  → {label}")
    guard.record(model=model, input_tokens=input_tok, output_tokens=output_tok)

    # Guard rails: stop if over budget
    if guard.is_over_budget():
        print("\n🚨 Budget exceeded! Stopping agent.\n")
        break

    time.sleep(0.1)  # simulate processing time

# ── 3. Print final summary ────────────────────────────────────────────────────
guard.status()

# ── 4. Show how to use guard as a gate in your own agent loop ─────────────────
print("─" * 44)
print("Example: Use guard.is_over_budget() as a gate")
print("─" * 44)
print("""
def run_agent_step(guard, model, prompt):
    if guard.is_over_budget():
        raise RuntimeError("Budget exceeded — halting agent.")

    # ... call your LLM here ...
    response = your_llm(model=model, prompt=prompt)

    # Record the actual token usage from the response
    guard.record(
        model=model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return response
""")
print("Install: pip install agent-budget-guard")
print("Docs:    https://github.com/woodwater2026/agent-budget-guard\n")
