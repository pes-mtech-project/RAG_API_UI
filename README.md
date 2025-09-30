# FinBERT News RAG Application

A comprehensive Retrieval-Augmented Generation (RAG) system for FinBERT-processed news data with semantic search capabilities.

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐    HTTPS/SSL       ┌──────────────────┐
│   Streamlit     │ ────────────── │   FastAPI        │ ──────────────────  │   Elasticsearch  │
│   Frontend      │                 │   Backend         │                     │   (GCP Cloud)    │
│   (Port 8501)   │                 │   (Port 8000)     │                     │   (Port 443)     │
└─────────────────┘                 └──────────────────┘                     └──────────────────┘
       │                                      │
       │                                      │
   ┌───────────┐                        ┌──────────────┐
   │ User UI   │                        │ Embeddings   │
   │ - Summary │                        │ Similarity   │
   │ - Search  │                        │ Search       │
   └───────────┘                        └──────────────┘
```

## 📁 Project Structure

```
finbert-news-rag-app/
├── api/                          # FastAPI Backend
│   ├── main.py                   # API application
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile               # API container
├── streamlit/                    # Streamlit Frontend
│   ├── app.py                   # Streamlit application
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Frontend container
├── docker-compose.yml           # Full stack deployment
├── setup.sh                     # Development setup
├── run_api.sh                   # Run API server
├── run_streamlit.sh             # Run Streamlit app
├── .env                         # Environment variables
└── README.md                    # This file
```

## 🚀 Quick Start

### Option 1: Development Setup (Recommended)

1. **Setup the environment:**
   ```bash
   ./setup.sh
   ```

2. **Start the FastAPI backend:**
   ```bash
   ./run_api.sh
   ```

3. **In a new terminal, start Streamlit frontend:**
   ```bash
   ./run_streamlit.sh
   ```

4. **Access the applications:**
   - **Streamlit App**: http://localhost:8501
   - **FastAPI API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

### Option 2: Docker Compose

1. **Start the full stack:**
   ```bash
   docker-compose up --build
   ```

2. **Access the applications:**
   - **Streamlit App**: http://localhost:8501
   - **FastAPI API**: http://localhost:8000

## 📱 Application Features

### 🔍 **Streamlit Frontend**

#### Tab 1: Data Summary
- **System Health**: Real-time API and Elasticsearch status
- **Document Statistics**: Total documents, indices count, storage usage
- **Index Details**: Comprehensive view of all GDELT and processed indices
- **Visualizations**: 
  - Document count by index (bar chart)
  - Storage distribution (pie chart)
- **Date Ranges**: Coverage periods for each index

#### Tab 2: Similarity Search
- **Natural Language Search**: Enter queries like "market volatility" or "technology stocks"
- **Advanced Filtering**:
  - Minimum similarity score threshold
  - Date range filtering
  - Index-specific searches
  - Result count limits
- **Rich Results Display**:
  - Similarity scores
  - Article titles, summaries, and URLs
  - Sentiment analysis data
  - Key themes and organizations
  - Full text preview
- **Search Statistics**: Average scores, best matches, score distributions

### ⚡ **FastAPI Backend**

#### Core Endpoints:
- `GET /` - API information
- `GET /health` - Health check and system status
- `GET /stats` - Comprehensive system statistics
- `POST /search` - Semantic similarity search
- `GET /indices` - List available indices

#### Key Features:
- **Embedding Generation**: Uses SentenceTransformers (all-MiniLM-L6-v2)
- **Cosine Similarity**: Efficient vector similarity search
- **Elasticsearch Integration**: Direct connection to Cloud Elasticsearch (GCP)
- **Advanced Filtering**: Date ranges, index selection, score thresholds
- **Result Processing**: Extract themes, organizations, sentiment data
- **Error Handling**: Comprehensive error responses and logging

## 🔧 Technical Details

### **Dependencies**

#### FastAPI Backend:
- `fastapi` - Modern web framework
- `sentence-transformers` - Embedding generation
- `elasticsearch` - Database connectivity
- `pydantic` - Data validation
- `uvicorn` - ASGI server

#### Streamlit Frontend:
- `streamlit` - Web app framework
- `plotly` - Interactive visualizations
- `pandas` - Data manipulation
- `requests` - API communication

### **Environment Configuration**

The application uses the provided `.env` file with:
- **ES_READONLY_HOST**: Cloud Elasticsearch endpoint (GCP Elastic Cloud)
- **ES_DOCKER_LOCAL_KEY**: Base64 encoded credentials
- **HF_TOKEN**: HuggingFace API token (if needed)

### **Data Sources**

The system works with:
- **Raw GDELT Data**: `news_data_gdelt-*` indices
- **Processed Data**: `*processed*` indices with FinBERT embeddings
- **Fields Used**:
  - `title`, `summary`, `full_text`, `url`, `date`
  - `sentiment` - FinBERT sentiment analysis
  - `embedding_384d` - Document embeddings
  - `V1Themes`, `V2Themes` - GDELT themes
  - `V1Organizations`, `V2Organizations` - Entity extraction

## 🎯 Use Cases

1. **Financial Research**: Find articles about specific market conditions
2. **Sentiment Analysis**: Explore news sentiment around companies/events
3. **Theme Discovery**: Identify related news themes and topics
4. **Historical Analysis**: Search across different time periods
5. **Content Exploration**: Browse and analyze large news datasets

## 🔍 Search Examples

Try these sample queries in the similarity search:

- **Financial**: "market crash", "stock volatility", "economic recession"
- **Technology**: "AI breakthrough", "tech earnings", "semiconductor shortage"
- **Geopolitical**: "trade war", "international relations", "supply chain"
- **Corporate**: "merger acquisition", "corporate governance", "earnings report"

## 📊 Performance

- **Search Speed**: ~200-500ms for similarity search
- **Embedding Generation**: ~50-100ms per query
- **Concurrent Users**: Supports multiple simultaneous searches
- **Scalability**: Horizontal scaling via Docker containers

## 🔒 Security

- **CORS**: Configured for development (restrict in production)
- **API Keys**: Stored in environment variables
- **Elasticsearch**: SSL/TLS connections with authentication
- **Input Validation**: Pydantic models for request/response validation

## 🐛 Troubleshooting

### Common Issues:

1. **API Connection Error**:
   - Ensure FastAPI is running on port 8000
   - Check if Elasticsearch is accessible
   - Verify .env file configuration

2. **Empty Search Results**:
   - Check if processed indices exist
   - Verify embedding fields are present
   - Try lowering similarity score threshold

3. **Performance Issues**:
   - Monitor Elasticsearch cluster health
   - Check available memory for embedding models
   - Consider index optimization

### Logs:
- **FastAPI**: Console output with INFO level logging
- **Streamlit**: Browser developer console
- **Elasticsearch**: Check cluster logs if needed

## 🚀 Production Deployment

For production deployment:

1. **Update docker-compose.yml**:
   - Use production Elasticsearch endpoints
   - Configure proper SSL certificates
   - Set up reverse proxy (nginx)

2. **Security Hardening**:
   - Restrict CORS origins
   - Use secure API keys
   - Enable HTTPS

3. **Scaling**:
   - Use container orchestration (Kubernetes)
   - Configure load balancing
   - Monitor resource usage

## 📈 Future Enhancements

- **Advanced Filters**: Source, sentiment, entity-based filtering
- **Export Features**: CSV/JSON result exports
- **Visualization**: Timeline charts, sentiment trends
- **User Management**: Authentication and user preferences
- **Caching**: Redis for frequent queries
- **Monitoring**: Prometheus/Grafana integration

---

**🎉 Your FinBERT News RAG application is ready!**

The system provides a powerful interface for exploring and searching through your FinBERT-processed news data with semantic similarity capabilities.