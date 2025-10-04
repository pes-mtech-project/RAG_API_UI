# FinBERT News RAG Application

A production-ready Financial News Retrieval-Augmented Generation (RAG) system with **modular architecture** following SOLID principles. Features advanced semantic vector search with multiple embedding dimensions, model caching optimization, and automated CI/CD pipelines.

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
# Start enhanced services with model caching optimization
docker-compose up --build

# Verify services and model loading
docker-compose ps
docker logs finbert-api  # Check model preloading status

# Test new embedding endpoints
curl http://localhost:8000/health
# Test legacy endpoints (backward compatibility)
curl -X POST http://your-api-url/search \
  -H "Content-Type: application/json" \
  -d '{"query": "HDFC Bank Finance", "limit": 5}'

# Debug search issues  
curl -X POST http://your-api-url/debug_search \
  -H "Content-Type: application/json" \
  -d '{"query": "search diagnostics", "limit": 5}'
```

## 📈 **Changelog & Recent Improvements**

### **🎉 Version 2.0 - Modular Architecture Overhaul (October 2025)**

#### **🚀 Major Enhancements**
- **✅ Modular Architecture**: Complete refactor following SOLID principles
- **✅ Multi-Embedding Support**: Added 384d, 768d, and 1155d dimensional search
- **✅ Model Caching**: Persistent storage eliminates download delays (4.9x speedup)
- **✅ Service Layer**: Clean separation with dependency injection
- **✅ Performance Optimization**: Sub-second response times achieved

#### **🔧 Technical Improvements**  
- **Router-Based Architecture**: Separated endpoints into logical modules
- **Pydantic Models**: Enhanced request/response validation
- **Elasticsearch 8.x Support**: Updated k-NN query syntax
- **Model Preloading**: Startup optimization for instant responses
- **Comprehensive Testing**: 138-request validation suite

#### **📊 Performance Metrics**
- **Response Time**: 0.31s average (down from 1.29s)
- **Success Rate**: 100% across all endpoints
- **Concurrent Load**: 4.49 requests/second sustained
- **Model Loading**: Cached vs 436MB downloads eliminated

#### **🏗️ Architecture Changes**
- **Before**: Monolithic `main.py` with model downloads
- **After**: Modular services with persistent caching
- **Entry Point**: Changed from `main.py` to `startup.py`
- **Service Injection**: FastAPI dependency injection patterns

### **🔄 Previous Releases**
- **v1.5**: AWS ECS deployment automation
- **v1.4**: GitHub Container Registry integration  
- **v1.3**: Streamlit UI enhancements
- **v1.2**: Base image optimization
- **v1.1**: Docker containerization
- **v1.0**: Initial FastAPI + Elasticsearch implementation

## 🤝 **Contributing**

### **Development Guidelines**
1. **Architecture**: Follow SOLID principles and service layer patterns
2. **Testing**: Add tests for new endpoints and services
3. **Performance**: Maintain sub-second response time targets
4. **Documentation**: Update README.md and API docs for changes

### **Pull Request Process**
```bash
# Create feature branch
git checkout -b feature/your-enhancement

# Develop with testing
python test_exhaustive_api.py  # Validate no regressions

# Submit PR with performance analysis
# Include before/after metrics in PR description
```

## 📞 **Support & Resources**

- **📊 Performance Report**: [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md)
- **🚀 Deployment Guide**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)  
- **🐛 Issues**: [GitHub Issues](https://github.com/pes-mtech-project/RAG_API_UI/issues)
- **📖 API Documentation**: http://localhost:8000/docs (when running)

---
**🎯 FinBERT RAG Application - Production-Ready Financial News Search with Modular Architecture**

# Access applications
# Streamlit UI: http://localhost:8501  
# FastAPI Docs: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

### **🔧 Development Workflow Options**

#### **Option 1: Full Container Development** (Recommended)
```bash
# Complete stack with model caching
docker-compose up --build

# Monitor model loading and caching
docker logs -f finbert-api

# Run comprehensive tests
python test_exhaustive_api.py
```

#### **Option 2: Hybrid Development** (Faster UI iterations)
```bash
# Run optimized API in container 
docker-compose up finbert-api

# Develop UI locally with hot-reload
cd streamlit && streamlit run app.py
```

#### **Option 3: Local Development** (Full control)
```bash
# API with model preloading (terminal 1)
cd api && python startup.py

# UI development (terminal 2)  
cd streamlit && streamlit run app.py
```

### **🐛 Troubleshooting**

#### **Model Download Issues** ✅ **RESOLVED**
```bash
# Problem: Models downloading on every API call
# Solution: Implemented persistent model caching

# Verify model caching is working
docker exec finbert-api ls -la ~/.cache/sentence_transformers/
docker logs finbert-api | grep "Model loaded from cache"
```

#### **Performance Issues**
```bash
# Check response times
time curl -X POST http://localhost:8000/search/cosine/embedding384d/ \
  -H "Content-Type: application/json" -d '{"query": "test", "size": 1}'

# Monitor container resources  
docker stats finbert-api

# Run performance validation
python test_model_caching.py
```

#### **Elasticsearch Connection Issues**
```bash
# Test Elasticsearch connectivity
curl http://localhost:8000/health

# Check logs for connection errors
docker logs finbert-api | grep -i elasticsearch

# Verify environment variables
docker exec finbert-api env | grep ES_
```
```

### **🚀 NEW: Test the Enhanced API Endpoints**
```bash
# Test 384d embedding search
curl -X POST "http://localhost:8000/search/cosine/embedding384d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence investment", "size": 5}'

# Test 768d embedding search  
curl -X POST "http://localhost:8000/search/cosine/embedding768d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "sovereign debt instruments", "size": 5}'

# Test combined 1155d embedding search
curl -X POST "http://localhost:8000/search/cosine/embedding1155d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "financial market analysis", "size": 5}'
```

> **📋 For detailed deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)**
> **📊 For performance analysis, see [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md)**

## 🏗️ **Modular Architecture (SOLID Principles)**

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐    HTTPS/SSL       ┌──────────────────┐
│   Streamlit     │ ────────────────│   FastAPI        │ ──────────────────  │   Elasticsearch  │
│   Frontend      │                 │ (Modular Router) │                     │   (GCP Cloud)    │  
│   (Port 8501)   │                 │   (Port 8000)    │                     │   (Port 443)     │
└─────────────────┘                 └──────────────────┘                     └──────────────────┘
                                              │
                                    ┌─────────────────┐
                                    │  Service Layer  │
                                    ├─────────────────┤
                                    │ EmbeddingService│──┐ Model Caching
                                    │ElasticsearchSvc │  │ (384d + 768d)
                                    │  SearchService  │  │ 
                                    │ ModelPreloader  │──┘ Persistent Cache
                                    └─────────────────┘
                                              │
                          ┌─────────────────────────────────────┐
                          │        API Endpoints                │
                          ├─────────────────────────────────────┤
                          │ /search/cosine/embedding384d/       │
                          │ /search/cosine/embedding768d/       │  
                          │ /search/cosine/embedding1155d/      │
                          │ /health                            │
                          └─────────────────────────────────────┘
```

### **🎯 Key Architecture Improvements**
- **✅ Modular Design**: Clean separation following SOLID principles
- **✅ Model Caching**: Persistent storage eliminates download delays  
- **✅ Multi-Embedding**: 384d, 768d, and 1155d dimensional search
- **✅ Service Layer**: Dependency injection for maintainability
- **✅ Performance**: Sub-second response times (0.31s average)

## 🐳 **Enhanced Containerized Services**

### **API Service (`finbert-api`) - Modular Architecture** 
- **Framework**: FastAPI with modular router-based design
- **Features**: 
  - ✅ **Multiple Embedding Endpoints**: 384d, 768d, 1155d dimensional search
  - ✅ **Model Caching**: Persistent model storage (~/.cache/sentence_transformers)
  - ✅ **Service Layer**: ElasticsearchService, EmbeddingService, SearchService
  - ✅ **Performance Optimized**: Sub-second response times, 4.9x speedup
  - ✅ **Production Ready**: 100% success rate across 138 test requests
- **Container**: `ghcr.io/pes-mtech-project/rag_api_ui/finbert-api`
- **Port**: 8000  
- **Entry Point**: `python startup.py` (with model preloading)
- **Scaling**: Auto-scaling based on CPU/Memory usage

### **UI Service (`finbert-ui`)** 
- **Framework**: Streamlit with enhanced search interface
- **Features**: Multi-dimensional embedding search, real-time results
- **Container**: `ghcr.io/pes-mtech-project/rag_api_ui/finbert-ui`
- **Port**: 8501

### **Base Image (`finbert-base`)**
- **Purpose**: Pre-built ML dependencies (torch, transformers, sentence-transformers) 
- **Models Included**: all-MiniLM-L6-v2 (384d), all-mpnet-base-v2 (768d)
- **Container**: `ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-base`
- **Build Time**: ~6 minutes (rebuilt weekly)
- **Performance**: 85-90% faster API builds, persistent model caching

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

## � **API Endpoints**

### **🚀 NEW: Multi-Dimensional Embedding Search**

#### **384d Embedding Search** (Fast, Efficient)
```bash
POST /search/cosine/embedding384d/
Content-Type: application/json
{
    "query": "financial technology innovation", 
    "size": 10
}
```
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Performance**: ~0.24s average response time
- **Best For**: Quick searches, high throughput scenarios

#### **768d Embedding Search** (Balanced, Accurate)
```bash
POST /search/cosine/embedding768d/
Content-Type: application/json
{
    "query": "sovereign debt instruments", 
    "size": 10
}
```
- **Model**: all-mpnet-base-v2 (768 dimensions) 
- **Performance**: ~0.29s average response time
- **Best For**: Balanced performance and accuracy

#### **1155d Enhanced Embedding Search** (Most Comprehensive)
```bash
POST /search/cosine/embedding1155d/
Content-Type: application/json
{
    "query": "market volatility analysis", 
    "size": 10
}
```
- **Model**: Combined 384d + 768d + 3d sentiment (1155 dimensions)
- **Performance**: ~0.39s average response time  
- **Best For**: Complex financial analysis, multi-modal search

#### **Health Check**
```bash
GET /health
```
- **Returns**: System status, Elasticsearch connectivity, model cache status

### **📊 Response Format**
```json
{
    "results": [
        {
            "id": "20250101000000-123",
            "score": 0.8567,
            "title": "Financial Market Analysis",
            "summary": "Comprehensive market analysis...",
            "url": "https://example.com/article",
            "date": "20250101000000",
            "sentiment": {"label": "positive", "score": 0.85}
        }
    ],
    "total_hits": 42,
    "query": "financial analysis",
    "embedding_field": "embedding_384d",
    "search_time_ms": 245
}
```

## �📁 **Enhanced Project Structure**

```
finbert-news-rag-app/
├── api/                         # 🔧 Modular FastAPI Backend
│   ├── startup.py               # Application entry point with model preloading
│   ├── app/
│   │   ├── main.py              # FastAPI application factory
│   │   ├── models/              # Pydantic request/response models
│   │   │   ├── search_models.py # Search request/response schemas
│   │   │   └── __init__.py
│   │   ├── routers/             # API endpoint routers
│   │   │   ├── search.py        # New multi-dimensional search endpoints
│   │   │   ├── legacy.py        # Backward compatibility endpoints
│   │   │   └── __init__.py
│   │   └── services/            # 🏗️ Service layer (SOLID principles)
│   │       ├── elasticsearch_service.py  # Database operations
│   │       ├── embedding_service.py      # Model management & caching
│   │       ├── search_service.py         # Business logic coordination
│   │       ├── model_preloader.py        # Startup model optimization
│   │       └── __init__.py
│   └── requirements.txt         # Backend dependencies
├── streamlit/                   # 🎨 Enhanced Frontend Service
│   ├── app.py                   # Multi-endpoint UI interface
│   └── requirements.txt         # Frontend dependencies
├── docker/                      # 🐳 Container Configuration
│   ├── Dockerfile.api           # Optimized API service container
│   └── Dockerfile.ui            # UI service container
├── .github/workflows/           # 🚀 CI/CD Pipeline
│   └── containers.yml           # Automated build and deployment
├── scripts/                     # 🛠️ Deployment Utilities
├── tests/                       # 🧪 NEW: Comprehensive Testing
│   ├── test_exhaustive_api.py   # 138-request performance test
│   └── test_model_caching.py    # Model caching validation
├── docker-compose.yml           # Enhanced local development stack
├── .env.example                 # Environment template
├── PERFORMANCE_REPORT.md        # 📊 NEW: Comprehensive performance analysis
└── README.md                    # Updated documentation
```

## � **Performance & Testing**

### **🎯 Performance Metrics (Verified October 2025)**
- **✅ 100% Success Rate**: 138 API requests completed successfully
- **⚡ Sub-Second Response**: 0.31s average across all endpoints
- **🚀 Model Caching**: 4.9x speedup (1.29s → 0.26s for 384d model)
- **🔄 Concurrent Load**: 4.49 requests/second sustained throughput
- **📈 Reliability**: Zero failures under concurrent load testing

### **Endpoint Performance Breakdown**
| Endpoint | Avg Response | Success Rate | Best Use Case |
|----------|-------------|-------------|---------------|
| **384d** | 0.239s | 100% | High-speed searches |
| **768d** | 0.294s | 100% | Balanced accuracy |
| **1155d** | 0.393s | 100% | Complex analysis |

### **🧪 Comprehensive Testing Suite**
```bash
# Run exhaustive API testing (138 requests)
python test_exhaustive_api.py

# Test model caching performance
python test_model_caching.py

# Load testing with concurrent requests
curl -X POST "http://localhost:8000/search/cosine/embedding384d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "size": 5}' &
```

### **🏆 Quality Assurance**
- **✅ Functional Testing**: All endpoints validated
- **✅ Performance Testing**: Response times benchmarked  
- **✅ Load Testing**: Concurrent request handling verified
- **✅ Caching Testing**: Model persistence confirmed
- **✅ Edge Case Testing**: Robust error handling
- **✅ Integration Testing**: End-to-end workflow validated

## �🔧 **Local Development**

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Git

### **🚀 Enhanced Quick Start**
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

## 📱 **Enhanced Application Features**

### 🎯 **Streamlit UI (Enhanced)**
- **Multi-Endpoint Dashboard**: Test all embedding dimensions in one interface
- **Performance Metrics**: Real-time response time monitoring  
- **Search Interface**: Natural language queries with advanced similarity scoring
- **Filtering**: Date range, similarity threshold, embedding dimension selection
- **Visualization**: Enhanced charts for embedding performance comparison
- **Export**: Results export with embedding metadata and detailed analytics

### ⚡ **FastAPI Backend (Modular Architecture)**

#### **🚀 NEW: Multi-Dimensional Search Endpoints**
- **`/search/cosine/embedding384d/`** - Fast 384d embedding search (all-MiniLM-L6-v2)
- **`/search/cosine/embedding768d/`** - Balanced 768d search (all-mpnet-base-v2)  
- **`/search/cosine/embedding1155d/`** - Enhanced combined search (384d+768d+3d sentiment)
- **`/health`** - Comprehensive system status with model cache info

#### **🔧 Service Layer Architecture**
- **EmbeddingService**: Model management with persistent caching
- **ElasticsearchService**: Optimized database operations
- **SearchService**: Business logic coordination with dependency injection
- **ModelPreloader**: Startup optimization for instant responses

#### **📊 Legacy Endpoints (Backward Compatibility)**
- **`/search`** - Original semantic similarity search 
- **`/stats`** - System and index statistics
- **`/docs`** - Interactive Swagger UI documentation
- **`/debug_search`** - Search analysis and troubleshooting

### 🔍 **Advanced Search Capabilities**
- **Multi-Model Support**: 
  - `all-MiniLM-L6-v2` (384d) - Speed optimized
  - `all-mpnet-base-v2` (768d) - Accuracy optimized
  - Combined embedding (1155d) - Comprehensive analysis
- **Persistent Caching**: Models cached in `~/.cache/sentence_transformers`
- **Performance Optimization**: Sub-second response times across all endpoints
- **Semantic Understanding**: Advanced financial terminology processing
- **Confidence Scoring**: Multiple similarity metrics and threshold filtering
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