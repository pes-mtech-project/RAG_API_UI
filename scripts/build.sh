#!/bin/bash

# Build FinBERT RAG Docker Containers
set -e

echo "🐳 Building FinBERT RAG Docker Containers"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REGISTRY="ghcr.io"
NAMESPACE="pes-mtech-project/rag_api_ui"
TAG="${1:-latest}"

echo -e "${BLUE}📋 Build Configuration:${NC}"
echo "Registry: $REGISTRY"
echo "Namespace: $NAMESPACE"
echo "Tag: $TAG"
echo ""

# Build API container
echo -e "${YELLOW}🏗️ Building API container...${NC}"
docker build -f docker/Dockerfile.api -t "$REGISTRY/$NAMESPACE/finbert-api:$TAG" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API container built successfully${NC}"
else
    echo -e "${RED}❌ API container build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 API container built successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Built Images:${NC}"
echo "• $REGISTRY/$NAMESPACE/finbert-api:$TAG"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test locally: ./scripts/deploy-local.sh"
echo "2. Push to registry: docker push $REGISTRY/$NAMESPACE/finbert-api:$TAG"