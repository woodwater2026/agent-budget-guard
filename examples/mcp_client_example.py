"""
Agent Budget Guard MCP Server Client Example

This shows how to use the Agent Budget Guard MCP server from a client application.
The MCP server provides budget tracking tools that can be used by any MCP-compatible client.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_budget_tools():
    """Example of using Agent Budget Guard MCP tools."""
    
    # Configure the MCP server (Agent Budget Guard)
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "agent_budget_guard.mcp_server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("Connected to Agent Budget Guard MCP Server")
            print("=" * 50)
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            print()
            
            # Example 1: Track a budget entry
            print("Example 1: Tracking budget usage")
            print("-" * 30)
            
            track_result = await session.call_tool(
                "budget_track",
                arguments={
                    "model": "anthropic/claude-sonnet-4-6",
                    "input_tokens": 5000,
                    "output_tokens": 800,
                    "task": "code-review"
                }
            )
            
            print(f"Track result: {track_result.content[0].text}")
            print()
            
            # Example 2: Check budget before expensive task
            print("Example 2: Checking budget before expensive task")
            print("-" * 30)
            
            check_result = await session.call_tool(
                "budget_check",
                arguments={
                    "model": "anthropic/claude-sonnet-4-6",
                    "estimated_tokens": 50000,
                    "task": "large-dataset-analysis"
                }
            )
            
            check_data = json.loads(check_result.content[0].text)
            print(f"Budget check: {check_data['decision']}")
            print(f"Estimated cost: ${check_data['estimated_usd']:.4f}")
            print(f"Today's total: ${check_data['today_usd']:.2f}")
            print()
            
            # Example 3: Get budget summary
            print("Example 3: Getting budget summary")
            print("-" * 30)
            
            summary_result = await session.call_tool(
                "budget_summary",
                arguments={
                    "days": 7
                }
            )
            
            summary_data = json.loads(summary_result.content[0].text)
            print(f"7-day summary:")
            print(f"  Total spend: ${summary_data['total_usd']:.2f}")
            print(f"  Calls: {summary_data['calls']}")
            print(f"  By model: {json.dumps(summary_data['by_model'], indent=4)}")
            print(f"  By task: {json.dumps(summary_data['by_task'], indent=4)}")

if __name__ == "__main__":
    print("Agent Budget Guard MCP Client Example")
    print("This demonstrates how to use the MCP server from any client.")
    print()
    
    # Run the async example
    asyncio.run(run_budget_tools())