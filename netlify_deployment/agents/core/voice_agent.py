"""voice_agent.py
VoiceAgent handles basic speech-to-text (STT) and text-to-speech (TTS) tasks.
- STT: Uses OpenAI Whisper (tiny) via the `whisper` package. Falls back to `faster-whisper` if installed.
- TTS: Supports both offline (pyttsx3) and online API providers (OpenAI, ElevenLabs, Google Cloud)
  with real-time streaming playback.

All heavy models are loaded lazily on first use so that importing the module is cheap.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict, Literal, Any
import tempfile
import time, platform, subprocess, shutil
import io
import threading
import queue

TtsProvider = Literal["pyttsx3", "openai", "elevenlabs", "google", "macos_say"]

class VoiceAgent:
    def __init__(
        self, 
        whisper_model_size: str = "base", 
        tts_voice: Optional[str] = None,
        tts_provider: TtsProvider = "pyttsx3",
        api_key: Optional[str] = None
    ):
        """Initialise the agent.
        Args:
            whisper_model_size: Model size to load. tiny / base / small / medium / large.
            tts_voice: Optional voice id/name for TTS.
            tts_provider: TTS provider to use ("pyttsx3", "openai", "elevenlabs", "google", "macos_say").
            api_key: API key for cloud TTS providers.
        """
        self.whisper_model_size = whisper_model_size
        self._whisper_model = None  # lazy
        self._tts_engine = None  # lazy
        self.tts_voice = tts_voice
        self.tts_provider = tts_provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ELEVENLABS_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # ---------------------------------------------------------
    # Lazy loaders
    # ---------------------------------------------------------
    def _load_whisper(self):
        if self._whisper_model is not None:
            return self._whisper_model
        try:
            # Try faster-whisper first (more stable for deployment)
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel(self.whisper_model_size)
            return self._whisper_model
        except ImportError:
            # Fallback to openai-whisper if available
            try:
                import whisper
                self._whisper_model = whisper.load_model(self.whisper_model_size)
                return self._whisper_model
            except ImportError:
                raise RuntimeError("Neither 'faster-whisper' nor 'whisper' is installed. Install faster-whisper to enable STT.")

    def _load_tts(self):
        if self._tts_engine is not None:
            return self._tts_engine
        try:
            import pyttsx3
            engine = pyttsx3.init()
            if self.tts_voice:
                # attempt to set requested voice
                for voice in engine.getProperty('voices'):
                    if self.tts_voice.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            # Slightly slower rate for clarity
            engine.setProperty('rate', 175)
            self._tts_engine = engine
            return engine
        except Exception as e:
            raise RuntimeError(f"Failed to initialise TTS engine: {e}")

    def _reset_tts_engine(self):
        """Reset the TTS engine if it's in a bad state."""
        self._tts_engine = None

    def _play_audio_stream(self, audio_data: bytes, sample_rate: int = 22050):
        """Play audio data directly using pygame or simpleaudio."""
        try:
            # Try pygame first (better cross-platform support)
            import pygame
            pygame.mixer.pre_init(frequency=sample_rate, size=-16, channels=1, buffer=512)
            pygame.mixer.init()
            
            # Convert bytes to pygame sound
            sound = pygame.sndarray.make_sound(
                __import__('numpy').frombuffer(audio_data, dtype='int16')
            )
            sound.play()
            
            # Wait for playback to finish
            while pygame.mixer.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            
        except ImportError:
            try:
                # Fallback to simpleaudio
                import simpleaudio as sa
                wave_obj = sa.WaveObject(audio_data, 1, 2, sample_rate)
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except ImportError:
                # Final fallback: write to temp file and play with system player
                temp_file = Path(tempfile.gettempdir()) / "temp_voice_output.wav"
                with open(temp_file, 'wb') as f:
                    # Write minimal WAV header + data
                    self._write_wav_header(f, len(audio_data), sample_rate)
                    f.write(audio_data)
                
                if platform.system() == "Darwin":
                    subprocess.run(["afplay", str(temp_file)], check=True)
                elif platform.system() == "Windows":
                    os.system(f'start /wait "" "{temp_file}"')
                else:  # Linux
                    subprocess.run(["aplay", str(temp_file)], check=True)
                
                # Clean up temp file
                try:
                    temp_file.unlink()
                except:
                    pass

    def _write_wav_header(self, f, data_length: int, sample_rate: int = 22050):
        """Write a basic WAV header to file object."""
        import struct
        
        # WAV header
        f.write(b'RIFF')
        f.write(struct.pack('<I', data_length + 36))  # File size - 8
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # Subchunk1Size
        f.write(struct.pack('<H', 1))   # AudioFormat (PCM)
        f.write(struct.pack('<H', 1))   # NumChannels (mono)
        f.write(struct.pack('<I', sample_rate))  # SampleRate
        f.write(struct.pack('<I', sample_rate * 2))  # ByteRate
        f.write(struct.pack('<H', 2))   # BlockAlign
        f.write(struct.pack('<H', 16))  # BitsPerSample
        f.write(b'data')
        f.write(struct.pack('<I', data_length))  # Subchunk2Size

    def _openai_tts_stream(self, text: str) -> bytes:
        """Generate speech using OpenAI TTS API."""
        try:
            import openai
            
            if not self.api_key:
                raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            
            client = openai.OpenAI(api_key=self.api_key)
            
            # Use alloy voice by default, or specified voice
            voice = self.tts_voice or "alloy"
            
            response = client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice,
                input=text,
                response_format="wav"
            )
            
            return response.content
            
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS failed: {e}")

    def _elevenlabs_tts_stream(self, text: str) -> bytes:
        """Generate speech using ElevenLabs TTS API."""
        try:
            import requests
            
            if not self.api_key:
                raise ValueError("ElevenLabs API key not provided. Set ELEVENLABS_API_KEY environment variable or pass api_key parameter.")
            
            # Use Rachel voice by default, or specified voice_id
            voice_id = self.tts_voice or "21m00Tcm4TlvDq8ikWAM"  # Rachel
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/wav",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            return response.content
            
        except ImportError:
            raise RuntimeError("requests package not installed. Run: pip install requests")
        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {e}")

    def _google_tts_stream(self, text: str) -> bytes:
        """Generate speech using Google Cloud TTS API."""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=self.tts_voice or "en-US-Wavenet-D",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )
            
            # Select the type of audio file to return
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=22050
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            return response.audio_content
            
        except ImportError:
            raise RuntimeError("google-cloud-texttospeech package not installed. Run: pip install google-cloud-texttospeech")
        except Exception as e:
            raise RuntimeError(f"Google Cloud TTS failed: {e}")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def speech_to_text(self, audio_path: str | Path, language: Optional[str] = None) -> str:
        """Transcribe an audio file to text."""
        model = self._load_whisper()
        # If using openai-whisper
        if hasattr(model, 'transcribe'):
            result = model.transcribe(str(audio_path), language=language)  # type: ignore[arg-type]
            return result['text'].strip()
        else:
            # faster-whisper returns segments and info
            segments, _info = model.transcribe(str(audio_path), language=language)
            return " ".join([seg.text for seg in segments]).strip()

    def speak(self, text: str, provider: Optional[str] = None, voice: Optional[str] = None, api_key: Optional[str] = None):
        """Speak text aloud in real-time using the specified or configured TTS provider.
        
        Args:
            text: Text to speak
            provider: TTS provider to use (overrides self.tts_provider if provided)
            voice: Voice to use (overrides self.tts_voice if provided)
            api_key: API key for cloud providers (overrides self.api_key if provided)
            
        Returns:
            Tuple of (message, provider_used, voice_used, duration_seconds) for API compatibility
        """
        import time
        
        if not text.strip():
            raise ValueError("Input text is empty.")
        
        # Use provided parameters or fall back to instance defaults
        actual_provider = provider or self.tts_provider
        actual_voice = voice or self.tts_voice
        actual_api_key = api_key or self.api_key
        
        # Update instance temporarily if different parameters provided
        original_provider = self.tts_provider
        original_voice = self.tts_voice
        original_api_key = self.api_key
        
        try:
            self.tts_provider = actual_provider
            self.tts_voice = actual_voice
            self.api_key = actual_api_key
            
            start_time = time.time()
            
            if actual_provider == "openai":
                audio_data = self._openai_tts_stream(text)
                self._play_audio_stream(audio_data)
            elif actual_provider == "elevenlabs":
                audio_data = self._elevenlabs_tts_stream(text)
                self._play_audio_stream(audio_data)
            elif actual_provider == "google":
                audio_data = self._google_tts_stream(text)
                self._play_audio_stream(audio_data)
            elif actual_provider == "macos_say" and platform.system() == "Darwin":
                # Direct macOS say command (real-time)
                voice_arg = ["-v", actual_voice] if actual_voice else []
                subprocess.run(["say", *voice_arg, text], check=True)
            else:
                # Fall back to pyttsx3 (local TTS)
                try:
                    engine = self._load_tts()
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    # Reset engine and try macOS fallback if available
                    self._reset_tts_engine()
                    if platform.system() == "Darwin":
                        print(f"[VoiceAgent] pyttsx3 failed ({e}), using macOS 'say' fallback")
                        voice_arg = ["-v", actual_voice] if actual_voice else []
                        subprocess.run(["say", *voice_arg, text], check=True)
                        actual_provider = "macos_say"  # Update to reflect actual provider used
                    else:
                        raise RuntimeError(f"TTS failed: {e}")
            
            duration_seconds = time.time() - start_time
            
            # For CLI compatibility, when called with default parameters
            if provider is None and voice is None and api_key is None:
                return  # Original behavior for CLI
            
            # For API compatibility, return detailed information
            return (
                "Speech completed successfully",
                actual_provider,
                actual_voice,
                duration_seconds
            )
            
        finally:
            # Restore original instance values
            self.tts_provider = original_provider
            self.tts_voice = original_voice
            self.api_key = original_api_key

    def text_to_speech(self, text: str, output_path: Optional[str | Path] = None, save_file: bool = True) -> Optional[str]:
        """Convert text to speech. 
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file (only used if save_file=True)
            save_file: Whether to save audio to file (default True for backward compatibility)
            
        Returns:
            Path to saved file if save_file=True, None otherwise
        """
        if not text.strip():
            raise ValueError("Input text is empty.")
        
        # For API providers, get audio data and optionally save or play directly
        if self.tts_provider in ["openai", "elevenlabs", "google"]:
            if self.tts_provider == "openai":
                audio_data = self._openai_tts_stream(text)
            elif self.tts_provider == "elevenlabs":
                audio_data = self._elevenlabs_tts_stream(text)
            else:  # google
                audio_data = self._google_tts_stream(text)
            
            if save_file:
                if output_path is None:
                    output_path = Path(tempfile.gettempdir()) / "voice_agent_output.wav"
                output_path = Path(output_path).expanduser().resolve()
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                return str(output_path)
            else:
                # Play directly without saving
                self._play_audio_stream(audio_data)
                return None
        
        # For local TTS providers, use existing file-based approach
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / "voice_agent_output.wav"
        output_path = Path(output_path).expanduser().resolve()
        
        # Try pyttsx3 first, but handle macOS issues gracefully
        pyttsx3_success = False
        try:
            engine = self._load_tts()
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            
            # Give pyttsx3 a little time to flush to disk
            for _ in range(5):
                if output_path.exists() and output_path.stat().st_size > 10000:  # Increased threshold
                    pyttsx3_success = True
                    break
                time.sleep(0.3)
                
            # Check if file is too small or has very short duration (indicates pyttsx3 failure on macOS)
            if pyttsx3_success and platform.system() == "Darwin" and output_path.exists():
                file_size = output_path.stat().st_size
                if file_size < 10000:  # Less than 10KB is suspicious for normal speech
                    pyttsx3_success = False
                else:
                    # Also check duration using ffprobe if available
                    try:
                        result = subprocess.run([
                            "ffprobe", "-i", str(output_path), 
                            "-show_entries", "format=duration", 
                            "-v", "quiet", "-of", "csv=p=0"
                        ], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            duration = float(result.stdout.strip())
                            if duration < 0.5:  # Less than 0.5 seconds is too short for normal speech
                                pyttsx3_success = False
                    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                        # If ffprobe fails, just rely on file size check
                        pass
        except Exception as e:
            print(f"[VoiceAgent] pyttsx3 failed: {e}")
            pyttsx3_success = False

        # Use macOS 'say' fallback if pyttsx3 failed
        if not pyttsx3_success and platform.system() == "Darwin":
            try:
                print("[VoiceAgent] Using macOS 'say' command for TTS.")
                # Use Darwin voice as default if no voice specified, as it's more reliable
                voice_to_use = self.tts_voice if self.tts_voice else "Darwin"
                voice_arg = ["-v", voice_to_use]
                
                # Check desired output format
                output_format = output_path.suffix.lower()
                
                if output_format == '.wav':
                    # Try to create WAV directly if ffmpeg is available
                    try:
                        subprocess.run([
                            "say",
                            *voice_arg,
                            text,
                            "-o", str(output_path),
                            "--data-format=LEI16@44100",
                            "--file-format=WAVE"
                        ], check=True, capture_output=True)
                        
                        # Verify the file was created successfully
                        if output_path.exists() and output_path.stat().st_size > 1000:
                            return str(output_path) if save_file else None
                        else:
                            raise subprocess.CalledProcessError(1, "say")
                            
                    except subprocess.CalledProcessError:
                        # If direct WAV creation fails, try AIFF then convert
                        temp_aiff = output_path.with_suffix('.aiff')
                        subprocess.run([
                            "say",
                            *voice_arg,
                            text,
                            "-o", str(temp_aiff)
                        ], check=True)
                        
                        # Try to convert using ffmpeg
                        try:
                            subprocess.run([
                                "ffmpeg", "-i", str(temp_aiff), 
                                "-y", str(output_path)  # -y to overwrite
                            ], check=True, capture_output=True)
                            temp_aiff.unlink()  # Remove temp file only after successful conversion
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            # If ffmpeg fails or is missing, rename AIFF to requested name
                            print(f"[VoiceAgent] Warning: ffmpeg not available for format conversion.")
                            print(f"[VoiceAgent] Created AIFF file instead: {temp_aiff}")
                            # Don't remove temp_aiff, user can convert manually
                            return str(temp_aiff) if save_file else None
                else:
                    # For AIFF or other formats, create directly
                    subprocess.run([
                        "say",
                        *voice_arg,
                        text,
                        "-o", str(output_path)
                    ], check=True)
                    
            except subprocess.CalledProcessError as e:
                print(f"[VoiceAgent] macOS 'say' fallback also failed: {e}")
                raise RuntimeError(f"Both pyttsx3 and macOS 'say' failed. You may need to install pyobjc: pip install pyobjc")
        elif not pyttsx3_success:
            raise RuntimeError("TTS failed and no fallback available on this platform")

        return str(output_path) if save_file else None

    def ask_and_speak(self, text: str) -> str:
        """Echo the input text back as audio (simple route). Returns WAV path."""
        return self.text_to_speech(text)

    def get_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available TTS providers and their voices."""
        providers = {
            "pyttsx3": {
                "description": "Local cross-platform TTS",
                "cost": "Free",
                "offline": True,
                "voices": ["system_default"]  # Simplified for API
            },
            "macos_say": {
                "description": "macOS native TTS",
                "cost": "Free", 
                "offline": True,
                "voices": ["Alex", "Samantha", "Victoria", "Daniel", "Karen", "Moira", "Tessa", "Allison", "Ava", "Susan"]
            },
            "openai": {
                "description": "OpenAI neural TTS",
                "cost": "$0.015/1K chars",
                "offline": False,
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "elevenlabs": {
                "description": "Natural AI voices",
                "cost": "$0.30/1K chars",
                "offline": False,
                "voices": ["21m00Tcm4TlvDq8ikWAM", "29vD33N1CtxCmqQRPOHJ", "AZnzlk1XvdvUeBnXmlld"]
            },
            "google": {
                "description": "Google Cloud TTS",
                "cost": "$4.00/1M chars",
                "offline": False,
                "voices": ["en-US-Wavenet-D", "en-US-Neural2-A", "en-GB-Neural2-A", "en-AU-Neural2-A", "es-ES-Neural2-C"]
            }
        }
        return providers

# Simple manual test
if __name__ == "__main__":
    agent = VoiceAgent()
    out = agent.text_to_speech("Hello from the voice agent")
    print("TTS saved to", out) 