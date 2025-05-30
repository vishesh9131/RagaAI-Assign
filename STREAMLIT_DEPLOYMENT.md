# Streamlit Cloud Deployment Guide

## 🚀 Quick Deploy

This AI Financial Assistant is ready for **one-click deployment** on Streamlit Cloud!

### Prerequisites
- GitHub repository (this repo)
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Deployment Steps

1. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)
2. **Connect GitHub**: Link your GitHub account
3. **Deploy App**:
   - Repository: `your-username/RagaAI-Assign`
   - Branch: `main` 
   - Main file path: `app.py`
4. **Click Deploy** 🚀

### Configuration Files

The following files are optimized for Streamlit Cloud deployment:

- ✅ **`app.py`** - Main Streamlit application (standalone, no complex imports)
- ✅ **`requirements.txt`** - Minimal dependencies compatible with Python 3.11-3.13
- ✅ **`.streamlit/config.toml`** - Streamlit configuration
- ✅ **`.streamlit/secrets.toml`** - API configuration 
- ✅ **`.python-version`** - Python 3.11 (compatible)
- ✅ **`runtime.txt`** - Python runtime specification
- ✅ **`packages.txt`** - No system packages needed

### Features

- 🤖 **6 AI Agents**: Market, Analysis, Language, Retriever, Scraping, Voice
- 💬 **Chat Interface**: Modern conversational UI
- 🎤 **Voice Input**: Upload audio files or record directly
- 🔊 **Voice Output**: AI-generated audio responses
- 📊 **Real-time Data**: Live financial market information
- 🌐 **API Integration**: Connects to Netlify-deployed backend

### Backend API

The app connects to: `https://ai-financial-assistant-multi-agent.netlify.app`

- ✅ Deployed on Netlify Functions
- ✅ Multi-agent orchestration
- ✅ Real-time financial data
- ✅ Voice processing capabilities

### Troubleshooting

If deployment fails:

1. **Check Python version**: App supports Python 3.11+
2. **Verify dependencies**: All packages in requirements.txt are compatible
3. **Test locally**: Run `streamlit run app.py` locally first
4. **Check logs**: View Streamlit Cloud deployment logs for specific errors

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py

# App will be available at http://localhost:8501
```

### Support

For issues:
1. Check Streamlit Cloud deployment logs
2. Verify API connectivity
3. Test with simple queries first

---

**🎉 Your AI Financial Assistant is ready for the cloud!** 