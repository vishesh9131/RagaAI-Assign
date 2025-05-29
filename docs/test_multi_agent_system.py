#!/usr/bin/env python3
"""
Test script to verify the Multi-Agent Financial Assistant System
"""

import requests
import json
import time
from datetime import datetime

def test_orchestrator_status():
    """Test if the orchestrator is running and accessible."""
    try:
        response = requests.get("http://localhost:8011/agents/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ FastAPI Orchestrator: WORKING")
            print(f"   - Version: {data['orchestrator_version']}")
            print(f"   - Available Agents: {len(data['available_agents'])}")
            print(f"   - Language Model: {data['language_model']}")
            return True
        else:
            print("❌ FastAPI Orchestrator: NOT RESPONDING")
            return False
    except Exception as e:
        print(f"❌ FastAPI Orchestrator: ERROR - {e}")
        return False

def test_streamlit_interface():
    """Test if the Streamlit interface is accessible."""
    try:
        response = requests.get("http://localhost:8501")
        if response.status_code == 200:
            print("✅ Streamlit Interface: WORKING")
            print("   - URL: http://localhost:8501")
            return True
        else:
            print("❌ Streamlit Interface: NOT RESPONDING")
            return False
    except Exception as e:
        print(f"❌ Streamlit Interface: ERROR - {e}")
        return False

def test_multi_agent_query():
    """Test a complex query that should trigger multiple agents."""
    query = "What is the current price of Tesla and Apple stocks? Compare their performance and explain market trends."
    
    print(f"\n🧠 Testing Multi-Agent Query:")
    print(f"   Query: '{query}'")
    
    try:
        payload = {
            "query": query,
            "voice_mode": False,
            "include_debug_info": True
        }
        
        response = requests.post(
            "http://localhost:8011/intelligent/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Query Processing: WORKING")
            print(f"   - Response Length: {len(data['response_text'])} characters")
            print(f"   - Confidence: {data['confidence']}")
            print(f"   - Agents Used: {len(data['agents_used'])}")
            
            # Display agent execution details
            print("\n📊 Agent Execution Results:")
            for i, agent in enumerate(data['agents_used'], 1):
                status_emoji = "✅" if agent['status'] == 'completed' else "❌"
                print(f"   {i}. {status_emoji} {agent['agent_name']}: {agent['status']}")
                print(f"      Description: {agent['description']}")
                if agent.get('error'):
                    print(f"      Error: {agent['error']}")
            
            # Show response preview
            print(f"\n💬 Response Preview:")
            print(f"   {data['response_text'][:200]}...")
            
            return len(data['agents_used']) >= 2  # Success if multiple agents used
        else:
            print(f"❌ Query Processing: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query Processing: ERROR - {e}")
        return False

def test_specific_agents():
    """Test specific agent functionality."""
    test_queries = [
        {
            "name": "Market Data Agent",
            "query": "Get the current price of AAPL stock",
            "expected_agents": ["market_data"]
        },
        {
            "name": "Analysis Agent", 
            "query": "Compare Tesla vs Apple stock performance",
            "expected_agents": ["analysis"]
        },
        {
            "name": "Multiple Agents",
            "query": "Analyze NVIDIA stock trends and explain the current market situation with latest news",
            "expected_agents": ["market_data", "analysis", "scraping", "explanation"]
        }
    ]
    
    print(f"\n🔬 Testing Specific Agent Combinations:")
    
    for test in test_queries:
        print(f"\n   Testing: {test['name']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            payload = {
                "query": test['query'],
                "voice_mode": False,
                "include_debug_info": True
            }
            
            response = requests.post(
                "http://localhost:8011/intelligent/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_names = [agent['agent_name'] for agent in data['agents_used']]
                
                print(f"   ✅ Triggered Agents: {agent_names}")
                print(f"   ✅ All Completed: {all(a['status'] == 'completed' for a in data['agents_used'])}")
                
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Run comprehensive multi-agent system tests."""
    print("🚀 Multi-Agent Financial Assistant System Test")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Basic connectivity
    print("\n1. 🔌 Testing System Connectivity:")
    orchestrator_ok = test_orchestrator_status()
    streamlit_ok = test_streamlit_interface()
    
    if not orchestrator_ok:
        print("\n❌ Cannot proceed - Orchestrator not running!")
        return
    
    # Test 2: Multi-agent query processing
    print("\n2. 🤖 Testing Multi-Agent Query Processing:")
    multi_agent_ok = test_multi_agent_query()
    
    # Test 3: Specific agent functionality
    test_specific_agents()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST SUMMARY:")
    print(f"   FastAPI Orchestrator: {'✅ WORKING' if orchestrator_ok else '❌ FAILED'}")
    print(f"   Streamlit Interface: {'✅ WORKING' if streamlit_ok else '❌ FAILED'}")
    print(f"   Multi-Agent Processing: {'✅ WORKING' if multi_agent_ok else '❌ FAILED'}")
    
    if orchestrator_ok and multi_agent_ok:
        print("\n🎉 SUCCESS: Multi-Agent System is fully operational!")
        print("\n🌐 Access Points:")
        print("   • Streamlit UI: http://localhost:8501")
        print("   • API Docs: http://localhost:8011/docs")
        print("   • Agent Status: http://localhost:8011/agents/status")
    else:
        print("\n⚠️  Some components are not working properly.")

if __name__ == "__main__":
    main() 