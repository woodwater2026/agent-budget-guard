import unittest
from unittest.mock import patch
import time
from cost_calculator import BudgetGuard
from circuit_breaker import CircuitBreaker # Import the external CircuitBreaker

class TestBudgetGuard(unittest.TestCase):
    def setUp(self):
        # BudgetGuard now loads from config.json by default
        # For testing, we might want to override some defaults or mock config loading
        self.guard = BudgetGuard()

    def test_cost_estimation(self):
        # Claude 3.5 Sonnet: $3.00/1M in, $15.00/1M out
        # 100k in, 10k out = (0.1 * 3.0) + (0.01 * 15.0) = 0.3 + 0.15 = 0.45
        cost = self.guard.estimate_cost("claude-3-5-sonnet", 100_000, 10_000)
        self.assertAlmostEqual(cost, 0.45)

    def test_budget_check_pass(self):
        # Reset circuit breaker for a clean test
        self.guard.breaker = CircuitBreaker()
        ok, msg = self.guard.check_budget(0.04, "routine")
        self.assertTrue(ok)
        self.assertEqual(msg, "Budget OK.")
        self.assertEqual(self.guard.breaker.check_state(), "CLOSED")

    def test_budget_check_fail_per_request_limit(self):
        # Reset circuit breaker for a clean test
        self.guard.breaker = CircuitBreaker()
        ok, msg = self.guard.check_budget(0.06, "routine")
        self.assertFalse(ok)
        self.assertIn("ALERT", msg)
        # Should record a failure for per-request limit
        self.assertEqual(self.guard.breaker.cost_failures, 1)
        self.assertEqual(self.guard.breaker.check_state(), "CLOSED") # Should still be closed if threshold is 1

    @patch('time.time', return_value=1000.0) # Mock time for consistent testing
    def test_circuit_breaker_tripping_cost_velocity(self, mock_time):
        # Configure a circuit breaker that trips easily
        self.guard.breaker = CircuitBreaker(cost_limit=0.50, cost_window_seconds=10, cost_failure_threshold=1)
        
        # First cost should be fine
        ok1, msg1 = self.guard.check_budget(0.30, "experiment")
        self.assertTrue(ok1)
        self.assertEqual(self.guard.breaker.check_state(), "CLOSED")

        # Second cost within the window should trip it
        mock_time.return_value += 1 # Advance time slightly within the window
        ok2, msg2 = self.guard.check_budget(0.30, "experiment")
        self.assertFalse(ok2)
        self.assertIn("Circuit is now OPEN", msg2)
        self.assertEqual(self.guard.breaker.check_state(), "OPEN")
        self.assertEqual(self.guard.breaker.cost_failures, 1) # Only one failure needed to open

        # Further requests should be blocked immediately
        mock_time.return_value += 1 # Advance time
        ok3, msg3 = self.guard.check_budget(0.10, "experiment")
        self.assertFalse(ok3)
        self.assertIn("Circuit is OPEN", msg3)
        self.assertEqual(self.guard.breaker.check_state(), "OPEN")

    @patch('time.time')
    def test_circuit_breaker_recovery(self, mock_time):
        mock_time.return_value = 1000.0
        # Configure a circuit breaker with a short recovery timeout
        self.guard.breaker = CircuitBreaker(cost_limit=0.50, cost_window_seconds=10, cost_failure_threshold=1, recovery_timeout=5)

        # 1. Trip the circuit breaker
        ok1, _ = self.guard.check_budget(0.30, "experiment")
        mock_time.return_value += 1
        ok2, _ = self.guard.check_budget(0.30, "experiment")
        self.assertFalse(ok2)
        self.assertEqual(self.guard.breaker.check_state(), "OPEN")

        # 2. Advance time past recovery timeout AND cost window to clear old events
        mock_time.return_value = 1000.0 + 1 + self.guard.breaker.recovery_timeout + self.guard.breaker.cost_window_seconds + 1 # Ensures old events are cleared
        self.assertEqual(self.guard.breaker.check_state(), "HALF_OPEN") # Check state should transition it

        # 3. Make a successful call in HALF_OPEN state
        ok3, msg3 = self.guard.check_budget(0.10, "experiment") # This should be fine
        self.assertTrue(ok3)
        self.assertIn("Budget OK", msg3)
        self.assertEqual(self.guard.breaker.check_state(), "CLOSED") # Should transition to CLOSED

        # 4. Trip again, then fail in HALF_OPEN (should go back to OPEN)
        self.guard.breaker = CircuitBreaker(cost_limit=0.50, cost_window_seconds=10, cost_failure_threshold=1, recovery_timeout=5)
        mock_time.return_value = 2000.0 # Reset time
        self.guard.check_budget(0.30, "experiment")
        mock_time.return_value += 1
        self.guard.check_budget(0.30, "experiment") # Trips it
        self.assertEqual(self.guard.breaker.check_state(), "OPEN")
        
        mock_time.return_value += 5.1 # Advance to HALF_OPEN
        self.assertEqual(self.guard.breaker.check_state(), "HALF_OPEN")

        # Now, simulate a failure in HALF_OPEN state
        mock_time.return_value += 1 # Small advance
        ok4, msg4 = self.guard.check_budget(0.60, "experiment") # This will exceed cost_limit
        self.assertFalse(ok4)
        self.assertIn("Circuit is now OPEN", msg4)
        self.assertEqual(self.guard.breaker.check_state(), "OPEN") # Should go back to OPEN

if __name__ == "__main__":
    unittest.main()
