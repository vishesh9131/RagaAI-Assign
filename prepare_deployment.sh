#!/bin/bash

echo "🚀 Preparing AI Financial Assistant for Deployment"
echo "=================================================="

# Create deployment directories
mkdir -p netlify_deployment/functions
mkdir -p netlify_deployment/dist
mkdir -p streamlit_deployment/.streamlit

# Copy files for Netlify deployment
echo "📦 Preparing Netlify deployment..."
cp -r orchestrator netlify_deployment/
cp -r agents netlify_deployment/

# Copy files for Streamlit deployment  
echo "📱 Preparing Streamlit deployment..."
cp streamlit_app.py streamlit_deployment/

# Set permissions
chmod +x netlify_deployment/functions/orchestrator.py

echo "✅ Deployment files prepared!"
echo ""
echo "🌐 Next Steps:"
echo "1. Push code to GitHub"
echo "2. Deploy to Netlify from netlify_deployment/"
echo "3. Deploy to Streamlit Cloud using streamlit_deployment/"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions" 