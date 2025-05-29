#!/usr/bin/env python3
"""Debug script to test orchestrator components independently."""

import re
import asyncio
import uuid
from orchestrator_fastapi import QueryRouter, execute_market_agent, language_agent, process_intelligent_query

async def test_query_router():
    """Test the query router independently."""
    router = QueryRouter()
    test_query = "What is the current price of AAPL stock?"
    
    print(f"Testing query: '{test_query}'")
    agent_types = router.classify_query(test_query)
    print(f"Matched agent types: {agent_types}")
    
    return agent_types

async def test_market_agent():
    """Test the market agent independently."""
    print("\nTesting market agent execution...")
    try:
        result = await execute_market_agent(
            "What is the current price of AAPL stock?", 
            "User wants AAPL stock price", 
            "test-session-123"
        )
        print(f"Market agent result: {result}")
        return result
    except Exception as e:
        print(f"Market agent failed: {e}")
        return None

async def test_language_agent():
    """Test the language agent independently."""
    print("\nTesting language agent...")
    try:
        result = language_agent.explain("What is AAPL stock?", "general")
        print(f"Language agent result: {result}")
        return result
    except Exception as e:
        print(f"Language agent failed: {e}")
        return None

async def test_full_orchestrator():
    """Test the full orchestrator process."""
    print("\n=== Testing Full Orchestrator ===")
    try:
        result = await process_intelligent_query("What is the current price of AAPL stock?", False, False)
        print(f"Orchestrator result:")
        print(f"  Response: {result.response_text[:100]}...")
        print(f"  Agents used: {len(result.agents_used)}")
        print(f"  Session ID: {result.session_id}")
        print(f"  Confidence: {result.confidence}")
        
        for i, agent in enumerate(result.agents_used):
            print(f"  Agent {i+1}: {agent.agent_name} - {agent.status}")
        
        return result
    except Exception as e:
        print(f"Full orchestrator failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("=== Orchestrator Debug Test ===")
    
    # Test 1: Query Router
    agent_types = await test_query_router()
    
    # Test 2: Language Agent
    await test_language_agent()
    
    # Test 3: Market Agent (if market_data was matched)
    if "market_data" in agent_types:
        await test_market_agent()
    else:
        print("Market agent not matched, skipping test")
    
    # Test 4: Full Orchestrator
    await test_full_orchestrator()

if __name__ == "__main__":
    asyncio.run(main()) 