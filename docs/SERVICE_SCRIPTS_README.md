# 🚀 AI Financial Assistant - Service Management Scripts

This directory contains convenient shell scripts to manage all services required for the AI Financial Assistant with voice functionality.

## 📋 Available Scripts

### 🟢 `start_services.sh`
**Starts all required services for the AI Financial Assistant**

- 🎤 **Voice Agent** (port 8000) - Speech-to-text and text-to-speech
- 🤖 **Orchestrator FastAPI** (port 8011) - Main API with 6 AI agents
- 🖥️ **Streamlit App** (port 8501) - User interface with voice auto-submit

**Features:**
- ✅ Automatic virtual environment activation
- ✅ Port conflict detection and cleanup
- ✅ Service health checks and readiness verification
- ✅ Comprehensive logging to `logs/` directory
- ✅ Process ID tracking for clean shutdowns
- ✅ API endpoint testing

### 🔴 `stop_services.sh`
**Gracefully stops all running services**

- 🛑 Graceful shutdown with SIGTERM first
- 🔨 Force kill if services don't respond
- 🧹 Cleanup of PID files and remaining processes
- 📊 Final verification of port status

### 🔍 `check_status.sh`
**Comprehensive status check of all services**

- 📊 Service status on each port
- 🔧 Process information from PID files
- 🧪 API health checks with response validation
- 📂 Log file information and sizes
- 🌐 Quick access URLs

## 🎯 Quick Start

### Start Everything
```bash
./start_services.sh
```

### Check Status
```bash
./check_status.sh
```

### Stop Everything
```bash
./stop_services.sh
```

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 AI Financial Assistant                      │
├─────────────────────────────────────────────────────────────┤
│  🖥️  Streamlit App (Port 8501)                             │
│  ├── 🎤 Voice Input with Auto-Submit                       │
│  ├── 💬 Chat Interface                                     │
│  └── 📊 Real-time Agent Status                            │
├─────────────────────────────────────────────────────────────┤
│  🤖 Orchestrator FastAPI (Port 8011)                       │
│  ├── 📈 Market Agent (Stock prices, company info)         │
│  ├── 📊 Analysis Agent (Portfolio analysis, trends)       │
│  ├── 🧠 Language Agent (Text summarization, Mistral AI)    │
│  ├── 🔍 Retriever Agent (Document search)                 │
│  ├── 🌐 Scraping Agent (Web content extraction)           │
│  └── 🎤 Voice Agent Integration                           │
├─────────────────────────────────────────────────────────────┤
│  🎤 Voice Agent (Port 8000)                               │
│  ├── 🗣️ Speech-to-Text (Multiple providers)               │
│  ├── 🔊 Text-to-Speech (macOS Say, OpenAI, ElevenLabs)    │
│  └── 🎙️ Real-time Voice Processing                        │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Virtual Environment
- Scripts automatically activate `market_env` if not already active
- Ensure your virtual environment has all required dependencies

### Ports Used
- **8000**: Voice Agent API
- **8011**: Orchestrator FastAPI (Main API)
- **8501**: Streamlit App (User Interface)

### Logs Directory
All services log to the `logs/` directory:
- `logs/voice_agent.log` - Voice processing logs
- `logs/orchestrator.log` - Main API and agent logs  
- `logs/streamlit.log` - User interface logs
- `logs/*.pid` - Process ID files for clean shutdowns

## 🎮 Usage Examples

### Start and Monitor
```bash
# Start all services
./start_services.sh

# Check status in another terminal
./check_status.sh

# View live logs
tail -f logs/orchestrator.log
tail -f logs/streamlit.log
tail -f logs/voice_agent.log
```

### Development Workflow
```bash
# Check what's running
./check_status.sh

# Stop everything for updates
./stop_services.sh

# Make your changes...

# Start everything again
./start_services.sh
```

### Troubleshooting
```bash
# Check status and logs
./check_status.sh

# Stop all services
./stop_services.sh

# Clear logs (optional)
rm -f logs/*.log

# Start fresh
./start_services.sh
```

## 🌐 Access URLs

Once services are running:

- **🖥️ Streamlit App**: http://localhost:8501
  - Main user interface with voice features
  - Real-time chat with AI agents
  - Voice auto-submit functionality

- **🤖 Orchestrator API**: http://localhost:8011
  - RESTful API for all agent interactions
  - Agent status and health endpoints

- **📚 API Documentation**: http://localhost:8011/docs
  - Interactive Swagger/OpenAPI documentation
  - Test API endpoints directly

- **🎤 Voice Agent**: http://localhost:8000
  - Voice processing API
  - Speech-to-text and text-to-speech endpoints

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Stop existing services
./stop_services.sh

# Check port status
lsof -i :8000,8011,8501

# Force kill if needed
kill -9 $(lsof -ti :8011)

# Start fresh
./start_services.sh
```

### Services Not Starting
```bash
# Check logs for errors
tail -n 50 logs/orchestrator.log
tail -n 50 logs/voice_agent.log

# Verify virtual environment
which python
pip list | grep -E "(streamlit|fastapi|uvicorn)"

# Check system resources
top
df -h
```

### Voice Features Not Working
```bash
# Test Voice Agent directly
curl http://localhost:8000/health

# Check macOS permissions for microphone
# System Preferences > Security & Privacy > Privacy > Microphone

# Verify TTS providers
python voice_cli.py speak "test message"
```

## 🔄 Service Dependencies

**Startup Order:**
1. 🎤 Voice Agent (8000) - Independent service
2. 🤖 Orchestrator FastAPI (8011) - Depends on agents
3. 🖥️ Streamlit App (8501) - Depends on Orchestrator

**Shutdown Order:**
1. 🖥️ Streamlit App - Frontend interface
2. 🤖 Orchestrator FastAPI - Main API
3. 🎤 Voice Agent - Background service

## 📝 Script Features

### Error Handling
- ✅ Exit on any error with clear messages
- ✅ Graceful fallbacks for missing services
- ✅ Comprehensive logging and debugging info

### Process Management  
- ✅ PID file tracking for clean shutdowns
- ✅ Port conflict detection and resolution
- ✅ Service health verification

### User Experience
- ✅ Colored output for easy reading
- ✅ Progress indicators and status updates
- ✅ Clear success/error messages
- ✅ Helpful next steps and URLs

---

**Ready to start your AI Financial Assistant? Run `./start_services.sh` and visit http://localhost:8501!** 🚀 