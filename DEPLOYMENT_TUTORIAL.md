# 🚀 Complete Deployment Tutorial: AI Financial Assistant

## Overview
This tutorial will guide you through deploying your AI Financial Assistant with:
- **Streamlit App** → Streamlit Cloud (Free)
- **Orchestrator API** → Netlify (Free tier)

## 📋 Prerequisites

1. **GitHub Account** (to store your code)
2. **Streamlit Cloud Account** (free at share.streamlit.io)
3. **Netlify Account** (free at netlify.com)
4. **API Keys** (Mistral AI, etc.)

---

## Part 1: 🎯 Prepare Your Code for Deployment

### Step 1: Create Deployment Branch
```bash
# Create a new branch for deployment
git checkout -b deployment

# Make sure all files are committed
git add .
git commit -m "Prepare for deployment"
```

### Step 2: Modify Orchestrator for Netlify Deployment

We need to create a serverless-compatible version of the orchestrator for Netlify.

---

## Part 2: 🌐 Deploy Orchestrator to Netlify

### Step 1: Create Netlify Functions

Create the necessary files for Netlify Functions:

#### A. Create `netlify.toml`
```toml
[build]
  command = "pip install -r requirements-netlify.txt"
  functions = "netlify/functions"
  publish = "dist"

[build.environment]
  PYTHON_VERSION = "3.11"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### B. Create Netlify Functions Directory Structure
```bash
mkdir -p netlify/functions
```

### Step 2: Create Serverless Orchestrator Functions

#### A. Create `netlify/functions/orchestrator.py`
```python
import json
import os
from datetime import datetime
import logging

# Import your orchestrator core logic
try:
    from orchestrator.core.agent_orchestrator import AgentOrchestrator
    from agents.core.market_agent import MarketAgent
    from agents.core.analysis_agent import AnalysisAgent
    # Add other agent imports
except ImportError:
    # Fallback for deployment
    pass

def handler(event, context):
    """
    Netlify Functions handler for orchestrator API
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        # Handle different API endpoints
        if path.endswith('/agents/status'):
            return handle_agents_status()
        elif path.endswith('/intelligent/query'):
            body = json.loads(event.get('body', '{}'))
            return handle_intelligent_query(body)
        elif path.endswith('/intelligent/voice'):
            # Handle voice requests
            return handle_voice_query(event)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def handle_agents_status():
    """Handle agents status endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        },
        'body': json.dumps({
            'available_agents': [
                {'name': 'Market Agent', 'description': 'Stock prices, company info', 'status': 'active'},
                {'name': 'Analysis Agent', 'description': 'Portfolio analysis, trends', 'status': 'active'},
                {'name': 'Language Agent', 'description': 'Text processing with Mistral AI', 'status': 'active'},
                {'name': 'Retriever Agent', 'description': 'Document search', 'status': 'active'},
                {'name': 'Scraping Agent', 'description': 'Web content extraction', 'status': 'active'},
                {'name': 'Voice Agent', 'description': 'Speech processing', 'status': 'active'}
            ],
            'orchestrator_version': '3.0.0',
            'language_model': 'Mistral AI',
            'active_sessions': 0
        })
    }

def handle_intelligent_query(body):
    """Handle intelligent query processing"""
    query = body.get('query', '')
    voice_mode = body.get('voice_mode', False)
    
    # Initialize orchestrator with environment variables
    mistral_api_key = os.environ.get('MISTRAL_API_KEY')
    
    try:
        # Process the query using your agents
        # This is simplified - you'll need to adapt your actual orchestrator logic
        
        response = {
            'response_text': f"I received your query: {query}. This is a demo response from the deployed orchestrator.",
            'confidence': 0.85,
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'agents_used': [
                {
                    'agent_name': 'Language Agent',
                    'status': 'completed',
                    'description': 'Processed natural language query'
                }
            ],
            'query_interpretation': 'Successfully parsed financial query',
            'routing_info': {'primary_agent': 'Language Agent'},
            'wav_audio_base64': None if not voice_mode else None
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Query processing failed: {str(e)}'})
        }

def handle_voice_query(event):
    """Handle voice query processing"""
    # Implement voice processing logic
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'response_text': 'Voice processing is not yet implemented in serverless mode',
            'confidence': 0.5
        })
    }
```

### Step 3: Create Requirements for Netlify
```bash
# Create requirements-netlify.txt (lighter version for serverless)
cat > requirements-netlify.txt << EOF
mistralai>=0.0.8
requests>=2.31.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
fastapi>=0.104.0
pydantic>=2.0.0
# Removed heavy dependencies for serverless deployment
EOF
```

### Step 4: Create Static Website Files
```bash
mkdir -p dist
```

Create `dist/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Financial Assistant API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .api-info { background: #f5f5f5; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🤖 AI Financial Assistant API</h1>
    <div class="api-info">
        <h2>Available Endpoints:</h2>
        <ul>
            <li><code>GET /api/agents/status</code> - Get agent status</li>
            <li><code>POST /api/intelligent/query</code> - Process queries</li>
            <li><code>POST /api/intelligent/voice</code> - Process voice</li>
        </ul>
        <p>This API powers the AI Financial Assistant Streamlit app.</p>
        <p><strong>Streamlit App:</strong> <a href="https://your-app.streamlit.app">View App</a></p>
    </div>
</body>
</html>
```

### Step 5: Deploy to Netlify

#### Option A: GitHub Integration (Recommended)
1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Netlify deployment files"
   git push origin deployment
   ```

2. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository
   - Select the `deployment` branch
   - Build settings:
     - Build command: `pip install -r requirements-netlify.txt`
     - Publish directory: `dist`
     - Functions directory: `netlify/functions`

3. **Add Environment Variables:**
   - In Netlify dashboard → Site Settings → Environment Variables
   - Add: `MISTRAL_API_KEY = your_mistral_api_key`

#### Option B: Direct Deploy
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod --dir=dist --functions=netlify/functions
```

---

## Part 3: 📱 Deploy Streamlit App to Streamlit Cloud

### Step 1: Prepare Streamlit App

#### A. Update Orchestrator URL
Edit `orchestrator/orchestrator_streamlit.py` to use your Netlify URL:

```python
# Replace localhost URL with your Netlify URL
ORCHESTRATOR_URL = "https://your-netlify-site.netlify.app/api"
```

#### B. Create Streamlit Configuration
Create `.streamlit/config.toml`:
```toml
[server]
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

#### C. Update `requirements.txt` for Streamlit Cloud
Make sure your `requirements.txt` works for Streamlit Cloud:
```txt
streamlit>=1.28.0
requests>=2.31.0
mistralai>=0.0.8
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
Pillow>=10.0.0
# openai-whisper==20231117  # Commented out - causes build issues
pydantic>=2.0.0
fastapi>=0.104.0
```

### Step 2: Deploy to Streamlit Cloud

1. **Push Changes to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin deployment
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select branch: `deployment`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Add Secrets:**
   - In your Streamlit app → Settings → Secrets
   - Add your secrets in TOML format:
   ```toml
   MISTRAL_API_KEY = "your_mistral_api_key"
   ORCHESTRATOR_URL = "https://your-netlify-site.netlify.app/api"
   ```

---

## Part 4: 🔧 Configuration & Testing

### Step 1: Update CORS Settings

Add CORS headers to your Netlify functions to allow Streamlit app access:

```python
# In netlify/functions/orchestrator.py, ensure all responses include:
'headers': {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE'
}
```

### Step 2: Test Your Deployment

1. **Test Netlify API:**
   ```bash
   curl https://your-netlify-site.netlify.app/api/agents/status
   ```

2. **Test Streamlit App:**
   - Visit your Streamlit app URL
   - Try asking a financial question
   - Check if the API calls work

### Step 3: Monitor and Debug

#### Netlify Logs:
- Netlify Dashboard → Functions → View logs

#### Streamlit Logs:
- Streamlit Cloud Dashboard → Your app → Manage → Logs

---

## Part 5: 🎯 Advanced Configuration

### Custom Domain (Optional)
1. **For Netlify:** Add custom domain in Netlify settings
2. **For Streamlit:** Upgrade to Streamlit for Teams

### Environment Management
```python
import os

# In your deployed code, always use environment variables
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
ORCHESTRATOR_URL = os.environ.get('ORCHESTRATOR_URL', 'http://localhost:8011')
```

### Performance Optimization
- Use caching in Streamlit: `@st.cache_data`
- Minimize API calls
- Use connection pooling for external APIs

---

## 🚀 Quick Deployment Checklist

- [ ] Create deployment branch
- [ ] Set up Netlify functions
- [ ] Create netlify.toml configuration
- [ ] Update requirements for serverless
- [ ] Push code to GitHub
- [ ] Deploy to Netlify with environment variables
- [ ] Update Streamlit app to use Netlify URL
- [ ] Deploy to Streamlit Cloud
- [ ] Add secrets to Streamlit Cloud
- [ ] Test both deployments
- [ ] Configure CORS if needed

---

## 🔍 Troubleshooting

### Common Issues:

1. **CORS Errors:**
   - Add proper CORS headers to Netlify functions
   - Update Access-Control-Allow-Origin settings

2. **API Connection Issues:**
   - Check environment variables in both platforms
   - Verify URLs are correct (https vs http)

3. **Build Failures:**
   - Check requirements.txt compatibility
   - Remove problematic dependencies

4. **Function Timeout:**
   - Netlify functions have 10-second timeout on free tier
   - Optimize your code for faster execution

---

## 📞 Support

If you encounter issues:
1. Check the deployment logs
2. Verify environment variables
3. Test API endpoints directly
4. Check CORS configuration

Your AI Financial Assistant should now be fully deployed and accessible worldwide! 🎉 