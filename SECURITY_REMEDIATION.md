# 🚨 SECURITY REMEDIATION GUIDE

**CRITICAL**: Hardcoded credentials detected in repository. Immediate action required.

---

## 🔍 **SECURITY ISSUES IDENTIFIED**

### **❌ Critical Issues Found**
1. **Hardcoded API Keys in `.env`**: Real HuggingFace, NewsAPI, Finnhub tokens exposed
2. **Email Credentials**: Subscription emails and passwords in plain text
3. **Elasticsearch Keys**: Production Elasticsearch credentials hardcoded
4. **Repository Risk**: If committed, these would be publicly visible on GitHub

### **✅ Immediate Actions Taken**
1. **Backup Created**: Original `.env` saved as `.env.backup` (NOT committed)
2. **Secure Template**: Created `.env.example` with placeholders
3. **Secure Deployment Script**: `deploy-ecr-secure.sh` with security checks
4. **Git Protection**: Verified `.env` is in `.gitignore`

---

## 🔧 **IMMEDIATE REMEDIATION STEPS**

### **Step 1: Secure Local Environment**
```bash
# 1. Move current .env with real credentials to secure location
mv .env .env.REAL_CREDENTIALS_DO_NOT_COMMIT

# 2. Copy template for development
cp .env.example .env

# 3. Manually edit .env with your actual values (but don't commit)
# Edit only what you need for local development
```

### **Step 2: Verify Git Security**
```bash
# Verify .env is ignored
git status  # Should not show .env as untracked

# Double-check .gitignore
grep -n "\.env" .gitignore  # Should show .env is ignored

# Check what would be committed
git add --dry-run .  # Should NOT include .env
```

### **Step 3: Use Secure Deployment Script**
```bash
# Use the secure version instead of original
./scripts/deploy-ecr-secure.sh  # ✅ SECURE

# NOT this one (has security warnings):
# ./scripts/deploy-ecr.sh  # ⚠️ INSECURE
```

---

## 🔐 **PRODUCTION SECURITY SETUP**

### **AWS Secrets Manager Configuration**

**Create Elasticsearch Secret:**
```bash
aws secretsmanager create-secret \
  --name "finbert-rag/elasticsearch/credentials" \
  --description "Elasticsearch credentials for FinBERT RAG production" \
  --secret-string '{
    "host": "your-real-elasticsearch-host",
    "key": "your-real-elasticsearch-key",
    "index": "news_finbert_embeddings"
  }' \
  --region ap-south-1
```

**Create API Tokens Secret:**
```bash
aws secretsmanager create-secret \
  --name "finbert-rag/api/tokens" \
  --description "API tokens for FinBERT RAG services" \
  --secret-string '{
    "hf_token": "your-real-hf-token",
    "newsapi_key": "your-real-newsapi-key",
    "finnhub_key": "your-real-finnhub-key"
  }' \
  --region ap-south-1
```

### **GitHub Actions Secrets Setup**

**Required GitHub Repository Secrets:**
```bash
# Go to: GitHub Repository → Settings → Secrets and variables → Actions

# Add these secrets:
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key  
AWS_ACCOUNT_ID=322158030810
```

### **ECS Task Definition Update**

**Update task definition to use Secrets Manager:**
```json
{
  "containerDefinitions": [
    {
      "name": "finbert-api",
      "secrets": [
        {
          "name": "ES_CLOUD_HOST",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:322158030810:secret:finbert-rag/elasticsearch/credentials:host::"
        },
        {
          "name": "ES_CLOUD_KEY", 
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:322158030810:secret:finbert-rag/elasticsearch/credentials:key::"
        },
        {
          "name": "HF_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:322158030810:secret:finbert-rag/api/tokens:hf_token::"
        }
      ]
    }
  ]
}
```

---

## 📋 **SECURITY CHECKLIST**

### **✅ Before Deployment**
- [ ] **Verified .env not in git**: `git status` shows no .env
- [ ] **Real credentials secured**: Moved to `.env.REAL_CREDENTIALS_DO_NOT_COMMIT`
- [ ] **Template in use**: Using `.env.example` as base for development
- [ ] **AWS Secrets created**: Production secrets in AWS Secrets Manager
- [ ] **GitHub secrets set**: Repository secrets configured

### **✅ During Deployment**
- [ ] **Use secure script**: `./scripts/deploy-ecr-secure.sh` (NOT the insecure one)
- [ ] **Monitor git commits**: Ensure no credentials in commit history
- [ ] **ECR security scanning**: Verify vulnerability scanning enabled
- [ ] **Environment validation**: Check production uses Secrets Manager

### **✅ After Deployment**
- [ ] **Rotate exposed keys**: Change any credentials that were hardcoded
- [ ] **Monitor access logs**: Check for unauthorized API usage
- [ ] **Security scan images**: Review ECR vulnerability reports
- [ ] **Test secret access**: Verify ECS can retrieve secrets from AWS

---

## 🚨 **CREDENTIAL ROTATION REQUIRED**

**Since credentials were exposed in code, rotate these immediately:**

### **HuggingFace Token**
1. Go to: https://huggingface.co/settings/tokens
2. Delete current token: `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`
3. Create new token with same permissions
4. Update in AWS Secrets Manager

### **NewsAPI Key**
1. Go to: https://newsapi.org/account
2. Regenerate API key: `e3171eae41cf471a9a6fd5a4d63b5470`
3. Update in AWS Secrets Manager

### **Finnhub Key**
1. Go to: https://finnhub.io/dashboard
2. Regenerate API key: `d1e2sh1r01qlt46s93n0d1e2sh1r01qlt46s93ng`
3. Update in AWS Secrets Manager

### **Elasticsearch Credentials**
1. Rotate Elasticsearch API key in your cloud provider
2. Update in AWS Secrets Manager
3. Test connectivity from ECS

---

## 📖 **SECURE DEVELOPMENT PRACTICES**

### **Local Development**
```bash
# ✅ GOOD: Use environment variables
export ES_CLOUD_HOST="your-host"
export ES_CLOUD_KEY="your-key"
./scripts/deploy-ecr-secure.sh

# ❌ BAD: Hardcode in files
echo "ES_CLOUD_KEY=real-key" >> .env
```

### **Production Deployment**
```bash
# ✅ GOOD: AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id "finbert-rag/elasticsearch/credentials"

# ❌ BAD: Environment files with real values
cat > .env.prod << EOF
ES_CLOUD_KEY=real-production-key
EOF
```

---

## 🎯 **SECURE DEPLOYMENT READY**

**After completing security remediation, deploy with:**

```bash
# 1. Verify security
./scripts/validate-ecr-deployment.sh

# 2. Deploy securely  
./scripts/deploy-ecr-secure.sh

# 3. Monitor deployment
# GitHub Actions will handle ECS deployment with secure secrets
```

---

**🔐 SECURITY IS PARAMOUNT - NEVER COMPROMISE ON CREDENTIAL SAFETY! 🔐**