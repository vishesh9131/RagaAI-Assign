# 📁 AI Financial Assistant - Project Structure

This document provides a comprehensive overview of the modular project structure after reorganization.

## 🏗️ Directory Structure

```
RagaAI-Assign/
├── 🤖 agents/                          # AI Agent Implementations
│   ├── core/                           # Core agent logic
│   │   ├── __init__.py                 # Package initialization
│   │   ├── analysis_agent.py           # Financial analysis & insights
│   │   ├── language_agent.py           # NLP & text generation (Mistral AI)
│   │   ├── market_agent.py             # Financial market data retrieval
│   │   ├── retriever_agent.py          # Vector-based document retrieval
│   │   ├── scraping_agent.py           # Web scraping & content extraction
│   │   └── voice_agent.py              # Speech-to-text & text-to-speech
│   ├── interfaces/                     # Agent interface definitions
│   └── __init__.py                     # Main package exports
│
├── 📊 data_ingestion/                  # Data Input/Output Interfaces
│   ├── api/                            # RESTful API endpoints
│   │   ├── __init__.py
│   │   └── analysis_fastapi.py         # Analysis agent API
│   ├── cli/                            # Command-line interfaces
│   │   ├── __init__.py
│   │   ├── analysis_cli.py             # Analysis CLI
│   │   ├── cli_interface.py            # Main CLI interface
│   │   ├── language_cli.py             # Language processing CLI
│   │   ├── retriever_cli.py            # Document retrieval CLI
│   │   ├── scraping_cli.py             # Web scraping CLI
│   │   └── voice_cli.py                # Voice interaction CLI
│   └── __init__.py
│
├── 🎯 orchestrator/                    # Agent Coordination & Management
│   ├── core/                           # Main orchestration logic
│   ├── faiss/                          # Vector database management
│   │   ├── api_faiss_store/            # API FAISS indices
│   │   ├── cli_faiss_store/            # CLI FAISS indices
│   │   └── orchestrator_faiss/         # Orchestrator FAISS indices
│   ├── __init__.py
│   ├── debug_orchestrator.py           # Debug utilities
│   ├── orchestrator_fastapi.py         # FastAPI orchestrator
│   ├── orchestrator_streamlit.py       # Streamlit orchestrator
│   └── *.log                           # Orchestrator logs
│
├── 🖥️ streamlit_app/                   # Web Application Interface
│   ├── components/                     # UI components
│   ├── __init__.py
│   ├── analysis_streamlit.py           # Analysis dashboard
│   ├── language_streamlit.py           # Language processing UI
│   ├── retriever_streamlit.py          # Document search UI
│   ├── scraping_streamlit.py           # Web scraping UI
│   ├── streamlit_interface.py          # Main Streamlit interface
│   └── voice_streamlit.py              # Voice interaction UI
│
├── 📚 docs/                            # Documentation
│   ├── ai_tool_usage.md                # AI tool usage log
│   ├── API_README.md                   # API documentation
│   ├── health_checker.md               # Health check documentation
│   ├── demo*.py                        # Demo scripts
│   ├── test_*.py                       # Test files
│   ├── *_SUMMARY.md                    # Project summaries
│   └── *.MD                            # Various documentation files
│
├── 📝 logs/                            # Application logs
│   ├── orchestrator.log               # Orchestrator logs
│   ├── streamlit.log                  # Streamlit logs
│   └── voice_agent.log                # Voice agent logs
│
├── 🔧 pids/                            # Process IDs for services
│   ├── orchestrator.pid               # Orchestrator process ID
│   ├── streamlit.pid                  # Streamlit process ID
│   └── voice_agent.pid                # Voice agent process ID
│
├── 🐍 market_env/                      # Python virtual environment
│   ├── bin/                           # Executables
│   ├── lib/                           # Python libraries
│   └── pyvenv.cfg                     # Environment configuration
│
├── 🐳 Docker Configuration
│   ├── Dockerfile                     # Docker image definition
│   ├── docker-compose.yml             # Multi-service orchestration
│   └── .dockerignore                  # Docker ignore patterns
│
├── 🚀 Setup & Management Scripts
│   ├── setup.sh                       # Complete project setup
│   ├── start_services.sh              # Start all services
│   ├── stop_services.sh               # Stop all services
│   ├── check_status.sh                # Check service status
│   └── doctor.sh                      # System diagnostics
│
├── 📋 Configuration Files
│   ├── main.py                        # Main FastAPI application
│   ├── requirements.txt               # Python dependencies
│   ├── health_checker.py              # Comprehensive health checker
│   └── PROJECT_STRUCTURE.md           # This file
│
└── 📖 Documentation
    ├── README.md                      # Main project documentation
    └── .DS_Store                      # macOS metadata (ignore)
```

## 🔗 Module Dependencies

### Core Dependencies
```
main.py
├── agents.core.*                      # All agent implementations
├── FastAPI                           # Web framework
└── Pydantic                          # Data validation

orchestrator/orchestrator_fastapi.py
├── agents.core.*                      # Agent coordination
├── FastAPI                           # API framework
└── Real-time status tracking

streamlit_app/orchestrator_streamlit.py
├── orchestrator/orchestrator_fastapi.py  # Backend API
├── Streamlit                         # UI framework
└── Plotly                           # Visualizations
```

### Agent Dependencies
```
agents/core/
├── market_agent.py      → yfinance, requests
├── analysis_agent.py    → pandas, numpy, nltk
├── language_agent.py    → mistralai, transformers
├── voice_agent.py       → openai, pyttsx3, pygame
├── scraping_agent.py    → requests, beautifulsoup4
└── retriever_agent.py   → faiss-cpu, sentence-transformers
```

## 🚦 Service Architecture

### Port Allocation
- **8000**: Main API (main.py)
- **8001**: Voice Agent (standalone)
- **8002**: Analysis Agent (standalone)
- **8003**: Language Agent (standalone)
- **8004**: Market Agent (standalone)
- **8005**: Retriever Agent (standalone)
- **8011**: Orchestrator API
- **8501**: Streamlit Web App

### Service Flow
```
User Request
    ↓
Streamlit UI (8501)
    ↓
Orchestrator API (8011)
    ↓
Agent Coordination
    ↓
Individual Agents (8000-8005)
    ↓
Response Aggregation
    ↓
User Interface
```

## 📦 Package Structure

### agents/
- **Purpose**: Core AI agent implementations
- **Exports**: All agent classes via `__init__.py`
- **Structure**: Modular, each agent is independent

### data_ingestion/
- **Purpose**: Data input/output interfaces
- **Structure**: Separated by interface type (API/CLI)
- **Flexibility**: Easy to add new interface types

### orchestrator/
- **Purpose**: Multi-agent coordination
- **Features**: Real-time status, FAISS management
- **Scalability**: Designed for horizontal scaling

### streamlit_app/
- **Purpose**: Web-based user interface
- **Features**: Interactive dashboards, real-time updates
- **Modularity**: Component-based architecture

## 🔧 Configuration Management

### Environment Variables
```bash
# Required
MISTRAL_API_KEY=your-mistral-key

# Optional
ALPHAVANTAGE_API_KEY=your-av-key
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

### FAISS Indices
- **orchestrator/faiss/orchestrator_faiss/**: Main orchestrator index
- **orchestrator/faiss/api_faiss_store/**: API-specific index
- **orchestrator/faiss/cli_faiss_store/**: CLI-specific index

## 🚀 Deployment Options

### 1. Local Development
```bash
./setup.sh                    # Initial setup
./start_services.sh           # Start all services
./check_status.sh             # Monitor services
```

### 2. Docker Deployment
```bash
docker-compose build          # Build images
docker-compose up -d          # Start services
docker-compose logs -f        # Monitor logs
```

### 3. Production Deployment
- Use Docker Compose with production configurations
- Set up reverse proxy (nginx)
- Configure SSL certificates
- Set up monitoring and logging

## 🧪 Testing & Health Checks

### Health Checker
```bash
python health_checker.py      # Full health check
python health_checker.py --mode cli    # CLI only
python health_checker.py --mode api    # API only
```

### Service Status
```bash
./check_status.sh             # Check all services
./doctor.sh                   # System diagnostics
```

## 📈 Scalability Considerations

### Horizontal Scaling
- Each agent can run as separate service
- Load balancer for multiple orchestrator instances
- Shared FAISS indices via network storage

### Performance Optimization
- Agent response caching
- Batch processing for multiple requests
- Async processing for I/O operations

## 🔒 Security Considerations

### API Keys
- Store in environment variables
- Use secrets management in production
- Rotate keys regularly

### Network Security
- Use HTTPS in production
- Implement rate limiting
- Add authentication/authorization

## 📊 Monitoring & Logging

### Log Files
- **logs/orchestrator.log**: Main orchestrator logs
- **logs/streamlit.log**: UI application logs
- **logs/voice_agent.log**: Voice processing logs

### Metrics
- Response times per agent
- Error rates and types
- Resource usage (CPU, memory)
- User interaction patterns

## 🔄 Maintenance

### Regular Tasks
- Update dependencies (`pip install -r requirements.txt --upgrade`)
- Clean old logs (`find logs/ -name "*.log" -mtime +7 -delete`)
- Backup FAISS indices
- Monitor disk usage

### Updates
- Test in development environment first
- Use blue-green deployment for zero downtime
- Maintain backward compatibility for APIs

This modular structure provides excellent separation of concerns, scalability, and maintainability for the AI Financial Assistant project. 