import argparse
import sys
import json
from orchestrator import GuardOrchestrator

def main():
    parser = argparse.ArgumentParser(description="🌊🌲 Agent Budget Guard CLI - 2026 Edition")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if a request is within budget")
    check_parser.add_argument("--model", required=True, help="Target model name")
    check_parser.add_argument("--prompt", required=True, help="The content of the prompt")
    check_parser.add_argument("--context", default="routine", choices=["routine", "high_roi", "experiment"], help="Task context")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show current configuration")

    args = parser.parse_args()

    orchestrator = GuardOrchestrator()

    if args.command == "check":
        messages = [{"role": "user", "content": args.prompt}]
        result = orchestrator.process_request(args.model, messages, args.context)
        print(json.dumps(result, indent=4))
    
    elif args.command == "config":
        with open("config.json", "r") as f:
            print(f.read())
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
