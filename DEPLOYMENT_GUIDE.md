# 🚀 AI Financial Assistant Deployment Guide

This guide will help you deploy your AI Financial Assistant on two platforms:
- **Netlify**: API backend (orchestrator + agents)
- **Streamlit Cloud**: Frontend web app

## 📋 Prerequisites

1. GitHub account
2. Netlify account (free)
3. Streamlit Cloud account (free)
4. Mistral API key

## 🌐 Part 1: Deploy API to Netlify

### Step 1: Prepare Your Repository

1. Copy these files to your repo root:
   ```
   netlify_deployment/
   ├── netlify.toml
   ├── requirements.txt
   ├── functions/
   │   └── orchestrator.py
   └── dist/
       └── index.html
   ```

2. Copy your entire `orchestrator/` and `agents/` folders to the repo root

### Step 2: Install Mangum for Netlify

Add `mangum` to your requirements:

```bash
echo "mangum==0.17.0" >> netlify_deployment/requirements.txt
```

### Step 3: Deploy to Netlify

1. Go to [Netlify](https://netlify.com)
2. Click "New site from Git"
3. Connect your GitHub repo
4. Configure build settings:
   - **Build command**: `echo 'Building API...'`
   - **Publish directory**: `netlify_deployment/dist`
   - **Functions directory**: `netlify_deployment/functions`

5. Add environment variables in Netlify dashboard:
   ```
   MISTRAL_API_KEY=your_mistral_api_key_here
   PYTHON_VERSION=3.11
   ```

6. Deploy! Your API will be available at: `https://your-site.netlify.app/api`

### Step 4: Test Your API

Visit `https://your-site.netlify.app/api/agents/status` to verify it's working.

## 📱 Part 2: Deploy Frontend to Streamlit Cloud

### Step 1: Prepare Streamlit Files

1. Copy these files to your repo:
   ```
   streamlit_deployment/
   ├── requirements.txt
   └── .streamlit/
       ├── config.toml
       └── secrets.toml
   ```

2. Copy `streamlit_app.py` to your repo root

### Step 2: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repo
4. Configure:
   - **Main file path**: `streamlit_app.py`
   - **Python version**: 3.11

5. Add secrets in Streamlit Cloud dashboard:
   ```toml
   ORCHESTRATOR_URL = "https://your-site.netlify.app/api"
   ```

6. Deploy! Your app will be available at: `https://your-app.streamlit.app`

## ✅ Testing the Complete Setup

1. **Test API**: Visit `https://your-site.netlify.app`
2. **Test App**: Visit `https://your-app.streamlit.app`
3. **Test Integration**: Ask a question in the Streamlit app

## 🔧 Troubleshooting

### API Issues
- Check Netlify function logs
- Verify environment variables
- Test individual endpoints

### Streamlit Issues  
- Check app logs in Streamlit Cloud
- Verify secrets configuration
- Test API connectivity

### Common Fixes
- Ensure all dependencies are in requirements.txt
- Check API URL format (no trailing slash)
- Verify CORS headers are set

## 📊 Architecture Overview

```
User Browser
    ↓
Streamlit Cloud (Frontend)
    ↓ HTTP Requests
Netlify Functions (API)
    ↓ Processes with
AI Agents (Market, Analysis, etc.)
    ↓ Returns
JSON Response to Streamlit
```

## 🎯 Benefits of This Setup

✅ **Scalable**: Both platforms auto-scale  
✅ **Cost-effective**: Free tiers available  
✅ **Fast**: Edge deployment on both platforms  
✅ **Reliable**: Built-in monitoring and error handling  
✅ **Easy to maintain**: Git-based deployments  

## 📞 Support

If you encounter issues:
1. Check the deployment logs
2. Verify all environment variables
3. Test API endpoints individually
4. Ensure requirements.txt is complete

Happy deploying! 🚀 