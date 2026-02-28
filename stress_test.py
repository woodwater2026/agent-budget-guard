import time
from cost_calculator import BudgetGuard

def run_stress_test():
    print("🌊🌲 Starting Agent Budget Guard Stress Test...")
    guard = BudgetGuard()
    
    # Pre-set a low limit for testing velocity
    guard.breaker.max_spending = 2.00 # $2 per 5 mins
    
    print(f"Test Parameters: Velocity Limit ${guard.breaker.max_spending} / {guard.breaker.time_window}s")
    
    requests = [
        ("claude-3-5-sonnet", 100000, 1000), # ~$0.315
        ("claude-3-5-sonnet", 200000, 2000), # ~$0.630
        ("claude-3-5-sonnet", 300000, 3000), # ~$0.945
        ("claude-3-5-sonnet", 400000, 4000), # ~$1.260 -> Should trip!
    ]
    
    for i, (model, in_t, out_t) in enumerate(requests):
        cost = guard.estimate_cost(model, in_t, out_t)
        print(f"\n[Request {i+1}] Model: {model}, Est. Cost: ${cost:.4f}")
        
        ok, msg = guard.check_budget(cost, context="high_roi")
        if ok:
            print(f"✅ Success: {msg}")
        else:
            print(f"🛑 FAILED (Expected): {msg}")
            break

if __name__ == "__main__":
    run_stress_test()
