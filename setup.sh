#!/bin/bash

# AI Financial Assistant - Setup Script
# This script sets up the entire project environment

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_status "🚀 Setting up AI Financial Assistant..."

# 1. Check Python version
print_status "🐍 Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_success "Python $PYTHON_VERSION found (✓ >= 3.9)"
    else
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# 2. Create virtual environment
print_status "📦 Creating virtual environment..."
if [ ! -d "market_env" ]; then
    python3 -m venv market_env
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# 3. Activate virtual environment
print_status "🔧 Activating virtual environment..."
source market_env/bin/activate
print_success "Virtual environment activated"

# 4. Upgrade pip
print_status "⬆️  Upgrading pip..."
pip install --upgrade pip

# 5. Install dependencies
print_status "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# 6. Create necessary directories
print_status "📁 Creating necessary directories..."
mkdir -p logs pids orchestrator/faiss docs
print_success "Directories created"

# 7. Set up environment variables
print_status "🔑 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# AI Financial Assistant Environment Variables

# Required API Keys
MISTRAL_API_KEY=NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal

# Optional API Keys
ALPHAVANTAGE_API_KEY=your-alphavantage-key-here
OPENAI_API_KEY=your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Application Settings
PYTHONPATH=.
LOG_LEVEL=INFO
EOF
    print_success "Environment file created (.env)"
    print_warning "Please update .env with your API keys if needed"
else
    print_warning ".env file already exists"
fi

# 8. Download NLTK data
print_status "📖 Downloading NLTK data..."
python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('vader_lexicon', quiet=True)
print('NLTK data downloaded successfully')
"
print_success "NLTK data downloaded"

# 9. Test imports
print_status "🧪 Testing imports..."
python -c "
try:
    from agents.core.market_agent import MarketDataAgent
    from agents.core.analysis_agent import AnalysisAgent
    from agents.core.language_agent import LanguageAgent
    from agents.core.voice_agent import VoiceAgent
    from agents.core.scraping_agent import ScrapingAgent
    from agents.core.retriever_agent import RetrieverAgent
    print('✅ All agent imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# 10. Make scripts executable
print_status "🔧 Making scripts executable..."
chmod +x start_services.sh
chmod +x stop_services.sh
chmod +x check_status.sh
chmod +x doctor.sh
print_success "Scripts made executable"

# 11. Run health check
print_status "🏥 Running initial health check..."
if [ -f "health_checker.py" ]; then
    python health_checker.py --mode cli --verbose || print_warning "Some health checks failed (this is normal on first setup)"
else
    print_warning "health_checker.py not found, skipping health check"
fi

# 12. Display setup summary
echo ""
print_success "🎉 Setup completed successfully!"
echo ""
echo -e "${BLUE}📋 Setup Summary:${NC}"
echo "├── ✅ Python 3.9+ verified"
echo "├── ✅ Virtual environment created (market_env)"
echo "├── ✅ Dependencies installed"
echo "├── ✅ Directories created"
echo "├── ✅ Environment variables configured"
echo "├── ✅ NLTK data downloaded"
echo "├── ✅ Agent imports tested"
echo "└── ✅ Scripts made executable"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Update .env file with your API keys (optional)"
echo "2. Start services: ${GREEN}./start_services.sh${NC}"
echo "3. Open browser: ${GREEN}http://localhost:8501${NC}"
echo "4. Check status: ${GREEN}./check_status.sh${NC}"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "├── Main README: README.md"
echo "├── AI Tool Usage: docs/ai_tool_usage.md"
echo "└── API Documentation: http://localhost:8000/docs (after starting)"
echo ""
echo -e "${BLUE}🐳 Docker Alternative:${NC}"
echo "├── Build: ${GREEN}docker-compose build${NC}"
echo "└── Run: ${GREEN}docker-compose up -d${NC}"
echo ""
print_success "Ready to use! 🚀" 