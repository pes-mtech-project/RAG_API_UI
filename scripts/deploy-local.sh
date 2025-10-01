#!/bin/bash

# Deploy FinBERT RAG Application Locally
set -e

echo "🚀 Deploying FinBERT RAG Application Locally"
echo "==========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo -e "${GREEN}✅ Docker Compose is available${NC}"
echo ""

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down || true

echo ""

# Build and start containers
echo -e "${YELLOW}🏗️ Building and starting containers...${NC}"
docker-compose up --build -d

echo ""

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Health check
echo -e "${BLUE}🔍 Performing health checks...${NC}"

API_HEALTHY=false
UI_HEALTHY=false

# Check API health
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API service is healthy${NC}"
        API_HEALTHY=true
        break
    else
        echo -e "${YELLOW}⏳ Waiting for API service... (attempt $i/10)${NC}"
        sleep 5
    fi
done

# Check UI health
for i in {1..10}; do
    if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UI service is healthy${NC}"
        UI_HEALTHY=true
        break
    else
        echo -e "${YELLOW}⏳ Waiting for UI service... (attempt $i/10)${NC}"
        sleep 5
    fi
done

echo ""

if [ "$API_HEALTHY" = true ] && [ "$UI_HEALTHY" = true ]; then
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Application URLs:${NC}"
    echo "• UI:       http://localhost:8501"
    echo "• API:      http://localhost:8000"
    echo "• API Docs: http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}📋 Useful commands:${NC}"
    echo "• View logs:        docker-compose logs -f"
    echo "• Stop services:    docker-compose down"
    echo "• Restart services: docker-compose restart"
else
    echo -e "${RED}❌ Some services failed to start properly${NC}"
    echo ""
    echo -e "${YELLOW}📋 Troubleshooting:${NC}"
    echo "• Check logs: docker-compose logs"
    echo "• Check status: docker-compose ps"
    echo "• Restart: docker-compose restart"
    exit 1
fi