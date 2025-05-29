#!/usr/bin/env python3
"""
Comprehensive Voice Debugging Script
This script will help identify exactly where the voice issue is occurring.
"""

import subprocess
import time
import requests
import json
from agents.core.voice_agent import VoiceAgent

def test_system_audio():
    """Test basic system audio functionality"""
    print("🔊 Testing System Audio")
    print("-" * 30)
    
    # Check volume settings
    result = subprocess.run(["osascript", "-e", "get volume settings"], 
                          capture_output=True, text=True)
    print(f"Volume settings: {result.stdout.strip()}")
    
    # Test system say command with different voices
    voices = ["Alex", "Samantha", "Daniel", "Karen"]
    for voice in voices:
        print(f"Testing voice: {voice}")
        try:
            subprocess.run(["say", "-v", voice, f"Testing {voice} voice"], 
                         check=True, timeout=10)
            print(f"✅ {voice} voice works")
            break  # If one works, they all should work
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ {voice} voice failed: {e}")
    
    print()

def test_voice_agent_direct():
    """Test Voice Agent directly"""
    print("🎤 Testing Voice Agent Direct")
    print("-" * 30)
    
    try:
        agent = VoiceAgent(tts_provider="macos_say")
        
        # Test with explicit parameters (API style)
        result = agent.speak("Testing Voice Agent with explicit parameters", 
                           provider="macos_say")
        print(f"✅ Voice Agent API style: {result}")
        
        # Test with default parameters (CLI style)
        result = agent.speak("Testing Voice Agent with default parameters")
        print(f"✅ Voice Agent CLI style: {result}")
        
    except Exception as e:
        print(f"❌ Voice Agent failed: {e}")
    
    print()

def test_api_endpoints():
    """Test API endpoints"""
    print("🌐 Testing API Endpoints")
    print("-" * 30)
    
    # Test Main API voice endpoint
    try:
        response = requests.post(
            "http://localhost:8000/voice/speak",
            json={"text": "Testing Main API voice endpoint", "provider": "macos_say"},
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ Main API voice endpoint: {response.json()}")
        else:
            print(f"❌ Main API voice endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Main API voice endpoint error: {e}")
    
    # Test Orchestrator API
    try:
        response = requests.post(
            "http://localhost:8011/intelligent/query",
            json={"query": "Just say hello", "voice_mode": True},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            has_audio = 'wav_audio_base64' in data and data['wav_audio_base64']
            print(f"✅ Orchestrator API: Audio generated = {has_audio}")
            if has_audio:
                audio_size = len(data['wav_audio_base64'])
                print(f"   Audio data size: {audio_size} characters")
        else:
            print(f"❌ Orchestrator API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Orchestrator API error: {e}")
    
    print()

def test_audio_file_playback():
    """Test audio file generation and playback"""
    print("🎵 Testing Audio File Generation")
    print("-" * 30)
    
    try:
        agent = VoiceAgent(tts_provider="macos_say")
        
        # Generate audio file
        wav_path = agent.text_to_speech("Testing audio file generation and playback")
        print(f"✅ Audio file generated: {wav_path}")
        
        if wav_path:
            # Check file size
            import os
            file_size = os.path.getsize(wav_path)
            print(f"   File size: {file_size} bytes")
            
            # Try to play with afplay
            print("Playing with afplay...")
            result = subprocess.run(["afplay", wav_path], 
                                  capture_output=True, timeout=10)
            if result.returncode == 0:
                print("✅ afplay successful")
            else:
                print(f"❌ afplay failed: {result.stderr}")
            
            # Try to play with say command on the file
            print("Playing with say command...")
            result = subprocess.run(["say", "-f", wav_path], 
                                  capture_output=True, timeout=10)
            if result.returncode == 0:
                print("✅ say command on file successful")
            else:
                print(f"❌ say command on file failed: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Audio file test failed: {e}")
    
    print()

def main():
    print("🔍 COMPREHENSIVE VOICE DEBUGGING")
    print("=" * 50)
    print("This script will test all aspects of voice functionality.")
    print("Listen carefully for audio output during each test.")
    print("=" * 50)
    print()
    
    test_system_audio()
    test_voice_agent_direct()
    test_api_endpoints()
    test_audio_file_playback()
    
    print("🏁 Debugging Complete!")
    print("=" * 50)
    print("If you heard audio during any test, the voice system is working.")
    print("If you didn't hear anything, the issue might be:")
    print("1. Audio output device (check System Preferences > Sound)")
    print("2. Volume too low (try increasing system volume)")
    print("3. Audio routed to disconnected device (Bluetooth headphones)")
    print("4. Browser audio settings (if testing via web interface)")

if __name__ == "__main__":
    main() 