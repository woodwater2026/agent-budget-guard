from cost_calculator import BudgetGuard
from circuit_breaker import CircuitBreaker

class ModelDegrader:
    def __init__(self, guard: BudgetGuard):
        self.guard = guard

    def auto_degrade(self, current_model, input_tokens, target_output_tokens, context="routine"):
        # Check Circuit Breaker state first
        circuit_state = self.guard.breaker.check_state()
        if circuit_state == "OPEN":
            return None, 0.0, "FAILURE: Circuit is OPEN, cannot process request."

        # 1. Estimate current cost
        current_cost = self.guard.estimate_cost(current_model, input_tokens, target_output_tokens)
        
        # 2. Check if it's within budget using BudgetGuard's integrated check_budget
        is_within_budget, budget_msg = self.guard.check_budget(current_cost, context)

        if is_within_budget:
            return current_model, current_cost, "Budget OK, no degradation needed."
        
        # If not within budget, attempt to degrade
        # 3. Try to find a cheaper model that fits
        limit = self.guard.thresholds.get(context, self.guard.default_threshold)
        cheaper_model, cheaper_cost, reason = self.guard.recommend_model(input_tokens, target_output_tokens, limit)
        
        if cheaper_model:
            # After recommending a cheaper model, check its budget again with the circuit breaker
            is_degraded_model_ok, degraded_msg = self.guard.check_budget(cheaper_cost, context)
            if is_degraded_model_ok:
                return cheaper_model, cheaper_cost, f"DEGRADED: Switched from {current_model} to {cheaper_model} to stay under ${limit:.4f}."
            else:
                return None, 0.0, f"FAILURE: Degraded model {cheaper_model} still triggered budget guard: {degraded_msg}"
        else:
            return None, 0.0, f"FAILURE: No models found within budget of ${limit:.4f}. Reason: {budget_msg}"

if __name__ == "__main__":
    guard = BudgetGuard()
    degrader = ModelDegrader(guard)
    
    # Test: Claude (expensive) -> Gemini (cheaper)
    model, cost, msg = degrader.auto_degrade("claude-3-5-sonnet", 200_000, 1000, context="routine")
    print(f"Model: {model}, Cost: ${cost:.4f}")
    print(f"Log: {msg}")
