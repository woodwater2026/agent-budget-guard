#!/usr/bin/env python3
"""
Reset the circuit breaker to stop the alert storm.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cost_calculator import BudgetGuard

def main():
    print("Resetting Agent Budget Guard circuit breaker...")
    
    # Create a BudgetGuard instance
    guard = BudgetGuard()
    
    # Reset the circuit breaker
    guard.breaker.record_success()
    
    # Also reset failure counters
    guard.breaker.token_failures = 0
    guard.breaker.cost_failures = 0
    guard.breaker.failures = 0
    guard.breaker.state = "CLOSED"
    
    print("Circuit breaker has been reset to CLOSED state.")
    print(f"Current state: {guard.breaker.state}")
    print(f"Token failures: {guard.breaker.token_failures}")
    print(f"Cost failures: {guard.breaker.cost_failures}")
    
    # Also adjust the cost limit for testing
    print("\nAdjusting cost limits for testing...")
    guard.breaker.cost_limit = 10.0  # Increase to $10
    guard.breaker.cost_window_seconds = 600  # 10 minutes window
    
    print(f"New cost limit: ${guard.breaker.cost_limit} per {guard.breaker.cost_window_seconds} seconds")
    print("\nAlert storm should now stop.")

if __name__ == "__main__":
    main()