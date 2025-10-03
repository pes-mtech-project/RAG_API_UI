# 🚀 Production Release & Deployment Guide

## Overview

This document outlines the production-ready workflow for the FinBERT News RAG application, including version management, container deployment, and release automation.

## 🎯 Release Strategy

### Branch Strategy
- **`main`**: Production-ready code, triggers production deployments
- **`develop`**: Development integration, triggers dev environment deployments  
- **`feature/*`**: Feature branches, no automatic deployments

### Versioning
- **Semantic Versioning**: `MAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- **Automatic Tagging**: Production workflow creates tags automatically
- **Container Tags**: Multiple tags per version for flexibility

## 🔧 Quick Start

### 1. Prepare for Release
```bash
# Check current status
./scripts/release-manager.sh status

# Prepare current branch for main merge
./scripts/release-manager.sh prepare
```

### 2. Create Production Release
```bash
# Patch release (1.2.3 → 1.2.4)
./scripts/release-manager.sh release patch

# Minor release (1.2.3 → 1.3.0)  
./scripts/release-manager.sh release minor

# Major release (1.2.3 → 2.0.0)
./scripts/release-manager.sh release major

# Custom version
./scripts/release-manager.sh release custom 2.1.5
```

### 3. Monitor Deployment
```bash
# Check deployment status
./scripts/release-manager.sh deployment

# View workflow progress on GitHub
gh run list --workflow="production-release.yml"
```

## 📦 Container Strategy

### Multi-Tag Approach
Each production build creates multiple tags:

```bash
# Version-specific tags
ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:1.2.3
ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:v1.2.3

# Environment tags  
ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:latest
ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:prod

# Build-specific tags
ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:prod-abc1234
```

### Container Features
- **Multi-stage builds** for optimized size
- **Security scanning** with vulnerability checks
- **Health checks** for container orchestration
- **Non-root users** for security
- **Build metadata** embedded in images

## 🚀 Deployment Workflows

### Production Release Workflow
**File**: `.github/workflows/production-release.yml`

**Triggers**:
- Push to `main` branch
- Version tags (`v*.*.*`)
- Manual dispatch with version input

**Steps**:
1. **Version Management**: Auto-increment or manual version
2. **Validation**: Docker files, infrastructure, environment
3. **Build & Push**: Multi-tag container images
4. **Deploy**: AWS ECS via CDK with rolling updates
5. **Release**: GitHub release with automated notes
6. **Notification**: Success/failure status

### Development Workflow  
**File**: `.github/workflows/development.yml`

**Triggers**:
- Push to non-main branches
- Pull requests to main/develop

**Features**:
- Code quality checks (flake8, black, isort)
- Security scanning
- Documentation validation
- Container build testing

### ECS Development Deployment
**File**: `.github/workflows/ecs-deployment.yml`

**Triggers**:
- Push to `develop` branch
- Manual dispatch

**Features**:
- Change detection (only deploy when needed)
- Development environment deployment
- Infrastructure updates

## 🏗️ Infrastructure

### AWS ECS Deployment
- **Cluster**: `finbert-rag-prod`
- **Service**: Auto-scaling with health checks
- **Load Balancer**: Application Load Balancer with SSL
- **Logging**: CloudWatch logs with structured logging
- **Monitoring**: ECS metrics and alarms

### CDK Infrastructure
```bash
cd infrastructure

# Deploy production
npm run deploy:prod

# Deploy development  
npm run deploy:dev

# View changes
npm run diff
```

## 📋 Pre-Release Checklist

### Code Quality
- [ ] All tests pass
- [ ] Code review completed
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Breaking changes documented

### Infrastructure  
- [ ] Infrastructure changes tested
- [ ] Secrets/environment variables updated
- [ ] Monitoring/alerting configured
- [ ] Backup strategy verified

### Deployment
- [ ] Container builds successfully
- [ ] Health checks pass
- [ ] Performance benchmarks met
- [ ] Rollback plan ready

## 🔍 Monitoring & Validation

### Automated Checks
```bash
# Health check endpoint
curl -f https://your-domain.com/health

# Semantic search validation
curl -X POST https://your-domain.com/search \
  -H "Content-Type: application/json" \
  -d '{"query": "federal reserve interest rates", "limit": 3}'
```

### Performance Metrics
- **Response Time**: < 2s for search queries
- **Availability**: > 99.9% uptime
- **Search Quality**: Semantic scores > 1.0
- **Resource Usage**: CPU < 80%, Memory < 85%

## 🚨 Troubleshooting

### Common Issues

#### 1. Container Build Failures
```bash
# Check Docker files
docker build -f docker/Dockerfile.api .

# Validate syntax
docker run --rm -i hadolint/hadolint < docker/Dockerfile.api
```

#### 2. Deployment Failures  
```bash
# Check ECS service status
aws ecs describe-services --cluster finbert-rag-prod --services finbert-api

# View logs
aws logs tail /ecs/finbert-api-prod --follow
```

#### 3. Health Check Failures
```bash
# Check container health
docker exec <container_id> curl -f http://localhost:8000/health

# Check Elasticsearch connection
docker exec <container_id> curl -f $ES_READONLY_HOST/_cluster/health
```

### Emergency Procedures

#### Rollback to Previous Version
```bash
# Via GitHub CLI
gh workflow run "production-release.yml" \
  -f version="1.2.2" \
  -f environment="prod" \
  -f force_deploy="true"

# Via AWS ECS Console
# 1. Go to ECS → Clusters → finbert-rag-prod
# 2. Update service with previous task definition
```

#### Hotfix Process
```bash
# Create hotfix branch from main
git checkout main
git pull origin main  
git checkout -b hotfix/critical-fix

# Make changes, test, commit
git add .
git commit -m "hotfix: critical issue fix"
git push origin hotfix/critical-fix

# Create PR to main, merge, then release
./scripts/release-manager.sh release patch
```

## 📚 Additional Resources

### GitHub Actions
- [Workflow Files](.github/workflows/)
- [Action Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)

### AWS Resources
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [ALB Health Checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)

### Container Registry
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Package Management](https://github.com/orgs/pes-mtech-project/packages)

## 🎉 Success Metrics

A successful production release should achieve:

- ✅ **Zero-downtime deployment** with rolling updates
- ✅ **Semantic search active** with scores > 1.0  
- ✅ **Health checks passing** within 2 minutes
- ✅ **Performance maintained** or improved
- ✅ **Monitoring active** with alerts configured
- ✅ **Rollback ready** if issues detected

---

**Questions or Issues?** Check the [troubleshooting section](#-troubleshooting) or create an issue in the repository.