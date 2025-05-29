#!/bin/bash

# Multi-Agent System Health Checker Runner
# This script activates the market environment and runs the health checker

echo "🔍 Multi-Agent System Health Checker"
echo "===================================="

# Check if market_env exists
if [ ! -d "market_env" ]; then
    echo "❌ Error: market_env directory not found!"
    echo "Please ensure you're in the project root directory."
    exit 1
fi

# Activate the virtual environment and run health checker
source market_env/bin/activate

# Check if health_checker.py exists
if [ ! -f "health_checker.py" ]; then
    echo "❌ Error: health_checker.py not found!"
    exit 1
fi

# Pass all arguments to health_checker.py
python health_checker.py "$@"

# Capture exit code
exit_code=$?

echo ""
echo "Health check completed with exit code: $exit_code"

if [ $exit_code -eq 0 ]; then
    echo "✅ Health check passed successfully!"
else
    echo "❌ Health check detected issues. Please review the results above."
fi

exit $exit_code 