# API Documentation

## FinBERT RAG API - Multi-Dimensional Embedding Search

### Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-production-domain.com`

---

## 🚀 **New Enhanced Endpoints**

### 1. **384d Embedding Search** (Fast)
**Endpoint**: `POST /search/cosine/embedding384d/`

**Description**: Fast semantic search using all-MiniLM-L6-v2 model (384 dimensions). Optimized for high-throughput scenarios.

**Request Body**:
```json
{
    "query": "artificial intelligence investment opportunities",
    "size": 10
}
```

**Response**:
```json
{
    "results": [
        {
            "id": "20250101000000-123",
            "score": 0.8567,
            "title": "AI Investment Trends in 2025",
            "summary": "Analysis of artificial intelligence investment...",
            "full_text": "Complete article text...",
            "url": "https://example.com/article",
            "date": "20250101000000",
            "sentiment": {"label": "positive", "score": 0.85},
            "themes": ["AI", "INVESTMENT", "TECHNOLOGY"]
        }
    ],
    "total_hits": 42,
    "query": "artificial intelligence investment opportunities",
    "embedding_field": "embedding_384d",
    "search_time_ms": 245
}
```

**Performance**: ~0.24s average response time

---

### 2. **768d Embedding Search** (Balanced)
**Endpoint**: `POST /search/cosine/embedding768d/`

**Description**: Balanced semantic search using all-mpnet-base-v2 model (768 dimensions). Optimal balance of speed and accuracy.

**Request Body**:
```json
{
    "query": "sovereign debt instruments trading at elevated risk premiums",
    "size": 5
}
```

**Performance**: ~0.29s average response time

---

### 3. **1155d Enhanced Embedding Search** (Comprehensive)
**Endpoint**: `POST /search/cosine/embedding1155d/`

**Description**: Advanced search combining 384d + 768d embeddings + 3d sentiment analysis (1155 total dimensions). Best for complex financial analysis.

**Request Body**:
```json
{
    "query": "market volatility impact on emerging economies",
    "size": 8
}
```

**Performance**: ~0.39s average response time

---

### 4. **Health Check**
**Endpoint**: `GET /health`

**Description**: System status including Elasticsearch connectivity and model cache information.

**Response**:
```json
{
    "status": "healthy",
    "api": "operational", 
    "elasticsearch": "green",
    "timestamp": "2025-10-04T08:34:51.761776",
    "model_cache": {
        "cache_directory": "/home/appuser/.cache/sentence_transformers",
        "cached_models": [
            "sentence-transformers_all-MiniLM-L6-v2",
            "all-MiniLM-L6-v2", 
            "sentence-transformers_all-mpnet-base-v2",
            "all-mpnet-base-v2"
        ],
        "loaded_models": []
    }
}
```

---

## 🔄 **Legacy Endpoints** (Backward Compatibility)

### Original Search
**Endpoint**: `POST /search`

**Description**: Original semantic search endpoint using 384d embeddings.

**Request Body**:
```json
{
    "query": "financial technology innovation",
    "limit": 10,
    "similarity_threshold": 0.7
}
```

---

## 📊 **Request Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Natural language search query |
| `size` | integer | No | 10 | Number of results to return (1-100) |
| `similarity_threshold` | float | No | 0.0 | Minimum similarity score (0.0-1.0) |

---

## 🎯 **Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique document identifier |
| `score` | float | Cosine similarity score (0.0-1.0) |
| `title` | string | Article headline |
| `summary` | string | AI-generated article summary |
| `full_text` | string | Complete article content |
| `url` | string | Original article URL |
| `date` | string | Publication date (YYYYMMDDHHMMSS) |
| `sentiment` | object | Sentiment analysis results |
| `themes` | array | Extracted financial themes |
| `organizations` | array | Mentioned organizations |

---

## ⚡ **Performance Benchmarks**

| Endpoint | Avg Response Time | Success Rate | Concurrent Capacity |
|----------|------------------|-------------|-------------------|
| **384d** | 0.239s | 100% | High throughput |
| **768d** | 0.294s | 100% | Balanced load |
| **1155d** | 0.393s | 100% | Complex queries |

**Overall System Performance**:
- **Success Rate**: 100% (138/138 test requests)
- **Concurrent Load**: 4.49 requests/second sustained
- **Model Caching**: 4.9x speedup (no downloads after initial load)

---

## 🔧 **Error Responses**

### 400 Bad Request
```json
{
    "detail": "Query parameter is required"
}
```

### 422 Validation Error
```json
{
    "detail": [
        {
            "loc": ["body", "query"],
            "msg": "field required", 
            "type": "value_error.missing"
        }
    ]
}
```

### 500 Internal Server Error
```json
{
    "detail": "Elasticsearch connection failed"
}
```

---

## 🧪 **Testing Examples**

### Financial Terminology Testing
```bash
# Test complex financial concepts
curl -X POST "http://localhost:8000/search/cosine/embedding768d/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quantitative easing impact on sovereign bond yields",
    "size": 5
  }'
```

### Performance Testing
```bash
# Measure response time
time curl -X POST "http://localhost:8000/search/cosine/embedding384d/" \
  -H "Content-Type: application/json" \
  -d '{"query": "market analysis", "size": 3}'
```

### Load Testing
```bash
# Concurrent requests
for i in {1..10}; do
  curl -X POST "http://localhost:8000/search/cosine/embedding384d/" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"test query $i\", \"size\": 1}" &
done
```

---

## 📚 **Interactive Documentation**

Visit `/docs` endpoint for interactive Swagger UI:
- **Local**: http://localhost:8000/docs
- **Production**: https://your-domain.com/docs

---

**🎯 For comprehensive performance analysis, see [PERFORMANCE_REPORT.md](../PERFORMANCE_REPORT.md)**