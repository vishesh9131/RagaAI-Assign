import argparse
from rich.console import Console
from pathlib import Path
from voice_agent import VoiceAgent

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Voice Agent CLI – speech-to-text and text-to-speech utilities")
    
    # Global options
    parser.add_argument("--tts-provider", type=str, choices=["pyttsx3", "openai", "elevenlabs", "google", "macos_say"], 
                       default="pyttsx3", help="TTS provider to use")
    parser.add_argument("--tts-voice", type=str, help="Voice to use for TTS")
    parser.add_argument("--api-key", type=str, help="API key for cloud TTS providers")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # STT
    stt_parser = subparsers.add_parser("stt", help="Transcribe an audio file to text")
    stt_parser.add_argument("audio_path", type=str, help="Path to audio file (wav/mp3 etc.)")
    stt_parser.add_argument("--language", type=str, default=None, help="ISO language code (optional)")

    # TTS (save to file)
    tts_parser = subparsers.add_parser("tts", help="Convert text to speech (WAV)")
    tts_parser.add_argument("text", type=str, help="Text to convert to speech (quote if spaces)")
    tts_parser.add_argument("--output", type=str, default=None, help="Output WAV file path")

    # Speak (real-time)
    speak_parser = subparsers.add_parser("speak", help="Speak text aloud in real-time")
    speak_parser.add_argument("text", type=str, help="Text to speak aloud (quote if spaces)")

    args = parser.parse_args()
    
    # Create agent with specified provider and options
    agent = VoiceAgent(
        tts_provider=args.tts_provider,
        tts_voice=args.tts_voice,
        api_key=args.api_key
    )

    if args.command == "stt":
        audio_path = Path(args.audio_path).expanduser()
        if not audio_path.exists():
            console.print(f"[red]File not found:[/red] {audio_path}")
            return
        text = agent.speech_to_text(audio_path, language=args.language)
        console.print(f"[bold green]Transcription:[/bold green] {text}")
        
    elif args.command == "tts":
        output = agent.text_to_speech(args.text, output_path=args.output, save_file=True)
        console.print(f"[bold blue]Audio saved to:[/bold blue] {output}")
        
    elif args.command == "speak":
        console.print(f"[bold cyan]Speaking:[/bold cyan] {args.text}")
        try:
            agent.speak(args.text)
            console.print("[bold green]✓[/bold green] Speech completed")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

if __name__ == "__main__":
    main() 