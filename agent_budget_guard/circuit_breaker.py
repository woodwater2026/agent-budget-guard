import time
import collections

class CircuitBreaker:
    """
    Implements a Circuit Breaker pattern to prevent token/cost spikes.
    States: CLOSED (normal), OPEN (tripped), HALF_OPEN (recovery testing).
    Tracks both token velocity and cost velocity.
    """
    def __init__(
        self, 
        recovery_timeout=300,  # 5 minutes for recovery
        token_velocity_limit=100000, 
        token_window_seconds=60, # 1 minute for token velocity
        token_failure_threshold=3,
        cost_limit=5.0,        # $5 cost limit
        cost_window_seconds=300, # 5 minutes for cost velocity
        cost_failure_threshold=3
    ):
        self.token_failure_threshold = token_failure_threshold
        self.cost_failure_threshold = cost_failure_threshold
        self.recovery_timeout = recovery_timeout
        self.token_velocity_limit = token_velocity_limit
        self.token_window_seconds = token_window_seconds
        self.cost_limit = cost_limit
        self.cost_window_seconds = cost_window_seconds
        
        self.state = "CLOSED"
        # Track overall failures for the old mechanism, but now
        # we'll use specific token_failures and cost_failures
        self.failures = 0 
        self.token_failures = 0
        self.cost_failures = 0
        self.last_failure_time = 0

        # For token velocity tracking
        self.token_events = collections.deque() # Stores (timestamp, tokens_used)

        # For cost velocity tracking
        self.cost_events = collections.deque() # Stores (timestamp, cost_incurred)

    def _clean_old_events(self, event_deque, window_seconds):
        now = time.time()
        while event_deque and event_deque[0][0] < now - window_seconds:
            event_deque.popleft()

    def _get_current_sum(self, event_deque):
        return sum(event[1] for event in event_deque)

    def check_state(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                print("[CIRCUIT BREAKER] Transitioning to HALF_OPEN...")
        return self.state

    def record_failure(self, reason="unknown", failure_type="general"):
        self.last_failure_time = time.time()

        if failure_type == "token":
            self.token_failures += 1
            if self.token_failures >= self.token_failure_threshold:
                self.state = "OPEN"
                print(f"[CIRCUIT BREAKER] CRITICAL: Circuit OPENED due to {reason} after {self.token_failures} token-related failures.")
        elif failure_type == "cost":
            self.cost_failures += 1
            if self.cost_failures >= self.cost_failure_threshold:
                self.state = "OPEN"
                print(f"[CIRCUIT BREAKER] CRITICAL: Circuit OPENED due to {reason} after {self.cost_failures} cost-related failures.")
        else:
            # Fallback for general failures, if any (can be removed if not needed)
            self.failures += 1
            # Using the minimum of the two thresholds as a general threshold for now
            # This part needs refinement if general failures are distinct
            general_failure_threshold = min(self.token_failure_threshold, self.cost_failure_threshold)
            if self.failures >= general_failure_threshold:
                 self.state = "OPEN"
                 print(f"[CIRCUIT BREAKER] CRITICAL: Circuit OPENED due to {reason} after {self.failures} general failures.")

        if self.state == "OPEN":
            print(f"[CIRCUIT BREAKER] Circuit is now OPEN due to {failure_type} failure.")

    def record_success(self):
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.token_failures = 0
            self.cost_failures = 0
            print("[CIRCUIT BREAKER] Recovery successful. Circuit CLOSED.")
        elif self.state == "CLOSED":
            self.token_failures = 0
            self.cost_failures = 0

    def track_usage(self, tokens=0, cost=0.0):
        """
        Tracks token and cost usage. Returns True if within limits, False if circuit should open.
        """
        now = time.time()

        # Token velocity check
        if tokens > 0:
            self.token_events.append((now, tokens))
            self._clean_old_events(self.token_events, self.token_window_seconds)
            current_tokens = self._get_current_sum(self.token_events)
            if current_tokens > self.token_velocity_limit:
                print(f"[CIRCUIT BREAKER] ALERT: Token velocity ({current_tokens} tokens) exceeded limit ({self.token_velocity_limit} tokens) in {self.token_window_seconds}s.")
                self.record_failure(reason="token_velocity", failure_type="token")
                return False

        # Cost velocity check
        if cost > 0.0:
            self.cost_events.append((now, cost))
            self._clean_old_events(self.cost_events, self.cost_window_seconds)
            current_cost = self._get_current_sum(self.cost_events)
            if current_cost > self.cost_limit:
                print(f"[CIRCUIT BREAKER] ALERT: Cost velocity (${current_cost:.2f}) exceeded limit (${self.cost_limit:.2f}) in {self.cost_window_seconds}s.")
                self.record_failure(reason="cost_velocity", failure_type="cost")
                return False
        
        return True

if __name__ == "__main__":
    # Test Case 1: Token velocity exceeding limit
    print("\n--- Test Case 1: Token Velocity Exceedance ---")
    cb_tokens = CircuitBreaker(token_failure_threshold=1, token_velocity_limit=1000, token_window_seconds=2)
    print(f"Initial State: {cb_tokens.check_state()}")
    assert cb_tokens.track_usage(tokens=500) == True
    assert cb_tokens.track_usage(tokens=600) == False # Should trip
    print(f"Current State: {cb_tokens.check_state()}")

    # Test Case 2: Cost velocity exceeding limit
    print("\n--- Test Case 2: Cost Velocity Exceedance ---")
    cb_cost = CircuitBreaker(cost_failure_threshold=1, cost_limit=1.0, cost_window_seconds=2)
    print(f"Initial State: {cb_cost.check_state()}")
    assert cb_cost.track_usage(cost=0.60) == True
    assert cb_cost.track_usage(cost=0.50) == False # Should trip
    print(f"Current State: {cb_cost.check_state()}")

    # Test Case 3: Recovery timeout (HALF_OPEN -> CLOSED)
    print("\n--- Test Case 3: Recovery Timeout ---")
    cb_recovery = CircuitBreaker(token_failure_threshold=1, recovery_timeout=2, token_velocity_limit=100)
    cb_recovery.track_usage(tokens=150) # Trip it
    print(f"State after trip: {cb_recovery.check_state()}")
    time.sleep(2.1) # Wait for recovery timeout
    print(f"State after timeout: {cb_recovery.check_state()}") # Should be HALF_OPEN
    cb_recovery.record_success() # Successfully handle a request
    print(f"State after success in HALF_OPEN: {cb_recovery.check_state()}") # Should be CLOSED

    # Test Case 4: No usage, just check state
    print("\n--- Test Case 4: No Usage ---")
    cb_no_usage = CircuitBreaker()
    print(f"Initial State: {cb_no_usage.check_state()}")
    cb_no_usage.track_usage() # No tokens or cost
    print(f"State after no usage tracking: {cb_no_usage.check_state()}")

    # Test Case 5: Multiple failures and recovery
    print("\n--- Test Case 5: Multiple Failures and Recovery ---")
    cb_multi_fail = CircuitBreaker(cost_failure_threshold=2, recovery_timeout=2, cost_limit=0.1, cost_window_seconds=10)
    print(f"Initial State: {cb_multi_fail.check_state()}")
    # 1st failure: cost=0.2, exceeds 0.1 limit. cost_failures = 1. Circuit should still be CLOSED.
    assert cb_multi_fail.track_usage(cost=0.2) == False
    print(f"State after 1st failure: {cb_multi_fail.check_state()}")

    # 2nd failure: cost=0.2, exceeds 0.1 limit. cost_failures = 2. Circuit should OPEN.
    assert cb_multi_fail.track_usage(cost=0.2) == False
    print(f"State after 2 failures: {cb_multi_fail.check_state()}")
    time.sleep(2.1)
    print(f"State after recovery timeout: {cb_multi_fail.check_state()}") # HALF_OPEN
    cb_multi_fail.record_success()
    print(f"State after success: {cb_multi_fail.check_state()}") # CLOSED
