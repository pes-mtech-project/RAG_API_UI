# GitHub Workflows Documentation

## 🏗️ Workflow Architecture

This repository uses a **dual-environment CI/CD strategy** with separate stacks for development and production:

### 📋 Current Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **Development Stack** | `develop-stack-deployment.yml` | `develop` branch | Development environment deployment |
| **Production Release** | `production-release-ecr.yml` | `main` branch | Production environment deployment |

## 🚀 Development Workflow (`develop` branch)

**File**: `.github/workflows/develop-stack-deployment.yml`

### Triggers:
- Push to `develop` branch
- Pull requests to `develop` branch  
- Manual workflow dispatch

### Pipeline Stages:
1. **🔍 Change Detection**: Detects API, UI, and infrastructure changes
2. **🛡️ Code Quality**: Formatting, linting, security checks
3. **🏗️ Build & Push**: Docker images to ECR development repositories
4. **🚀 ECS Deployment**: Updates development ECS services
5. **🧪 Testing**: Health checks and endpoint validation

### Development Infrastructure:
- **ECR Repositories**: 
  - `finbert-rag/api-dev`
  - `finbert-rag/ui-dev`
- **ECS Cluster**: `finbert-rag-dev-cluster`
- **Services**: 
  - `finbert-api-dev`
  - `finbert-ui-dev`
- **Image Tags**: `dev-YYYYMMDD-HHMMSS-{sha}`

### Features:
- ✅ Intelligent change detection
- ✅ Code quality gates (Black, Flake8, Bandit, Safety)
- ✅ Security scanning
- ✅ Automated testing
- ✅ Separate development infrastructure
- ✅ Health check validation

## 🏭 Production Workflow (`main` branch)

**File**: `.github/workflows/production-release-ecr.yml`

### Triggers:
- Push to `main` branch
- Git tags (`v*.*.*`)
- Manual workflow dispatch

### Pipeline Stages:
1. **🔍 Change Detection**: Production-grade change validation
2. **🏗️ Build & Push**: Docker images to ECR production repositories  
3. **🚀 ECS Deployment**: Updates production ECS services
4. **✅ Validation**: Production health checks and smoke tests

### Production Infrastructure:
- **ECR Repositories**:
  - `finbert-rag/api` 
  - `finbert-rag/ui`
- **ECS Cluster**: `finbert-rag-prod-cluster`
- **Services**:
  - `finbert-api-prod`
  - `finbert-ui-prod` 
- **Image Tags**: `v{version}`, `latest`, `prod`

### Features:
- ✅ Production-grade security
- ✅ Semantic versioning
- ✅ AWS Secrets Manager integration
- ✅ Multi-environment support
- ✅ Comprehensive validation
- ✅ Rollback capabilities

## 🔄 Branch Strategy

```
develop ────► Development Stack (dev-cluster)
    │
    ├── PR ──► Code Review
    │
    ▼
main ────────► Production Stack (prod-cluster)
```

### Workflow:
1. **Feature Development**: Work on `develop` branch
2. **Automatic Deployment**: Changes deploy to development environment
3. **Testing & Validation**: Test in development environment  
4. **Pull Request**: Create PR from `develop` to `main`
5. **Production Deployment**: Merge triggers production deployment

## 🔐 Required Secrets

### AWS Configuration:
- `AWS_ACCESS_KEY_ID`: AWS access key for ECR and ECS
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_ACCOUNT_ID`: AWS account ID for ECR registry

### Application Secrets:
- `ELASTICSEARCH_HOST`: Elasticsearch endpoint
- `ELASTICSEARCH_API_KEY`: Elasticsearch credentials
- `HUGGINGFACE_TOKEN`: HuggingFace API token

## 📊 Monitoring & Debugging

### Workflow Status:
- **Development**: Monitor develop branch workflow runs
- **Production**: Monitor main branch workflow runs

### Common Issues:
1. **Build Failures**: Check Docker build logs
2. **Deployment Failures**: Verify AWS credentials and ECS configuration
3. **Health Check Failures**: Check application logs in ECS

### Debugging Commands:
```bash
# Check ECS service status
aws ecs describe-services --cluster {cluster-name} --services {service-name}

# View ECS task logs  
aws logs get-log-events --log-group-name /ecs/{service-name}

# Check ECR images
aws ecr describe-images --repository-name {repo-name}
```

## 🏷️ Version Management

### Development Versions:
- Format: `dev-YYYYMMDD-HHMMSS-{short-sha}`
- Example: `dev-20251004-142530-a1b2c3d4`

### Production Versions:
- Format: `v{major}.{minor}.{patch}`
- Example: `v2.1.0`
- Also tagged as: `latest`, `prod`

## 🛠️ Manual Operations

### Force Deployment:
```bash
# Development
gh workflow run develop-stack-deployment.yml --ref develop -f force_deploy=true

# Production  
gh workflow run production-release-ecr.yml --ref main -f force_deploy=true
```

### Emergency Rollback:
```bash
# Rollback to previous version
aws ecs update-service --cluster {cluster} --service {service} --task-definition {previous-task-def}
```

## 📈 Performance & Optimization

### Build Optimization:
- ✅ Docker layer caching
- ✅ Multi-stage builds
- ✅ Change detection to skip unnecessary builds

### Deployment Optimization:
- ✅ Parallel service updates
- ✅ Health check integration
- ✅ Rollback on failure

---

**For additional help, refer to the AWS ECS and ECR documentation, or check the workflow run logs in GitHub Actions.**