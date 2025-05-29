#!/usr/bin/env python3
"""
Simple example showing how to use the Voice Agent for real-time TTS.
"""

from voice_agent import VoiceAgent

def main():
    print("🎙️ Voice Agent Real-time TTS Examples\n")
    
    # Example 1: Basic real-time speech
    print("1. Basic real-time speech (local TTS)...")
    agent = VoiceAgent()
    agent.speak("Hello! I can speak in real-time without creating files.")
    
    # Example 2: Using macOS native TTS (faster on Mac)
    print("\n2. Using macOS native TTS for faster speech...")
    fast_agent = VoiceAgent(tts_provider="macos_say", tts_voice="Samantha")
    fast_agent.speak("This uses macOS native speech synthesis which is much faster.")
    
    # Example 3: Compare file vs real-time
    print("\n3. Comparing file generation vs real-time playback...")
    
    # Real-time (no file saved)
    print("   Real-time playback:")
    agent.text_to_speech("This plays immediately without saving a file.", save_file=False)
    
    # File generation
    print("   File generation:")
    output_path = agent.text_to_speech("This saves to a file first.", output_path="example_output.wav")
    print(f"   Audio saved to: {output_path}")
    
    # Example 4: Error handling
    print("\n4. Error handling example...")
    try:
        # This will work even if pyttsx3 has issues on macOS
        agent.speak("The system gracefully handles TTS engine failures.")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ Examples completed!")
    print("\nTo use cloud TTS APIs:")
    print("• Set OPENAI_API_KEY and use tts_provider='openai'")
    print("• Set ELEVENLABS_API_KEY and use tts_provider='elevenlabs'")
    print("• Set up Google Cloud credentials and use tts_provider='google'")

if __name__ == "__main__":
    main() 