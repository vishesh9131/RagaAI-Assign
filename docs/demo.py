#!/usr/bin/env python3
"""
Demo script for the enhanced Voice Agent with real-time TTS capabilities.
This script demonstrates various TTS providers and features.
"""

import os
import time
from voice_agent import VoiceAgent
from rich.console import Console

console = Console()

def demo_local_tts():
    """Demo local TTS providers."""
    console.print("\n🎯 [bold cyan]Local TTS Providers Demo[/bold cyan]")
    
    # pyttsx3 (cross-platform)
    console.print("\n1. Testing pyttsx3 (cross-platform local TTS)...")
    agent = VoiceAgent(tts_provider="pyttsx3")
    agent.speak("Hello! I'm using the pyttsx3 engine for local text to speech.")
    
    # macOS say (if on macOS)
    if os.system("which say") == 0:  # Check if 'say' command exists
        console.print("\n2. Testing macOS native TTS...")
        agent = VoiceAgent(tts_provider="macos_say", tts_voice="Samantha")
        agent.speak("Now I'm using the macOS native speech synthesis. This is much faster!")
    
    console.print("✅ Local TTS demo completed!\n")

def demo_api_tts():
    """Demo API-based TTS providers (requires API keys)."""
    console.print("\n🌐 [bold cyan]API TTS Providers Demo[/bold cyan]")
    
    # Check for OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        console.print("\n1. Testing OpenAI TTS API...")
        try:
            agent = VoiceAgent(tts_provider="openai", tts_voice="nova")
            agent.speak("This is OpenAI's neural text to speech with the Nova voice.")
            console.print("✅ OpenAI TTS working!")
        except Exception as e:
            console.print(f"❌ OpenAI TTS failed: {e}")
    else:
        console.print("⚠️  OpenAI API key not found (set OPENAI_API_KEY)")
    
    # Check for ElevenLabs API key  
    if os.getenv("ELEVENLABS_API_KEY"):
        console.print("\n2. Testing ElevenLabs TTS API...")
        try:
            agent = VoiceAgent(tts_provider="elevenlabs")
            agent.speak("This is ElevenLabs text to speech, known for very natural sounding voices.")
            console.print("✅ ElevenLabs TTS working!")
        except Exception as e:
            console.print(f"❌ ElevenLabs TTS failed: {e}")
    else:
        console.print("⚠️  ElevenLabs API key not found (set ELEVENLABS_API_KEY)")
    
    # Check for Google Cloud credentials
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        console.print("\n3. Testing Google Cloud TTS API...")
        try:
            agent = VoiceAgent(tts_provider="google", tts_voice="en-US-Wavenet-D")
            agent.speak("This is Google Cloud text to speech with neural voices.")
            console.print("✅ Google Cloud TTS working!")
        except Exception as e:
            console.print(f"❌ Google Cloud TTS failed: {e}")
    else:
        console.print("⚠️  Google Cloud credentials not found (set GOOGLE_APPLICATION_CREDENTIALS)")

def demo_file_vs_realtime():
    """Demo the difference between file generation and real-time speech."""
    console.print("\n⚡ [bold cyan]File vs Real-time Speech Demo[/bold cyan]")
    
    agent = VoiceAgent(tts_provider="macos_say" if os.system("which say") == 0 else "pyttsx3")
    
    # Real-time speech (no file)
    console.print("\n1. Real-time speech (no file saved)...")
    start_time = time.time()
    agent.text_to_speech("This is real-time speech without saving a file.", save_file=False)
    realtime_duration = time.time() - start_time
    console.print(f"⏱️  Real-time speech took: {realtime_duration:.2f} seconds")
    
    # File generation
    console.print("\n2. Generating audio file...")
    start_time = time.time()
    output_path = agent.text_to_speech("This speech will be saved to a file.", output_path="demo_output.wav")
    file_duration = time.time() - start_time
    console.print(f"⏱️  File generation took: {file_duration:.2f} seconds")
    console.print(f"📁 Audio saved to: {output_path}")
    
    # Cleanup
    try:
        os.remove("demo_output.wav")
        console.print("🗑️  Cleaned up demo file")
    except:
        pass

def demo_speech_to_text():
    """Demo speech-to-text if audio file exists."""
    console.print("\n🎤 [bold cyan]Speech-to-Text Demo[/bold cyan]")
    
    # Create a sample audio file first
    agent = VoiceAgent()
    sample_text = "This is a test of speech to text transcription capabilities."
    
    console.print("1. Creating sample audio file...")
    audio_path = agent.text_to_speech(sample_text, output_path="sample_audio.wav")
    
    console.print("2. Transcribing the audio back to text...")
    try:
        transcribed_text = agent.speech_to_text(audio_path)
        console.print(f"📝 Original: {sample_text}")
        console.print(f"📝 Transcribed: {transcribed_text}")
        
        if sample_text.lower() in transcribed_text.lower():
            console.print("✅ Speech-to-text working correctly!")
        else:
            console.print("⚠️  Transcription differs from original")
    except Exception as e:
        console.print(f"❌ Speech-to-text failed: {e}")
    finally:
        # Cleanup
        try:
            os.remove("sample_audio.wav")
            console.print("🗑️  Cleaned up sample audio file")
        except:
            pass

def main():
    """Run all demos."""
    console.print("[bold green]🎙️  Voice Agent Real-time TTS Demo[/bold green]")
    console.print("This demo showcases the new real-time speech capabilities.\n")
    
    # Demo local TTS (always available)
    demo_local_tts()
    
    # Demo API TTS (requires API keys)
    demo_api_tts()
    
    # Demo file vs real-time performance
    demo_file_vs_realtime()
    
    # Demo speech-to-text
    demo_speech_to_text()
    
    console.print("\n🎉 [bold green]Demo completed![/bold green]")
    console.print("\nTo use API providers, set your API keys:")
    console.print("• export OPENAI_API_KEY='your-key'")
    console.print("• export ELEVENLABS_API_KEY='your-key'") 
    console.print("• export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account.json'")

if __name__ == "__main__":
    main() 