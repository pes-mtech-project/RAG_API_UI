#!/bin/bash

# Run FastAPI development server

echo "🚀 Starting FastAPI backend..."
echo "API will be available at: http://localhost:8000"
echo "Interactive docs at: http://localhost:8000/docs"
echo ""

cd api
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload