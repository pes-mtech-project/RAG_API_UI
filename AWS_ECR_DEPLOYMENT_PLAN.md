# AWS ECR Production Deployment Plan

**Date**: October 4, 2025  
**Project**: FinBERT News RAG Application  
**Version**: 2.0 (Modular Architecture Release)  
**Target**: AWS ECR + ECS Production Deployment

---

## 🎯 **Deployment Overview**

### **Current State Analysis**
- ✅ **Modular Architecture**: Complete SOLID principles refactor implemented
- ✅ **Model Caching**: 4.9x performance improvement with persistent storage
- ✅ **Multi-Embedding**: 384d, 768d, 1155d dimensional search endpoints
- ✅ **Testing Validated**: 138 requests, 100% success rate, sub-second responses
- ✅ **Docker Optimized**: Container builds working locally
- 🔄 **Git Status**: 1 commit ahead of origin/main (needs push)

### **Deployment Target**
- **Registry**: AWS ECR (Elastic Container Registry)
- **Orchestration**: AWS ECS Fargate
- **Environment**: Production (replacing current GHCR setup)
- **Region**: ap-south-1 (Mumbai)
- **Load Balancer**: Application Load Balancer with SSL

---

## 📋 **Pre-Deployment Checklist**

### **✅ Code Preparation**
- [x] Modular architecture implementation complete
- [x] Model caching optimization implemented
- [x] Comprehensive testing suite validated
- [x] Documentation updated
- [ ] **REQUIRED**: Push latest changes to origin/main
- [ ] **REQUIRED**: Create production release tag

### **🔧 Infrastructure Requirements**
- [ ] **AWS ECR Repository Setup**
- [ ] **ECS Cluster Configuration**
- [ ] **Task Definition Updates**
- [ ] **Environment Variables Migration**
- [ ] **Load Balancer Configuration**

### **🔐 Security & Access**
- [ ] **AWS CLI Configuration**
- [ ] **ECR Push Permissions**
- [ ] **ECS Deployment Permissions**
- [ ] **Environment Secrets Management**

---

## 🚀 **Phase 1: Pre-Deployment Setup**

### **Step 1.1: Git Repository Sync**
```bash
# Push latest modular architecture changes
git status
git add .
git commit -m "🚀 PRODUCTION: Modular architecture v2.0 with model caching"
git push origin main

# Create production release tag
git tag -a v2.0.0 -m "Production Release: Modular Architecture with Model Caching
- Multi-dimensional embedding search (384d, 768d, 1155d)
- 4.9x performance improvement with model caching
- SOLID principles architecture implementation
- 100% success rate across 138 test requests"

git push origin v2.0.0
```

### **Step 1.2: AWS ECR Repository Creation**
```bash
# Create ECR repositories for both services
aws ecr create-repository \
  --repository-name finbert-rag/api \
  --region ap-south-1 \
  --image-scanning-configuration scanOnPush=true

aws ecr create-repository \
  --repository-name finbert-rag/ui \
  --region ap-south-1 \
  --image-scanning-configuration scanOnPush=true

# Get repository URIs
aws ecr describe-repositories --region ap-south-1 --query 'repositories[*].repositoryUri'
```

### **Step 1.3: Docker Registry Migration**
```bash
# Login to AWS ECR
aws ecr get-login-password --region ap-south-1 | \
docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com

# Set ECR variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com"
export ECR_API_REPO="${ECR_REGISTRY}/finbert-rag/api"
export ECR_UI_REPO="${ECR_REGISTRY}/finbert-rag/ui"
```

### **Step 1.4: AWS Secrets Manager Configuration**
```bash
# Create (or update) Elasticsearch credentials secret
cat <<'JSON' > es-prod.json
{
  "host": "https://your-elasticsearch-cluster.es.amazonaws.com:443",
  "key": "base64_encoded_api_key",
  "index": "news_finbert_embeddings"
}
JSON

aws secretsmanager create-secret \
  --name finbert-rag/elasticsearch/credentials \
  --description "FinBERT Elasticsearch credentials" \
  --secret-string file://es-prod.json \
  --region ap-south-1

# Create API token secret (HuggingFace, etc.)
cat <<'JSON' > api-tokens.json
{
  "huggingface_token": "hf_xxx"
}
JSON

aws secretsmanager create-secret \
  --name finbert-rag/api/tokens \
  --description "FinBERT API tokens" \
  --secret-string file://api-tokens.json \
  --region ap-south-1

# Grant ECS task execution role read access to the secrets
aws iam attach-role-policy \
  --role-name FinBertRagProdStack-FinBertExecutionRoleXXXXXXXX \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```
> Replace the execution role name with the value from `aws ecs describe-task-definition`.  
> For tighter security, prefer a custom policy that only allows `secretsmanager:GetSecretValue` on the specific ARNs.

---

## 🏗️ **Phase 2: Container Build & Push**

### **Step 2.1: Build Production Images**
```bash
# Build API with modular architecture
docker build -t ${ECR_API_REPO}:latest \
  -t ${ECR_API_REPO}:v2.0.0 \
  -t ${ECR_API_REPO}:prod \
  -f docker/Dockerfile.api .

# Build UI service
docker build -t ${ECR_UI_REPO}:latest \
  -t ${ECR_UI_REPO}:v2.0.0 \
  -t ${ECR_UI_REPO}:prod \
  -f docker/Dockerfile.ui .

# Verify images
docker images | grep finbert-rag
```

### **Step 2.2: Push to ECR**
```bash
# Push API images with all tags
docker push ${ECR_API_REPO}:latest
docker push ${ECR_API_REPO}:v2.0.0
docker push ${ECR_API_REPO}:prod

# Push UI images with all tags
docker push ${ECR_UI_REPO}:latest
docker push ${ECR_UI_REPO}:v2.0.0
docker push ${ECR_UI_REPO}:prod

# Verify push successful
aws ecr list-images --repository-name finbert-rag/api --region ap-south-1
aws ecr list-images --repository-name finbert-rag/ui --region ap-south-1
```

---

## 🔧 **Phase 3: Infrastructure Configuration**

### **Step 3.1: Update GitHub Workflows for ECR**

**Update `.github/workflows/production-release.yml`:**
```yaml
env:
  REGISTRY: <account-id>.dkr.ecr.ap-south-1.amazonaws.com
  API_IMAGE_NAME: finbert-rag/api
  UI_IMAGE_NAME: finbert-rag/ui
  AWS_REGION: ap-south-1
```

**Update workflow authentication:**
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ap-south-1

- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2
```

### **Step 3.2: Update CDK Infrastructure**

**Update `infrastructure/lib/finbert-rag-stack.ts`:**
```typescript
// Update container image references
const apiImage = ecs.ContainerImage.fromEcrRepository(
  ecr.Repository.fromRepositoryName(this, 'ApiRepo', 'finbert-rag/api'),
  'latest'
);

const uiImage = ecs.ContainerImage.fromEcrRepository(
  ecr.Repository.fromRepositoryName(this, 'UiRepo', 'finbert-rag/ui'),
  'latest'
);
```

### **Step 3.3: Environment Variables Migration**
```bash
# Create production environment file
cat > .env.prod << EOF
# Production ECR Configuration
REGISTRY=${ECR_REGISTRY}
API_IMAGE=${ECR_API_REPO}:latest
UI_IMAGE=${ECR_UI_REPO}:latest

# Application Configuration
API_PORT=8000
UI_PORT=8501
ENVIRONMENT=production

# Elasticsearch Configuration (from existing secrets)
ES_CLOUD_HOST=${ES_CLOUD_HOST}
ES_CLOUD_KEY=${ES_CLOUD_KEY}
ES_CLOUD_INDEX=${ES_CLOUD_INDEX}
EOF
```

---

## 🚀 **Phase 4: Production Deployment**

### **Step 4.1: Deploy Infrastructure**
```bash
# Navigate to infrastructure directory
cd infrastructure

# Install dependencies
npm install

# Synthesize CloudFormation template
npm run synth

# Deploy to production
npm run deploy:prod

# Verify deployment
aws ecs list-clusters --region ap-south-1
aws ecs list-services --cluster finbert-rag-prod --region ap-south-1
```

### **Step 4.2: Update ECS Task Definition**
```bash
# Create new task definition with ECR images
aws ecs register-task-definition \
  --cli-input-json file://task-definition-prod.json \
  --region ap-south-1

# Update service with new task definition
aws ecs update-service \
  --cluster finbert-rag-prod \
  --service finbert-rag-service \
  --task-definition finbert-rag-task:LATEST \
  --region ap-south-1
```

### **Step 4.3: Monitor Deployment**
```bash
# Watch service deployment
aws ecs wait services-stable \
  --cluster finbert-rag-prod \
  --services finbert-rag-service \
  --region ap-south-1

# Check service status
aws ecs describe-services \
  --cluster finbert-rag-prod \
  --services finbert-rag-service \
  --region ap-south-1 \
  --query 'services[0].deployments'

# Monitor task health
aws ecs list-tasks \
  --cluster finbert-rag-prod \
  --service-name finbert-rag-service \
  --region ap-south-1
```

---

## 🧪 **Phase 5: Production Validation**

### **Step 5.1: Health Check Validation**
```bash
# Get load balancer DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region ap-south-1)

# Test health endpoint
curl https://${ALB_DNS}/health

# Expected response:
# {
#   "status": "healthy",
#   "api": "operational",
#   "elasticsearch": "green",
#   "model_cache": {
#     "cached_models": [...],
#     "loaded_models": []
#   }
# }
```

### **Step 5.2: API Endpoint Testing**
```bash
# Test 384d embedding search
curl -X POST "https://${ALB_DNS}/search/cosine/embedding384d/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence investment",
    "size": 3
  }'

# Test 768d embedding search
curl -X POST "https://${ALB_DNS}/search/cosine/embedding768d/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sovereign debt instruments",
    "size": 3
  }'

# Test 1155d enhanced search
curl -X POST "https://${ALB_DNS}/search/cosine/embedding1155d/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial market analysis",
    "size": 3
  }'
```

### **Step 5.3: Performance Validation**
```bash
# Run production performance test
time curl -X POST "https://${ALB_DNS}/search/cosine/embedding384d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "test performance", "size": 1}'

# Expected: < 0.5s response time
# Expected: 100% success rate
# Expected: Model caching working (no download logs)
```

---

## 📊 **Phase 6: Monitoring & Rollback Plan**

### **Step 6.1: Set Up Monitoring**
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "FinBERT-RAG-Production" \
  --dashboard-body file://monitoring-dashboard.json \
  --region ap-south-1

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "FinBERT-API-High-Error-Rate" \
  --alarm-description "API error rate > 5%" \
  --metric-name "4XXError" \
  --namespace "AWS/ApplicationELB" \
  --statistic "Sum" \
  --period 300 \
  --threshold 5 \
  --comparison-operator "GreaterThanThreshold" \
  --region ap-south-1
```

### **Step 6.2: Rollback Plan**
```bash
# Emergency rollback to previous GHCR version
aws ecs update-service \
  --cluster finbert-rag-prod \
  --service finbert-rag-service \
  --task-definition finbert-rag-task:PREVIOUS \
  --region ap-south-1

# Or rollback to specific stable version
docker pull ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:v1.2.0
docker tag ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api:v1.2.0 ${ECR_API_REPO}:rollback
docker push ${ECR_API_REPO}:rollback
```

---

## 🔐 **Security Considerations**

### **ECR Security**
- ✅ **Image Scanning**: Enabled on push
- ✅ **Repository Policies**: Restrict access to specific IAM roles
- ✅ **Encryption**: Images encrypted at rest
- ✅ **Lifecycle Policies**: Automatic cleanup of old images

### **ECS Security** 
- ✅ **Task Execution Role**: Minimal permissions
- ✅ **Security Groups**: Restrict network access
- ✅ **Secrets Management**: Environment variables from AWS Secrets Manager
- ✅ **VPC Configuration**: Private subnets with NAT gateway

---

## 📅 **Deployment Timeline**

| Phase | Duration | Dependencies |
|-------|----------|-------------|
| **Pre-Deployment** | 30 min | Git sync, ECR setup |
| **Container Build** | 45 min | Docker builds, ECR push |
| **Infrastructure** | 20 min | CDK updates, workflow changes |
| **Deployment** | 15 min | ECS service update |
| **Validation** | 30 min | Health checks, performance testing |
| **Total** | **~2.5 hours** | End-to-end deployment |

---

## ✅ **Success Criteria**

### **Technical Validation**
- [ ] All containers pushed to ECR successfully
- [ ] ECS service running with desired task count
- [ ] Load balancer health checks passing
- [ ] All API endpoints responding < 0.5s
- [ ] Model caching working (no downloads in logs)
- [ ] 100% success rate on test requests

### **Performance Validation**
- [ ] 384d endpoint: < 0.25s average response
- [ ] 768d endpoint: < 0.30s average response  
- [ ] 1155d endpoint: < 0.40s average response
- [ ] Concurrent load: > 4 requests/second
- [ ] Model cache: 4.9x speedup maintained

### **Security Validation**
- [ ] HTTPS endpoints accessible
- [ ] HTTP traffic redirected to HTTPS
- [ ] Environment secrets properly configured
- [ ] No sensitive data in container logs

---

## 🚨 **Risk Mitigation**

### **High-Risk Items**
1. **Model Cache Migration**: Ensure persistent volume properly configured
2. **Environment Variables**: Verify all Elasticsearch credentials migrated
3. **Performance Impact**: Monitor response times during initial load
4. **DNS Propagation**: Allow time for load balancer DNS updates

### **Contingency Plans**
1. **Immediate Rollback**: Keep GHCR images as backup
2. **Performance Issues**: Scale ECS tasks horizontally
3. **Cache Problems**: Pre-warm models during deployment
4. **Network Issues**: Validate security group rules

---

**🎯 Ready for AWS ECR Production Deployment - Modular Architecture v2.0**

*This plan ensures zero-downtime deployment of the enhanced FinBERT RAG application with comprehensive validation and rollback capabilities.*
