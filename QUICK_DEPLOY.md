# 🚀 Quick Deployment Guide

## ⚡ Fast Track to Deployment (15 minutes)

### Step 1: Run the Deployment Script
```bash
./deploy.sh
```

### Step 2: Deploy to Netlify (5 minutes)
1. Go to [netlify.com](https://netlify.com) → Sign up/Login
2. Click **"New site from Git"**
3. Connect GitHub → Select this repository
4. **Branch**: `deployment`
5. **Build settings**:
   - Build command: `pip install -r requirements-netlify.txt`
   - Publish directory: `dist`  
   - Functions directory: `netlify/functions`
6. **Environment variables**:
   - `MISTRAL_API_KEY` = `your_mistral_api_key`
7. Click **Deploy**

### Step 3: Deploy to Streamlit Cloud (5 minutes)
1. Go to [share.streamlit.io](https://share.streamlit.io) → Sign up/Login
2. Click **"New app"**
3. Connect GitHub → Select this repository
4. **Branch**: `deployment`
5. **Main file**: `app.py`
6. Click **"Advanced settings"** → **Secrets**:
   ```toml
   MISTRAL_API_KEY = "your_mistral_api_key"
   ORCHESTRATOR_URL = "https://YOUR-NETLIFY-SITE.netlify.app/api"
   ```
7. Click **Deploy**

### Step 4: Update Links (2 minutes)
1. Copy your Streamlit app URL
2. Edit `dist/index.html`:
   ```html
   <a href="https://YOUR-STREAMLIT-APP.streamlit.app">Launch Streamlit App →</a>
   ```
3. Commit and push changes

### Step 5: Test (3 minutes)
1. Visit your Netlify site → Should show API landing page
2. Test API: `curl https://YOUR-NETLIFY-SITE.netlify.app/api/agents/status`
3. Visit your Streamlit app → Should connect to API
4. Ask a test question: "What is the current price of AAPL?"

## 🎯 Required Accounts & API Keys

- **GitHub Account** (free)
- **Netlify Account** (free) 
- **Streamlit Cloud Account** (free)
- **Mistral AI API Key** - Get from [console.mistral.ai](https://console.mistral.ai)

## 🔧 Troubleshooting

**API Connection Issues:**
- Check environment variables are set correctly
- Verify URLs (https vs http)
- Check Netlify function logs

**Build Failures:**
- Check requirements.txt compatibility
- Review build logs in deployment platforms
- Ensure all files are committed to deployment branch

**CORS Errors:**
- Netlify functions already include CORS headers
- Check browser developer console for specific errors

## ✅ Success Indicators

- ✅ Netlify site shows API landing page
- ✅ API status endpoint returns agent list  
- ✅ Streamlit app loads without errors
- ✅ Streamlit app shows "🟢 Connected to API"
- ✅ Test queries return AI responses

## 📞 Need Help?

Check the full tutorial in `DEPLOYMENT_TUTORIAL.md` for detailed explanations and advanced configurations.

Your AI Financial Assistant is now live and accessible worldwide! 🌍✨ 