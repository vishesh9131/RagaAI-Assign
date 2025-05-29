#!/usr/bin/env python3
"""
Demo script showing voice integration with the AI Financial Assistant.
This demonstrates the same functionality that's built into the Streamlit app.
"""

import subprocess
import os

def demo_voice_response(text: str):
    """Demonstrate speaking a financial assistant response."""
    print(f"\n💬 Assistant Response:")
    print(f"'{text}'\n")
    
    print("🔊 Speaking response aloud...")
    
    # Use the same voice CLI integration as the Streamlit app
    cmd = [
        'python', 'voice_cli.py',
        '--tts-provider', 'macos_say',
        '--tts-voice', 'Samantha',
        'speak', text
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ Voice output completed!")
    else:
        print(f"❌ Voice output failed: {result.stderr}")

def main():
    print("🚀 AI Financial Assistant - Voice Integration Demo")
    print("=" * 60)
    print()
    print("This demonstrates the voice output feature that's integrated")
    print("into the Streamlit orchestrator app.")
    print()
    
    # Demo different types of financial responses
    demo_responses = [
        "Welcome to the AI Financial Assistant. How can I help you with your investments today?",
        
        "As of today, Apple's stock performance shows a positive change. It closed at $190.50, up by $2.30 or 1.22% from yesterday's value of $188.20.",
        
        "Based on current market analysis, the technology sector is showing strong growth, with a total portfolio value increase of 3.2% over the past week.",
        
        "Your investment in the Asia-Pacific region shows a diversified portfolio across manufacturing, technology, and renewable energy sectors, totaling approximately $45,000.",
    ]
    
    for i, response in enumerate(demo_responses, 1):
        print(f"\n📊 Demo {i}/4:")
        print("-" * 40)
        demo_voice_response(response)
        
        if i < len(demo_responses):
            input("\nPress Enter to continue to next demo...")
    
    print("\n" * 2)
    print("🎉 Demo completed!")
    print()
    print("🌟 To use voice output in the Streamlit app:")
    print("   1. Open http://localhost:8501")
    print("   2. Toggle 'Voice Output' in the sidebar")
    print("   3. Ask any financial question")
    print("   4. The assistant's response will be spoken aloud!")
    print()
    print("📝 Voice settings can be configured in the sidebar:")
    print("   • Provider: Choose between pyttsx3, macos_say, OpenAI, etc.")
    print("   • Voice: Select from available voices (e.g., Samantha, Alex)")
    print()

if __name__ == "__main__":
    main() 