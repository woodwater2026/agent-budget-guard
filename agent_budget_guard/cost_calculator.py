import sys
import json
import os
import time

from circuit_breaker import CircuitBreaker

class BudgetGuard:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        self.breaker = CircuitBreaker(cost_limit=5.00, cost_window_seconds=300) # $5 limit every 5 mins
        
        # 2026 Model Pricing Metadata (per 1M tokens)
        self.model_pricing = {
            "gemini-flash-1.5": {"input": 0.075, "output": 0.30, "batch_discount": 0.5},
            "deepseek-v3": {"input": 0.14, "output": 0.28, "batch_discount": 0.5},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "batch_discount": 0.0}
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

    def estimate_cost(self, model, input_tokens, output_tokens, is_batch=False):
        pricing = self.model_pricing.get(model)
        if not pricing:
            return 0.0
        
        multiplier = 1.0 - pricing.get("batch_discount", 0.0) if is_batch else 1.0
        cost = ((input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])) * multiplier
        return cost

    def recommend_model(self, input_tokens, target_output_tokens, max_budget=0.01):
        """
        Suggests the best model based on the provided budget.
        Now includes a 'downgrade_reason' for transparency.
        """
        recommendations = []
        for model, pricing in self.model_pricing.items():
            est_cost = self.estimate_cost(model, input_tokens, target_output_tokens)
            if est_cost <= max_budget:
                recommendations.append({"model": model, "cost": est_cost})
        
        # Sort by cost (ascending)
        recommendations.sort(key=lambda x: x["cost"])
        
        if recommendations:
            best = recommendations[0]
            return best["model"], best["cost"], "Under budget"
        return None, 0.0, "No model found within budget"

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
        current_circuit_state = self.breaker.check_state()
        if current_circuit_state == "OPEN":
            msg = "[CIRCUIT BREAKER] Request blocked: Circuit is OPEN due to prior budget breaches."
            self.trigger_notification(msg)
            return False, msg
        
        # Track usage; this will call record_failure internally if limits are exceeded
        usage_within_limits = self.breaker.track_usage(cost=estimated_cost)
        
        new_circuit_state = self.breaker.check_state()

        if not usage_within_limits or new_circuit_state == "OPEN":
            # If track_usage returned False, or it turned OPEN, then a limit was hit
            msg = f"[CIRCUIT BREAKER] Request blocked: Circuit is now {new_circuit_state} due to cost velocity exceeding limits."
            self.trigger_notification(msg)
            return False, msg

        # If we reach here, usage was within limits (track_usage returned True)
        # and the circuit is not OPEN (it could be CLOSED or HALF_OPEN)
        if current_circuit_state == "HALF_OPEN" and new_circuit_state == "CLOSED":
            # Successful request in HALF_OPEN state leads to CLOSED
            self.breaker.record_success()
            print("[CIRCUIT BREAKER] HALF_OPEN to CLOSED transition due to successful request.")

        # 2. Check per-request limit (only if circuit is not open)
        limit = self.thresholds.get(context, self.default_threshold)
        if estimated_cost > limit:
            alert_msg = f"ALERT: Estimated cost ${estimated_cost:.4f} exceeds {context} limit of ${limit:.4f}."
            self.trigger_notification(alert_msg)
            self.breaker.record_failure(reason="per_request_limit", failure_type="cost") # Record as a cost failure
            return False, alert_msg
        
        # If all checks pass and state was HALF_OPEN, record success (handled above if it transitions to CLOSED)
        # If it's CLOSED and passes, nothing special to do.
        if new_circuit_state == "HALF_OPEN" and usage_within_limits:
            self.breaker.record_success() # If in half-open and successful, close it.
        
        return True, "Budget OK."

    def trigger_notification(self, message):
        print(f"[NOTIFICATION SYSTEM] Sending alert: {message}")
        try:
            from notifier import send_alert_email
            send_alert_email("⚠️ Agent Budget Alert", message)
        except ImportError:
            print("[ERROR] Notifier module not found.")

    def get_meter_data(self):
        """
        Export usage data for external micro-billing systems (2026 standard).
        """
        return {
            "total_window_spending": sum(entry[1] for entry in self.breaker.history),
            "window_seconds": self.breaker.time_window,
            "models_tracked": list(self.model_pricing.keys())
        }

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
