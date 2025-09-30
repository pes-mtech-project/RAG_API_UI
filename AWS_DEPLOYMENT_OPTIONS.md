# 🚀 **AWS Free Tier Deployment Options for FinBERT News RAG App**

**Date**: September 30, 2025  
**Application**: FinBERT News RAG (FastAPI + Streamlit + Elasticsearch Cloud)

## 📊 **Current Application Analysis**

### **Components**
1. **FastAPI Backend** (`api/`)
   - 7 REST endpoints
   - Elasticsearch Cloud integration
   - HuggingFace embeddings (384D vectors)
   - Dependencies: torch, transformers, sentence-transformers
   - Memory usage: ~1-2GB (due to ML models)

2. **Streamlit Frontend** (`streamlit/`)
   - Interactive web dashboard
   - Plotly visualizations
   - Search interface
   - Dependencies: streamlit, plotly, pandas
   - Memory usage: ~200-500MB

3. **External Dependencies**
   - **Elasticsearch Cloud**: GCP Elastic Cloud (already configured)
   - **HuggingFace Models**: Downloaded at runtime (~500MB-1GB)

## 🎯 **AWS Free Tier Deployment Options**

### **Option 1: EC2 t2.micro + Application Load Balancer** ⭐ **RECOMMENDED**

#### **📋 Architecture**
```
Internet → ALB → EC2 t2.micro (FastAPI:8000 + Streamlit:8501)
                      ↓
               Elasticsearch Cloud (GCP)
```

#### **✅ Free Tier Benefits**
- **EC2 t2.micro**: 750 hours/month (24/7 for 1 month)
- **Application Load Balancer**: 750 hours/month + 15GB data processing
- **Data Transfer**: 15GB/month out to internet
- **EBS Storage**: 30GB SSD
- **Elastic IP**: 1 static IP (free when attached)

#### **⚙️ Setup Steps**

1. **Launch EC2 t2.micro**
   ```bash
   # Instance specifications
   Instance Type: t2.micro (1 vCPU, 1GB RAM)
   OS: Amazon Linux 2023
   Storage: 30GB gp3 EBS (free tier)
   Security Group: HTTP(80), HTTPS(443), SSH(22)
   ```

2. **Install Dependencies**
   ```bash
   # Connect to EC2
   ssh -i your-key.pem ec2-user@your-ec2-ip
   
   # Install Python 3.11
   sudo dnf update -y
   sudo dnf install python3.11 python3.11-pip git -y
   
   # Install application
   git clone https://github.com/your-username/finbert-news-rag-app.git
   cd finbert-news-rag-app
   
   # Install API dependencies
   cd api && pip3.11 install -r requirements.txt
   cd ../streamlit && pip3.11 install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Copy .env file with cloud Elasticsearch credentials
   cp .env.example .env
   # Edit .env with your ES_READONLY_HOST and ES_READONLY_KEY
   ```

4. **Create Systemd Services**
   ```bash
   # FastAPI service
   sudo tee /etc/systemd/system/finbert-api.service > /dev/null <<EOF
   [Unit]
   Description=FinBERT RAG API
   After=network.target
   
   [Service]
   Type=exec
   User=ec2-user
   WorkingDirectory=/home/ec2-user/finbert-news-rag-app/api
   ExecStart=/usr/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Streamlit service
   sudo tee /etc/systemd/system/finbert-streamlit.service > /dev/null <<EOF
   [Unit]
   Description=FinBERT RAG Streamlit
   After=network.target
   
   [Service]
   Type=exec
   User=ec2-user
   WorkingDirectory=/home/ec2-user/finbert-news-rag-app/streamlit
   ExecStart=/usr/bin/python3.11 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start services
   sudo systemctl enable finbert-api finbert-streamlit
   sudo systemctl start finbert-api finbert-streamlit
   ```

5. **Setup Application Load Balancer**
   ```bash
   # Create ALB with two target groups:
   # Target Group 1: FastAPI (port 8000) - /api/*
   # Target Group 2: Streamlit (port 8501) - /*
   # Route /api/* to FastAPI, everything else to Streamlit
   ```

#### **💰 Cost Estimate (Free Tier)**
- **EC2 t2.micro**: $0 (750 hours free)
- **ALB**: $0 (750 hours free)
- **EBS 30GB**: $0 (free tier)
- **Data Transfer**: $0 (first 15GB free)
- **Total**: **$0** for first 12 months

#### **⚠️ Limitations**
- **RAM**: 1GB may be tight for ML models (torch, transformers)
- **CPU**: Single vCPU may cause slower embedding generation
- **Model Downloads**: ~1GB HuggingFace models will consume disk space

---

### **Option 2: ECS Fargate (Spot) + Application Load Balancer**

#### **📋 Architecture**
```
Internet → ALB → ECS Fargate (2 services: API + Streamlit)
                        ↓
                 Elasticsearch Cloud (GCP)
```

#### **✅ Free Tier Benefits**
- **Fargate**: Some compute hours free for new accounts
- **ALB**: 750 hours/month free
- **ECR**: 500MB storage free

#### **⚙️ Setup Steps**

1. **Create Docker Images**
   ```dockerfile
   # api/Dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   
   # streamlit/Dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
   ```

2. **Push to ECR**
   ```bash
   # Build and push images to Amazon ECR
   aws ecr create-repository --repository-name finbert-api
   aws ecr create-repository --repository-name finbert-streamlit
   ```

3. **Create ECS Services**
   - **Task Definition**: 0.5 vCPU, 1GB RAM per service
   - **Service**: 1 task each for API and Streamlit
   - **Networking**: ALB with path-based routing

#### **💰 Cost Estimate**
- **Fargate**: ~$15-25/month (after free tier)
- **ALB**: $0 (free tier)
- **ECR**: $0 (500MB free)

---

### **Option 3: Lightsail Container Service** 💡 **COST-EFFECTIVE**

#### **📋 Architecture**
```
Internet → Lightsail Load Balancer → Container Service (API + Streamlit)
                                           ↓
                                  Elasticsearch Cloud (GCP)
```

#### **✅ Benefits**
- **Predictable Pricing**: $10/month for nano service
- **Built-in Load Balancer**: Included
- **Easy Container Deployment**: Simple CLI/UI
- **SSL Certificate**: Free Let's Encrypt

#### **⚙️ Setup Steps**

1. **Create Container Service**
   ```bash
   aws lightsail create-container-service \
     --service-name finbert-rag \
     --power nano \
     --scale 1
   ```

2. **Deploy Containers**
   ```json
   {
     "api": {
       "image": "your-api-image",
       "ports": {"8000": "HTTP"},
       "environment": {
         "ES_READONLY_HOST": "your-host",
         "ES_READONLY_KEY": "your-key"
       }
     },
     "streamlit": {
       "image": "your-streamlit-image",
       "ports": {"8501": "HTTP"}
     }
   }
   ```

#### **💰 Cost Estimate**
- **Nano Service**: $10/month (512MB RAM, 0.25 vCPU)
- **Data Transfer**: 1TB included
- **Total**: **$10/month**

---

### **Option 4: Lambda + API Gateway (Serverless)** ⚡ **AUTO-SCALING**

#### **📋 Architecture**
```
Internet → CloudFront → API Gateway → Lambda Functions → Elasticsearch Cloud
             ↓
        S3 (Static Streamlit Build)
```

#### **✅ Benefits**
- **True Serverless**: Pay per request
- **Auto-scaling**: Handle traffic spikes
- **No Server Management**: Fully managed

#### **⚠️ Challenges**
- **Cold Starts**: ML model loading (~10-30 seconds)
- **Memory Limits**: 10GB max (sufficient for models)
- **Timeout**: 15 minutes max per request
- **Complex Setup**: Requires Lambda layers for large dependencies

#### **⚙️ Setup Approach**

1. **API Lambda Functions**
   ```python
   # Separate Lambda for each endpoint
   # Use Lambda Layers for torch/transformers
   # Implement model caching in /tmp
   ```

2. **Static Streamlit Build**
   ```bash
   # Convert Streamlit to static React/Vue app
   # Or use Streamlit Cloud (separate from AWS)
   ```

#### **💰 Cost Estimate**
- **Lambda**: ~$5-15/month (depending on usage)
- **API Gateway**: ~$3-10/month
- **S3**: ~$1/month
- **CloudFront**: Free tier (1TB)

---

## 🎯 **FINAL RECOMMENDATION**

### **🥇 Best Option: EC2 t2.micro + ALB (Option 1)**

#### **Why This is Optimal:**

1. **✅ Completely Free** for 12 months
2. **✅ Simple Architecture** - Easy to manage
3. **✅ Full Control** - Root access, custom configurations
4. **✅ Persistent Storage** - Models stay loaded
5. **✅ Real-time Performance** - No cold starts
6. **✅ Easy Debugging** - Direct SSH access

#### **🚀 Quick Deployment Script**

```bash
#!/bin/bash
# deploy-to-aws.sh

# 1. Launch EC2 t2.micro via AWS Console
# 2. SSH into instance and run:

# Install dependencies
sudo dnf update -y
sudo dnf install python3.11 python3.11-pip git nginx -y

# Clone and setup app
git clone https://github.com/your-repo/finbert-news-rag-app.git
cd finbert-news-rag-app

# Install Python packages
cd api && python3.11 -m pip install -r requirements.txt --user
cd ../streamlit && python3.11 -m pip install -r requirements.txt --user

# Configure environment
cp .env.example .env
# Edit .env with your Elasticsearch credentials

# Create systemd services (from Option 1 above)
# Setup nginx reverse proxy
# Configure ALB with SSL

echo "✅ Deployment complete!"
echo "🌐 API: http://your-alb-dns/api/health"
echo "📊 Streamlit: http://your-alb-dns/"
```

### **🔄 Migration from Current Setup**

Your current local setup → AWS EC2 migration:

1. **Code**: Already working perfectly ✅
2. **Database**: Keep using GCP Elastic Cloud ✅  
3. **Models**: HuggingFace models will download automatically ✅
4. **Environment**: Copy `.env` file with cloud credentials ✅

### **📈 Scaling Plan**

1. **Phase 1**: Start with t2.micro (free)
2. **Phase 2**: Upgrade to t3.small if needed ($15/month)
3. **Phase 3**: Add Auto Scaling Group + multiple AZs
4. **Phase 4**: Consider ECS/EKS for containerization

---

**🎉 Your FinBERT RAG app is ready for AWS deployment with $0 cost for the first year!**