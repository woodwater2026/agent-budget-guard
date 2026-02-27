import sys
import json
import os

class BudgetGuard:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        
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

    def check_budget(self, estimated_cost, context="routine"):
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
    # Test estimation for 100k input / 10k output on Sonnet
    cost = guard.estimate_cost("claude-3-5-sonnet", 100_000, 10_000)
    print(f"Estimated Sonnet Cost: ${cost:.4f}")
    ok, msg = guard.check_budget(cost, "routine")
    print(msg)
