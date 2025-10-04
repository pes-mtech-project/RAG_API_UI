#!/bin/bash

# AWS ECR Production Deployment Script
# FinBERT News RAG Application - Modular Architecture v2.0

set -e  # Exit on any error

echo "🚀 Starting AWS ECR Production Deployment..."
echo "=================================================="

# Configuration
AWS_REGION="ap-south-1"
PROJECT_NAME="finbert-rag"
VERSION="v2.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure'."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

get_aws_account_id() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    log_info "AWS Account ID: ${AWS_ACCOUNT_ID}"
}

setup_ecr_variables() {
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    ECR_API_REPO="${ECR_REGISTRY}/${PROJECT_NAME}/api"
    ECR_UI_REPO="${ECR_REGISTRY}/${PROJECT_NAME}/ui"
    
    log_info "ECR Registry: ${ECR_REGISTRY}"
    log_info "API Repository: ${ECR_API_REPO}"
    log_info "UI Repository: ${ECR_UI_REPO}"
}

create_ecr_repositories() {
    log_info "Creating ECR repositories..."
    
    # Create API repository
    if aws ecr describe-repositories --repository-names "${PROJECT_NAME}/api" --region ${AWS_REGION} &> /dev/null; then
        log_warning "API repository already exists"
    else
        aws ecr create-repository \
            --repository-name "${PROJECT_NAME}/api" \
            --region ${AWS_REGION} \
            --image-scanning-configuration scanOnPush=true
        log_success "API repository created"
    fi
    
    # Create UI repository
    if aws ecr describe-repositories --repository-names "${PROJECT_NAME}/ui" --region ${AWS_REGION} &> /dev/null; then
        log_warning "UI repository already exists"
    else
        aws ecr create-repository \
            --repository-name "${PROJECT_NAME}/ui" \
            --region ${AWS_REGION} \
            --image-scanning-configuration scanOnPush=true
        log_success "UI repository created"
    fi
}

docker_login_ecr() {
    log_info "Logging into ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin ${ECR_REGISTRY}
    log_success "ECR login successful"
}

commit_and_tag_code() {
    log_info "Committing and tagging code..."
    
    # Add deployment plan to git
    git add AWS_ECR_DEPLOYMENT_PLAN.md
    
    # Check if there are uncommitted changes
    if git diff --staged --quiet; then
        log_warning "No changes to commit"
    else
        git commit -m "📋 AWS ECR Deployment Plan - Production Release v2.0.0"
        log_success "Changes committed"
    fi
    
    # Push to origin
    git push origin main
    log_success "Pushed to origin/main"
    
    # Create and push tag
    if git tag -l | grep -q "^${VERSION}$"; then
        log_warning "Tag ${VERSION} already exists"
        git tag -d ${VERSION}
        git push origin :refs/tags/${VERSION}
    fi
    
    git tag -a ${VERSION} -m "Production Release: Modular Architecture with Model Caching
- Multi-dimensional embedding search (384d, 768d, 1155d)
- 4.9x performance improvement with model caching
- SOLID principles architecture implementation
- 100% success rate across 138 test requests"
    
    git push origin ${VERSION}
    log_success "Tag ${VERSION} created and pushed"
}

build_docker_images() {
    log_info "Building Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t ${ECR_API_REPO}:latest \
        -t ${ECR_API_REPO}:${VERSION} \
        -t ${ECR_API_REPO}:prod \
        -f docker/Dockerfile.api .
    
    # Build UI image
    log_info "Building UI image..."
    docker build -t ${ECR_UI_REPO}:latest \
        -t ${ECR_UI_REPO}:${VERSION} \
        -t ${ECR_UI_REPO}:prod \
        -f docker/Dockerfile.ui .
    
    log_success "Docker images built successfully"
}

push_images_to_ecr() {
    log_info "Pushing images to ECR..."
    
    # Push API images
    log_info "Pushing API images..."
    docker push ${ECR_API_REPO}:latest
    docker push ${ECR_API_REPO}:${VERSION}
    docker push ${ECR_API_REPO}:prod
    
    # Push UI images
    log_info "Pushing UI images..."
    docker push ${ECR_UI_REPO}:latest
    docker push ${ECR_UI_REPO}:${VERSION}
    docker push ${ECR_UI_REPO}:prod
    
    log_success "All images pushed to ECR successfully"
}

verify_ecr_images() {
    log_info "Verifying ECR images..."
    
    echo "API Repository Images:"
    aws ecr list-images --repository-name "${PROJECT_NAME}/api" --region ${AWS_REGION} --output table
    
    echo "UI Repository Images:"
    aws ecr list-images --repository-name "${PROJECT_NAME}/ui" --region ${AWS_REGION} --output table
    
    log_success "ECR image verification complete"
}

create_production_env() {
    log_info "Creating production environment file..."
    
    cat > .env.prod << EOF
# Production ECR Configuration
REGISTRY=${ECR_REGISTRY}
API_IMAGE=${ECR_API_REPO}:latest
UI_IMAGE=${ECR_UI_REPO}:latest

# Application Configuration
API_PORT=8000
UI_PORT=8501
ENVIRONMENT=production

# Elasticsearch Configuration (update with your actual values)
ES_CLOUD_HOST=\${ES_CLOUD_HOST}
ES_CLOUD_KEY=\${ES_CLOUD_KEY}
ES_CLOUD_INDEX=\${ES_CLOUD_INDEX}
EOF
    
    log_success "Production environment file created: .env.prod"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure..."
    
    cd infrastructure
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing CDK dependencies..."
        npm install
    fi
    
    # Synthesize template
    log_info "Synthesizing CloudFormation template..."
    npm run synth
    
    # Deploy to production
    log_info "Deploying to production environment..."
    npm run deploy:prod
    
    cd ..
    log_success "Infrastructure deployment complete"
}

main() {
    echo "🚀 AWS ECR Production Deployment - FinBERT RAG v2.0"
    echo "=================================================="
    
    check_prerequisites
    get_aws_account_id
    setup_ecr_variables
    
    echo
    log_info "Starting deployment phases..."
    
    # Phase 1: Pre-Deployment Setup
    echo
    echo "📋 Phase 1: Pre-Deployment Setup"
    echo "--------------------------------"
    commit_and_tag_code
    create_ecr_repositories
    docker_login_ecr
    
    # Phase 2: Container Build & Push
    echo
    echo "🏗️ Phase 2: Container Build & Push"
    echo "----------------------------------"
    build_docker_images
    push_images_to_ecr
    verify_ecr_images
    
    # Phase 3: Infrastructure Configuration
    echo
    echo "🔧 Phase 3: Infrastructure Configuration"
    echo "---------------------------------------"
    create_production_env
    
    # Optional: Deploy infrastructure (uncomment if needed)
    # deploy_infrastructure
    
    echo
    echo "🎉 ECR Deployment Complete!"
    echo "=========================="
    log_success "Images successfully deployed to AWS ECR"
    log_success "Repository URIs:"
    log_success "  API: ${ECR_API_REPO}"
    log_success "  UI: ${ECR_UI_REPO}"
    
    echo
    log_info "Next steps:"
    echo "  1. Update GitHub Actions workflows to use ECR"
    echo "  2. Deploy infrastructure: cd infrastructure && npm run deploy:prod"
    echo "  3. Update ECS services to use new ECR images"
    echo "  4. Run validation tests"
    
    echo
    log_info "Deployment plan: AWS_ECR_DEPLOYMENT_PLAN.md"
}

# Execute main function
main "$@"