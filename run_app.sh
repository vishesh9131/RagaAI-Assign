#!/bin/bash

# 🚀 AI Financial Assistant - Clean Startup Script
# This script ensures a clean environment and starts the Streamlit app

echo "🚀 Starting AI Financial Assistant with Deployed API..."
echo "================================================="

# Set environment variables for production mode
export DEPLOYMENT_MODE="production"
export ORCHESTRATOR_URL="https://orch.netlify.app/api"

# Disable PyTorch warnings that might interfere
export PYTHONWARNINGS="ignore:UserWarning"

# Clear any existing Streamlit cache
echo "🧹 Clearing Streamlit cache..."
rm -rf ~/.streamlit

# Show configuration
echo "📍 Configuration:"
echo "   Mode: $DEPLOYMENT_MODE"
echo "   API URL: $ORCHESTRATOR_URL"
echo "   App Port: 8501"
echo ""

# Test API connectivity first
echo "🔍 Testing API connectivity..."
if curl -s --max-time 5 "$ORCHESTRATOR_URL/agents/status" > /dev/null; then
    echo "✅ API is reachable at $ORCHESTRATOR_URL"
else
    echo "⚠️  Warning: API might not be reachable, but app will still work"
fi

echo ""
echo "🌐 Starting Streamlit app..."
echo "   Local URL: http://localhost:8501"
echo "   Network URL: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "🎯 Integration Status: DEPLOYED API"
echo "📱 Ready to use! Ask financial questions and get AI-powered insights!"
echo "================================================="

# Start Streamlit with clean environment
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 