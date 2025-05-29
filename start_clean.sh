#!/bin/bash

# 🚀 Clean Startup Script for AI Financial Assistant
# This script starts the app with proper environment isolation

echo "🚀 Starting AI Financial Assistant (Clean Mode)..."
echo "=================================================="

# Set production environment
export DEPLOYMENT_MODE="production"
export ORCHESTRATOR_URL="https://orch.netlify.app/api"

# Disable problematic PyTorch features
export TORCH_LOGS="-all"
export OMP_NUM_THREADS=1
export PYTHONPATH=""

# Disable Streamlit watchers that cause PyTorch conflicts
export STREAMLIT_SERVER_FILE_WATCHER_TYPE="none"
export STREAMLIT_SERVER_RUN_ON_SAVE=false

# Clear Python cache to avoid conflicts
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Environment configured"
echo "📍 API URL: $ORCHESTRATOR_URL"
echo "🎯 Mode: $DEPLOYMENT_MODE"
echo ""

# Start Streamlit with minimal configuration
echo "🌐 Starting Streamlit..."
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --logger.level error \
    --server.fileWatcherType none \
    --server.runOnSave false \
    --browser.gatherUsageStats false 