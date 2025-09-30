#!/bin/bash

# Development setup and run script for FinBERT News RAG App

set -e

echo "🚀 FinBERT News RAG Application Setup"
echo "====================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists pip3; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

echo "✅ Dependencies check passed"

# Setup API
echo ""
echo "🔧 Setting up FastAPI backend..."
cd api
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip3 install -r requirements.txt

echo "✅ FastAPI setup complete"

# Setup Streamlit
echo ""
echo "🔧 Setting up Streamlit frontend..."
cd ../streamlit
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip3 install -r requirements.txt

echo "✅ Streamlit setup complete"

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the applications:"
echo "1. Start FastAPI backend: ./run_api.sh"
echo "2. Start Streamlit frontend: ./run_streamlit.sh"
echo "3. Or use Docker: docker-compose up"
echo ""
echo "📱 Access URLs:"
echo "- FastAPI API: http://localhost:8000"
echo "- FastAPI Docs: http://localhost:8000/docs"
echo "- Streamlit App: http://localhost:8501"