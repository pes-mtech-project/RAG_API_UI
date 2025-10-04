# FinBERT News RAG Application

A production-ready Financial News Retrieval-Augmented Generation (RAG) system built with AWS ECS Fargate, GitHub Container Registry, and automated CI/CD pipelines. Features semantic vector search, automated versioning, and zero-downtime deployments.

## 🎯 Quick Start

### Production Release
```bash
# Prepare for main branch merge
./scripts/release-manager.sh prepare

# Create production release (patch/minor/major)
./scripts/release-manager.sh release patch

# Check deployment status
./scripts/release-manager.sh deployment
```

### Local Development
```bash
# Start all services
docker-compose up --build

# API only (with local Elasticsearch)  
cd api && uvicorn main:app --reload
```

> **📋 For detailed deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)**

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐    HTTPS/SSL       ┌──────────────────┐
│   Streamlit     │ ────────────────│   FastAPI        │ ──────────────────  │   Elasticsearch  │
│   Frontend      │                 │   Backend        │                     │   (GCP Cloud)    │
│   (Port 8501)   │                 │   (Port 8000)    │                     │   (Port 443)     │
└─────────────────┘                 └──────────────────┘                     └──────────────────┘
       │                                      │                                      │
       │                              ┌──────────────┐                        ┌──────────────┐
   ┌───────────┐                      │     ALB      │                        │ Embeddings   │
   │  AWS ECS  │                      │ Load Balancer│                        │ Similarity   │
   │  Fargate  │                      │  Auto-Scale  │                        │ Search       │
   └───────────┘                      └──────────────┘                        └──────────────┘
```

## 🐳 Containerized Services

### API Service (`finbert-api`)
- **Framework**: FastAPI with FinBERT integration
- **Features**: Financial news analysis, semantic search, RAG operations
- **Container**: `ghcr.io/pes-mtech-project/rag_api_ui/finbert-api`
- **Port**: 8000
- **Scaling**: Auto-scaling based on CPU/Memory usage

### Base Image (`finbert-base`)
- **Purpose**: Pre-built ML dependencies (torch, transformers, sentence-transformers)
- **Container**: `ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-base`
- **Build Time**: ~6 minutes (rebuilt weekly)
- **Performance**: 85-90% faster API builds

## � Production Workflow

### Release Process
1. **Development**: Work on `develop` or `feature/*` branches
2. **Testing**: Automated quality checks and development deployment
3. **Preparation**: Use `./scripts/release-manager.sh prepare` 
4. **PR & Merge**: Create PR to `main`, review, and merge
5. **Release**: Use `./scripts/release-manager.sh release patch/minor/major`
6. **Deployment**: Automated production deployment with version tagging

### Version Management
- **Semantic Versioning**: `MAJOR.MINOR.PATCH` format
- **Auto-tagging**: GitHub releases created automatically  
- **Container Tags**: Multiple tags per version (`latest`, `prod`, `v1.2.3`)
- **Rollback Ready**: Previous versions always available

## �🚀 Deployment Environments

### Production (main branch → `latest` tag)
- **Infrastructure**: AWS ECS Fargate cluster (`finbert-rag-prod`)
- **Load Balancer**: Application Load Balancer with SSL
- **Container Tags**: `latest`, `prod`, `v1.2.3`
- **Scaling**: 1-10 tasks based on demand
- **Monitoring**: CloudWatch logs, health checks, performance metrics

### Development (develop branch → `develop` tag)  
- **Infrastructure**: Separate ECS cluster (`finbert-rag-dev`)
- **Container Tags**: `develop`, `dev`
- **Features**: Smart build detection, quick deployments
- **Testing**: Automated health checks, rollback capability

### Infrastructure Details
- **Region**: AWS ap-south-1 (Mumbai)
- **Instance Type**: t3.micro
- **Container Registry**: GitHub Container Registry (ghcr.io)

### 🌐 Custom Domains (Route53)
- **Production**: [`news-rag.lauki.co`](http://news-rag.lauki.co) 
- **Development**: [`news-rag-dev.lauki.co`](http://news-rag-dev.lauki.co)
- **Management**: Automated DNS updates via Route53 on every deployment
- **Features**: Stable URLs, automatic failover, 5-minute TTL for fast updates

> **📋 For DNS management details, see [DNS_MANAGEMENT.md](DNS_MANAGEMENT.md)**

### Automated CI/CD
- **Production**: Triggered on push to `main` branch (Full stack deployment)
- **Development**: Triggered on push to `develop` branch (API-only deployment)
- **Build**: Docker containers with multi-stage builds
- **Registry**: GitHub Container Registry with environment-specific tagging
- **Deploy**: Automated deployment to tagged EC2 instances
- **Health Checks**: Container health validation post-deployment

### Deployment Architecture
- **Production**: Full stack (API + UI) on single instance
- **Development**: Separate containers - API on dev instance, UI runs locally/separately
- **Benefits**: Independent scaling, isolated development, better resource utilization

## 📁 Project Structure

```
finbert-news-rag-app/
├── api/                         # FastAPI Backend Service
│   ├── main.py                  # API application with RAG endpoints
│   └── requirements.txt         # Backend dependencies
├── streamlit/                   # Streamlit Frontend Service  
│   ├── app.py                   # UI application with search interface
│   └── requirements.txt         # Frontend dependencies
├── docker/                      # Container Configuration
│   ├── Dockerfile.api           # API service container
│   └── Dockerfile.ui            # UI service container
├── .github/workflows/           # CI/CD Pipeline
│   └── containers.yml           # Automated build and deployment
├── scripts/                     # Deployment Utilities
├── docker-compose.yml           # Local development stack
├── docker-compose.prod.yml      # Production deployment stack
├── .env.example                 # Environment template
├── test-ssh.sh                  # SSH connectivity testing
├── diagnose-instance.sh         # System diagnostics  
├── restart-instance.sh          # Instance restart automation
└── README.md                    # Documentation
```

## 🔧 Local Development

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/pes-mtech-project/RAG_API_UI.git
cd RAG_API_UI

# Copy and configure environment
cp .env.example .env
# Edit .env with your Elasticsearch credentials

# Start services with Docker Compose
docker-compose up --build

# Access applications
# UI: http://localhost:8501
# API: http://localhost:8000/docs
```

### Development Mode

#### Separate Container Deployment (Recommended for Development)
For development, the API and UI are deployed as separate containers:

```bash
# API-only deployment (runs on development instance)
# This is handled by GitHub Actions on the develop branch
# API available at: http://43.204.102.6:8010

# UI-only deployment (run locally or separately)
./run-ui-separately.sh [API_HOST] [API_PORT]
# Default: ./run-ui-separately.sh 43.204.102.6 8010

# UI will be available at: http://localhost:8501
```

#### Local Development (Traditional)
```bash
# API development (separate terminal)
cd api
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# UI development (separate terminal)  
cd streamlit
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 📱 Application Features

### 🎯 Streamlit UI
- **Dashboard**: System health, document statistics, index overview
- **Search Interface**: Natural language queries with similarity scoring
- **Filtering**: Date range, similarity threshold, index selection
- **Visualization**: Charts for document distribution and search results
- **Export**: Results export and detailed view capabilities

### ⚡ FastAPI Backend
- **Health Check**: `/health` - System status and connectivity
- **Search Endpoint**: `/search` - Semantic similarity search with embedding
- **Statistics**: `/stats` - Comprehensive system and index statistics  
- **Interactive Docs**: `/docs` - Swagger UI for API exploration
- **Debug Search**: `/debug_search` - Analyze search issues and field compatibility
- **Test Search**: `/test_search` - Use pregenerated embeddings for testing

### 🔍 Search Capabilities
- **Embedding Model**: SentenceTransformers (all-MiniLM-L6-v2)
- **Search Types**: Semantic similarity, keyword matching, hybrid search
- **Result Scoring**: Confidence scores with threshold filtering
- **Rich Metadata**: Sentiment analysis, key themes, organizations

## 🛠️ Operations & Maintenance

### Production Environment
```bash
# Check production deployment status
./diagnose-instance.sh

# Test production SSH connectivity
./test-ssh.sh

# Restart production instance
./restart-instance.sh

# Monitor production containers
docker logs finbert-api
docker logs finbert-ui
```

### Development Environment  
```bash
# Check development deployment status
./diagnose-dev-instance.sh

# Test development SSH connectivity
./test-ssh-dev.sh

# Restart development instance
./restart-dev-instance.sh

# Monitor development containers
docker logs finbert-api-dev
docker logs finbert-ui-dev
```

### Manual Container Management
```bash
# Production stack
docker-compose -f docker-compose.prod.yml restart

# Development stack (on dev instance)
docker-compose -f docker-compose.dev.yml restart
```

### Logs and Debugging
```bash
# View container logs
docker logs finbert-api --tail 50 -f
docker logs finbert-ui --tail 50 -f

# System diagnostics
./diagnose-instance.sh

# Test search functionality
python test_search_api.py

# Elasticsearch diagnostics (requires ES credentials)
python elasticsearch_diagnostics.py
```

### Search Troubleshooting
```bash
# Test API health
curl http://your-api-url/health

# Debug search issues
curl -X POST http://your-api-url/debug_search \
  -H "Content-Type: application/json" \
  -d '{"query": "HDFC Bank Finance", "limit": 5}'

# Test with pregenerated embeddings
curl -X POST http://your-api-url/test_search \
  -H "Content-Type: application/json" \
  -d '{"use_pregenerated": true}'
```

## 🔒 Security & Configuration

### Environment Variables
- `ELASTICSEARCH_HOST`: Elasticsearch server URL
- `ELASTICSEARCH_USERNAME`: Authentication username  
- `ELASTICSEARCH_PASSWORD`: Authentication password
- `ELASTICSEARCH_USE_SSL`: SSL configuration (true/false)

### Security Groups
- **SSH**: Port 22 (restricted to authorized IPs)
- **HTTP**: Ports 8000, 8501 (public access)
- **HTTPS**: Port 443 (SSL termination)

### SSH Access
```bash
# Connect to production instance
ssh -i finbert-rag-key-new.pem ec2-user@3.109.148.242
```

## 📊 Performance & Scaling

### Resource Requirements
- **Development**: 2GB RAM, 1 CPU core
- **Production**: t3.micro (1GB RAM, 1 vCPU) - current deployment
- **Recommended**: t3.small+ for higher traffic

### Scaling Options
- **Horizontal**: Multiple EC2 instances with load balancer
- **Vertical**: Larger instance types for memory-intensive operations
- **Container**: Kubernetes deployment for advanced orchestration

## 🤝 Contributing

### Development Workflow
1. **Development Branch**: All new features start in `develop` branch
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/amazing-feature
   ```

2. **Local Testing**: Test changes with Docker Compose
   ```bash
   docker-compose up --build
   ```

3. **Development Deployment**: Push to `develop` for automated testing
   ```bash
   git commit -m 'Add amazing feature'
   git push origin feature/amazing-feature
   # Create PR to develop branch
   ```

4. **Development Environment**: Changes automatically deploy to development instance
   - Access at development URLs (ports 8010/8511)
   - Separate infrastructure from production

5. **Production Release**: After verification on develop
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

### Branch Strategy
- **`main`**: Production-ready code, auto-deploys to production instance
- **`develop`**: Integration branch, auto-deploys to development instance  
- **`feature/*`**: Feature branches, create PR to `develop`
- **`hotfix/*`**: Critical fixes, can merge directly to `main`

### Code Standards
- Python: PEP 8 formatting, type hints
- Docker: Multi-stage builds, non-root users, health checks
- Documentation: Clear docstrings and README updates

## 📋 Version History

### v1.0.0 (2025-10-01)
- ✅ Initial production release
- ✅ Containerized FastAPI + Streamlit architecture
- ✅ GitHub Container Registry integration
- ✅ Automated CI/CD pipeline to AWS EC2
- ✅ Semantic search with embedding similarity
- ✅ Interactive UI with search and visualization
- ✅ Health monitoring and diagnostics tools
- ✅ Production deployment with automated restart capabilities

## 📞 Support

For issues, questions, or contributions:
- **Repository**: [GitHub Issues](https://github.com/pes-mtech-project/RAG_API_UI/issues)
- **Production Instance**: http://3.109.148.242:8501
- **API Documentation**: http://3.109.148.242:8000/docs

---

**Status**: ✅ Production Ready | **Last Updated**: October 1, 2025