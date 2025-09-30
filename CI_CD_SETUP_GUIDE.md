# 🚀 **Complete CI/CD Setup Guide for FinBERT News RAG App**

**Repository**: https://github.com/pes-mtech-project/RAG_API_UI  
**Target**: AWS EC2 deployment with GitHub Actions

## 📋 **What We've Created**

### **1. GitHub Actions Workflows**

#### **🔄 `.github/workflows/deploy.yml` - Main Deployment Pipeline**
- **Triggers**: Push to main, PRs, manual dispatch
- **Stages**: Test → Build → Deploy → Notify
- **Features**:
  - ✅ Dependency validation
  - ✅ Import testing
  - ✅ Automated EC2 deployment
  - ✅ Health checks
  - ✅ Service management (systemd)

#### **🏗️ `.github/workflows/infrastructure.yml` - AWS Setup**
- **Purpose**: Create/destroy AWS infrastructure
- **Features**:
  - ✅ EC2 t2.micro instance
  - ✅ Security groups with proper ports
  - ✅ Nginx reverse proxy setup
  - ✅ Auto-install Python 3.11 & dependencies

#### **🔍 `.github/workflows/development.yml` - Development Checks**
- **Triggers**: Feature branches, PRs
- **Features**:
  - ✅ Code quality (flake8, black, isort)
  - ✅ Security scanning (bandit, safety)
  - ✅ Dependency analysis
  - ✅ Performance testing
  - ✅ Integration testing

## 🎯 **Step-by-Step Setup Instructions**

### **Phase 1: GitHub Repository Setup** ✅ **COMPLETED**

Your repo is already set up at: https://github.com/pes-mtech-project/RAG_API_UI

### **Phase 2: AWS Account Preparation**

1. **Create AWS Account** (if not done)
   - Sign up for AWS Free Tier
   - Verify email and add payment method

2. **Create IAM User for GitHub Actions**
   ```bash
   # Go to AWS Console → IAM → Users → Create User
   Username: github-actions-finbert-rag
   
   # Attach policies:
   - AmazonEC2FullAccess
   - ElasticLoadBalancingFullAccess (if using ALB)
   ```

3. **Generate Access Keys**
   ```bash
   # Save these securely - you'll need them for GitHub Secrets
   AWS_ACCESS_KEY_ID: AKIA...
   AWS_SECRET_ACCESS_KEY: xyz...
   ```

### **Phase 3: GitHub Secrets Configuration**

Add these secrets in GitHub: `Settings → Secrets and variables → Actions`

#### **Required Secrets:**
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xyz...

# Will be generated after infrastructure setup
EC2_INSTANCE_ID=i-1234567890abcdef0
EC2_HOST=54.123.45.67

# SSH Key (will be generated)
EC2_SSH_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
...
```

#### **Optional Secrets:**
```bash
# For Slack notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### **Phase 4: Infrastructure Deployment**

1. **Run Infrastructure Setup**
   ```bash
   # Go to GitHub → Actions → "Setup AWS Infrastructure"
   # Click "Run workflow" → Set destroy: false → Run
   ```

2. **Collect Generated Information**
   - Check workflow output for:
     - `EC2_INSTANCE_ID`
     - `EC2_HOST` (Public IP)
     - SSH private key (if generated)

3. **Add Missing Secrets**
   - Add the generated values to GitHub Secrets

### **Phase 5: Application Deployment**

1. **Trigger Deployment**
   ```bash
   git add .
   git commit -m "Add CI/CD workflows and deployment configuration"
   git push origin main
   ```

2. **Monitor Deployment**
   - Go to GitHub → Actions tab
   - Watch "Deploy to AWS EC2" workflow
   - Check each stage: Test → Build → Deploy

### **Phase 6: Post-Deployment Setup**

1. **SSH into EC2 (one-time setup)**
   ```bash
   ssh -i finbert-rag-key.pem ec2-user@YOUR_EC2_HOST
   
   # Create systemd services (this will be automated)
   sudo tee /etc/systemd/system/finbert-api.service > /dev/null <<EOF
   [Unit]
   Description=FinBERT RAG API
   After=network.target
   
   [Service]
   Type=exec
   User=ec2-user
   WorkingDirectory=/home/ec2-user/finbert-news-rag-app/api
   Environment=PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin
   ExecStart=/usr/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=3
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo tee /etc/systemd/system/finbert-streamlit.service > /dev/null <<EOF
   [Unit]
   Description=FinBERT RAG Streamlit
   After=network.target
   
   [Service]
   Type=exec
   User=ec2-user
   WorkingDirectory=/home/ec2-user/finbert-news-rag-app/streamlit
   Environment=PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin
   ExecStart=/usr/bin/python3.11 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   Restart=always
   RestartSec=3
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Reload and enable services
   sudo systemctl daemon-reload
   sudo systemctl enable finbert-api finbert-streamlit
   ```

2. **Copy Environment File**
   ```bash
   # Copy .env with your Elasticsearch credentials
   scp -i finbert-rag-key.pem .env ec2-user@YOUR_EC2_HOST:/home/ec2-user/finbert-news-rag-app/
   ```

## 🔄 **CI/CD Workflow Explained**

### **Automated Process:**

1. **Developer pushes code** → GitHub repository
2. **GitHub Actions triggered** → Runs tests
3. **Tests pass** → Builds application  
4. **Build successful** → Deploys to EC2
5. **Deployment commands**:
   - Pull latest code
   - Stop existing services
   - Update dependencies
   - Restart services
   - Health checks
6. **Success notification** → Slack/email

### **Manual Triggers:**

- **Infrastructure**: Run manually to create/destroy AWS resources
- **Deployment**: Automatic on main branch push
- **Development**: Automatic on feature branch push/PR

## 🎯 **Access URLs (After Deployment)**

```bash
# Direct access
API: http://YOUR_EC2_HOST:8000/docs
Streamlit: http://YOUR_EC2_HOST:8501

# Through Nginx reverse proxy  
API: http://YOUR_EC2_HOST/api/docs
Streamlit: http://YOUR_EC2_HOST/
Health: http://YOUR_EC2_HOST/health
```

## 🛡️ **Security Features**

- ✅ IAM roles with minimal permissions
- ✅ Security groups with specific port access
- ✅ SSH key-based authentication
- ✅ Environment variable protection
- ✅ Code security scanning
- ✅ Dependency vulnerability checks

## 💰 **Cost Optimization**

- ✅ **t2.micro**: Free tier eligible (750 hours/month)
- ✅ **EBS**: 30GB free
- ✅ **Data Transfer**: 15GB/month free
- ✅ **Load Balancer**: Free tier available
- ✅ **Total Cost**: $0 for first 12 months

## 🔧 **Maintenance & Monitoring**

### **Automated Health Checks:**
- API endpoint monitoring
- Service status verification
- Automatic restart on failure

### **Logging:**
- GitHub Actions logs
- SystemD service logs
- Application logs

### **Updates:**
- Automatic deployment on code push
- Dependency updates via CI/CD
- Infrastructure updates via workflow

## 🚀 **Next Steps**

1. **Set up AWS account and IAM user**
2. **Add GitHub Secrets**
3. **Run infrastructure workflow**  
4. **Push code to trigger deployment**
5. **Monitor and test**

Your FinBERT News RAG application is now ready for production deployment with full CI/CD automation! 🎉

---

**📧 Support**: Check GitHub Actions logs for troubleshooting  
**🔗 Repository**: https://github.com/pes-mtech-project/RAG_API_UI  
**⚡ Status**: Ready for deployment