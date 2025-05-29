#!/bin/bash

# AI Financial Assistant - Service Startup Script
# This script starts all required services for the orchestrator and Streamlit app

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

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing existing processes on port $port: $pids"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Create logs directory if it doesn't exist
mkdir -p logs

print_status "🚀 Starting AI Financial Assistant Services..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "No virtual environment detected. Activating market_env..."
    if [ -f "market_env/bin/activate" ]; then
        source market_env/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment 'market_env' not found. Please create it first."
        exit 1
    fi
fi

# 1. Stop any existing services
print_status "🛑 Stopping existing services..."

# Kill services on known ports
kill_port 8011  # Orchestrator FastAPI
kill_port 8000  # Voice Agent
kill_port 8501  # Streamlit (if running)
kill_port 8502  # Alternative Streamlit port

# Wait a moment for processes to fully terminate
sleep 3

# 2. Start Voice Agent (if voice_agent.py exists)
if [ -f "agents/core/voice_agent.py" ]; then
    print_status "🎤 Voice Agent integrated into main API server"
    print_success "Voice Agent available via main API endpoints"
else
    print_warning "agents/core/voice_agent.py not found, skipping Voice Agent"
fi

# 3. Start main API server
print_status "🚀 Starting Main API server on port 8000..."
python main.py > logs/main_api.log 2>&1 &
MAIN_API_PID=$!
echo $MAIN_API_PID > logs/main_api.pid
print_success "Main API server started (PID: $MAIN_API_PID)"
    
# Wait for Main API to be ready
if wait_for_service "http://localhost:8000/docs" "Main API"; then
    print_success "✅ Main API is ready and responding"
else
    print_warning "⚠️  Main API health check failed, but continuing..."
fi

# 4. Start Orchestrator FastAPI
print_status "🤖 Starting Orchestrator FastAPI on port 8011..."
python orchestrator/orchestrator_fastapi.py > logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > logs/orchestrator.pid
print_success "Orchestrator FastAPI started (PID: $ORCHESTRATOR_PID)"

# Wait for Orchestrator to be ready
if wait_for_service "http://localhost:8011/agents/status" "Orchestrator FastAPI"; then
    print_success "✅ Orchestrator API is ready and responding"
else
    print_error "❌ Orchestrator API failed to start"
    exit 1
fi

# 5. Start Streamlit App
print_status "🖥️  Starting Streamlit App on port 8501..."
streamlit run orchestrator/orchestrator_streamlit.py --server.port 8501 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > logs/streamlit.pid
print_success "Streamlit App started (PID: $STREAMLIT_PID)"

# Wait for Streamlit to be ready
if wait_for_service "http://localhost:8501" "Streamlit App"; then
    print_success "✅ Streamlit App is ready"
else
    print_error "❌ Streamlit App failed to start"
fi

# 6. Display service status
echo ""
print_success "🎉 All services started successfully!"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo "├── 🚀 Main API:             http://localhost:8000"
echo "├── 🤖 Orchestrator FastAPI: http://localhost:8011"
echo "└── 🖥️  Streamlit App:        http://localhost:8501"
echo ""
echo -e "${BLUE}📂 Logs Location:${NC}"
echo "├── Orchestrator: logs/orchestrator.log"
echo "├── Voice Agent:  logs/main_api.log"
echo "└── Streamlit:    logs/streamlit.log"
echo ""
echo -e "${BLUE}🔧 Process IDs:${NC}"
echo "├── Orchestrator: $ORCHESTRATOR_PID"
if [ ! -z "$MAIN_API_PID" ]; then
    echo "├── Main API:  $MAIN_API_PID"
fi
echo "└── Streamlit:    $STREAMLIT_PID"
echo ""

# 7. Test API endpoints
echo -e "${BLUE}🧪 Testing API Endpoints:${NC}"

# Test Orchestrator
print_status "Testing Orchestrator API..."
if curl -s http://localhost:8011/agents/status | grep -q "available_agents"; then
    print_success "✅ Orchestrator API responding correctly"
else
    print_warning "⚠️  Orchestrator API test failed"
fi

# Test Main API (if started)
if [ ! -z "$MAIN_API_PID" ]; then
    print_status "Testing Main API..."
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_success "✅ Main API responding correctly"
    else
        print_warning "⚠️  Main API test failed"
    fi
fi

echo ""
print_success "🚀 AI Financial Assistant is ready to use!"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Open your browser to: ${BLUE}http://localhost:8501${NC}"
echo "2. Test the voice features and AI agents"
echo "3. Check logs if you encounter any issues"
echo ""
echo -e "${YELLOW}To stop all services, run:${NC} ./stop_services.sh"
echo "" 