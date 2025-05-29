#!/bin/bash

# 🚀 AI Financial Assistant - Deployment Script
# This script helps you deploy to both Streamlit Cloud and Netlify

set -e

echo "🚀 AI Financial Assistant - Deployment Script"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create deployment branch if it doesn't exist
echo "📦 Preparing deployment branch..."
git checkout -b deployment 2>/dev/null || git checkout deployment

# Stage all changes
echo "📝 Staging changes..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "✅ No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Prepare for deployment - $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Push to GitHub
echo "🌐 Pushing to GitHub..."
git push origin deployment

echo ""
echo "✅ Deployment files are ready!"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. 🌐 Deploy to Netlify:"
echo "   • Go to https://netlify.com"
echo "   • Click 'New site from Git'"
echo "   • Select this GitHub repository"
echo "   • Choose 'deployment' branch"
echo "   • Build settings:"
echo "     - Build command: pip install -r requirements-netlify.txt"
echo "     - Publish directory: dist"
echo "     - Functions directory: netlify/functions"
echo "   • Add environment variable: MISTRAL_API_KEY"
echo ""
echo "2. 📱 Deploy to Streamlit Cloud:"
echo "   • Go to https://share.streamlit.io"
echo "   • Click 'New app'"
echo "   • Select this GitHub repository"
echo "   • Choose 'deployment' branch"
echo "   • Main file path: app.py"
echo "   • Add secrets in app settings:"
echo "     - MISTRAL_API_KEY = your_key"
echo "     - ORCHESTRATOR_URL = your_netlify_url/api"
echo ""
echo "3. 🔧 Configuration:"
echo "   • Update dist/index.html with your Streamlit app URL"
echo "   • Test both deployments"
echo "   • Monitor logs for any issues"
echo ""
echo "🎉 Happy deploying!" 