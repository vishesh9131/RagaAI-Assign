#!/bin/bash

# AI Financial Assistant - Service Stop Script
# This script stops all running services for the orchestrator and Streamlit app

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

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_status "Stopping $service_name on port $port (PIDs: $pids)..."
        echo $pids | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Check if processes are still running, force kill if necessary
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$remaining_pids" ]; then
            print_warning "Force killing remaining processes: $remaining_pids"
            echo $remaining_pids | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        print_success "$service_name stopped"
    else
        print_status "$service_name (port $port) is not running"
    fi
}

# Function to kill process by PID file
kill_by_pidfile() {
    local pidfile=$1
    local service_name=$2
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill -TERM $pid 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "Force killing $service_name (PID: $pid)..."
                kill -9 $pid 2>/dev/null || true
            fi
            print_success "$service_name stopped"
        else
            print_status "$service_name (PID: $pid) is not running"
        fi
        rm -f "$pidfile"
    else
        print_status "No PID file found for $service_name"
    fi
}

print_status "🛑 Stopping AI Financial Assistant Services..."

# Stop services using PID files (more graceful)
if [ -d "logs" ]; then
    print_status "📂 Checking PID files..."
    
    # Stop by PID files first (more graceful)
    kill_by_pidfile "logs/streamlit.pid" "Streamlit App"
    kill_by_pidfile "logs/orchestrator.pid" "Orchestrator FastAPI"
    kill_by_pidfile "logs/voice_agent.pid" "Voice Agent"
fi

# Stop services by port (backup method)
print_status "🔍 Checking for remaining processes on ports..."

kill_port 8501 "Streamlit App"
kill_port 8502 "Alternative Streamlit"
kill_port 8011 "Orchestrator FastAPI"
kill_port 8000 "Voice Agent"

# Kill any remaining Python processes related to our services
print_status "🧹 Cleaning up remaining processes..."

# Find and kill any remaining orchestrator or streamlit processes
REMAINING_PROCESSES=$(ps aux | grep -E "(orchestrator_|voice_|streamlit)" | grep -v grep | awk '{print $2}' 2>/dev/null || true)

if [ ! -z "$REMAINING_PROCESSES" ]; then
    print_warning "Found remaining processes: $REMAINING_PROCESSES"
    echo $REMAINING_PROCESSES | xargs kill -TERM 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    STILL_RUNNING=$(ps aux | grep -E "(orchestrator_|voice_|streamlit)" | grep -v grep | awk '{print $2}' 2>/dev/null || true)
    if [ ! -z "$STILL_RUNNING" ]; then
        print_warning "Force killing stubborn processes: $STILL_RUNNING"
        echo $STILL_RUNNING | xargs kill -9 2>/dev/null || true
    fi
fi

# Clean up PID files
if [ -d "logs" ]; then
    print_status "🗑️  Cleaning up PID files..."
    rm -f logs/*.pid
fi

# Final verification
print_status "🔍 Final verification..."
ACTIVE_PORTS=$(lsof -i :8000,8011,8501,8502 2>/dev/null | grep LISTEN || true)

if [ -z "$ACTIVE_PORTS" ]; then
    print_success "✅ All services stopped successfully!"
else
    print_warning "⚠️  Some ports may still be in use:"
    echo "$ACTIVE_PORTS"
fi

echo ""
print_success "🎯 Service shutdown complete!"
echo ""
echo -e "${BLUE}📊 Port Status:${NC}"
echo "├── 8000 (Voice Agent):     $(lsof -i :8000 >/dev/null 2>&1 && echo '🔴 In Use' || echo '✅ Free')"
echo "├── 8011 (Orchestrator):    $(lsof -i :8011 >/dev/null 2>&1 && echo '🔴 In Use' || echo '✅ Free')"
echo "└── 8501 (Streamlit):       $(lsof -i :8501 >/dev/null 2>&1 && echo '🔴 In Use' || echo '✅ Free')"
echo ""
echo -e "${GREEN}To start services again, run:${NC} ./start_services.sh"
echo "" 