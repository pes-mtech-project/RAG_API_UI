#!/bin/bash

echo "🔍 FinBERT App Status Check"
echo "=========================="

# Check if processes are running
if [ -f /home/ec2-user/api.pid ]; then
    API_PID=$(cat /home/ec2-user/api.pid)
    if ps -p $API_PID > /dev/null; then
        echo "✅ API is running (PID: $API_PID)"
    else
        echo "❌ API is not running"
    fi
else
    echo "❌ API PID file not found"
fi

if [ -f /home/ec2-user/streamlit.pid ]; then
    STREAMLIT_PID=$(cat /home/ec2-user/streamlit.pid)
    if ps -p $STREAMLIT_PID > /dev/null; then
        echo "✅ Streamlit is running (PID: $STREAMLIT_PID)"
    else
        echo "❌ Streamlit is not running"
    fi
else
    echo "❌ Streamlit PID file not found"
fi

# Test health endpoints
echo ""
echo "🏥 Health Checks:"

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
fi

if curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Streamlit health check passed"
else
    echo "❌ Streamlit health check failed"
fi

# Show recent log entries
echo ""
echo "📝 Recent logs:"
echo "--- API Log (last 5 lines) ---"
tail -5 /home/ec2-user/api.log 2>/dev/null || echo "No API log found"

echo ""
echo "--- Streamlit Log (last 5 lines) ---"
tail -5 /home/ec2-user/streamlit.log 2>/dev/null || echo "No Streamlit log found"