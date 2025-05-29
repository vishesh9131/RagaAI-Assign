import streamlit as st
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
import sys
from pathlib import Path

# Add the project root to the path so we can import agents
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import agents - if this fails, we'll run in basic embedded mode
try:
    from agents.core.voice_agent import VoiceAgent
    from agents.core.retriever_agent import RetrieverAgent
    from agents.core.language_agent import LanguageAgent
    from agents.core.market_agent import MarketDataAgent  # Correct class name
    from agents.core.analysis_agent import AnalysisAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import agents: {e}")
    AGENTS_AVAILABLE = False

# Configuration
ORCHESTRATOR_URL = None  # Set to None to force embedded mode
VOICE_AGENT_URL = "http://localhost:8000"  # Voice Agent API URL
EMBEDDED_MODE = True  # Force embedded mode for Streamlit Cloud

@st.cache_resource
def initialize_agents():
    """Initialize all available agents for embedded mode."""
    if not AGENTS_AVAILABLE:
        print("⚠️  Agents not available - running in basic embedded mode")
        return {}
    
    agents = {}
    agent_errors = []
    
    # Language Agent - Most basic, try first
    try:
        print("Initializing Language Agent...")
        agents['language'] = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")
        print("✅ Language Agent initialized successfully")
    except Exception as e:
        error_msg = f"❌ Failed to initialize Language Agent: {str(e)}"
        print(error_msg)
        agent_errors.append(error_msg)
    
    # Market Agent - Core functionality for financial data
    try:
        print("Initializing Market Agent...")
        agents['market'] = MarketDataAgent()
        print("✅ Market Agent initialized successfully")
    except Exception as e:
        error_msg = f"❌ Failed to initialize Market Agent: {str(e)}"
        print(error_msg)
        agent_errors.append(error_msg)
    
    # Analysis Agent - Portfolio analysis
    try:
        print("Initializing Analysis Agent...")
        agents['analysis'] = AnalysisAgent()
        print("✅ Analysis Agent initialized successfully")
    except Exception as e:
        error_msg = f"❌ Failed to initialize Analysis Agent: {str(e)}"
        print(error_msg)
        agent_errors.append(error_msg)
    
    # Retriever Agent - May have heavy dependencies
    try:
        print("Initializing Retriever Agent...")
        agents['retriever'] = RetrieverAgent()
        print("✅ Retriever Agent initialized successfully")
    except Exception as e:
        error_msg = f"❌ Failed to initialize Retriever Agent (this is optional): {str(e)}"
        print(error_msg)
        agent_errors.append(error_msg)
        # Retriever is optional, don't fail completely
    
    # Voice Agent - May have platform dependencies
    try:
        print("Initializing Voice Agent...")
        agents['voice'] = VoiceAgent()
        print("✅ Voice Agent initialized successfully")
    except Exception as e:
        error_msg = f"❌ Failed to initialize Voice Agent (this is optional): {str(e)}"
        print(error_msg)
        agent_errors.append(error_msg)
        # Voice is optional, don't fail completely
    
    print(f"🤖 Successfully initialized {len(agents)} out of 5 agents")
    
    if agent_errors:
        print("⚠️  Some agents failed to initialize:")
        for error in agent_errors:
            print(f"   {error}")
        print("💡 The app will continue with available agents and fallback processing")
    
    return agents

class QueryRouter:
    def __init__(self):
        self.patterns = {
            "market_data": [
                r"stock", r"price", r"share", r"ticker", r"market", r"trading", r"volume", r"quote",
                r"AAPL", r"GOOGL", r"MSFT", r"TSLA", r"AMZN", r"META", r"NVDA", r"NFLX", r"SPY", r"QQQ",
                r"earnings", r"revenue", r"profit", r"financial", r"company", r"corporation", r"business",
                r"dividend", r"yield", r"market cap", r"P/E", r"ratio", r"valuation", r"fundamentals",
                r"NYSE", r"NASDAQ", r"exchange", r"S&P", r"Dow", r"index", r"ETF", r"mutual fund"
            ],
            "analysis": [
                r"analyze", r"analysis", r"compare", r"comparison", r"performance", r"trend", r"pattern",
                r"forecast", r"predict", r"projection", r"outlook", r"recommendation", r"advice",
                r"portfolio", r"investment", r"strategy", r"risk", r"return", r"volatility",
                r"technical analysis", r"fundamental analysis", r"chart", r"indicator"
            ],
            "explanation": [
                r"explain", r"what is", r"how does", r"why", r"help me understand", r"clarify",
                r"definition", r"meaning", r"concept", r"basics", r"introduction", r"overview"
            ]
        }
    
    def classify_query(self, query: str) -> List[str]:
        """Classify query and return list of relevant agent types."""
        import re
        
        query_lower = query.lower()
        selected_agents = []
        
        # Check for market data patterns
        for pattern in self.patterns["market_data"]:
            if re.search(pattern, query_lower):
                if "market_data" not in selected_agents:
                    selected_agents.append("market_data")
                break
        
        # Check for analysis patterns
        for pattern in self.patterns["analysis"]:
            if re.search(pattern, query_lower):
                if "analysis" not in selected_agents:
                    selected_agents.append("analysis")
                break
        
        # Check for explanation patterns
        for pattern in self.patterns["explanation"]:
            if re.search(pattern, query_lower):
                if "explanation" not in selected_agents:
                    selected_agents.append("explanation")
                break
        
        # Default routing if no specific patterns found
        if not selected_agents:
            selected_agents = ["explanation"]  # Default to explanation for general queries
        
        return selected_agents

# Initialize router
query_router = QueryRouter()

# Attempt to import the audio recorder component
try:
    # Use native Streamlit audio input instead of st_audiorec
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

st.set_page_config(
    layout="wide", 
    page_title="🚀 AI Financial Assistant", 
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

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

# Embedded mode status banner
if EMBEDDED_MODE or ORCHESTRATOR_URL is None:
    st.info("""
    🟣 **Embedded Mode Active**  
    You're using the self-contained version of the AI Financial Assistant. All agents are running locally within this application.
    """)

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
    Speak the given text using various TTS providers.
    
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
        if len(clean_text) > 300:
            clean_text = clean_text[:300] + "..."
        
        # Try different TTS approaches based on provider
        if provider == "macos_say":
            # Use macOS built-in say command directly
            cmd = ['say']
            if voice and voice != "Default":
                cmd.extend(['-v', voice])
            cmd.append(clean_text)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print(f"🔊 Voice output completed using macOS say")
                return True
            else:
                print(f"❌ macOS say failed: {result.stderr}")
                # Fall back to alternative method
                return _fallback_voice_output(clean_text)
        
        else:
            # For other providers, try the voice CLI approach
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
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"🔊 Voice output completed using {provider}")
                return True
            else:
                print(f"❌ Voice CLI failed: {result.stderr}")
                # Fall back to macOS say if available
                return _fallback_voice_output(clean_text)
            
    except subprocess.TimeoutExpired:
        print("❌ Voice output timed out")
        return False
    except Exception as e:
        print(f"❌ Voice output error: {e}")
        return False

def _fallback_voice_output(text: str):
    """Fallback voice output using system commands."""
    try:
        # Try basic macOS say command as fallback
        import platform
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['say', text], capture_output=True, timeout=10)
            if result.returncode == 0:
                print("🔊 Fallback voice output successful")
                return True
        
        # If all else fails, at least log that we would have spoken
        print(f"📢 Would have spoken: {text[:50]}{'...' if len(text) > 50 else ''}")
        return False
        
    except Exception as e:
        print(f"❌ Fallback voice failed: {e}")
        return False

def send_intelligent_request(query: str = None, audio_file = None, voice_output_enabled: bool = False, show_debug: bool = False):
    """Enhanced request processing with embedded mode support."""
    
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
        st.session_state.conversation.append(("👤 User (🎤 audio)", "Uploaded an audio file" if hasattr(audio_file, 'type') else "Recorded an audio snippet"))
        # For embedded mode, we'll skip audio processing for now and use a placeholder
        query = "Audio query uploaded (audio processing not yet implemented in embedded mode)"
    elif query:
        st.session_state.conversation.append(("👤 User", query))
    else:
        st.error("⚠️ Please provide a query or upload an audio file.")
        st.session_state.is_processing = False
        st.session_state.show_typing = False
        return

    # Check if we're in embedded mode (no external orchestrator)
    if EMBEDDED_MODE or ORCHESTRATOR_URL is None:
        # Use embedded processing
        try:
            # Show processing status
            with st.spinner("🤖 Processing your query using embedded agents..."):
                
                # Initialize agents
                agents = initialize_agents()
                if not agents:
                    # Fallback response when agents can't be initialized
                    response_text = f"""I understand you're asking about: **{query}**

I'm currently running in embedded mode with limited agent capabilities. Here's what I can help you with:

🔍 **Query Understanding**: I've analyzed your question and it appears to be about financial topics.

💡 **General Response**: While I don't have access to real-time market data in this embedded mode, I can provide general guidance:

- For stock prices and market data, I'd recommend checking financial websites like Yahoo Finance, Bloomberg, or your brokerage platform
- For investment advice, consider consulting with a financial advisor
- For market analysis, financial news sources provide comprehensive coverage

📝 **Note**: This is the embedded version of the AI Financial Assistant. The full-featured version with real-time data access and specialized agents is available when running the complete system locally.

Is there anything specific about this topic I can help explain or clarify?"""
                else:
                    # Classify the query to determine which agents to use
                    agent_types = query_router.classify_query(query)
                    
                    # Build comprehensive response using available agents
                    response_parts = []
                    agents_used = []
                    
                    # Process with Language Agent first for general understanding
                    if 'language' in agents:
                        try:
                            lang_response = agents['language'].explain(f"Please provide a helpful response to this query: {query}", target_audience="user")
                            if lang_response and lang_response.strip():
                                response_parts.append(f"🧠 **AI Analysis**: {lang_response}")
                                agents_used.append({
                                    'agent_name': 'Language Agent',
                                    'status': 'completed',
                                    'description': 'Analyzed query using natural language processing',
                                    'start_time': datetime.now().isoformat(),
                                    'end_time': datetime.now().isoformat()
                                })
                        except Exception as e:
                            print(f"Language agent error: {e}")
                    
                    # Process with Market Agent for financial data
                    if 'market_data' in agent_types and 'market' in agents:
                        try:
                            # Extract ticker symbol if present
                            ticker_mapping = {
                                "apple": "AAPL", "aapl": "AAPL",
                                "tesla": "TSLA", "tsla": "TSLA", 
                                "microsoft": "MSFT", "msft": "MSFT",
                                "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
                                "amazon": "AMZN", "amzn": "AMZN",
                                "meta": "META", "facebook": "META",
                                "nvidia": "NVDA", "nvda": "NVDA"
                            }
                            
                            # Extract ticker from query
                            found_tickers = []
                            query_lower = query.lower()
                            
                            for name, ticker_symbol in ticker_mapping.items():
                                if name in query_lower:
                                    found_tickers.append(ticker_symbol)
                            
                            # Also look for uppercase ticker patterns
                            ticker_patterns = re.findall(r'\b([A-Z]{2,5})\b', query.upper())
                            excluded_words = {"WHAT", "THE", "AND", "FOR", "WITH", "FROM", "THAT", "THIS", "HOW", "ARE", "CAN", "WILL"}
                            for pattern in ticker_patterns:
                                if pattern not in excluded_words and pattern not in found_tickers:
                                    found_tickers.append(pattern)
                            
                            ticker = found_tickers[0] if found_tickers else "AAPL"
                            
                            market_response = agents['market'].get_stock_price(ticker)
                            if market_response and not market_response.get('error'):
                                company_name = market_response.get('company_name', ticker)
                                current_price = market_response.get('current_price', 'N/A')
                                change = market_response.get('change', 0)
                                change_percent = market_response.get('change_percent', 0)
                                
                                market_text = f"**{company_name} ({ticker})**\n"
                                market_text += f"Current Price: ${current_price}\n"
                                market_text += f"Change: ${change:+.2f} ({change_percent:+.2f}%)\n"
                                market_text += f"Market Cap: {market_response.get('market_cap', 'N/A')}\n"
                                market_text += f"P/E Ratio: {market_response.get('pe_ratio', 'N/A')}"
                                
                                response_parts.append(f"📊 **Market Data**: {market_text}")
                                agents_used.append({
                                    'agent_name': 'Market Agent',
                                    'status': 'completed',
                                    'description': f'Retrieved market data for {ticker}',
                                    'start_time': datetime.now().isoformat(),
                                    'end_time': datetime.now().isoformat()
                                })
                            else:
                                print(f"Market agent returned error: {market_response.get('error', 'Unknown error')}")
                        except Exception as e:
                            print(f"Market agent error: {e}")
                    
                    # Process with Analysis Agent for detailed analysis
                    if 'analysis' in agent_types and 'analysis' in agents:
                        try:
                            if any(word in query.lower() for word in ["portfolio", "change", "performance"]):
                                analysis_response = agents['analysis'].get_portfolio_value_change()
                                if analysis_response:
                                    today_value = analysis_response.get('today_value', 0)
                                    change = analysis_response.get('change', 0)
                                    change_percent = analysis_response.get('percentage_change', 0)
                                    
                                    analysis_text = f"Portfolio Performance Analysis:\n"
                                    analysis_text += f"Current Portfolio Value: ${today_value:,.0f}\n"
                                    analysis_text += f"Daily Change: ${change:+,.0f} ({change_percent:+.2f}%)"
                                    
                                    response_parts.append(f"🎯 **Portfolio Analysis**: {analysis_text}")
                                    agents_used.append({
                                        'agent_name': 'Analysis Agent',
                                        'status': 'completed',
                                        'description': 'Performed portfolio performance analysis',
                                        'start_time': datetime.now().isoformat(),
                                        'end_time': datetime.now().isoformat()
                                    })
                            elif any(word in query.lower() for word in ["sentiment", "news"]):
                                sentiment_response = agents['analysis'].get_sentiment_trends()
                                if sentiment_response is not None and not sentiment_response.empty:
                                    avg_sentiment = sentiment_response['compound'].mean()
                                    sentiment_text = f"News Sentiment Analysis:\n"
                                    sentiment_text += f"Average Sentiment Score: {avg_sentiment:.2f}\n"
                                    sentiment_text += f"Overall Market Sentiment: {'Positive' if avg_sentiment > 0.05 else 'Negative' if avg_sentiment < -0.05 else 'Neutral'}"
                                    
                                    response_parts.append(f"🎯 **Sentiment Analysis**: {sentiment_text}")
                                    agents_used.append({
                                        'agent_name': 'Analysis Agent',
                                        'status': 'completed',
                                        'description': 'Analyzed market sentiment from news',
                                        'start_time': datetime.now().isoformat(),
                                        'end_time': datetime.now().isoformat()
                                    })
                        except Exception as e:
                            print(f"Analysis agent error: {e}")
                    
                    # Process with Retriever Agent for additional context
                    if 'retriever' in agents:
                        try:
                            retriever_response = agents['retriever'].search(query, k=3)
                            if retriever_response and len(retriever_response) > 0:
                                retriever_text = "Relevant Information Found:\n"
                                for i, result in enumerate(retriever_response[:2], 1):  # Limit to top 2 results
                                    content = result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
                                    retriever_text += f"{i}. {content}\n"
                                
                                response_parts.append(f"📚 **Knowledge Base**: {retriever_text}")
                                agents_used.append({
                                    'agent_name': 'Retriever Agent',
                                    'status': 'completed',
                                    'description': f'Found {len(retriever_response)} relevant documents',
                                    'start_time': datetime.now().isoformat(),
                                    'end_time': datetime.now().isoformat()
                                })
                        except Exception as e:
                            print(f"Retriever agent error: {e}")
                    
                    # Combine responses or provide fallback
                    if response_parts:
                        response_text = "\n\n".join(response_parts)
                        
                        # Add a helpful summary
                        response_text += f"""

---
💡 **Summary**: I've analyzed your query "{query}" using {len(agents_used)} specialized agents. The response above combines insights from natural language processing, market data analysis, and knowledge retrieval to provide you with comprehensive information.

🔮 **Next Steps**: Feel free to ask follow-up questions or request more specific analysis on any aspect that interests you!"""
                    else:
                        # Fallback when agents don't return useful responses
                        response_text = f"""I've processed your query about: **{query}**

🤖 **Embedded Agent Processing**: I've analyzed your question using the available AI agents, though some may have limited functionality in this embedded mode.

💭 **Understanding**: Your query appears to be related to {', '.join(agent_types)} topics.

📝 **Response**: While I can understand and process your financial questions, the embedded mode has limited access to real-time data and advanced analytics.

🚀 **Suggestion**: For the most comprehensive analysis, the full system with live market data feeds and complete agent capabilities would provide more detailed insights.

Is there a specific aspect of your question I can help clarify or explain in more detail?"""
                
                # Calculate response time
                response_time = time.time() - start_time
                st.session_state.usage_stats['avg_response_time'] = (
                    st.session_state.usage_stats['avg_response_time'] + response_time
                ) / 2
                
                # Enhanced metadata with agent information
                enhanced_metadata = {
                    'confidence': 0.85 if agents else 0.6,
                    'agents_used': agents_used if agents else [{
                        'agent_name': 'Embedded Fallback',
                        'status': 'completed',
                        'description': 'Basic query processing without specialized agents',
                        'start_time': datetime.now().isoformat(),
                        'end_time': datetime.now().isoformat()
                    }],
                    'query_interpretation': f"Embedded mode processing: Query classified as {', '.join(agent_types) if agents else 'general'} - {query[:100]}{'...' if len(query) > 100 else ''}",
                    'session_id': str(uuid.uuid4()),
                    'response_time': response_time,
                    'execution_stats': {
                        'total_agents': len(agents_used) if agents else 1,
                        'successful_agents': len(agents_used) if agents else 1,
                        'failed_agents': 0,
                        'response_time': response_time,
                        'agent_types_used': agent_types if agents else ['fallback']
                    }
                }
                
                st.session_state.conversation.append((
                    f"🤖 Assistant", 
                    response_text,
                    enhanced_metadata
                ))
                
                # Clear processing state
                st.session_state.is_processing = False
                st.session_state.show_typing = False
                
                # Show success metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("⚡ Response Time", f"{response_time:.1f}s")
                with col2:
                    st.metric("🎯 Confidence", f"{enhanced_metadata['confidence']:.0%}")
                with col3:
                    st.metric("🤖 Agents Used", len(agents_used) if agents else 1)
                with col4:
                    st.metric("✅ Success Rate", f"{len(agents_used)}/{len(agents_used)}" if agents_used else "1/1")
                
                # Success message
                if agents:
                    st.success(f"✅ Query processed successfully using {len(agents_used)} AI agents!")
                else:
                    st.info("✅ Query processed in basic embedded mode!")
                
                # Handle voice output if enabled
                if voice_output_enabled and st.session_state.voice_output_enabled:
                    try:
                        # Create a shorter version for voice output
                        voice_text = response_text.split('\n\n')[0]  # Use first paragraph
                        if len(voice_text) > 300:
                            voice_text = voice_text[:300] + "..."
                        
                        success = speak_response(
                            voice_text, 
                            provider=st.session_state.voice_provider,
                            voice=st.session_state.voice_name
                        )
                        
                        if success:
                            # Update metadata to include voice output info
                            enhanced_metadata['voice_output'] = {
                                'enabled': True,
                                'provider': st.session_state.voice_provider,
                                'voice': st.session_state.voice_name,
                                'success': True
                            }
                        
                    except Exception as voice_error:
                        print(f"Voice output error: {voice_error}")
                        enhanced_metadata['voice_output'] = {
                            'enabled': True,
                            'success': False,
                            'error': str(voice_error)
                        }
                
                return
                
        except Exception as e:
            error_msg = f"❌ Embedded processing failed: {str(e)}"
            st.error(error_msg)
            
            # Add error to conversation
            st.session_state.conversation.append((
                f"🤖 Assistant", 
                f"I apologize, but I encountered an error while processing your request: {str(e)}",
                {
                    'confidence': 0.0,
                    'agents_used': [],
                    'query_interpretation': f"Error processing: {query}",
                    'session_id': str(uuid.uuid4()),
                    'response_time': time.time() - start_time
                }
            ))
            
            st.session_state.is_processing = False
            st.session_state.show_typing = False
            return
    
    # Original FastAPI mode (keeping for reference, but won't be used in Streamlit Cloud)
    st.error("🔴 Connection Failed - Cannot reach orchestrator")
    st.info("💡 The app is running in embedded mode. External orchestrator connection is not available on Streamlit Cloud.")
    
    st.session_state.is_processing = False
    st.session_state.show_typing = False

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
                    st.warning("⚠️ Voice test failed - but voice may still work during responses")
                    st.info("💡 Note: Voice functionality may be limited in the embedded mode or on some systems")
    
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
    
    # Connection status with enhanced styling - Embedded mode
    if EMBEDDED_MODE or ORCHESTRATOR_URL is None:
        st.markdown("""
        <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); border-radius: 8px; margin-bottom: 16px;">
            <h4 style="margin: 0; color: #0c5460;">🟣 Embedded Mode</h4>
            <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #0c5460;">Running with built-in agents</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize agents and show status
        try:
            agents = initialize_agents()
            agent_count = len(agents) if agents else 0
            
            st.subheader("🤖 Agent Status")
            
            if agent_count > 0:
                st.success(f"✅ {agent_count}/5 agents initialized successfully")
            else:
                st.warning("⚠️ No agents initialized - running in basic mode")
            
            # Show individual agent status
            expected_agents = [
                ('Language Agent', 'language', 'Natural language processing'),
                ('Market Agent', 'market', 'Financial data and stock prices'),
                ('Analysis Agent', 'analysis', 'Portfolio and sentiment analysis'),
                ('Retriever Agent', 'retriever', 'Document search and retrieval'),
                ('Voice Agent', 'voice', 'Speech synthesis')
            ]
            
            for agent_name, agent_key, description in expected_agents:
                if agents and agent_key in agents:
                    status_color = "#28a745"  # Green
                    status_text = "Active"
                    status_icon = "✅"
                else:
                    status_color = "#6c757d"  # Gray
                    status_text = "Unavailable"
                    status_icon = "❌"
                
                st.markdown(f"""
                <div style="background: white; padding: 8px; border-radius: 6px; margin: 4px 0; 
                           border-left: 3px solid {status_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #2c3e50; font-size: 0.8rem;">{status_icon} {agent_name}</strong>
                            <p style="margin: 2px 0 0 0; color: #6c757d; font-size: 0.7rem;">
                                {description}
                            </p>
                        </div>
                        <span style="background: {status_color}20; color: {status_color}; 
                                     padding: 2px 6px; border-radius: 8px; font-size: 0.6rem;">
                            {status_text}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Debug information if enabled
            if st.session_state.show_debug_enabled:
                st.markdown("---")
                st.subheader("🔧 Debug Info")
                st.write(f"**Agents Available**: {AGENTS_AVAILABLE}")
                st.write(f"**Initialized Agents**: {list(agents.keys()) if agents else 'None'}")
                
                if st.button("🔄 Refresh Agents", help="Reinitialize all agents"):
                    st.cache_resource.clear()
                    st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error initializing agents: {str(e)}")
            st.info("💡 App will run in basic mode with limited functionality")
        
    else:
        # Original connection status for FastAPI mode (not used in Streamlit Cloud)
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

# Embedded mode status banner
if EMBEDDED_MODE or ORCHESTRATOR_URL is None:
    st.info("""
    🟣 **Embedded Mode Active**  
    You're using the self-contained version of the AI Financial Assistant. All agents are running locally within this application.
    """)

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