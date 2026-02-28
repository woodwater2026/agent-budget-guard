import time

class CircuitBreaker:
    """
    Implements a Circuit Breaker pattern to prevent token/cost spikes.
    States: CLOSED (normal), OPEN (tripped), HALF_OPEN (recovery testing).
    """
    def __init__(self, failure_threshold=3, recovery_timeout=60, token_velocity_limit=100000):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.token_velocity_limit = token_velocity_limit
        
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = 0
        self.total_tokens_window = 0
        self.window_start_time = time.time()

    def check_state(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                print("[CIRCUIT BREAKER] Transitioning to HALF_OPEN...")
        return self.state

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            print(f"[CIRCUIT BREAKER] CRITICAL: Circuit OPENED due to {self.failures} consecutive failures.")

    def record_success(self):
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            print("[CIRCUIT BREAKER] Recovery successful. Circuit CLOSED.")
        elif self.state == "CLOSED":
            self.failures = 0

    def track_token_velocity(self, tokens):
        # Rolling 60s window for token velocity
        now = time.time()
        if now - self.window_start_time > 60:
            self.total_tokens_window = 0
            self.window_start_time = now
        
        self.total_tokens_window += tokens
        if self.total_tokens_window > self.token_velocity_limit:
            print(f"[CIRCUIT BREAKER] ALERT: Token velocity {self.total_tokens_window} exceeded limit {self.token_velocity_limit}")
            self.record_failure()
            return False
        return True

if __name__ == "__main__":
    cb = CircuitBreaker(failure_threshold=2, token_velocity_limit=1000)
    # Simulate usage
    print(f"Initial State: {cb.check_state()}")
    cb.track_token_velocity(1500) # Exceeds limit
    cb.track_token_velocity(500)  # Second failure
    print(f"Current State: {cb.check_state()}")
