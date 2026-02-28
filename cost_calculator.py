import sys
import json
import os
import time

class CircuitBreaker:
    def __init__(self, time_window=60, max_spending=1.00):
        self.time_window = time_window # seconds
        self.max_spending = max_spending # USD
        self.history = [] # list of (timestamp, cost)

    def is_tripped(self, current_cost):
        now = time.time()
        # Cleanup old history
        self.history = [entry for entry in self.history if now - entry[0] <= self.time_window]
        
        current_window_spending = sum(entry[1] for entry in self.history)
        if current_window_spending + current_cost > self.max_spending:
            return True, f"CIRCUIT BREAKER TRIPPED: Spending velocity too high. Window spending: ${current_window_spending:.4f}"
        
        self.history.append((now, current_cost))
        return False, "Velocity OK."

class BudgetGuard:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        self.breaker = CircuitBreaker(time_window=300, max_spending=5.00) # $5 limit every 5 mins
        
        # 2026 Model Pricing Metadata (per 1M tokens)
        self.model_pricing = {
            "gemini-flash-1.5": {"input": 0.075, "output": 0.30},
            "deepseek-v3": {"input": 0.14, "output": 0.28},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00}
        }

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.default_threshold = config.get("default_threshold", 0.10)
                self.thresholds = config.get("thresholds", {})
                self.notification_email = config.get("notification_email", "")
        else:
            self.default_threshold = 0.10
            self.thresholds = {"high_roi": 5.00, "routine": 0.05, "experiment": 0.50}
            self.notification_email = ""

    def estimate_cost(self, model, input_tokens, output_tokens):
        pricing = self.model_pricing.get(model)
        if not pricing:
            return 0.0
        cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        return cost

    def recommend_model(self, input_tokens, target_output_tokens, max_budget=0.01):
        """
        Suggests the best model based on the provided budget.
        """
        recommendations = []
        for model, pricing in self.model_pricing.items():
            est_cost = self.estimate_cost(model, input_tokens, target_output_tokens)
            if est_cost <= max_budget:
                recommendations.append((model, est_cost))
        
        # Sort by cost (ascending)
        recommendations.sort(key=lambda x: x[1])
        return recommendations[0] if recommendations else (None, 0.0)

    def prepare_request(self, model, messages, context="routine"):
        """
        Cleans messages and checks budget before confirming the request.
        """
        try:
            from token_optimizer import TokenOptimizer
            optimizer = TokenOptimizer()
            optimized_messages = optimizer.optimize_payload(messages)
            
            # Simple token estimation (approximate)
            input_tokens = sum(len(m['content']) // 4 for m in optimized_messages)
            cost = self.estimate_cost(model, input_tokens, target_output_tokens=500) # Assumption
            
            ok, msg = self.check_budget(cost, context)
            return ok, msg, optimized_messages
        except ImportError:
            return True, "Optimizer not found, proceeding with raw messages.", messages

    def check_budget(self, estimated_cost, context="routine"):
        # 1. Check spending velocity (Circuit Breaker)
        tripped, b_msg = self.breaker.is_tripped(estimated_cost)
        if tripped:
            self.trigger_notification(b_msg)
            return False, b_msg

        # 2. Check per-request limit
        limit = self.thresholds.get(context, self.default_threshold)
        if estimated_cost > limit:
            alert_msg = f"ALERT: Estimated cost ${estimated_cost:.4f} exceeds {context} limit of ${limit:.4f}."
            self.trigger_notification(alert_msg)
            return False, alert_msg
        return True, "Budget OK."

    def trigger_notification(self, message):
        print(f"[NOTIFICATION SYSTEM] Sending alert: {message}")
        try:
            from notifier import send_alert_email
            send_alert_email("⚠️ Agent Budget Alert", message)
        except ImportError:
            print("[ERROR] Notifier module not found.")

# Quick Test
if __name__ == "__main__":
    guard = BudgetGuard()
    
    print("--- Per-Request Limit Test ---")
    cost = guard.estimate_cost("claude-3-5-sonnet", 100_000, 10_000)
    ok, msg = guard.check_budget(cost, "routine")
    print(msg)

    print("\n--- Circuit Breaker Velocity Test ---")
    # Simulate rapid calls ($0.60 each, limit $5.00 total)
    for i in range(10):
        ok, msg = guard.check_budget(0.60, "experiment")
        print(f"Request {i+1}: {msg}")
        if not ok: break
