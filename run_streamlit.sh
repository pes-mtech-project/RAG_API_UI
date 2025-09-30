#!/bin/bash

# Run Streamlit development server

echo "🚀 Starting Streamlit frontend..."
echo "App will be available at: http://localhost:8501"
echo ""

cd streamlit
source venv/bin/activate
streamlit run app.py --server.port 8501