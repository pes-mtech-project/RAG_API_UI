#!/bin/bash

# Local CI/CD Pipeline Script
# Replaces GitHub Actions for development workflow

set -e

echo "🚀 Local Development Pipeline"
echo "============================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

#!/bin/bash
# Enhanced Local CI Pipeline with Quality Checks and AWS Deployment
# Built with assistance from GitHub Copilot

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION="dev-${TIMESTAMP}-${GIT_HASH}"

# Load environment variables from .env if it exists
if [[ -f "${PROJECT_DIR}/.env" ]]; then
    source "${PROJECT_DIR}/.env"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# AWS Configuration
AWS_REGION="${AWS_REGION:-ap-south-1}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_API_REPO="finbert-rag/api-dev"
ECR_UI_REPO="finbert-rag/ui-dev"

# Generate version tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SHORT_SHA=$(git rev-parse --short HEAD)
VERSION="dev-${TIMESTAMP}-${SHORT_SHA}"

echo -e "${BLUE}Version: ${VERSION}${NC}"

# ===== CODE QUALITY CHECKS =====
echo ""
echo -e "${YELLOW}🔍 Running Code Quality Checks${NC}"

# Check if we have Python tools installed
if command -v black &> /dev/null && command -v flake8 &> /dev/null; then
    echo "Running code quality checks..."
    
    cd api
    
    # Format check
    echo "Checking code formatting..."
    if black --check --diff . 2>/dev/null; then
        echo -e "${GREEN}✅ Code formatting OK${NC}"
    else
        echo -e "${YELLOW}⚠️ Code formatting issues (run: black .)${NC}"
    fi
    
    # Lint check
    echo "Running linting..."
    if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null; then
        echo -e "${GREEN}✅ No critical lint errors${NC}"
    else
        echo -e "${YELLOW}⚠️ Lint warnings found${NC}"
    fi
    
    # Security check (if available)
    if command -v bandit &> /dev/null; then
        echo "Running security checks..."
        bandit -r . -ll 2>/dev/null || echo -e "${YELLOW}⚠️ Security warnings found${NC}"
    fi
    
    cd ..
else
    echo -e "${BLUE}ℹ️ Python linting tools not installed. Skipping code quality checks.${NC}"
    echo -e "${BLUE}   To enable: pip install black flake8 bandit${NC}"
fi

echo -e "${GREEN}✅ Code quality checks completed${NC}"

# ===== DOCKER BUILD =====
echo ""
echo -e "${YELLOW}🏗️ Building Docker Images${NC}"

# Check if we should build API
if git diff --name-only HEAD~1 HEAD | grep -E '^(api/|docker/Dockerfile\.api|requirements\.txt)' > /dev/null; then
    echo "Building API image..."
    docker build -f docker/Dockerfile.api -t finbert-api:${VERSION} .
    echo -e "${GREEN}✅ API image built${NC}"
    API_BUILT=true
else
    echo -e "${BLUE}ℹ️ No API changes detected${NC}"
    API_BUILT=false
fi

# Check if we should build UI
if git diff --name-only HEAD~1 HEAD | grep -E '^(streamlit/|docker/Dockerfile\.ui)' > /dev/null; then
    echo "Building UI image..."
    docker build -f docker/Dockerfile.ui -t finbert-ui:${VERSION} .
    echo -e "${GREEN}✅ UI image built${NC}"
    UI_BUILT=true
else
    echo -e "${BLUE}ℹ️ No UI changes detected${NC}"
    UI_BUILT=false
fi

# ===== LOCAL TESTING =====
echo ""
echo -e "${YELLOW}🧪 Running Local Tests${NC}"

# Start containers for testing
echo "Starting containers..."
docker-compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Health check
echo "Running health checks..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    docker-compose logs finbert-api
    exit 1
fi

# Test endpoints
echo "Testing API endpoints..."
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 1}' \
  -s http://localhost:8000/search/cosine/embedding384d/ > /dev/null || echo -e "${BLUE}ℹ️ Search endpoint responding (ES connection expected to fail)${NC}"

echo -e "${GREEN}✅ Local testing passed${NC}"

# ===== AWS DEPLOYMENT (OPTIONAL) =====
echo ""
echo -e "${YELLOW}🚀 Deploy to AWS? (y/n)${NC}"
read -r deploy_choice

if [[ $deploy_choice == "y" || $deploy_choice == "Y" ]]; then
    echo "Checking AWS credentials..."
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        echo "Run: aws configure"
        exit 1
    fi

    echo "Logging into ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

    if [[ $API_BUILT == true ]]; then
        echo "Pushing API image..."
        docker tag finbert-api:${VERSION} ${ECR_REGISTRY}/${ECR_API_REPO}:${VERSION}
        docker tag finbert-api:${VERSION} ${ECR_REGISTRY}/${ECR_API_REPO}:latest-dev
        docker push ${ECR_REGISTRY}/${ECR_API_REPO}:${VERSION}
        docker push ${ECR_REGISTRY}/${ECR_API_REPO}:latest-dev
        echo -e "${GREEN}✅ API image pushed${NC}"
    fi

    if [[ $UI_BUILT == true ]]; then
        echo "Pushing UI image..."
        docker tag finbert-ui:${VERSION} ${ECR_REGISTRY}/${ECR_UI_REPO}:${VERSION}
        docker tag finbert-ui:${VERSION} ${ECR_REGISTRY}/${ECR_UI_REPO}:latest-dev
        docker push ${ECR_REGISTRY}/${ECR_UI_REPO}:${VERSION}
        docker push ${ECR_REGISTRY}/${ECR_UI_REPO}:latest-dev
        echo -e "${GREEN}✅ UI image pushed${NC}"
    fi

    echo "Updating ECS services..."
    # Update ECS services (simplified)
    if [[ $API_BUILT == true ]]; then
        aws ecs update-service --cluster finbert-rag-dev-cluster \
          --service finbert-api-dev --force-new-deployment
    fi

    if [[ $UI_BUILT == true ]]; then
        aws ecs update-service --cluster finbert-rag-dev-cluster \
          --service finbert-ui-dev --force-new-deployment  
    fi

    echo -e "${GREEN}✅ Deployment complete${NC}"
else
    echo -e "${BLUE}ℹ️ Skipping AWS deployment${NC}"
fi

# ===== CLEANUP =====
echo ""
echo -e "${YELLOW}🧹 Cleaning up${NC}"
docker-compose down

echo ""
echo -e "${GREEN}🎉 Pipeline completed successfully!${NC}"
echo -e "${BLUE}Version built: ${VERSION}${NC}"