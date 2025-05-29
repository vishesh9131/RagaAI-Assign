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

# Configuration - use environment variables for deployment
ORCHESTRATOR_URL = os.environ.get('ORCHESTRATOR_URL', 'http://localhost:8011')
VOICE_AGENT_URL = os.environ.get('VOICE_AGENT_URL', 'http://localhost:8000')

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
    
    .deployment-info {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
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
    
    .input-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-top: 1rem;
        border: 1px solid #e9ecef;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'usage_stats' not in st.session_state:
    st.session_state.usage_stats = {'queries_today': 0, 'total_queries': 0, 'avg_response_time': 0}

# Header with modern design and deployment info
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">🚀 AI Financial Assistant</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Powered by Mistral AI • Multi-Agent Intelligence • Cloud Deployment</p>
</div>
""", unsafe_allow_html=True)

# Deployment status info
st.markdown(f"""
<div class="deployment-info">
    <h4 style="margin: 0 0 8px 0; color: #155724;">🌐 Deployment Status</h4>
    <p style="margin: 0; color: #155724; font-size: 0.9rem;">
        <strong>API Endpoint:</strong> {ORCHESTRATOR_URL}<br>
        <strong>Deployment:</strong> Streamlit Cloud + Netlify Serverless
    </p>
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

def display_conversation():
    """Display conversation with modern chat bubbles."""
    chat_container = st.container()
    
    with chat_container:
        # Display conversation messages
        for entry in st.session_state.conversation:
            if len(entry) == 2:
                speaker, text = entry
                metadata = {}
            else:
                speaker, text, metadata = entry
            
            timestamp = datetime.now().strftime("%H:%M")
            
            if speaker.startswith("👤"):
                # User message
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
                
                # Assistant message
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
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def send_query_to_api(query: str):
    """Send query to the orchestrator API."""
    st.session_state.is_processing = True
    st.session_state.usage_stats['queries_today'] += 1
    st.session_state.usage_stats['total_queries'] += 1
    
    start_time = time.time()
    
    try:
        # Add user message to conversation
        st.session_state.conversation.append(("👤 User", query))
        
        # Send request to API
        payload = {
            "query": query,
            "voice_mode": False,
            "include_debug_info": False
        }
        
        with st.spinner("🤖 AI is processing your query..."):
            response = requests.post(
                f"{ORCHESTRATOR_URL}/intelligent/query",
                json=payload,
                timeout=30
            )
        
        response_time = time.time() - start_time
        st.session_state.usage_stats['avg_response_time'] = (
            st.session_state.usage_stats['avg_response_time'] + response_time
        ) / 2
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response_text', 'No response received')
            confidence = data.get('confidence', 0.0)
            
            # Add response to conversation
            metadata = {
                'confidence': confidence,
                'response_time': response_time,
                'session_id': data.get('session_id'),
                'agents_used': data.get('agents_used', [])
            }
            
            st.session_state.conversation.append((
                "🤖 Assistant", 
                response_text,
                metadata
            ))
            
            # Display success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⚡ Response Time", f"{response_time:.1f}s")
            with col2:
                st.metric("🎯 Confidence", f"{confidence:.1%}")
            with col3:
                agents_count = len(data.get('agents_used', []))
                st.metric("🤖 Agents Used", agents_count)
                
        else:
            st.error(f"API Error: {response.status_code}")
            error_message = f"Sorry, I encountered an error (Status: {response.status_code}). Please try again."
            st.session_state.conversation.append(("🤖 Assistant", error_message, {'confidence': 0.0}))
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
        st.session_state.conversation.append(("🤖 Assistant", "Request timed out. Please try again.", {'confidence': 0.0}))
    except requests.exceptions.ConnectionError:
        st.error(f"🚫 Cannot connect to API at {ORCHESTRATOR_URL}")
        st.session_state.conversation.append(("🤖 Assistant", f"Cannot connect to the AI service. Please check if the API is running.", {'confidence': 0.0}))
    except Exception as e:
        st.error(f"💥 Unexpected error: {e}")
        st.session_state.conversation.append(("🤖 Assistant", f"An unexpected error occurred: {str(e)}", {'confidence': 0.0}))
    finally:
        st.session_state.is_processing = False

# Sidebar
with st.sidebar:
    st.subheader("⚙️ Settings")
    
    # API Status Check
    st.markdown("#### 🔗 API Connection")
    try:
        with st.spinner("Checking API..."):
            status_response = requests.get(f"{ORCHESTRATOR_URL}/agents/status", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            st.success(f"🟢 Connected to API")
            st.info(f"Agents available: {len(status_data.get('available_agents', []))}")
        else:
            st.error(f"🔴 API Error: {status_response.status_code}")
    except Exception as e:
        st.error(f"🔴 Cannot reach API: {str(e)}")
    
    # Usage Statistics
    st.subheader("📊 Usage Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📈 Today", st.session_state.usage_stats['queries_today'])
    with col2:
        st.metric("📊 Total", st.session_state.usage_stats['total_queries'])
    
    if st.session_state.usage_stats['avg_response_time'] > 0:
        st.metric("⚡ Avg Response", f"{st.session_state.usage_stats['avg_response_time']:.1f}s")
    
    # Quick Actions
    st.subheader("🚀 Quick Queries")
    quick_queries = [
        "What's the current price of AAPL stock?",
        "Analyze Tesla's performance this month",
        "What are the latest market trends?",
        "Give me investment advice for tech stocks"
    ]
    
    for query in quick_queries:
        if st.button(f"💡 {query[:30]}...", key=f"quick_{hash(query)}", use_container_width=True):
            st.session_state.example_query = query
            st.rerun()

# Main content
display_conversation()

# Input area
st.markdown('<div class="input-container">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 💭 Ask Your Financial Question")
    
    # Get example query if set
    default_query = st.session_state.get('example_query', '')
    if 'example_query' in st.session_state:
        del st.session_state.example_query
    
    user_input = st.text_area(
        "Your financial query",
        value=default_query,
        height=120,
        placeholder="💡 Examples:\n• What's the current price of AAPL?\n• Analyze Tesla's performance vs competitors\n• Should I invest in renewable energy stocks?",
        help="Ask about stocks, market analysis, portfolio management, or any financial topic",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 🎮 Actions")
    
    button_disabled = st.session_state.is_processing
    button_label = "⏳ Processing..." if button_disabled else "🚀 Ask AI"
    
    if st.button(button_label, use_container_width=True, type="primary", disabled=button_disabled):
        if user_input and user_input.strip():
            send_query_to_api(user_input.strip())
            st.rerun()
        else:
            st.warning("⚠️ Please enter a query.")
    
    # Control buttons
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear", use_container_width=True, disabled=st.session_state.is_processing):
            st.session_state.conversation = []
            st.session_state.usage_stats = {'queries_today': 0, 'total_queries': 0, 'avg_response_time': 0}
            st.rerun()
    
    with col_b:
        if st.button("📥 Export", use_container_width=True):
            export_data = {
                "conversation": st.session_state.conversation,
                "usage_stats": st.session_state.usage_stats,
                "export_timestamp": datetime.now().isoformat()
            }
            conversation_json = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                "💾 Download",
                conversation_json,
                f"ai_financial_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("### 🌟 AI Financial Assistant - Cloud Deployment")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🚀 Deployment Info**
    - Streamlit Cloud hosting
    - Netlify serverless API
    - Real-time processing
    """)

with col2:
    st.markdown("""
    **🤖 AI Capabilities**
    - Multi-agent intelligence
    - Financial data analysis  
    - Natural language processing
    """)

with col3:
    st.markdown("""
    **📊 Features**
    - Real-time responses
    - Usage analytics
    - Export conversations
    """)

st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           border-radius: 15px; margin-top: 20px; color: white;">
    <h3 style="margin: 0;">🚀 AI Financial Assistant - Cloud Edition</h3>
    <p style="margin: 8px 0 0 0; opacity: 0.9;">
        Powered by Mistral AI • Deployed on Streamlit Cloud & Netlify • Enterprise Ready
    </p>
</div>
""", unsafe_allow_html=True) 