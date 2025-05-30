#!/usr/bin/env python3
"""
Main entry point for the AI Financial Assistant Streamlit application.
This file serves as the main entry point for Streamlit Cloud deployment.
"""

import os
import streamlit as st

# Set deployment mode - will use deployed API by default
os.environ["DEPLOYMENT_MODE"] = "production"
os.environ["ORCHESTRATOR_URL"] = "https://ai-financial-assistant-multi-agent.netlify.app/app/"

# Import and run the main orchestrator streamlit app
# This import will execute the orchestrator_streamlit.py file which contains all the app logic
from orchestrator import orchestrator_streamlit 