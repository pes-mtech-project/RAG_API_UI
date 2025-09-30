#!/bin/bash
set -e

echo "🚀 Starting FinBERT App Deployment..."
echo "====================================="

# Update system
echo "🔧 Updating system..."
sudo yum update -y
sudo yum install -y python3 python3-pip git curl

# Create app directory
echo "📁 Setting up application directory..."
sudo mkdir -p /home/ec2-user/finbert-news-rag-app
sudo chown ec2-user:ec2-user /home/ec2-user/finbert-news-rag-app

# Navigate to app directory
cd /home/ec2-user/finbert-news-rag-app

# Clone or update code
if [ -d ".git" ]; then
    echo "📥 Updating existing code..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone https://github.com/pes-mtech-project/RAG_API_UI.git .
fi

# Install API dependencies
echo "🔧 Installing API dependencies..."
cd api
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt

# Install Streamlit dependencies
echo "🔧 Installing Streamlit dependencies..."
cd ../streamlit
python3 -m pip install --user -r requirements.txt
cd ..

# Kill existing processes
echo "🛑 Stopping existing services..."
pkill -f "uvicorn main:app" || true
pkill -f "streamlit run" || true
sleep 5

# Start API in background
echo "🚀 Starting API service..."
cd api
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /home/ec2-user/api.log 2>&1 &
API_PID=$!
echo $API_PID > /home/ec2-user/api.pid
echo "✅ API started with PID: $API_PID"

# Start Streamlit in background
echo "🚀 Starting Streamlit service..."
cd ../streamlit
nohup /home/ec2-user/.local/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /home/ec2-user/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > /home/ec2-user/streamlit.pid
echo "✅ Streamlit started with PID: $STREAMLIT_PID"

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check if processes are still running
if ps -p $API_PID > /dev/null; then
    echo "✅ API is running (PID: $API_PID)"
else
    echo "❌ API process died, checking logs..."
    tail -20 /home/ec2-user/api.log
    exit 1
fi

if ps -p $STREAMLIT_PID > /dev/null; then
    echo "✅ Streamlit is running (PID: $STREAMLIT_PID)"
else
    echo "❌ Streamlit process died, checking logs..."
    tail -20 /home/ec2-user/streamlit.log
    exit 1
fi

# Health checks
echo "🏥 Running health checks..."

# Test API
API_HEALTHY=false
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API health check passed"
        API_HEALTHY=true
        break
    else
        echo "⏳ API health check $i/10..."
        sleep 5
    fi
done

# Test Streamlit
STREAMLIT_HEALTHY=false
for i in {1..10}; do
    if curl -f http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ Streamlit health check passed"
        STREAMLIT_HEALTHY=true
        break
    else
        echo "⏳ Streamlit health check $i/10..."
        sleep 5
    fi
done

# Final status
if [ "$API_HEALTHY" = true ] && [ "$STREAMLIT_HEALTHY" = true ]; then
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "====================================="
    echo ""
    PUBLIC_IP=$(curl -s http://ifconfig.me || echo "UNKNOWN")
    echo "🔗 Access your application:"
    echo "   📊 Streamlit UI: http://$PUBLIC_IP:8501"
    echo "   🔌 API Docs: http://$PUBLIC_IP:8000/docs"
    echo "   ❤️  Health Check: http://$PUBLIC_IP:8000/health"
    echo ""
    echo "📝 Log files:"
    echo "   API: /home/ec2-user/api.log"
    echo "   Streamlit: /home/ec2-user/streamlit.log"
    echo ""
    echo "Deployment completed at: $(date)" > /home/ec2-user/deployment-status.txt
else
    echo "❌ Some services failed health checks"
    echo "📋 Check logs:"
    echo "   API: tail -20 /home/ec2-user/api.log"
    echo "   Streamlit: tail -20 /home/ec2-user/streamlit.log"
    exit 1
fi