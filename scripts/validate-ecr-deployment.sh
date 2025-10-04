#!/bin/bash

# AWS ECR Deployment Validation Script
# Validates prerequisites and configuration for ECR deployment

set -e

echo "🔍 AWS ECR Deployment Validation"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# Validation functions
check_aws_cli() {
    log_info "Checking AWS CLI..."
    if command -v aws &> /dev/null; then
        AWS_VERSION=$(aws --version 2>&1 | cut -d/ -f2 | cut -d' ' -f1)
        log_success "AWS CLI installed: v${AWS_VERSION}"
    else
        log_error "AWS CLI not found. Install with: brew install awscli"
        return 1
    fi
}

check_docker() {
    log_info "Checking Docker..."
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log_success "Docker installed: v${DOCKER_VERSION}"
        
        # Check if Docker is running
        if docker ps &> /dev/null; then
            log_success "Docker daemon is running"
        else
            log_error "Docker daemon is not running. Please start Docker Desktop."
            return 1
        fi
    else
        log_error "Docker not found. Install Docker Desktop."
        return 1
    fi
}

check_aws_credentials() {
    log_info "Checking AWS credentials..."
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
        USER_ARN=$(aws sts get-caller-identity --query 'Arn' --output text)
        log_success "AWS credentials configured"
        log_info "Account ID: ${ACCOUNT_ID}"
        log_info "User: ${USER_ARN}"
    else
        log_error "AWS credentials not configured. Run: aws configure"
        return 1
    fi
}

check_git_status() {
    log_info "Checking Git status..."
    if git status &> /dev/null; then
        BRANCH=$(git branch --show-current)
        log_success "Git repository: branch ${BRANCH}"
        
        # Check for uncommitted changes
        if git diff --quiet && git diff --staged --quiet; then
            log_success "No uncommitted changes"
        else
            log_warning "Uncommitted changes detected"
        fi
        
        # Check commits ahead of origin
        if git log origin/main..HEAD --oneline | grep -q .; then
            COMMITS_AHEAD=$(git log origin/main..HEAD --oneline | wc -l)
            log_warning "${COMMITS_AHEAD} commits ahead of origin/main"
        else
            log_success "Branch up to date with origin/main"
        fi
    else
        log_error "Not in a Git repository"
        return 1
    fi
}

check_docker_files() {
    log_info "Checking Docker files..."
    
    if [[ -f "docker/Dockerfile.api" ]]; then
        log_success "API Dockerfile found: docker/Dockerfile.api"
    else
        log_error "API Dockerfile not found: docker/Dockerfile.api"
        return 1
    fi
    
    if [[ -f "docker/Dockerfile.ui" ]]; then
        log_success "UI Dockerfile found: docker/Dockerfile.ui"
    else
        log_error "UI Dockerfile not found: docker/Dockerfile.ui"
        return 1
    fi
}

check_infrastructure() {
    log_info "Checking infrastructure configuration..."
    
    if [[ -d "infrastructure" ]]; then
        log_success "Infrastructure directory found"
        
        if [[ -f "infrastructure/package.json" ]]; then
            log_success "CDK package.json found"
        else
            log_warning "CDK package.json not found"
        fi
        
        if [[ -f "infrastructure/lib/finbert-rag-stack.ts" ]]; then
            log_success "CDK stack definition found"
        else
            log_warning "CDK stack definition not found"
        fi
    else
        log_warning "Infrastructure directory not found"
    fi
}

check_environment_vars() {
    log_info "Checking environment variables..."
    
    # Check if .env file exists
    if [[ -f ".env" ]]; then
        log_success ".env file found"
        
        # Check for key variables
        if grep -q "ES_CLOUD_HOST" .env; then
            log_success "Elasticsearch configuration found in .env"
        else
            log_warning "Elasticsearch configuration not found in .env"
        fi
    else
        log_warning ".env file not found - will need for deployment"
    fi
}

test_docker_build() {
    log_info "Testing Docker build (dry run)..."
    
    # Test API build
    if docker build -t ecr-test-api -f docker/Dockerfile.api . --dry-run &> /dev/null; then
        log_success "API Docker build validation passed"
    else
        log_warning "API Docker build validation failed (this is a dry-run test)"
    fi
    
    # Clean up any test images
    docker rmi ecr-test-api &> /dev/null || true
}

check_ecr_permissions() {
    log_info "Checking ECR permissions..."
    
    # Test ECR access
    if aws ecr describe-repositories --region ap-south-1 &> /dev/null; then
        log_success "ECR access verified"
    else
        log_warning "ECR access may be limited or region ap-south-1 not accessible"
    fi
}

generate_deployment_summary() {
    echo
    echo "📋 Deployment Configuration Summary"
    echo "=================================="
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "Unknown")
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com"
    
    echo "AWS Account: ${ACCOUNT_ID}"
    echo "ECR Registry: ${ECR_REGISTRY}"
    echo "API Repository: ${ECR_REGISTRY}/finbert-rag/api"
    echo "UI Repository: ${ECR_REGISTRY}/finbert-rag/ui"
    echo "Target Region: ap-south-1"
    echo "ECS Cluster: finbert-rag-prod"
    
    echo
    echo "📝 Next Steps:"
    echo "1. Run: ./scripts/deploy-ecr.sh"
    echo "2. Update GitHub Actions secrets if needed:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - AWS_ACCOUNT_ID"
    echo "3. Trigger production deployment via GitHub Actions"
}

main() {
    echo "🚀 Validating AWS ECR Deployment Prerequisites"
    echo "============================================="
    
    ERROR_COUNT=0
    
    # Run all checks
    check_aws_cli || ((ERROR_COUNT++))
    check_docker || ((ERROR_COUNT++))
    check_aws_credentials || ((ERROR_COUNT++))
    check_git_status || ((ERROR_COUNT++))
    check_docker_files || ((ERROR_COUNT++))
    check_infrastructure
    check_environment_vars
    check_ecr_permissions
    
    echo
    echo "🎯 Validation Summary"
    echo "===================="
    
    if [[ $ERROR_COUNT -eq 0 ]]; then
        log_success "All critical validations passed! ✅"
        log_success "Ready for AWS ECR deployment 🚀"
        
        generate_deployment_summary
        
        echo
        echo "🚀 Ready to deploy? Run:"
        echo "   ./scripts/deploy-ecr.sh"
        
    else
        log_error "${ERROR_COUNT} critical issues found ❌"
        log_error "Please resolve issues before deployment"
        exit 1
    fi
}

# Execute validation
main "$@"