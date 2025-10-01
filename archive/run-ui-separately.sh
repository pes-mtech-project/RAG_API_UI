#!/bin/bash

# Run Streamlit UI as separate container
# This connects to the API service running on the development instance

API_HOST=${1:-43.204.102.6}
API_PORT=${2:-8010}

echo "Starting Streamlit UI container..."
echo "Connecting to API at: http://$API_HOST:$API_PORT"

# Set the API URL environment variable
export API_URL="http://$API_HOST:$API_PORT"

# Run the UI container
docker-compose -f docker-compose.ui.yml up -d

# Check status
echo "Checking container status..."
docker ps | grep finbert-ui-standalone

echo "Streamlit UI should be available at: http://localhost:8501"
echo "To stop the UI container: docker-compose -f docker-compose.ui.yml down"