# 🔐 PRODUCTION CREDENTIALS REQUIRED

**Before running `./scripts/setup-aws-secrets.sh`, have these credentials ready:**

---

## 📋 **REQUIRED CREDENTIALS**

### **🔍 Elasticsearch Configuration (REQUIRED)**
```
Elasticsearch Cloud Host: your-deployment.es.region.cloud.es.io
Elasticsearch API Key: your-production-elasticsearch-api-key
Elasticsearch Index: news_finbert_embeddings
```

### **🤗 HuggingFace Token (REQUIRED)**
```
HuggingFace Token: your-production-hf-token
```
*Get from: https://huggingface.co/settings/tokens*

### **📰 Optional API Keys**
```
NewsAPI Key: your-newsapi-key (optional)
Finnhub Key: your-finnhub-key (optional) 
AlphaVantage Key: your-alphavantage-key (optional)
```

---

## 🚀 **EXECUTE DEPLOYMENT**

**Now run the complete deployment sequence:**

```bash
# 1. Set up AWS Secrets Manager (interactive)
./scripts/setup-aws-secrets.sh

# 2. Validate deployment environment
./scripts/validate-ecr-deployment.sh

# 3. Deploy to ECR securely  
./scripts/deploy-ecr-secure.sh
```

---

## 📊 **EXPECTED OUTCOMES**

### **After Step 1 (Secrets Setup)**:
- ✅ AWS Secrets Manager configured with production credentials
- ✅ `ecs-secrets-config.json` generated for ECS integration
- ✅ IAM policies created for ECS secret access

### **After Step 2 (Validation)**:
- ✅ All prerequisites confirmed
- ✅ AWS permissions verified
- ✅ Docker environment validated

### **After Step 3 (ECR Deployment)**:
- ✅ Docker images built and pushed to ECR
- ✅ Git repository tagged with v2.0.0
- ✅ Ready for ECS deployment via GitHub Actions

---

## 🎯 **READY TO PROCEED**

**Your deployment infrastructure is prepared and ready. Execute when you have your production credentials available.**

**Estimated time**: ~30-45 minutes total for complete deployment