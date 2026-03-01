import unittest
import json
import os
from orchestrator import GuardOrchestrator

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        # Create a temp config for testing
        self.config_path = "test_config.json"
        with open(self.config_path, "w") as f:
            json.dump({
                "default_threshold": 0.01,
                "thresholds": {"routine": 0.01},
                "notification_email": "test@example.com"
            }, f)
        self.orchestrator = GuardOrchestrator(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_full_flow_blocked_and_recommended(self):
        # 1. Provide a message that would be expensive on Sonnet
        messages = [{"role": "user", "content": "x" * 100000}] # Very long
        
        # 2. Process with a model that should exceed budget
        result = self.orchestrator.process_request("claude-3-5-sonnet", messages, "routine")
        
        # 3. Verify it's blocked and recommends a cheaper model
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["recommended_model"], "gemini-flash-1.5")
        print(f"E2E Test Success: Blocked Sonnet, Recommended {result['recommended_model']}")

if __name__ == "__main__":
    unittest.main()
