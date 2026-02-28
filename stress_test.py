import time
from orchestrator import GuardOrchestrator

def run_stress_test():
    orchestrator = GuardOrchestrator()
    print("🌊🌲 Agent Budget Guard - Financial Stress Test\n")
    
    # Scenario 1: Recursive Loop Simulation
    print("[TEST 1] Simulating Recursive Loop ($0.60 per call)...")
    for i in range(12):
        messages = [{"role": "user", "content": f"Loop iteration {i}"}]
        result = orchestrator.process_request("claude-3-5-sonnet", messages, context="experiment")
        
        if result["status"] == "blocked":
            print(f"✅ Success: System BLOCKED at iteration {i+1}. Reason: {result['message']}")
            break
        else:
            print(f"Request {i+1}: OK (Estimated Cost: ${result['estimated_cost']:.4f})")
        time.sleep(0.1)

    # Scenario 2: High-Value Target
    print("\n[TEST 2] Simulating High-Value Request over $5.00 limit...")
    huge_prompt = "A" * 10_000_000 # Massive fake prompt
    messages = [{"role": "user", "content": huge_prompt}]
    result = orchestrator.process_request("claude-3-5-sonnet", messages, context="high_roi")
    
    if result["status"] == "blocked":
        print(f"✅ Success: High-value request BLOCKED. {result['message']}")
    else:
        print(f"❌ Failure: High-value request allowed! Cost: ${result['estimated_cost']:.4f}")

if __name__ == "__main__":
    run_stress_test()
