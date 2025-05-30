import streamlit as st

# Configure page FIRST - this must be the very first Streamlit command
st.set_page_config(
    layout="wide", 
    page_title="🚀 AI Financial Assistant", 
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Now import other libraries
import requests
import base64
import time
import json
import threading
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import uuid
from typing import Dict, List, Any
import html
import io
import re
import subprocess
import os

# Configuration - Use environment variables or secrets, fallback to deployed API
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL") or st.secrets.get("ORCHESTRATOR_URL")

# Display deployment info in sidebar
st.sidebar.info(f"🚀 Mode: Streamlit Cloud")
st.sidebar.info(f"🌐 API: {ORCHESTRATOR_URL}")

# Enhanced Custom CSS for modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .chat-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-height: 600px;
        overflow-y: auto;
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 5px 20px;
        max-width: 70%;
        margin: 8px 0 8px auto;
        box-shadow: 0 3px 15px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: white;
        color: #2c3e50;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 5px;
        max-width: 75%;
        margin: 8px auto 8px 0;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #20c997;
    }
    
    .input-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-top: 1rem;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">🚀 AI Financial Assistant</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Powered by Mistral AI • Multi-Agent Intelligence • Real-time Analysis</p>
</div>
""", unsafe_allow_html=True)

def send_query_to_api(query: str = None, audio_file = None, voice_mode: bool = False):
    """Send query to deployed API."""
    st.session_state.is_processing = True
    
    try:
        if audio_file:
            # Voice query
            endpoint = f"{ORCHESTRATOR_URL}/intelligent/voice"
            files = {'audio': (audio_file.name, audio_file, audio_file.type)}
            data = {
                'voice_mode': voice_mode,
                'include_debug': False
            }
            response = requests.post(endpoint, files=files, data=data, timeout=120)
            st.session_state.conversation.append(("👤 User (🎤 audio)", "Uploaded an audio file"))
        elif query:
            # Text query
            endpoint = f"{ORCHESTRATOR_URL}/intelligent/query"
            payload = {
                "query": query,
                "voice_mode": voice_mode,
                "include_debug_info": False
            }
            response = requests.post(endpoint, json=payload, timeout=120)
            st.session_state.conversation.append(("👤 User", query))
        else:
            st.error("⚠️ Please provide a query or upload an audio file.")
            return

        if response.status_code == 200:
            data = response.json()
            
            # Handle different API response formats
            if 'response_text' in data:
                # New format (orchestrator_fastapi.py)
                response_text = data['response_text']
                confidence = data.get('confidence', 0.0)
                agents_used = data.get('agents_used', [])
                query_interpretation = data.get('query_interpretation', '')
                session_id = data.get('session_id', '')
            elif 'response' in data:
                # Current deployed format
                response_text = data['response']
                confidence = data.get('confidence', 0.0)
                agents_used = []  # Not available in current format
                query_interpretation = f"Query processed: {query}"
                session_id = data.get('timestamp', '')
            else:
                st.error("Unexpected API response format")
                st.json(data)  # Show the actual response for debugging
                return
            
            # Add response to conversation
            st.session_state.conversation.append((
                f"🤖 Assistant", 
                response_text,
                {
                    'confidence': confidence,
                    'agents_used': agents_used,
                    'query_interpretation': query_interpretation,
                    'session_id': session_id
                }
            ))
            
            # Show success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Confidence", f"{confidence:.1%}")
            with col2:
                st.metric("🤖 Agents Used", len(agents_used) if agents_used else "N/A")
            with col3:
                if agents_used:
                    successful_count = len([a for a in agents_used if a.get('status') == 'completed'])
                    st.metric("✅ Success Rate", f"{successful_count}/{len(agents_used)}")
                else:
                    st.metric("✅ API Status", "Online")
            
            # Play audio if available
            if data.get('wav_audio_base64'):
                st.success("🔊 Audio response generated!")
                audio_bytes = base64.b64decode(data['wav_audio_base64'])
                st.audio(audio_bytes, format="audio/wav")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The query might be too complex.")
    except requests.exceptions.RequestException as e:
        st.error(f"🚫 Connection error: {e}")
    except Exception as e:
        st.error(f"💥 Unexpected error: {e}")
        st.write("Debug info:", str(e))
    finally:
        st.session_state.is_processing = False

def display_conversation():
    """Display conversation history."""
    if st.session_state.conversation:
        st.markdown("### 💬 Conversation")
        
        for entry in st.session_state.conversation:
            if len(entry) == 2:
                speaker, text = entry
                metadata = {}
            else:
                speaker, text, metadata = entry
            
            if speaker.startswith("👤"):
                st.markdown(f'<div class="user-message">{text}</div>', unsafe_allow_html=True)
            elif speaker.startswith("🤖"):
                st.markdown(f'<div class="assistant-message">{text}</div>', unsafe_allow_html=True)
                
                # Show agent details if available
                agents_used = metadata.get('agents_used', [])
                if agents_used:
                    with st.expander("🤖 Agent Details", expanded=False):
                        for agent in agents_used:
                            agent_name = agent.get('agent_name', 'Unknown Agent')
                            status = agent.get('status', 'completed')
                            description = agent.get('description', 'Processing...')
                            
                            status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                            st.markdown(f"**{status_icon} {agent_name}**: {description}")

# Sidebar
with st.sidebar:
    st.subheader("🎛️ Control Center")
    
    # Connection status
    try:
        status_response = requests.get(f"{ORCHESTRATOR_URL}/agents/status", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            st.success("🟢 API Online")
            
            st.subheader("🤖 Available Agents")
            # Handle different status response formats
            if 'available_agents' in status_data:
                agents = status_data['available_agents']
                for agent in agents:
                    agent_name = agent.get('name', 'Unknown Agent')
                    agent_status = agent.get('status', 'unknown')
                    capabilities = agent.get('capabilities', [])
                    cap_text = ', '.join(capabilities[:2]) if capabilities else 'AI processing'
                    st.markdown(f"✅ **{agent_name}** - {agent_status}")
                    st.caption(f"🔧 {cap_text}")
            else:
                # Fallback for simple status
                st.markdown("✅ **AI Financial Assistant** - active")
                st.caption("🔧 Financial analysis, market data")
        else:
            st.error("🔴 API Offline")
    except Exception as e:
        st.error("🔴 Connection Failed")
        st.caption(f"Error: {str(e)[:50]}...")
    
    st.subheader("⚙️ Settings")
    voice_mode = st.toggle("🔊 Voice Output", value=False, help="Enable AI voice responses")

# Main interface
display_conversation()

# Input area
st.markdown('<div class="input-container">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 💭 Ask Your Financial Question")
    
    user_input = st.text_area(
        "Your financial query",
        height=120,
        placeholder="💡 Examples:\n• What's the current price of AAPL?\n• Analyze Tesla's performance vs competitors\n• Should I invest in renewable energy stocks?",
        help="Ask about stocks, market analysis, portfolio management, economic trends, or any financial topic",
        label_visibility="collapsed"
    )
    
    uploaded_file = st.file_uploader(
        "🎤 Or upload audio (WAV, MP3, M4A format):", 
        type=["wav", "mp3", "m4a"],
        help="Upload a voice recording for speech-to-text processing"
    )
    
    recorded_audio = st.audio_input("🎙️ Record your voice")

with col2:
    st.markdown("### 🎮 Actions")
    
    if st.session_state.is_processing:
        st.button("⏳ Processing...", disabled=True, use_container_width=True)
    else:
        if st.button("🚀 Ask AI", use_container_width=True, type="primary"):
            if recorded_audio:
                send_query_to_api(audio_file=recorded_audio, voice_mode=voice_mode)
            elif uploaded_file:
                send_query_to_api(audio_file=uploaded_file, voice_mode=voice_mode)
            elif user_input and user_input.strip():
                send_query_to_api(query=user_input.strip(), voice_mode=voice_mode)
            else:
                st.warning("⚠️ Please enter a query or upload an audio file.")
            st.rerun()
    
    if st.button("🗑️ Clear", use_container_width=True, disabled=st.session_state.is_processing):
        st.session_state.conversation = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 25px; 
           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           border-radius: 15px; margin-top: 30px; color: white;
           box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
    <h3 style="margin: 0 0 8px 0; font-weight: 700;">🚀 AI Financial Assistant</h3>
    <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
        Deployed on Streamlit Cloud • API on Netlify • Real-time Financial Intelligence
    </p>
</div>
""", unsafe_allow_html=True) 