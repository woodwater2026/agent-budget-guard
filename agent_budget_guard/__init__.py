"""
Agent Budget Guard — LLM cost monitoring and budget enforcement.

Quick start:
    from agent_budget_guard import BudgetGuard

    guard = BudgetGuard(budget_usd=1.0)
    cost = guard.record(model="gpt-4o", input_tokens=500, output_tokens=200)
    guard.status()
"""

__version__ = "0.1.1"
__all__ = ["BudgetGuard"]

# Model pricing per 1M tokens (input, output)
_PRICING = {
    "gpt-4o":              {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":         {"input": 0.15,  "output": 0.60},
    "claude-3-5-sonnet":   {"input": 3.00,  "output": 15.00},
    "claude-3-haiku":      {"input": 0.25,  "output": 1.25},
    "gemini-1.5-flash":    {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":      {"input": 1.25,  "output": 5.00},
    "deepseek-v3":         {"input": 0.14,  "output": 0.28},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _PRICING.get(model, {"input": 1.0, "output": 3.0})  # fallback
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


class BudgetGuard:
    """
    Minimal LLM cost tracker. Wrap your LLM calls, see spending in your terminal.

    Example:
        guard = BudgetGuard(budget_usd=1.0)
        response = your_llm_call(...)
        guard.record(model="gpt-4o", input_tokens=500, output_tokens=200)
        guard.status()
    """

    def __init__(self, budget_usd: float = 1.0, verbose: bool = True):
        self.budget_usd = budget_usd
        self.verbose = verbose
        self.total_cost = 0.0
        self.call_count = 0
        self._calls = []

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Record an LLM call and return its cost in USD."""
        cost = _estimate_cost(model, input_tokens, output_tokens)
        self.total_cost += cost
        self.call_count += 1
        self._calls.append({"model": model, "input": input_tokens, "output": output_tokens, "cost": cost})
        if self.verbose:
            remaining = self.budget_usd - self.total_cost
            status = "⚠️" if remaining < 0 else "✅"
            print(f"[BudgetGuard] {status} ${cost:.5f} | total=${self.total_cost:.4f} | remaining=${remaining:.4f}")
        return cost

    def is_over_budget(self) -> bool:
        """Returns True if spending has exceeded the budget."""
        return self.total_cost > self.budget_usd

    def status(self):
        """Print a budget summary to the terminal."""
        pct = (self.total_cost / self.budget_usd * 100) if self.budget_usd else 0
        bar_filled = int(pct / 5)
        bar = "█" * min(bar_filled, 20) + "░" * max(0, 20 - bar_filled)
        print(f"\n{'='*44}")
        print(f"  Agent Budget Guard  v{__version__}")
        print(f"{'='*44}")
        print(f"  [{bar}] {pct:.1f}%")
        print(f"  Calls:    {self.call_count}")
        print(f"  Spent:    ${self.total_cost:.5f}")
        print(f"  Budget:   ${self.budget_usd:.4f}")
        print(f"  Status:   {'⚠️  OVER BUDGET' if self.is_over_budget() else '✅ Within budget'}")
        print(f"{'='*44}\n")
