#!/usr/bin/env python3
"""
Test script to verify Netlify API integration
"""
import requests
import json
import time

# Test URLs
BASE_URL = "https://ai-financial-assistant-multi-agent.netlify.app"
API_BASE = f"{BASE_URL}/api"

def test_api_endpoints():
    """Test all API endpoints"""
    print("🧪 Testing AI Financial Assistant API Integration")
    print("=" * 60)
    
    # Test 1: Landing page
    print("1. Testing landing page...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200 and "AI Financial Assistant" in response.text:
            print("   ✅ Landing page: OK")
        else:
            print(f"   ❌ Landing page: Failed (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Landing page: Error - {e}")
    
    # Test 2: Direct function access
    print("\n2. Testing direct function access...")
    try:
        function_url = f"{BASE_URL}/.netlify/functions/orchestrator"
        response = requests.get(function_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Function endpoint: Accessible")
        else:
            print(f"   ❌ Function endpoint: Failed (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Function endpoint: Error - {e}")
    
    # Test 3: API endpoints through redirects
    print("\n3. Testing API endpoints...")
    
    # Test agents/status
    try:
        status_url = f"{API_BASE}/agents/status"
        response = requests.get(status_url, timeout=10)
        print(f"   GET {status_url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Agents status: OK")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Response (text): {response.text[:200]}...")
        else:
            print(f"   ❌ Agents status: Failed")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Agents status: Error - {e}")
    
    # Test intelligent/query
    print("\n   Testing intelligent query...")
    try:
        query_url = f"{API_BASE}/intelligent/query"
        payload = {"query": "What is Apple stock price?", "voice_mode": False}
        response = requests.post(query_url, json=payload, timeout=30)
        print(f"   POST {query_url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Intelligent query: OK")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"   Response (text): {response.text[:300]}...")
        else:
            print(f"   ❌ Intelligent query: Failed")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Intelligent query: Error - {e}")

def test_streamlit_config():
    """Test Streamlit configuration"""
    print("\n4. Testing Streamlit configuration...")
    print("=" * 60)
    
    # Check if Streamlit app can load the config
    try:
        import os
        os.environ["ORCHESTRATOR_URL"] = API_BASE
        
        # Import streamlit app components
        import streamlit as st
        print("   ✅ Streamlit imports: OK")
        print(f"   📍 Configured API URL: {API_BASE}")
        
        # Test URL construction
        test_endpoints = [
            f"{API_BASE}/agents/status",
            f"{API_BASE}/intelligent/query", 
            f"{API_BASE}/intelligent/voice"
        ]
        
        for endpoint in test_endpoints:
            print(f"   🔗 Endpoint: {endpoint}")
            
    except Exception as e:
        print(f"   ❌ Streamlit config: Error - {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_streamlit_config()
    
    print("\n" + "=" * 60)
    print("🚀 Integration Summary:")
    print(f"   API Base URL: {API_BASE}")
    print(f"   Landing Page: {BASE_URL}")
    print("   Next steps:")
    print("   1. If API endpoints fail, check Netlify function logs")
    print("   2. Verify function deployment succeeded")
    print("   3. Test Streamlit app locally: streamlit run streamlit_app.py")
    print("   4. Deploy Streamlit app to Streamlit Cloud") 