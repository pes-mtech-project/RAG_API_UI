#!/bin/bash

# 🔐 AWS Secrets Manager Setup for FinBERT RAG Production
# PREREQUISITE: Run this script BEFORE ECR deployment
# Creates and configures all required secrets for production deployment

set -e

echo "🔐 AWS Secrets Manager Setup for FinBERT RAG Production"
echo "======================================================"

# Configuration
AWS_REGION="ap-south-1"
PROJECT_NAME="finbert-rag"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_security() { echo -e "${YELLOW}[🔐]${NC} $1"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install with: brew install awscli"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
    
    # Check permissions
    log_info "Checking Secrets Manager permissions..."
    if ! aws secretsmanager list-secrets --region ${AWS_REGION} &> /dev/null; then
        log_error "Missing Secrets Manager permissions. Required: secretsmanager:*"
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

prompt_for_credentials() {
    log_security "CREDENTIAL COLLECTION - Enter your production credentials"
    log_warning "These will be stored securely in AWS Secrets Manager"
    echo

    # Elasticsearch Credentials
    echo "🔍 Elasticsearch Configuration:"
    read -p "Elasticsearch Cloud Host (e.g., your-deployment.es.us-east1.gcp.cloud.es.io): " ES_HOST
    read -s -p "Elasticsearch API Key: " ES_KEY
    echo
    read -p "Elasticsearch Index Name [news_finbert_embeddings]: " ES_INDEX
    ES_INDEX=${ES_INDEX:-"news_finbert_embeddings"}
    echo

    # HuggingFace Token
    echo "🤗 HuggingFace Configuration:"
    read -s -p "HuggingFace Token (from https://huggingface.co/settings/tokens): " HF_TOKEN
    echo
    echo

    # Optional API Keys
    echo "📰 Optional API Keys (press Enter to skip):"
    read -p "NewsAPI Key (optional): " NEWSAPI_KEY
    read -p "Finnhub API Key (optional): " FINNHUB_KEY
    read -p "AlphaVantage API Key (optional): " ALPHAVANTAGE_KEY
    echo

    # Validate required fields
    if [[ -z "$ES_HOST" || -z "$ES_KEY" || -z "$HF_TOKEN" ]]; then
        log_error "Required fields missing. Elasticsearch host, key, and HuggingFace token are mandatory."
        exit 1
    fi

    log_success "Credentials collected successfully"
}

create_elasticsearch_secret() {
    log_info "Creating Elasticsearch credentials secret..."
    
    SECRET_NAME="${PROJECT_NAME}/elasticsearch/credentials"
    SECRET_VALUE=$(cat <<EOF
{
    "host": "${ES_HOST}",
    "key": "${ES_KEY}",
    "index": "${ES_INDEX}"
}
EOF
)

    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "${SECRET_NAME}" --region ${AWS_REGION} &> /dev/null; then
        log_warning "Secret ${SECRET_NAME} already exists. Updating..."
        aws secretsmanager update-secret \
            --secret-id "${SECRET_NAME}" \
            --secret-string "${SECRET_VALUE}" \
            --region ${AWS_REGION} > /dev/null
        log_success "Elasticsearch secret updated"
    else
        aws secretsmanager create-secret \
            --name "${SECRET_NAME}" \
            --description "Elasticsearch credentials for FinBERT RAG production deployment" \
            --secret-string "${SECRET_VALUE}" \
            --region ${AWS_REGION} > /dev/null
        log_success "Elasticsearch secret created: ${SECRET_NAME}"
    fi
}

create_api_tokens_secret() {
    log_info "Creating API tokens secret..."
    
    SECRET_NAME="${PROJECT_NAME}/api/tokens"
    SECRET_VALUE=$(cat <<EOF
{
    "hf_token": "${HF_TOKEN}",
    "huggingface_token": "${HF_TOKEN}",
    "newsapi_key": "${NEWSAPI_KEY:-""}",
    "finnhub_key": "${FINNHUB_KEY:-""}",
    "alphavantage_key": "${ALPHAVANTAGE_KEY:-""}"
}
EOF
)

    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "${SECRET_NAME}" --region ${AWS_REGION} &> /dev/null; then
        log_warning "Secret ${SECRET_NAME} already exists. Updating..."
        aws secretsmanager update-secret \
            --secret-id "${SECRET_NAME}" \
            --secret-string "${SECRET_VALUE}" \
            --region ${AWS_REGION} > /dev/null
        log_success "API tokens secret updated"
    else
        aws secretsmanager create-secret \
            --name "${SECRET_NAME}" \
            --description "API tokens for FinBERT RAG services" \
            --secret-string "${SECRET_VALUE}" \
            --region ${AWS_REGION} > /dev/null
        log_success "API tokens secret created: ${SECRET_NAME}"
    fi
}

create_ecs_execution_role_policy() {
    log_info "Creating ECS execution role policy for Secrets Manager access..."
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    POLICY_NAME="FinBertRagSecretsManagerPolicy"
    
    POLICY_DOCUMENT=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/elasticsearch/credentials*",
                "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/api/tokens*"
            ]
        }
    ]
}
EOF
)

    # Check if policy exists
    if aws iam get-policy --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" &> /dev/null; then
        log_warning "Policy ${POLICY_NAME} already exists. Updating..."
        aws iam create-policy-version \
            --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" \
            --policy-document "${POLICY_DOCUMENT}" \
            --set-as-default > /dev/null
        log_success "IAM policy updated"
    else
        aws iam create-policy \
            --policy-name "${POLICY_NAME}" \
            --policy-document "${POLICY_DOCUMENT}" \
            --description "Allows ECS tasks to access FinBERT RAG secrets" > /dev/null
        log_success "IAM policy created: ${POLICY_NAME}"
    fi

    # Attach to ECS execution role (if it exists)
    ECS_ROLE_NAME="ecsTaskExecutionRole"
    if aws iam get-role --role-name "${ECS_ROLE_NAME}" &> /dev/null; then
        aws iam attach-role-policy \
            --role-name "${ECS_ROLE_NAME}" \
            --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" 2>/dev/null || true
        log_success "Policy attached to ECS execution role"
    else
        log_warning "ECS execution role not found. Will need to attach policy during infrastructure setup."
    fi
}

generate_ecs_task_definition_snippet() {
    log_info "Generating ECS task definition snippet..."
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    
    cat > ecs-secrets-config.json << EOF
{
  "secrets": [
    {
      "name": "ES_CLOUD_HOST",
      "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/elasticsearch/credentials:host::"
    },
    {
      "name": "ES_CLOUD_KEY",
      "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/elasticsearch/credentials:key::"
    },
    {
      "name": "ES_CLOUD_INDEX",
      "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/elasticsearch/credentials:index::"
    },
    {
      "name": "HF_TOKEN",
      "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/api/tokens:hf_token::"
    },
    {
      "name": "HUGGINGFACE_TOKEN",
      "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/api/tokens:huggingface_token::"
    }
  ]
}
EOF

    log_success "ECS task definition snippet created: ecs-secrets-config.json"
}

verify_secrets() {
    log_info "Verifying secrets were created successfully..."
    
    # Test Elasticsearch secret
    if aws secretsmanager get-secret-value \
        --secret-id "${PROJECT_NAME}/elasticsearch/credentials" \
        --region ${AWS_REGION} &> /dev/null; then
        log_success "Elasticsearch secret accessible ✓"
    else
        log_error "Elasticsearch secret not accessible ✗"
        exit 1
    fi
    
    # Test API tokens secret
    if aws secretsmanager get-secret-value \
        --secret-id "${PROJECT_NAME}/api/tokens" \
        --region ${AWS_REGION} &> /dev/null; then
        log_success "API tokens secret accessible ✓"
    else
        log_error "API tokens secret not accessible ✗"
        exit 1
    fi
    
    log_success "All secrets verified successfully!"
}

display_summary() {
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    
    echo
    echo "🎉 AWS Secrets Manager Setup Complete!"
    echo "======================================"
    
    echo
    echo "📋 Created Secrets:"
    echo "  ✅ ${PROJECT_NAME}/elasticsearch/credentials"
    echo "  ✅ ${PROJECT_NAME}/api/tokens"
    
    echo
    echo "🔐 Secret ARNs:"
    echo "  📍 Elasticsearch: arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/elasticsearch/credentials"
    echo "  📍 API Tokens: arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:${PROJECT_NAME}/api/tokens"
    
    echo
    echo "📄 Files Created:"
    echo "  📋 ecs-secrets-config.json - ECS task definition snippet"
    
    echo
    echo "✅ Next Steps:"
    echo "  1. Review generated ecs-secrets-config.json"
    echo "  2. Run ECR deployment: ./scripts/deploy-ecr-secure.sh"
    echo "  3. Update ECS task definition to use secrets"
    echo "  4. Deploy infrastructure: cd infrastructure && npm run deploy:prod"
    
    echo
    log_success "🚀 Ready for secure production deployment!"
}

main() {
    echo "🔐 Setting up AWS Secrets Manager for FinBERT RAG Production"
    echo "==========================================================="
    
    check_prerequisites
    
    echo
    log_security "This script will create secure storage for your production credentials"
    log_warning "Ensure you have your Elasticsearch and HuggingFace credentials ready"
    
    echo
    read -p "Continue with secrets setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Setup cancelled by user"
        exit 0
    fi
    
    prompt_for_credentials
    create_elasticsearch_secret
    create_api_tokens_secret
    create_ecs_execution_role_policy
    generate_ecs_task_definition_snippet
    verify_secrets
    display_summary
}

# Execute main function
main "$@"