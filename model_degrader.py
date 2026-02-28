from cost_calculator import BudgetGuard

class ModelDegrader:
    def __init__(self, guard: BudgetGuard):
        self.guard = guard

    def auto_degrade(self, current_model, input_tokens, target_output_tokens, context="routine"):
        # 1. Estimate current cost
        current_cost = self.guard.estimate_cost(current_model, input_tokens, target_output_tokens)
        
        # 2. Check if it's within budget
        limit = self.guard.thresholds.get(context, self.guard.default_threshold)
        if current_cost <= limit:
            return current_model, current_cost, "Budget OK, no degradation needed."
        
        # 3. Try to find a cheaper model that fits
        # recommend_model returns (model, cost, reason)
        cheaper_model, cheaper_cost, reason = self.guard.recommend_model(input_tokens, target_output_tokens, limit)
        
        if cheaper_model:
            return cheaper_model, cheaper_cost, f"DEGRADED: Switched from {current_model} to {cheaper_model} to stay under ${limit:.4f}."
        else:
            return None, 0.0, f"FAILURE: No models found within budget of ${limit:.4f}."

if __name__ == "__main__":
    guard = BudgetGuard()
    degrader = ModelDegrader(guard)
    
    # Test: Claude (expensive) -> Gemini (cheaper)
    model, cost, msg = degrader.auto_degrade("claude-3-5-sonnet", 200_000, 1000, context="routine")
    print(f"Model: {model}, Cost: ${cost:.4f}")
    print(f"Log: {msg}")
