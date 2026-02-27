import json
import os
from cost_calculator import BudgetGuard
from token_optimizer import TokenOptimizer

class GuardOrchestrator:
    """
    Main entry point for coordinating cost estimation,
    token optimization, and model routing.
    """
    def __init__(self, config_path="config.json"):
        self.guard = BudgetGuard(config_path)
        self.optimizer = TokenOptimizer()

    def process_request(self, model, messages, context="routine"):
        # 1. Optimize tokens (strip whitespace, etc)
        optimized_messages = self.optimizer.optimize_payload(messages)
        
        # 2. Calculate current token counts
        input_text = " ".join([m["content"] for m in optimized_messages])
        input_tokens = len(input_text) // 4 # Standard 2026 rough estimation (4 chars/token)
        
        # 3. Estimate cost
        est_cost = self.guard.estimate_cost(model, input_tokens, 500) # Assuming 500 output
        
        # 4. Check budget
        ok, msg = self.guard.check_budget(est_cost, context)
        
        if not ok:
            # 5. Recommend cheaper model if over budget
            limit = self.guard.thresholds.get(context, 0.10)
            rec_model, rec_cost = self.guard.recommend_model(input_tokens, 500, limit)
            return {
                "status": "blocked",
                "message": msg,
                "recommended_model": rec_model,
                "estimated_saving": f"${(est_cost - rec_cost):.4f}" if rec_model else "N/A"
            }
        
        return {
            "status": "ok",
            "optimized_messages": optimized_messages,
            "estimated_cost": est_cost
        }

if __name__ == "__main__":
    orchestrator = GuardOrchestrator()
    sample_msgs = [{"role": "user", "content": "Analyze this large codebase..."}]
    # Test high-cost scenario
    result = orchestrator.process_request("claude-3-5-sonnet", sample_msgs, "routine")
    print(json.dumps(result, indent=4))
