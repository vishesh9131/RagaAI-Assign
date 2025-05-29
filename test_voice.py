#!/usr/bin/env python3
"""
Voice Agent Test Script
This script tests the voice functionality to debug any issues.
"""

import sys
import time
from agents.core.voice_agent import VoiceAgent

def test_voice_functionality():
    print("🎤 Testing Voice Agent Functionality")
    print("=" * 50)
    
    # Test 1: Direct macOS say command
    print("\n1. Testing direct macOS 'say' command...")
    import subprocess
    try:
        subprocess.run(["say", "Direct macOS say test"], check=True)
        print("✅ Direct macOS say command works")
    except Exception as e:
        print(f"❌ Direct macOS say failed: {e}")
        return
    
    # Test 2: Voice Agent with macos_say provider
    print("\n2. Testing Voice Agent with macos_say provider...")
    try:
        agent = VoiceAgent(tts_provider="macos_say")
        result = agent.speak("Voice Agent macOS say test", provider="macos_say")
        print(f"✅ Voice Agent macos_say result: {result}")
    except Exception as e:
        print(f"❌ Voice Agent macos_say failed: {e}")
    
    # Test 3: Voice Agent with pyttsx3 provider
    print("\n3. Testing Voice Agent with pyttsx3 provider...")
    try:
        agent = VoiceAgent(tts_provider="pyttsx3")
        result = agent.speak("Voice Agent pyttsx3 test", provider="pyttsx3")
        print(f"✅ Voice Agent pyttsx3 result: {result}")
    except Exception as e:
        print(f"❌ Voice Agent pyttsx3 failed: {e}")
    
    # Test 4: Text-to-speech file generation
    print("\n4. Testing text-to-speech file generation...")
    try:
        agent = VoiceAgent(tts_provider="macos_say")
        wav_path = agent.text_to_speech("File generation test")
        print(f"✅ TTS file generated: {wav_path}")
        
        # Try to play the generated file
        if wav_path:
            print("Playing generated file...")
            subprocess.run(["afplay", wav_path], check=True)
            print("✅ Generated file played successfully")
    except Exception as e:
        print(f"❌ TTS file generation failed: {e}")
    
    print("\n" + "=" * 50)
    print("Voice functionality test completed!")

if __name__ == "__main__":
    test_voice_functionality() 