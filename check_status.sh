#!/bin/bash

# AI Financial Assistant - Status Check Script
# This script checks the status of all services

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local port=$1
    local service_name=$2
    local url=$3
    
    if lsof -i :$port > /dev/null 2>&1; then
        if [ ! -z "$url" ] && curl -s $url > /dev/null 2>&1; then
            echo -e "├── $service_name: ${GREEN}✅ Running & Responding${NC} (Port: $port)"
        else
            echo -e "├── $service_name: ${YELLOW}⚠️  Running but not responding${NC} (Port: $port)"
        fi
    else
        echo -e "├── $service_name: ${RED}❌ Not Running${NC} (Port: $port)"
    fi
}

echo -e "${BLUE}🔍 AI Financial Assistant - Service Status Check${NC}"
echo ""

echo -e "${BLUE}📊 Service Status:${NC}"
check_service 8000 "Main API           " "http://localhost:8000/docs"
check_service 8011 "Orchestrator FastAPI" "http://localhost:8011/agents/status"
check_service 8501 "Streamlit App      " "http://localhost:8501"
echo ""

# Check process status
echo -e "${BLUE}🔧 Process Information:${NC}"
if [ -d "logs" ]; then
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            service_name=$(basename "$pidfile" .pid)
            pid=$(cat "$pidfile")
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "├── $service_name: ${GREEN}✅ PID $pid${NC}"
            else
                echo -e "├── $service_name: ${RED}❌ PID $pid (not running)${NC}"
            fi
        fi
    done
else
    echo "├── No PID files found (logs directory not present)"
fi
echo ""

# Test API endpoints
echo -e "${BLUE}🧪 API Health Checks:${NC}"

# Test Orchestrator
if curl -s http://localhost:8011/agents/status | grep -q "available_agents" 2>/dev/null; then
    agent_count=$(curl -s http://localhost:8011/agents/status | grep -o '"name"' | wc -l | tr -d ' ')
    echo -e "├── Orchestrator API: ${GREEN}✅ Responding ($agent_count agents available)${NC}"
else
    echo -e "├── Orchestrator API: ${RED}❌ Not responding${NC}"
fi

# Test Main API
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "├── Main API:         ${GREEN}✅ Responding${NC}"
else
    echo -e "├── Main API:         ${RED}❌ Not responding${NC}"
fi

# Test Streamlit
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "├── Streamlit App:    ${GREEN}✅ Responding${NC}"
else
    echo -e "├── Streamlit App:    ${RED}❌ Not responding${NC}"
fi
echo ""

# Show logs information
echo -e "${BLUE}📂 Log Files:${NC}"
if [ -d "logs" ]; then
    for logfile in logs/*.log; do
        if [ -f "$logfile" ]; then
            service_name=$(basename "$logfile" .log)
            size=$(ls -lh "$logfile" | awk '{print $5}')
            modified=$(ls -l "$logfile" | awk '{print $6, $7, $8}')
            echo "├── $service_name: $size (Modified: $modified)"
        fi
    done
else
    echo "├── No log files found"
fi
echo ""

# Quick actions
echo -e "${BLUE}⚡ Quick Actions:${NC}"
echo "├── Start all services:  ./start_services.sh"
echo "├── Stop all services:   ./stop_services.sh"
echo "├── Check status:        ./check_status.sh"
echo "└── View logs:          tail -f logs/[service].log"
echo ""

# Show URLs
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "├── 🖥️  Streamlit App:        http://localhost:8501"
echo "├── 🚀 Main API:             http://localhost:8000"
echo "├── 📚 Main API Docs:        http://localhost:8000/docs"
echo "├── 🤖 Orchestrator API:     http://localhost:8011"
echo "└── 📚 Orchestrator Docs:    http://localhost:8011/docs"
echo "" 