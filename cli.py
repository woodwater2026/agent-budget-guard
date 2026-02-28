import argparse
import sys
import json
from orchestrator import GuardOrchestrator

def main():
    parser = argparse.ArgumentParser(description="Agent Budget Guard CLI - Secure your AI spending.")
    parser.add_argument("--model", type=str, default="claude-3-5-sonnet", help="Target LLM model")
    parser.add_argument("--prompt", type=str, required=True, help="The prompt to analyze")
    parser.add_argument("--context", type=str, default="routine", choices=["routine", "high_roi", "experiment"], help="Task context")
    
    args = parser.parse_args()
    
    orchestrator = GuardOrchestrator()
    messages = [{"role": "user", "content": args.prompt}]
    
    print(f"🌊🌲 Agent Budget Guard (V0.2.1-Alpha)")
    print(f"Checking request for model: {args.model} under context: {args.context}...\n")
    
    result = orchestrator.process_request(args.model, messages, args.context)
    
    if result["status"] == "ok":
        print(f"✅ Budget OK. Estimated cost: ${result['estimated_cost']:.4f}")
        print("-" * 30)
        print("Ready to proceed.")
    else:
        print(f"❌ BLOCKED: {result['message']}")
        if result.get("recommended_model"):
            print(f"💡 Recommendation: Use '{result['recommended_model']}' instead.")
            print(f"💰 Estimated Saving: {result['estimated_saving']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
