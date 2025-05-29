import streamlit as st
from pathlib import Path
from voice_agent import VoiceAgent
import base64

st.set_page_config(page_title="Voice Agent", layout="centered")

agent = VoiceAgent()

st.title("🎙️ Voice Agent")

mode = st.radio("Choose Mode", ["Speech ➜ Text", "Text ➜ Speech"], horizontal=True)

if mode == "Speech ➜ Text":
    audio_file = st.file_uploader("Upload audio file (wav, mp3, m4a)")
    language = st.text_input("Language code (optional)")
    if st.button("Transcribe") and audio_file:
        with st.spinner("Transcribing..."):
            temp_path = Path("temp_uploaded_audio")
            temp_path.write_bytes(audio_file.read())
            try:
                text = agent.speech_to_text(temp_path, language=language or None)
                st.success(text)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
elif mode == "Text ➜ Speech":
    text_input = st.text_area("Enter text to speak", height=200)
    if st.button("Generate Speech") and text_input.strip():
        with st.spinner("Generating speech..."):
            wav_path = agent.text_to_speech(text_input)
        st.success(f"Audio saved to {wav_path}")
        # Offer playback
        audio_bytes = Path(wav_path).read_bytes()
        st.audio(audio_bytes, format="audio/wav")
        # Offer download
        b64 = base64.b64encode(audio_bytes).decode()
        href = f'<a href="data:audio/wav;base64,{b64}" download="voice_output.wav">Download wav</a>'
        st.markdown(href, unsafe_allow_html=True) 