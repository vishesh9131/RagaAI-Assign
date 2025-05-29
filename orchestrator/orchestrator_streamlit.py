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

# Try to import the new direct-callable functions from orchestrator_fastapi
try:
    from orchestrator.orchestrator_fastapi import (
        initialize_agents as fastapi_initialize_agents,
        get_agent_status as fastapi_get_agent_status,
        process_intelligent_query_sync as fastapi_process_intelligent_query_sync,
    )
    ORCHESTRATOR_INTEGRATED = True
except ImportError as e:
    st.error(f"Failed to import orchestrator functions: {e}. App may not function correctly.")
    ORCHESTRATOR_INTEGRATED = False
    # Define dummy functions if import fails, so the app doesn't crash immediately
    def fastapi_initialize_agents(): 
        return {}
    def fastapi_get_agent_status(): 
        return {"available_agents": [], "language_model": "N/A", "orchestrator_version": "N/A"}
    def fastapi_process_intelligent_query_sync(query, voice_mode=False, include_debug=False):
        return {"response_text": "Error: Orchestrator not integrated.", "agents_used": [], "query_interpretation": query, "confidence": 0, "session_id": "error"}

# Configure MISTRAL_API_KEY for integrated language agent
if "MISTRAL_API_KEY" not in os.environ and ORCHESTRATOR_INTEGRATED:
    if "MISTRAL_API_KEY" in st.secrets:
        os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]

# Configuration
ORCHESTRATOR_URL = "http://localhost:8011"
VOICE_AGENT_URL = "http://localhost:8000"  # Voice Agent API URL

# Enhanced Custom CSS for modern design with proper chat sizing
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
    
    .chat-message-container {
        display: flex;
        margin-bottom: 1.5rem;
        align-items: flex-end;
        gap: 12px;
    }
    
    .user-message-container {
        justify-content: flex-end;
    }
    
    .assistant-message-container {
        justify-content: flex-start;
    }
    
    .chat-avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        order: 2;
    }
    
    .assistant-avatar {
        background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
        color: white;
        order: 1;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 5px 20px;
        max-width: 70%;
        min-width: 100px;
        box-shadow: 0 3px 15px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease;
        order: 1;
        word-wrap: break-word;
        position: relative;
    }
    
    .assistant-message {
        background: white;
        color: #2c3e50;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 5px;
        max-width: 75%;
        min-width: 120px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        animation: slideInLeft 0.3s ease;
        border-left: 4px solid #20c997;
        order: 2;
        word-wrap: break-word;
        position: relative;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-size: 0.8rem;
        opacity: 0.9;
    }
    
    .message-content {
        line-height: 1.5;
        font-size: 0.95rem;
    }
    
    .message-footer {
        margin-top: 8px;
        font-size: 0.7rem;
        opacity: 0.7;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .confidence-indicator {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .confidence-high { background: #d4edda; color: #155724; }
    .confidence-medium { background: #fff3cd; color: #856404; }
    .confidence-low { background: #f8d7da; color: #721c24; }
    
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .agent-waiting { border-left-color: #6c757d; }
    .agent-executing { 
        border-left-color: #ffc107;
        background: linear-gradient(90deg, rgba(255,193,7,0.05) 0%, transparent 100%);
    }
    .agent-completed { 
        border-left-color: #28a745;
        background: linear-gradient(90deg, rgba(40,167,69,0.05) 0%, transparent 100%);
    }
    .agent-failed { 
        border-left-color: #dc3545;
        background: linear-gradient(90deg, rgba(220,53,69,0.05) 0%, transparent 100%);
    }
    
    .progress-container {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 16px 0;
    }
    
    .progress-bar-custom {
        width: 100%;
        height: 8px;
        background: #e9ecef;
        border-radius: 8px;
        overflow: hidden;
        margin: 12px 0;
        position: relative;
    }
    
    .progress-fill-custom {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 8px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .progress-fill-custom::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-online { background: #d4edda; color: #155724; }
    .status-offline { background: #f8d7da; color: #721c24; }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        border: 1px solid #e9ecef;
    }
    
    .metric-card:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    .input-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-top: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 4px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
    }
    
    .typing-avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .typing-bubble {
        background: white;
        border-radius: 20px 20px 20px 5px;
        padding: 12px 18px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #20c997;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #20c997;
        animation: typingAnimation 1.5s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typingAnimation {
        0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
        30% { opacity: 1; transform: translateY(-5px); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .sidebar-section {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    .example-query {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    
    .example-query:hover {
        background: #e9ecef;
        border-color: #667eea;
        transform: translateX(4px);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 12px;
        margin: 16px 0;
    }
    
    .conversation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding: 12px 0;
        border-bottom: 2px solid #e9ecef;
    }
    
    .conversation-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .conversation-stats {
        display: flex;
        gap: 15px;
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    .scroll-indicator {
        position: sticky;
        bottom: 10px;
        right: 10px;
        background: #667eea;
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        margin-left: auto;
        z-index: 100;
    }
    
    .scroll-indicator:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'agent_statuses' not in st.session_state:
    st.session_state.agent_statuses = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'usage_stats' not in st.session_state:
    st.session_state.usage_stats = {'queries_today': 0, 'total_queries': 0, 'avg_response_time': 0}
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
if 'show_typing' not in st.session_state:
    st.session_state.show_typing = False
if 'agent_flow' not in st.session_state:
    st.session_state.agent_flow = []
if 'voice_output_enabled' not in st.session_state:
    st.session_state.voice_output_enabled = True
if 'show_debug_enabled' not in st.session_state:
    st.session_state.show_debug_enabled = False
if 'auto_scroll_enabled' not in st.session_state:
    st.session_state.auto_scroll_enabled = True
if 'show_agent_details_enabled' not in st.session_state:
    st.session_state.show_agent_details_enabled = True
# Add session state for audio auto-submit tracking
if 'previous_audio_bytes' not in st.session_state:
    st.session_state.previous_audio_bytes = None
if 'auto_submit_enabled' not in st.session_state:
    st.session_state.auto_submit_enabled = True

# Header with modern design
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">🚀 AI Financial Assistant</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Powered by Mistral AI • Multi-Agent Intelligence • Real-time Analysis</p>
</div>
""", unsafe_allow_html=True)

def get_confidence_class(confidence):
    """Get CSS class based on confidence level."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def get_agent_status_class(status):
    """Get CSS class based on agent status."""
    status_map = {
        "waiting": "agent-waiting",
        "executing": "agent-executing", 
        "completed": "agent-completed",
        "failed": "agent-failed"
    }
    return status_map.get(status, "agent-waiting")

def get_status_icon(status):
    """Get icon based on status."""
    icon_map = {
        "waiting": "⏸️",
        "executing": "⚡",
        "completed": "✅",
        "failed": "❌"
    }
    return icon_map.get(status, "❓")

def get_agent_status_color(status: str) -> str:
    """Get hex color based on agent status for styling."""
    color_map = {
        "waiting": "#6c757d",    # Gray
        "executing": "#ffc107",   # Yellow/Orange
        "completed": "#28a745",   # Green
        "failed": "#dc3545"       # Red
    }
    return color_map.get(status, "#6c757d") # Default to gray

def create_query_understanding_display(query_interpretation, confidence):
    """Create enhanced query understanding display."""
    if not query_interpretation:
        return ""
    
    return f"""
    <div class="query-understanding">
        <div class="query-understanding-title">
            🧠 AI Understanding
        </div>
        <div class="query-understanding-content">
            {query_interpretation}
        </div>
    </div>
    """

def create_typing_indicator():
    """Create an enhanced typing indicator."""
    return """
    <div class="typing-indicator">
        <div class="typing-avatar">🤖</div>
        <div class="typing-bubble">
            <span style="font-size: 0.8rem; color: #6c757d;">AI is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    </div>
    """

def display_enhanced_real_time_status(session_id):
    """Enhanced real-time execution status with beautiful visualizations."""
    if not session_id:
        return
    
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/execution/status/{session_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Overall progress with enhanced styling
            progress = data.get('progress_percentage', 0.0)
            current_step = data.get('current_step', 'Unknown')
            overall_status = data.get('overall_status', 'unknown')
            
            # Status emoji mapping
            status_emoji = {
                'initializing': '🚀',
                'routing': '🧭', 
                'executing': '⚡',
                'completed': '✅',
                'failed': '❌'
            }
            
            st.markdown(f"""
            <div class="progress-container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0; color: #2c3e50;">
                        {status_emoji.get(overall_status, '🔄')} {current_step}
                    </h3>
                    <span style="font-size: 1.2rem; font-weight: 600; color: #667eea;">
                        {progress:.1f}%
                    </span>
                </div>
                <div class="progress-bar-custom">
                    <div class="progress-fill-custom" style="width: {progress}%"></div>
                </div>
                <p style="margin: 8px 0 0 0; color: #6c757d; font-size: 0.9rem;">
                    Processing your request with AI agents...
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced agent status cards
            agents = data.get('agents_status', [])
            if agents:
                st.markdown("### 🤖 Agent Execution Dashboard")
                
                # Create columns for agent cards
                cols = st.columns(min(len(agents), 3))
                
                for i, agent in enumerate(agents):
                    col_idx = i % 3
                    with cols[col_idx]:
                        status_class = get_agent_status_class(agent['status'])
                        icon = get_status_icon(agent['status'])
                        
                        # Calculate execution time
                        time_info = ""
                        if agent.get('start_time') and agent.get('end_time'):
                            start = datetime.fromisoformat(agent['start_time'].replace('Z', '+00:00'))
                            end = datetime.fromisoformat(agent['end_time'].replace('Z', '+00:00'))
                            duration = (end - start).total_seconds()
                            time_info = f"⏱️ {duration:.1f}s"
                        elif agent.get('start_time') and agent['status'] == "executing":
                            start = datetime.fromisoformat(agent['start_time'].replace('Z', '+00:00'))
                            duration = (datetime.now(start.tzinfo) - start).total_seconds()
                            time_info = f"⏱️ {duration:.1f}s"
                        
                        # Status badge color
                        badge_color = get_agent_status_color(agent['status'])
                        
                        st.markdown(f"""
                        <div class="agent-card {status_class}">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <h4 style="margin: 0 0 8px 0; color: #2c3e50;">
                                        {icon} {agent['agent_name']}
                                    </h4>
                                    <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">
                                        {agent['description']}
                                    </p>
                                </div>
                                <span class="status-badge" style="background-color: {badge_color}20; color: {badge_color};">
                                    {agent['status'].title()}
                                </span>
                            </div>
                            {f'<p style="margin: 8px 0 0 0; color: #495057; font-size: 0.8rem;">{time_info}</p>' if time_info else ''}
                            {f'<p style="margin: 8px 0 0 0; color: #dc3545; font-size: 0.8rem;">❌ {agent.get("error", "")}</p>' if agent['status'] == 'failed' else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add mini progress bar for executing agents
                        if agent['status'] == 'executing':
                            st.progress(0.5)  # Indeterminate progress
                            
            return overall_status
            
    except Exception as e:
        st.error(f"Error fetching status: {e}")
        return "error"

def display_enhanced_conversation():
    """Display conversation with modern chat bubbles and proper sizing."""
    # Conversation header
    st.markdown(f"""
    <div class="conversation-header">
        <div class="conversation-title">
            💬 Conversation
        </div>
        <div class="conversation-stats">
            <span>📊 {len(st.session_state.conversation)} messages</span>
            <span>🤖 AI Assistant</span>
            <span>⚡ Real-time</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a container for the chat with proper height
    chat_container = st.container()
    
    with chat_container:
        # Show typing indicator if processing
        if st.session_state.show_typing:
            st.markdown(create_typing_indicator(), unsafe_allow_html=True)
        
        # Display conversation messages with enhanced bubbles
        for entry in st.session_state.conversation:
            if len(entry) == 2:
                speaker, text = entry
                metadata = {}
            else:
                speaker, text, metadata = entry
            
            timestamp = datetime.now().strftime("%H:%M")
            
            if speaker.startswith("👤"):
                # User message with proper sizing
                st.markdown(f"""
                <div class="chat-message-container user-message-container">
                    <div class="user-message">
                        <div class="message-header">
                            <span style="font-weight: 500;">You</span>
                        </div>
                        <div class="message-content">{text}</div>
                        <div class="message-footer">
                            <span>{timestamp}</span>
                        </div>
                    </div>
                    <div class="chat-avatar user-avatar">👤</div>
                </div>
                """, unsafe_allow_html=True)
                
            elif speaker.startswith("🤖"):
                confidence = metadata.get('confidence', 0.0)
                confidence_class = get_confidence_class(confidence)
                
                # Assistant message with proper sizing
                st.markdown(f"""
                <div class="chat-message-container assistant-message-container">
                    <div class="chat-avatar assistant-avatar">🤖</div>
                    <div class="assistant-message">
                        <div class="message-header">
                            <span style="font-weight: 500;">AI Assistant</span>
                            <span class="confidence-indicator {confidence_class}">
                                🎯 {confidence:.0%}
                            </span>
                        </div>
                        <div class="message-content">{text}</div>
                        <div class="message-footer">
                            <span>{timestamp}</span>
                            <span>⚡ {metadata.get('response_time', 0):.1f}s</span>
                            {f'<span>🔊 {metadata.get("voice_output", {}).get("provider", "")} Voice</span>' if metadata.get('voice_output', {}).get('enabled') else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show enhanced query understanding
                if metadata.get('query_interpretation'):
                    st.markdown(
                        create_query_understanding_display(
                            metadata['query_interpretation'], 
                            confidence
                        ), 
                        unsafe_allow_html=True
                    )
                
                # Show agent flow visualization using Streamlit blocks
                if metadata.get('agents_used') and st.session_state.show_agent_details_enabled: # Added check for show_agent_details
                    st.markdown("---_**Agent Execution Flow:**_---") # More subtle title
                    agents_data = metadata['agents_used']
                    
                    for i, agent in enumerate(agents_data, 1):
                        agent_name = agent.get('agent_name', agent.get('name', 'Unknown Agent'))
                        status = agent.get('status', 'completed')
                        description = agent.get('description', 'Processing...')
                        icon = get_status_icon(status)
                        
                        # Timing information
                        timing_info = ""
                        if agent.get('start_time') and agent.get('end_time'):
                            try:
                                start = datetime.fromisoformat(agent['start_time'].replace('Z', '+00:00'))
                                end = datetime.fromisoformat(agent['end_time'].replace('Z', '+00:00'))
                                duration = (end - start).total_seconds()
                                timing_info = f"⏱️ {duration:.1f}s"
                            except Exception as e:
                                print(f"Error parsing agent timing: {e}")
                                timing_info = ""
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="border: 1px solid #e9ecef; border-left: 4px solid {get_agent_status_color(status)}; 
                                        border-radius: 8px; padding: 12px; margin: 8px 0; 
                                        box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h5 style="margin: 0; color: #2c3e50;">{i}. {icon} {agent_name}</h5>
                                    <span style="background-color: {get_agent_status_color(status)}20; 
                                                 color: {get_agent_status_color(status)}; 
                                                 padding: 4px 10px; border-radius: 15px; 
                                                 font-size: 0.8rem; font-weight: 500;">
                                        {status.title()}
                                    </span>
                                </div>
                                <p style="margin: 8px 0 4px 0; color: #495057; font-size: 0.9rem;">{description}</p>
                                {f'<p style="margin: 0; color: #6c757d; font-size: 0.75rem; text-align: right;">{timing_info}</p>' if timing_info else ''}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if agent.get('status') == 'failed' and agent.get('error'):
                                st.error(f"Error: {agent.get('error')}")
                    st.markdown("---") # End of flow separator
                
            else:
                # Error or system messages
                st.markdown(f"""
                <div style="text-align: center; margin: 16px 0; padding: 12px; background: #f8f9fa; border-radius: 8px; color: #6c757d; font-size: 0.9rem; border-left: 3px solid #dc3545;">
                    <strong>{speaker}:</strong> {text}
                </div>
                """, unsafe_allow_html=True)

def speak_response(text: str, provider: str = "macos_say", voice: str = None):
    """
    Speak the given text using the Voice CLI directly.
    
    Args:
        text: Text to speak
        provider: TTS provider to use (default: macos_say for speed)
        voice: Optional voice to use
    """
    try:
        # Clean the text for better speech (remove markdown, special characters)
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold markdown
        clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)  # Remove italic markdown
        clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)   # Remove code markdown
        clean_text = re.sub(r'#{1,6}\s*([^\n]+)', r'\1', clean_text)  # Remove headers
        clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)  # Remove links
        clean_text = re.sub(r'\n+', ' ', clean_text)  # Replace newlines with spaces
        clean_text = ' '.join(clean_text.split())  # Clean up extra spaces
        
        # Limit text length for reasonable speech duration
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        # Build the voice CLI command
        cmd = ['python', 'data_ingestion/cli/voice_cli.py']
        
        # Add provider and voice options
        if provider:
            cmd.extend(['--tts-provider', provider])
        if voice:
            cmd.extend(['--tts-voice', voice])
        
        # Add speak command and text
        cmd.extend(['speak', clean_text])
        
        # Execute the command
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode == 0:
            print(f"🔊 Voice output completed using {provider}")
            return True
        else:
            print(f"❌ Voice output failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Voice output timed out")
        return False
    except Exception as e:
        print(f"❌ Voice output error: {e}")
        return False

def send_intelligent_request(query: str = None, audio_file = None, voice_output_enabled: bool = False, show_debug: bool = False):
    """Enhanced request processing with better UX and agent flow tracking."""
    endpoint = ""
    payload = {}
    files = None

    # Set processing state and show typing
    st.session_state.is_processing = True
    st.session_state.show_typing = True
    
    # Update usage stats
    st.session_state.usage_stats['queries_today'] += 1
    st.session_state.usage_stats['total_queries'] += 1
    
    # Record start time for response time calculation
    start_time = time.time()

    # Prepare request
    if audio_file:
        endpoint = f"{ORCHESTRATOR_URL}/intelligent/voice"
        # Determine file type for the request
        file_type = getattr(audio_file, 'type', 'audio/wav') # Default to audio/wav if type attr is missing
        files = {'audio': (audio_file.name, audio_file, file_type)}
        payload = {
            'voice_mode': voice_output_enabled,
            'include_debug': show_debug
        }
        st.session_state.conversation.append(("👤 User (🎤 audio)", "Uploaded an audio file" if hasattr(audio_file, 'type') else "Recorded an audio snippet"))
    elif query:
        endpoint = f"{ORCHESTRATOR_URL}/intelligent/query"
        payload = {
            "query": query,
            "voice_mode": voice_output_enabled,
            "include_debug_info": show_debug
        }
        st.session_state.conversation.append(("👤 User", query))
    else:
        st.error("⚠️ Please provide a query or upload an audio file.")
        st.session_state.is_processing = False
        st.session_state.show_typing = False
        return

    # Show enhanced status container
    status_container = st.empty()
    
    try:
        # Start the request in a separate thread
        response_container = {"response": None, "error": None}
        
        def make_request():
            try:
                if files:
                    response = requests.post(endpoint, files=files, data=payload, timeout=120)
                else:
                    response = requests.post(endpoint, json=payload, timeout=120)
                response.raise_for_status()
                response_container["response"] = response.json()
            except Exception as e:
                response_container["error"] = e

        # Start request thread
        request_thread = threading.Thread(target=make_request)
        request_thread.start()
        
        # Poll for status updates
        session_id = None
        overall_status = "initializing"
        agent_flow_data = []
        
        while request_thread.is_alive() or overall_status not in ["completed", "failed", "error"]:
            if not session_id and response_container.get("response"):
                session_id = response_container["response"].get("session_id")
                st.session_state.current_session_id = session_id
            
            if session_id:
                with status_container.container():
                    overall_status = display_enhanced_real_time_status(session_id)
                    
                    # Collect agent flow data
                    try:
                        flow_response = requests.get(f"{ORCHESTRATOR_URL}/execution/status/{session_id}", timeout=5)
                        if flow_response.status_code == 200:
                            flow_data = flow_response.json()
                            agent_flow_data = flow_data.get('agents_status', [])
                    except:
                        pass
            
            time.sleep(0.5)
            
            if not request_thread.is_alive():
                break
        
        # Clear status and typing indicator
        status_container.empty()
        st.session_state.show_typing = False
        
        # Wait for thread completion
        request_thread.join()
        
        # Calculate response time
        response_time = time.time() - start_time
        st.session_state.usage_stats['avg_response_time'] = (
            st.session_state.usage_stats['avg_response_time'] + response_time
        ) / 2
        
        # Handle response
        if response_container.get("error"):
            raise response_container["error"]
            
        data = response_container["response"]
        
        # Store agent statuses with enhanced data
        agents_used = data.get('agents_used', [])
        if not agents_used and agent_flow_data:
            # Use flow data if agents_used is empty
            agents_used = agent_flow_data
        
        st.session_state.agent_statuses = agents_used
        
        # Add response to conversation with enhanced metadata
        confidence = data.get('confidence', 0.0)
        response_text = data['response_text']
        
        # Enhanced metadata with agent flow information
        enhanced_metadata = {
            'confidence': confidence,
            'agents_used': agents_used,
            'query_interpretation': data.get('query_interpretation', ''),
            'audio': data.get('wav_audio_base64'),
            'session_id': data.get('session_id'),
            'response_time': response_time,
            'agent_flow': agent_flow_data,
            'routing_info': data.get('routing_info', {}),
            'execution_stats': {
                'total_agents': len(agents_used),
                'successful_agents': len([a for a in agents_used if a.get('status') == 'completed']),
                'failed_agents': len([a for a in agents_used if a.get('status') == 'failed']),
                'response_time': response_time
            }
        }
        
        st.session_state.conversation.append((
            f"🤖 Assistant", 
            response_text,
            enhanced_metadata
        ))
        
        # Voice output - speak the response if enabled
        if voice_output_enabled and response_text:
            # Add voice indicator to the enhanced metadata
            enhanced_metadata['voice_output'] = {
                'enabled': True,
                'provider': st.session_state.get('voice_provider', 'macos_say'),
                'voice': st.session_state.get('voice_name', 'Samantha')
            }
            
            with st.spinner("🔊 Speaking response..."):
                # Use a thread to avoid blocking the UI
                def speak_in_background():
                    # Get user's voice settings or use defaults
                    provider = st.session_state.get('voice_provider', 'macos_say')
                    voice = st.session_state.get('voice_name', 'Samantha')
                    speak_response(response_text, provider=provider, voice=voice)
                
                # Start voice output in background thread
                voice_thread = threading.Thread(target=speak_in_background)
                voice_thread.daemon = True  # Daemon thread so it doesn't block app shutdown
                voice_thread.start()
        
        # Show enhanced success metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⚡ Response Time", f"{response_time:.1f}s", 
                     delta=f"{response_time-2:.1f}s" if response_time > 2 else None)
        with col2:
            st.metric("🎯 Confidence", f"{confidence:.1%}", 
                     delta=f"{confidence-0.8:.1%}" if confidence < 0.8 else "✅ High")
        with col3:
            st.metric("🤖 Agents Used", len(agents_used),
                     delta=f"+{len(agents_used)}" if len(agents_used) > 1 else None)
        with col4:
            successful_count = len([a for a in agents_used if a.get('status') == 'completed'])
            st.metric("✅ Success Rate", f"{successful_count}/{len(agents_used)}" if agents_used else "N/A")
        
        # Show agent execution summary
        if agents_used:
            with st.expander("📊 Detailed Agent Execution Summary", expanded=False):
                agent_df = pd.DataFrame([{
                    'Agent': agent.get('name', 'Unknown'),
                    'Status': agent.get('status', 'unknown'),
                    'Description': agent.get('description', 'N/A')[:50] + '...' if len(agent.get('description', '')) > 50 else agent.get('description', 'N/A'),
                    'Duration': f"{agent.get('duration', 0):.1f}s" if agent.get('duration') else 'N/A'
                } for agent in agents_used])
                
                st.dataframe(agent_df, use_container_width=True)
        
        # Play audio if available
        if data.get('wav_audio_base64'):
            st.success("🔊 Audio response generated!")
            audio_bytes = base64.b64decode(data['wav_audio_base64'])
            st.audio(audio_bytes, format="audio/wav")

        # Clean up session
        if session_id:
            try:
                requests.delete(f"{ORCHESTRATOR_URL}/execution/status/{session_id}")
            except:
                pass

    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The query might be too complex.")
        st.info("💡 Try breaking your question into smaller parts or checking your connection.")
    except requests.exceptions.RequestException as e:
        st.error(f"🚫 Connection error: {e}")
        st.info("💡 Make sure the Orchestrator service is running on port 8011")
    except Exception as e:
        st.error(f"💥 Unexpected error: {e}")
        st.info("💡 Please try again or contact support if the issue persists.")
    finally:
        st.session_state.is_processing = False
        st.session_state.show_typing = False
        st.session_state.current_session_id = None

# Enhanced Sidebar with better organization
with st.sidebar:
    
    # #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.subheader("⚙️ Advanced Settings")
    st.toggle("🔊 Voice Output", value=st.session_state.voice_output_enabled, help="Enable AI voice responses", key="voice_output_enabled")
    st.toggle("🐛 Debug Mode", value=st.session_state.show_debug_enabled, help="Show detailed debugging information", key="show_debug_enabled")
    st.toggle("📜 Auto-scroll Chat", value=st.session_state.auto_scroll_enabled, help="Automatically scroll to latest messages", key="auto_scroll_enabled")
    st.toggle("🤖 Show Agent Details", value=st.session_state.show_agent_details_enabled, help="Display detailed agent execution flow", key="show_agent_details_enabled")
    st.toggle("🚀 Auto-submit Voice", value=st.session_state.auto_submit_enabled, help="Automatically submit voice recordings to AI", key="auto_submit_enabled")
    
    # Voice Configuration (only show if voice output is enabled)
    if st.session_state.voice_output_enabled:
        st.markdown("#### 🎙️ Voice Settings")
        
        # Initialize voice settings in session state if not present
        if 'voice_provider' not in st.session_state:
            st.session_state.voice_provider = "macos_say"
        if 'voice_name' not in st.session_state:
            st.session_state.voice_name = "Samantha"
        
        # Voice provider selection
        voice_provider = st.selectbox(
            "TTS Provider",
            options=["macos_say", "pyttsx3", "openai", "elevenlabs", "google"],
            index=["macos_say", "pyttsx3", "openai", "elevenlabs", "google"].index(st.session_state.voice_provider),
            help="Choose the text-to-speech provider. macOS Say is fastest on Mac.",
            key="voice_provider"
        )
        
        # Voice selection based on provider
        if voice_provider == "macos_say":
            voice_options = ["Samantha", "Alex", "Victoria", "Daniel", "Karen", "Moira", "Tessa"]
            default_voice = "Samantha"
        elif voice_provider == "openai":
            voice_options = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            default_voice = "nova"
        elif voice_provider == "elevenlabs":
            voice_options = ["21m00Tcm4TlvDq8ikWAM", "29vD33N1CtxCmqQRPOHJ", "AZnzlk1XvdvUeBnXmlld"]
            default_voice = "21m00Tcm4TlvDq8ikWAM"
        elif voice_provider == "google":
            voice_options = ["en-US-Wavenet-D", "en-US-Neural2-A", "en-GB-Neural2-A", "en-AU-Neural2-A"]
            default_voice = "en-US-Wavenet-D"
        else:  # pyttsx3
            voice_options = ["Default", "Voice 1", "Voice 2"]
            default_voice = "Default"
        
        # Set default if current voice not in options
        if st.session_state.voice_name not in voice_options:
            st.session_state.voice_name = default_voice
        
        voice_name = st.selectbox(
            "Voice",
            options=voice_options,
            index=voice_options.index(st.session_state.voice_name) if st.session_state.voice_name in voice_options else 0,
            help=f"Choose the voice for {voice_provider} TTS",
            key="voice_name"
        )
        
        # Test voice button
        if st.button("🔊 Test Voice", use_container_width=True, 
                    help="Test the selected voice with a sample message"):
            test_text = "Hello! This is a test of the selected voice for your AI financial assistant."
            with st.spinner("Testing voice..."):
                success = speak_response(test_text, provider=voice_provider, voice=voice_name)
                if success:
                    st.success("✅ Voice test completed!")
                else:
                    st.error("❌ Voice test failed. Check your settings.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.subheader("📊 Usage Analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📈 Today", st.session_state.usage_stats['queries_today'], 
                 delta=f"+{st.session_state.usage_stats['queries_today']}")
    with col2:
        st.metric("📊 Total", st.session_state.usage_stats['total_queries'],
                 delta=f"+{st.session_state.usage_stats['total_queries']}")
    if st.session_state.usage_stats['avg_response_time'] > 0:
        st.metric("⚡ Avg Response", f"{st.session_state.usage_stats['avg_response_time']:.1f}s",
                 delta=f"{'Fast' if st.session_state.usage_stats['avg_response_time'] < 3 else 'Slow'}")
    if st.session_state.conversation:
        st.metric("💬 Messages", len(st.session_state.conversation))
    st.markdown('</div>', unsafe_allow_html=True)


    #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.header("🎛️ Control Center")
    
    # Connection status with enhanced styling
    try:
        status_response = requests.get(f"{ORCHESTRATOR_URL}/agents/status", timeout=3)
        if status_response.status_code == 200:
            status_data = status_response.json()
            st.markdown("""
            <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-radius: 8px; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #155724;">🟢 System Online</h4>
                <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #155724;">All systems operational</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("🤖 Available Agents")
            agent_data = status_data.get('available_agents', [])
            for i, agent in enumerate(agent_data):
                status_color = "#28a745"
                st.markdown(f"""
                <div style="background: white; padding: 12px; border-radius: 8px; margin: 6px 0; 
                           border-left: 4px solid {status_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #2c3e50; font-size: 0.9rem;">{agent['name']}</strong>
                            <p style="margin: 4px 0 0 0; color: #6c757d; font-size: 0.75rem; line-height: 1.3;">
                                {agent['description'][:80]}{'...' if len(agent['description']) > 80 else ''}
                            </p>
                        </div>
                        <span style="background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem;">
                            Ready
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); border-radius: 8px; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #721c24;">🔴 System Offline</h4>
                <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #721c24;">Please start the orchestrator</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); border-radius: 8px; margin-bottom: 16px;">
            <h4 style="margin: 0; color: #721c24;">🔴 Connection Failed</h4>
            <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #721c24;">Cannot reach orchestrator</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    # st.subheader("⚙️ Advanced Settings")
    # st.toggle("🔊 Voice Output", value=st.session_state.voice_output_enabled, help="Enable AI voice responses", key="voice_output_enabled")
    # st.toggle("🐛 Debug Mode", value=st.session_state.show_debug_enabled, help="Show detailed debugging information", key="show_debug_enabled")
    # st.toggle("📜 Auto-scroll Chat", value=st.session_state.auto_scroll_enabled, help="Automatically scroll to latest messages", key="auto_scroll_enabled")
    # st.toggle("🤖 Show Agent Details", value=st.session_state.show_agent_details_enabled, help="Display detailed agent execution flow", key="show_agent_details_enabled")
    
    # # Voice Configuration (only show if voice output is enabled)
    # if st.session_state.voice_output_enabled:
    #     st.markdown("#### 🎙️ Voice Settings")
        
    #     # Initialize voice settings in session state if not present
    #     if 'voice_provider' not in st.session_state:
    #         st.session_state.voice_provider = "macos_say"
    #     if 'voice_name' not in st.session_state:
    #         st.session_state.voice_name = "Samantha"
        
    #     # Voice provider selection
    #     voice_provider = st.selectbox(
    #         "TTS Provider",
    #         options=["macos_say", "pyttsx3", "openai", "elevenlabs", "google"],
    #         index=["macos_say", "pyttsx3", "openai", "elevenlabs", "google"].index(st.session_state.voice_provider),
    #         help="Choose the text-to-speech provider. macOS Say is fastest on Mac.",
    #         key="voice_provider"
    #     )
        
    #     # Voice selection based on provider
    #     if voice_provider == "macos_say":
    #         voice_options = ["Samantha", "Alex", "Victoria", "Daniel", "Karen", "Moira", "Tessa"]
    #         default_voice = "Samantha"
    #     elif voice_provider == "openai":
    #         voice_options = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    #         default_voice = "nova"
    #     elif voice_provider == "elevenlabs":
    #         voice_options = ["21m00Tcm4TlvDq8ikWAM", "29vD33N1CtxCmqQRPOHJ", "AZnzlk1XvdvUeBnXmlld"]
    #         default_voice = "21m00Tcm4TlvDq8ikWAM"
    #     elif voice_provider == "google":
    #         voice_options = ["en-US-Wavenet-D", "en-US-Neural2-A", "en-GB-Neural2-A", "en-AU-Neural2-A"]
    #         default_voice = "en-US-Wavenet-D"
    #     else:  # pyttsx3
    #         voice_options = ["Default", "Voice 1", "Voice 2"]
    #         default_voice = "Default"
        
    #     # Set default if current voice not in options
    #     if st.session_state.voice_name not in voice_options:
    #         st.session_state.voice_name = default_voice
        
    #     voice_name = st.selectbox(
    #         "Voice",
    #         options=voice_options,
    #         index=voice_options.index(st.session_state.voice_name) if st.session_state.voice_name in voice_options else 0,
    #         help=f"Choose the voice for {voice_provider} TTS",
    #         key="voice_name"
    #     )
        
    #     # Test voice button
    #     if st.button("🔊 Test Voice", use_container_width=True, 
    #                 help="Test the selected voice with a sample message"):
    #         test_text = "Hello! This is a test of the selected voice for your AI financial assistant."
    #         with st.spinner("Testing voice..."):
    #             success = speak_response(test_text, provider=voice_provider, voice=voice_name)
    #             if success:
    #                 st.success("✅ Voice test completed!")
    #             else:
    #                 st.error("❌ Voice test failed. Check your settings.")
    
    # st.markdown('</div>', unsafe_allow_html=True)
    
    # #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    # st.subheader("📊 Usage Analytics")
    # col1, col2 = st.columns(2)
    # with col1:
    #     st.metric("📈 Today", st.session_state.usage_stats['queries_today'], 
    #              delta=f"+{st.session_state.usage_stats['queries_today']}")
    # with col2:
    #     st.metric("📊 Total", st.session_state.usage_stats['total_queries'],
    #              delta=f"+{st.session_state.usage_stats['total_queries']}")
    # if st.session_state.usage_stats['avg_response_time'] > 0:
    #     st.metric("⚡ Avg Response", f"{st.session_state.usage_stats['avg_response_time']:.1f}s",
    #              delta=f"{'Fast' if st.session_state.usage_stats['avg_response_time'] < 3 else 'Slow'}")
    # if st.session_state.conversation:
    #     st.metric("💬 Messages", len(st.session_state.conversation))
    # st.markdown('</div>', unsafe_allow_html=True)
    
    # #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    # st.subheader("🚀 Smart Quick Actions")
    # quick_queries = [
    #     ("📈", "Stock Price", "What's the current price of AAPL stock?", "#667eea"),
    #     ("📊", "Portfolio Analysis", "Analyze my portfolio performance this month", "#28a745"),
    #     ("🔍", "Market Trends", "What are the latest market trends in tech stocks?", "#17a2b8"),
    #     ("💰", "Top Performers", "Show me the best performing stocks today", "#ffc107"),
    #     ("📰", "Financial News", "Get me the latest financial headlines and analysis", "#6f42c1"),
    #     ("🎯", "Investment Advice", "Give me investment advice for emerging markets", "#e83e8c")
    # ]
    # for icon, label, query, color in quick_queries:
    #     if st.button(f"{icon} {label}", key=f"smart_{label}", use_container_width=True, 
    #                 help=f"Click to ask: {query}"):
    #         st.session_state.example_query = query
    #         st.rerun()
    # st.markdown('</div>', unsafe_allow_html=True)
    
    #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.subheader("⚡ System Performance")
    cpu_usage = 45
    memory_usage = 62
    response_quality = 95
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💻 CPU", f"{cpu_usage}%", delta=f"{'Normal' if cpu_usage < 70 else 'High'}")
        st.metric("🎯 Quality", f"{response_quality}%", delta="Excellent")
    with col2:
        st.metric("🧠 Memory", f"{memory_usage}%", delta=f"{'Good' if memory_usage < 80 else 'High'}")
        st.metric("🔗 Uptime", "99.9%", delta="Stable")
    st.markdown('</div>', unsafe_allow_html=True)

# Main chat interface with enhanced layout
main_col1, main_col2 = st.columns([4, 1])

with main_col1:
    display_enhanced_conversation()

with main_col2:
    # Real-time metrics panel
    st.markdown("### 📊 Live Metrics")
    
    if st.session_state.conversation:
        # Calculate conversation stats
        user_messages = len([msg for msg in st.session_state.conversation if msg[0].startswith("👤")])
        ai_messages = len([msg for msg in st.session_state.conversation if msg[0].startswith("🤖")])
        
        st.metric("👤 Your Messages", user_messages)
        st.metric("🤖 AI Responses", ai_messages)
        
        # Recent agent activity
        if st.session_state.agent_statuses:
            st.markdown("#### 🤖 Recent Agents")
            for agent in st.session_state.agent_statuses[-3:]:  # Show last 3 agents
                status_emoji = get_status_icon(agent.get('status', 'completed'))
                st.markdown(f"""
                <div style="background: white; padding: 8px; border-radius: 6px; margin: 4px 0; 
                           border-left: 3px solid #20c997; font-size: 0.8rem;">
                    {status_emoji} <strong>{agent.get('agent_name', agent.get('name', 'Agent'))}</strong>
                </div>
                """, unsafe_allow_html=True)

# Enhanced input area with better layout
st.markdown('<div class="input-container">', unsafe_allow_html=True)

input_col1, input_col2 = st.columns([3, 1])

with input_col1:
    st.markdown("### 💭 Ask Your Financial Question")
    
    # Enhanced text input with better UX
    user_input = st.text_area(
        "Your financial query",
        value=st.session_state.get('example_query', ''),
        height=120,
        placeholder="💡 Examples:\n• What's the current price of AAPL?\n• Analyze Tesla's performance vs competitors\n• Should I invest in renewable energy stocks?\n• Explain the latest Fed interest rate decision",
        help="Ask about stocks, market analysis, portfolio management, economic trends, or any financial topic",
        label_visibility="collapsed",
        key="main_input"
    )
    
    # Clear example query after use
    if 'example_query' in st.session_state:
        del st.session_state.example_query
    
    # Enhanced file upload
    uploaded_file = st.file_uploader(
        "🎤 Or upload audio (WAV, MP3, M4A format):", 
        type=["wav", "mp3", "m4a"],
        help="Upload a voice recording for speech-to-text processing (WAV, MP3, M4A supported)"
    )

    # Input suggestions
    if not user_input and not uploaded_file:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #20c997;">
            <small style="color: #6c757d;">
                💡 <strong>Pro Tips:</strong> Be specific with ticker symbols, ask for comparisons, 
                or request analysis of market trends for better results.
            </small>
        </div>
        """, unsafe_allow_html=True)

    # Audio recording section
    # st.markdown("---_**OR**_---") # Separator 
    st.markdown("---")
    st.markdown("🎙️ **Record Audio Directly:**")
    
    # Show current auto-submit status
    if st.session_state.auto_submit_enabled:
        st.info("💡 **Auto-submit is ON** - Your voice recordings will be automatically sent to AI")
    else:
        st.info("📋 **Manual mode** - Click 'Ask AI' after recording to submit")
    
    recorded_audio_bytes = st.audio_input("🎙️ Record your voice", key="audio_input")
    
    # Auto-submit functionality for recorded audio
    if recorded_audio_bytes is not None and st.session_state.auto_submit_enabled:
        # Check if this is a new recording by comparing with previous audio
        if (st.session_state.previous_audio_bytes is None or 
            st.session_state.previous_audio_bytes != recorded_audio_bytes):
            
            # Update the previous audio state
            st.session_state.previous_audio_bytes = recorded_audio_bytes
            
            # Display auto-submit notification
            st.success("🎤 ✅ Voice recorded successfully! Auto-submitting to AI...")
            
            # Auto-trigger the AI request if not already processing
            if not st.session_state.is_processing:
                # Add a small delay to ensure the UI updates properly
                time.sleep(0.5)
                
                # Automatically send the audio to the AI
                send_intelligent_request(
                    audio_file=recorded_audio_bytes, 
                    voice_output_enabled=st.session_state.voice_output_enabled,
                    show_debug=st.session_state.show_debug_enabled
                )
                st.rerun()
        else:
            # Show status for existing audio
            st.success("🎤 ✅ Voice recording ready (already submitted)")
    elif recorded_audio_bytes is not None:
        # Show status when auto-submit is disabled
        st.warning("🎤 📋 Voice recorded - Click 'Ask AI' to submit")

with input_col2:
    st.markdown("### 🎮 Actions")
    
    # Enhanced send button with better states
    button_disabled = st.session_state.is_processing
    
    # Check if audio was just auto-submitted
    audio_auto_submitted = (recorded_audio_bytes is not None and 
                          st.session_state.auto_submit_enabled and 
                          st.session_state.previous_audio_bytes == recorded_audio_bytes)
    
    if st.session_state.is_processing:
        button_label = "⏳ Processing..."
        button_help = "Please wait while your query is being processed by AI agents"
        button_type = "secondary"
    elif audio_auto_submitted:
        button_label = "🎤 Audio Submitted"
        button_help = "Voice recording was automatically submitted to AI"
        button_type = "secondary"
    else:
        button_label = "🚀 Ask AI"
        button_help = "Send your question to the intelligent financial assistant"
        button_type = "primary"
    
    send_button = st.button(
        button_label, 
        use_container_width=True, 
        type=button_type, 
        disabled=button_disabled or audio_auto_submitted,
        help=button_help
    )
    
    if send_button:
        if recorded_audio_bytes and not audio_auto_submitted: 
            send_intelligent_request(
                audio_file=recorded_audio_bytes, 
                voice_output_enabled=st.session_state.voice_output_enabled,
                show_debug=st.session_state.show_debug_enabled
            )
        elif uploaded_file:
            send_intelligent_request(
                audio_file=uploaded_file, 
                voice_output_enabled=st.session_state.voice_output_enabled,
                show_debug=st.session_state.show_debug_enabled
            )
        elif user_input and user_input.strip():
            send_intelligent_request(
                query=user_input.strip(), 
                voice_output_enabled=st.session_state.voice_output_enabled,
                show_debug=st.session_state.show_debug_enabled
            )
        else:
            st.warning("⚠️ Please enter a query or upload an audio file.")
        st.rerun()
    
    # Enhanced action buttons
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear", use_container_width=True, disabled=st.session_state.is_processing,
                    help="Clear conversation history"):
            st.session_state.conversation = []
            st.session_state.agent_statuses = []
            st.session_state.usage_stats = {'queries_today': 0, 'total_queries': 0, 'avg_response_time': 0}
            # Reset audio state when clearing conversation
            st.session_state.previous_audio_bytes = None
            st.rerun()
    
    with col_b:
        if st.button("📥 Export", use_container_width=True, help="Export conversation and analytics"):
            export_data = {
                "conversation": st.session_state.conversation,
                "usage_stats": st.session_state.usage_stats,
                "export_timestamp": datetime.now().isoformat(),
                "agent_statuses": st.session_state.agent_statuses
            }
            conversation_json = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                "💾 Download Data",
                conversation_json,
                f"ai_financial_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )

    # Add a reset audio button when audio is present
    if recorded_audio_bytes is not None:
        if st.button("🎤 Reset Audio", use_container_width=True, disabled=st.session_state.is_processing,
                    help="Clear current audio recording to record a new one"):
            st.session_state.previous_audio_bytes = None
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Enhanced processing indicator
if st.session_state.is_processing:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
                padding: 20px; border-radius: 12px; margin: 20px 0; 
                border-left: 4px solid #ffc107; text-align: center;
                box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);">
        <h3 style="margin: 0 0 8px 0; color: #856404;">🧠 AI Financial Assistant is analyzing...</h3>
        <p style="margin: 0; color: #856404; font-size: 1rem;">
            Multiple intelligent agents are working together to provide you with comprehensive financial insights
        </p>
        <div style="margin-top: 12px;">
            <small style="color: #856404; opacity: 0.8;">
                🔄 Query Analysis → 🤖 Agent Routing → 📊 Data Processing → 🎯 Response Generation
            </small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Enhanced footer with comprehensive information
st.markdown("---")
st.markdown("### 🌟 Enhanced AI Financial Assistant Features")

feature_col1, feature_col2, feature_col3, feature_col4 = st.columns(4)

with feature_col1:
    st.markdown("""
    <div class="metric-card">
        <h4 style="color: #667eea; margin-bottom: 12px;">💡 Smart Queries</h4>
        <ul style="text-align: left; font-size: 0.9rem; margin: 0; padding-left: 20px;">
            <li>Natural language processing</li>
            <li>Context-aware responses</li>
            <li>Multi-step analysis</li>
            <li>Real-time data integration</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with feature_col2:
    st.markdown("""
    <div class="metric-card">
        <h4 style="color: #20c997; margin-bottom: 12px;">🤖 Agent Intelligence</h4>
        <ul style="text-align: left; font-size: 0.9rem; margin: 0; padding-left: 20px;">
            <li>6 specialized AI agents</li>
            <li>Parallel processing</li>
            <li>Intelligent routing</li>
            <li>Real-time status tracking</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with feature_col3:
    st.markdown("""
    <div class="metric-card">
        <h4 style="color: #28a745; margin-bottom: 12px;">📊 Data Sources</h4>
        <ul style="text-align: left; font-size: 0.9rem; margin: 0; padding-left: 20px;">
            <li>Live market data</li>
            <li>Financial news feeds</li>
            <li>Economic indicators</li>
            <li>Company fundamentals</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with feature_col4:
    st.markdown("""
    <div class="metric-card">
        <h4 style="color: #6f42c1; margin-bottom: 12px;">🎯 Capabilities</h4>
        <ul style="text-align: left; font-size: 0.9rem; margin: 0; padding-left: 20px;">
            <li>Voice input/output</li>
            <li>Portfolio analysis</li>
            <li>Market predictions</li>
            <li>Investment recommendations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Final enhanced status indicator
st.markdown("""
<div style="text-align: center; padding: 25px; 
           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           border-radius: 15px; margin-top: 30px; color: white;
           box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
    <h3 style="margin: 0 0 8px 0; font-weight: 700;">🚀 AI Financial Assistant v3.0</h3>
    <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
        Intelligent • Lightning Fast • Comprehensive • Reliable
    </p>
    <div style="margin-top: 12px; font-size: 0.9rem; opacity: 0.8;">
        Powered by <strong>Mistral AI</strong> • Enhanced with <strong>Multi-Agent Intelligence</strong> • 
        Real-time <strong>Financial Data</strong>
    </div>
</div>
""", unsafe_allow_html=True) 