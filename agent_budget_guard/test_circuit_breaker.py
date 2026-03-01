import unittest
import unittest
from unittest.mock import patch
import collections
from circuit_breaker import CircuitBreaker

class TestCircuitBreaker(unittest.TestCase):

    def setUp(self):
        self.initial_time = 0
        self.mock_time_patcher = patch('time.time', side_effect=lambda: self.initial_time)
        self.mock_time = self.mock_time_patcher.start()
        self.addCleanup(self.mock_time_patcher.stop)

    def advance_time(self, seconds):
        self.initial_time += seconds

    def test_token_velocity_exceedance(self):
        print("\n--- Test Case: Token Velocity Exceedance ---")
        cb = CircuitBreaker(token_failure_threshold=1, token_velocity_limit=1000, token_window_seconds=2)
        self.assertEqual(cb.state, "CLOSED")
        self.assertTrue(cb.track_usage(tokens=500))
        self.assertFalse(cb.track_usage(tokens=600)) # Should trip
        self.assertEqual(cb.state, "OPEN")
        print(f"Current State: {cb.state}")

    def test_cost_velocity_exceedance(self):
        print("\n--- Test Case: Cost Velocity Exceedance ---")
        cb = CircuitBreaker(cost_failure_threshold=1, cost_limit=1.0, cost_window_seconds=2)
        self.assertEqual(cb.state, "CLOSED")
        self.assertTrue(cb.track_usage(cost=0.60))
        self.assertFalse(cb.track_usage(cost=0.50)) # Should trip
        self.assertEqual(cb.state, "OPEN")
        print(f"Current State: {cb.state}")

    def test_recovery_timeout_half_open_to_closed(self):
        print("\n--- Test Case: Recovery Timeout (HALF_OPEN -> CLOSED) ---")
        cb = CircuitBreaker(token_failure_threshold=1, recovery_timeout=2, token_velocity_limit=100)
        cb.track_usage(tokens=150) # Trip it
        self.assertEqual(cb.state, "OPEN")
        self.advance_time(2.1) # Wait for recovery timeout
        self.assertEqual(cb.check_state(), "HALF_OPEN") # Should be HALF_OPEN
        cb.record_success() # Successfully handle a request
        self.assertEqual(cb.state, "CLOSED") # Should be CLOSED
        print(f"State after success in HALF_OPEN: {cb.state}")

    def test_no_usage_state_remains_closed(self):
        print("\n--- Test Case: No Usage ---")
        cb = CircuitBreaker()
        self.assertEqual(cb.state, "CLOSED")
        cb.track_usage() # No tokens or cost
        self.assertEqual(cb.state, "CLOSED")
        print(f"State after no usage tracking: {cb.state}")

    def test_multiple_failures_and_recovery(self):
        print("\n--- Test Case: Multiple Failures and Recovery ---")
        cb = CircuitBreaker(cost_failure_threshold=2, recovery_timeout=2, cost_limit=0.1, cost_window_seconds=10)
        self.assertEqual(cb.state, "CLOSED")
        # 1st failure: cost=0.2, exceeds 0.1 limit. cost_failures = 1. Circuit should still be CLOSED.
        self.assertFalse(cb.track_usage(cost=0.2))
        self.assertEqual(cb.state, "CLOSED") # Still closed because threshold is 2

        # 2nd failure: cost=0.2, exceeds 0.1 limit. cost_failures = 2. Circuit should OPEN.
        self.assertFalse(cb.track_usage(cost=0.2))
        self.assertEqual(cb.state, "OPEN")
        self.advance_time(2.1)
        self.assertEqual(cb.check_state(), "HALF_OPEN") # HALF_OPEN
        cb.record_success()
        self.assertEqual(cb.state, "CLOSED") # CLOSED
        print(f"State after success: {cb.state}")

    def test_token_and_cost_failures_independent(self):
        print("\n--- Test Case: Independent Token and Cost Failures ---")
        cb = CircuitBreaker(token_failure_threshold=1, cost_failure_threshold=1,
                            token_velocity_limit=10, cost_limit=0.1,
                            token_window_seconds=1, cost_window_seconds=1)
        self.assertEqual(cb.state, "CLOSED")

        # Trip token circuit
        self.assertFalse(cb.track_usage(tokens=15))
        self.assertEqual(cb.state, "OPEN")
        self.assertEqual(cb.token_failures, 1)
        self.assertEqual(cb.cost_failures, 0)
        
        # Simulate recovery for token circuit
        self.advance_time(cb.recovery_timeout + 0.1)
        cb.check_state() # Should transition to HALF_OPEN
        self.assertEqual(cb.state, "HALF_OPEN")
        cb.record_success() # Now in HALF_OPEN, should reset and close
        self.assertEqual(cb.token_failures, 0)
        self.assertEqual(cb.cost_failures, 0)
        self.assertEqual(cb.state, "CLOSED")

        # Trip cost circuit
        self.assertFalse(cb.track_usage(cost=0.2))
        self.assertEqual(cb.state, "OPEN")
        self.assertEqual(cb.token_failures, 0) # Token failures should remain 0
        self.assertEqual(cb.cost_failures, 1)
        print(f"State after cost trip: {cb.state}")


    def test_usage_at_limit(self):
        print("\n--- Test Case: Usage Exactly at Limit ---")
        cb = CircuitBreaker(token_velocity_limit=100, cost_limit=1.0,
                            token_failure_threshold=1, cost_failure_threshold=1)
        self.assertTrue(cb.track_usage(tokens=100))
        self.assertEqual(cb.state, "CLOSED")
        self.assertTrue(cb.track_usage(cost=1.0))
        self.assertEqual(cb.state, "CLOSED")

    def test_consecutive_usage_exceeds_limit(self):
        print("\n--- Test Case: Consecutive Usage Exceeds Limit ---")
        cb = CircuitBreaker(token_velocity_limit=100, token_window_seconds=10, token_failure_threshold=1)
        self.assertTrue(cb.track_usage(tokens=50))
        self.assertTrue(cb.track_usage(tokens=40))
        self.assertFalse(cb.track_usage(tokens=20)) # 50 + 40 + 20 = 110 > 100
        self.assertEqual(cb.state, "OPEN")

    def test_half_open_failure_reopens_circuit(self):
        print("\n--- Test Case: HALF_OPEN Failure Reopens Circuit ---")
        cb = CircuitBreaker(token_failure_threshold=1, recovery_timeout=2, token_velocity_limit=100)
        cb.track_usage(tokens=150) # Trip it
        self.assertEqual(cb.state, "OPEN")
        self.advance_time(2.1)
        self.assertEqual(cb.check_state(), "HALF_OPEN")
        self.assertFalse(cb.track_usage(tokens=101)) # Fail again in HALF_OPEN
        self.assertEqual(cb.state, "OPEN")

if __name__ == '__main__':
    unittest.main()
