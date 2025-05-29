#!/usr/bin/env python3
"""Test script to verify the fixed interface and orchestrator are working."""

import requests
import json
import time

def test_orchestrator():
    """Test the FastAPI orchestrator."""
    try:
        print("🔍 Testing FastAPI Orchestrator...")
        response = requests.get("http://localhost:8011/agents/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ FastAPI Orchestrator: WORKING")
            print(f"   Version: {data.get('orchestrator_version')}")
            print(f"   Available Agents: {len(data.get('available_agents', []))}")
            print(f"   Language Model: {data.get('language_model')}")
            return True
        else:
            print(f"❌ FastAPI Orchestrator: Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI Orchestrator: Connection failed - {e}")
        return False

def test_streamlit():
    """Test the Streamlit interface."""
    try:
        print("\n🔍 Testing Streamlit Interface...")
        response = requests.get("http://localhost:8501/", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit Interface: WORKING")
            print("   Access at: http://localhost:8501")
            return True
        else:
            print(f"❌ Streamlit Interface: Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit Interface: Connection failed - {e}")
        return False

def test_query():
    """Test a simple query through the orchestrator."""
    try:
        print("\n🔍 Testing Query Processing...")
        payload = {
            "query": "What's the current price of AAPL?",
            "voice_mode": False,
            "include_debug_info": False
        }
        
        response = requests.post(
            "http://localhost:8011/intelligent/query", 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query Processing: WORKING")
            print(f"   Response: {data.get('response_text', '')[:100]}...")
            print(f"   Confidence: {data.get('confidence', 0):.1%}")
            print(f"   Agents Used: {len(data.get('agents_used', []))}")
            return True
        else:
            print(f"❌ Query Processing: Failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query Processing: Failed - {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 AI Financial Assistant - System Test")
    print("=" * 50)
    
    tests = [
        test_orchestrator,
        test_streamlit,
        test_query
    ]
    
    results = []
    for test in tests:
        results.append(test())
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   FastAPI Orchestrator: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"   Streamlit Interface: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"   Query Processing: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED! System is ready to use.")
        print("🌐 Visit: http://localhost:8501")
    else:
        print("\n⚠️  Some tests failed. Check the services.")

if __name__ == "__main__":
    main() 