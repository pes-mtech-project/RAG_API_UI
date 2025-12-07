# Container Management Scripts

This directory contains scripts for managing Docker containers locally and in production.

## 🚀 AWS ECR Production Deployment Scripts (NEW)

### `validate-ecr-deployment.sh`
**Purpose**: Validates all prerequisites for AWS ECR deployment  
**Usage**: `./scripts/validate-ecr-deployment.sh`  
**Features**:
- Checks AWS CLI configuration and credentials
- Validates Docker installation and daemon status  
- Verifies Git repository status and commits
- Tests Docker build configurations
- Validates ECR permissions and access

### `setup-aws-secrets.sh` ⚡ **PREREQUISITE**
**Purpose**: Set up AWS Secrets Manager for production credentials  
**Usage**: `./scripts/setup-aws-secrets.sh`  
**Features**:
- Interactive credential collection (secure prompts)
- AWS Secrets Manager secret creation and management
- ECS IAM role and policy configuration
- ECS task definition snippet generation
- Secret verification and validation

### `deploy-ecr-secure.sh` 🔐 **RECOMMENDED**
**Purpose**: SECURE AWS ECR production deployment with credential protection  
**Usage**: `./scripts/deploy-ecr-secure.sh`  
**Features**:
- Security scanning for hardcoded credentials
- Automated ECR repository creation with vulnerability scanning
- Docker image building with multi-tag support (latest, v2.0.0, prod)
- Image push to AWS ECR with verification
- Git commit and tag management for release tracking
- Secure environment templating (no credential exposure)
- AWS Secrets Manager integration guidance

## Legacy Scripts

- `build.sh` - Build containers locally with GHCR tags
- `deploy-local.sh` - Deploy containers locally with Docker Compose  
- `release-manager.sh` - Legacy release management (superseded by ECR deployment)
- `test-workflows.sh` - Test GitHub Actions workflows
- `validate-docker-tags.sh` - Validate Docker image tags

## 🎯 Quick Start - ECR Production Deployment

```bash
# 1. PREREQUISITE: Set up AWS Secrets Manager (MUST DO FIRST)
./scripts/setup-aws-secrets.sh

# 2. Validate deployment prerequisites  
./scripts/validate-ecr-deployment.sh



# 3. Deploy to AWS ECR securely (if validation passes)
./scripts/deploy-ecr-secure.sh

# 4. Deploy infrastructure with secrets integration
cd infrastructure && npm run deploy:prod

# 5. GitHub Actions workflow handles ECS deployment automatically
# (Triggered on push to main with ECR images and secrets configured)
```

## Environment Requirements

### AWS ECR Deployment Requirements
- **AWS CLI**: v2.x with configured credentials
- **Docker**: Running Docker daemon  
- **Git**: Repository with clean working directory
- **AWS Permissions**: ECR push/pull, ECS deployment rights
- **Region**: ap-south-1 (Mumbai) configured

### Environment Variables (`.env` file)
```bash
# Elasticsearch Configuration
ES_CLOUD_HOST=your-elasticsearch-host
ES_CLOUD_KEY=your-api-key  
ES_CLOUD_INDEX=news_finbert_embeddings

# AWS Configuration (optional - can use AWS CLI config)
AWS_ACCOUNT_ID=123456789012
AWS_REGION=ap-south-1
```

## 📋 ECR Deployment Architecture

**Image Repositories**:
- `<account-id>.dkr.ecr.ap-south-1.amazonaws.com/finbert-rag/api`
- `<account-id>.dkr.ecr.ap-south-1.amazonaws.com/finbert-rag/ui`

**Image Tags**:
- `latest` - Current production version
- `v2.0.0` - Semantic version (modular architecture)  
- `prod` - Production-ready tag

**GitHub Actions Integration**:
- Workflow: `.github/workflows/production-release-ecr.yml`
- Triggers: Push to main, version tags (v*.*.*), manual dispatch
- Deployment: Automated ECS service updates with ECR images