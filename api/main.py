"""
FastAPI application for FinBERT News RAG System
Handles heavy lifting for document retrieval and similarity search
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer
import elasticsearch
from elasticsearch import Elasticsearch
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinBERT News RAG API",
    description="API for similarity search and document retrieval from FinBERT processed news data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    min_score: float = 0.5
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source_index: Optional[str] = None

class EmbeddingSearchQuery(BaseModel):
    embedding: List[float]
    limit: int = 10
    min_score: float = 0.5
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source_index: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    score: float
    title: str
    summary: str
    full_text: str
    url: str
    date: str
    published_dt: str
    rag_doc_url: str
    sentiment: Dict[str, Any]
    themes: Optional[List[str]] = None
    organizations: Optional[List[str]] = None

class IndexStats(BaseModel):
    index_name: str
    doc_count: int
    size_in_bytes: int
    date_range: Dict[str, str]

class SystemStats(BaseModel):
    total_documents: int
    total_indices: int
    indices: List[IndexStats]
    cluster_health: str

# Global variables for models and connections
sentence_model = None
es_client = None

def get_elasticsearch_client():
    """Initialize Elasticsearch client"""
    global es_client
    if es_client is None:
        # Use cloud Elasticsearch with readonly credentials
        es_host = os.getenv('ES_READONLY_HOST', 'https://my-elasticsearch-project-a901ed.es.asia-south1.gcp.elastic.cloud:443')
        es_key = os.getenv('ES_READONLY_KEY', 'ZzlOZ21aa0JBUXZGb3RVb01rLUY6blBPOVphYmE2MjVTZ1o2eGZWOUpxQQ==')
        
        # Try both API key and basic auth formats
        try:
            # First try as API key (newer format)
            es_client = Elasticsearch(
                es_host,
                api_key=es_key,
                verify_certs=True,
                ssl_show_warn=False,
                request_timeout=30
            )
        except Exception:
            # Fallback to basic auth (decode base64 credentials)
            credentials = base64.b64decode(es_key).decode('utf-8')
            username, password = credentials.split(':')
            
            es_client = Elasticsearch(
                es_host,
                basic_auth=(username, password),
                verify_certs=True,
                ssl_show_warn=False,
                request_timeout=30
            )
    return es_client

def get_sentence_model():
    """Initialize sentence transformer model"""
    global sentence_model
    if sentence_model is None:
        logger.info("Loading sentence transformer model...")
        sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Sentence transformer model loaded successfully")
    return sentence_model

@app.on_event("startup")
async def startup_event():
    """Initialize models and connections on startup"""
    logger.info("Starting up FinBERT News RAG API...")
    try:
        # Initialize Elasticsearch client
        es = get_elasticsearch_client()
        
        # Try to get cluster info (might fail with readonly permissions)
        try:
            cluster_info = es.info()
            logger.info(f"Connected to Elasticsearch: {cluster_info['cluster_name']}")
        except Exception as e:
            logger.warning(f"Could not get cluster info (readonly permissions): {e}")
            logger.info("Connected to Elasticsearch with readonly access")
        
        # Initialize sentence model
        get_sentence_model()
        
        logger.info("API startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FinBERT News RAG API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint - always returns healthy for load balancer"""
    es_status = "disconnected"
    try:
        es = get_elasticsearch_client()
        
        # Try cluster health (might fail with readonly permissions)
        try:
            cluster_health = es.cluster.health()
            es_status = cluster_health["status"]
        except Exception:
            # If cluster health fails, try a simple search to test connectivity
            try:
                es.search(index="*", size=0, body={"query": {"match_all": {}}})
                es_status = "accessible"
            except Exception:
                es_status = "readonly_limited"
        
    except Exception as e:
        logger.warning(f"Elasticsearch connection issue during health check: {e}")
        es_status = "disconnected"
    
    # Always return 200 OK for load balancer health checks
    # Elasticsearch issues shouldn't fail container health
    return {
        "status": "healthy", 
        "api": "operational",
        "elasticsearch": es_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics (limited by readonly permissions)"""
    try:
        es = get_elasticsearch_client()
        
        # Try to get cluster health (may fail with readonly permissions)
        cluster_health_status = "unknown"
        try:
            cluster_health = es.cluster.health()
            cluster_health_status = cluster_health["status"]
        except Exception:
            cluster_health_status = "readonly_limited"
        
        # Try basic search to get approximate document counts
        indices = []
        total_docs = 0
        
        # Common index patterns to try
        index_patterns = ["*processed*", "*gdelt*", "*news*", "news_finbert_embeddings"]
        
        for pattern in index_patterns:
            try:
                # Use count API to get document count
                count_result = es.count(index=pattern)
                if count_result["count"] > 0:
                    indices.append(IndexStats(
                        index_name=pattern,
                        doc_count=count_result["count"],
                        size_in_bytes=0,  # Cannot get size with readonly
                        date_range={"from": "N/A", "to": "N/A"}  # Cannot get date range with readonly
                    ))
                    total_docs += count_result["count"]
            except Exception:
                # Pattern doesn't exist or no permissions
                continue
        
        return SystemStats(
            total_documents=total_docs,
            total_indices=len(indices),
            indices=sorted(indices, key=lambda x: x.doc_count, reverse=True),
            cluster_health=cluster_health_status
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {e}")

@app.post("/search", response_model=List[SearchResult])
async def similarity_search(search_query: SearchQuery):
    """Perform similarity search using embeddings"""
    try:
        logger.info(f"Processing search query: '{search_query.query}'")
        
        # Generate query embedding
        model = get_sentence_model()
        query_embedding = model.encode(search_query.query).tolist()
        
        es = get_elasticsearch_client()
        
        # Determine which index to search
        if search_query.source_index:
            index_pattern = search_query.source_index
        else:
            # Search in available indices by default (prioritize finbert embeddings)
            index_pattern = "news_finbert_embeddings,*processed*,*news*"
        
        # Try different embedding field names
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        search_successful = False
        response = None
        
        for embedding_field in embedding_fields:
            try:
                # Build search query
                search_body = {
                    "size": search_query.limit,
                    "min_score": search_query.min_score,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": f"cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0",
                                            "params": {"query_vector": query_embedding}
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "_source": [
                        "news_title", "news_summary", "news_body", "url", "date", 
                        "v2_themes", "v1_themes", "v2_organizations", "v1_organizations",
                        "author", "source_common_name", "published_dt", "embedding_model"
                    ]
                }
                
                # Add date range filter if specified
                if search_query.date_from or search_query.date_to:
                    date_filter = {"range": {"date": {}}}
                    if search_query.date_from:
                        date_filter["range"]["date"]["gte"] = search_query.date_from
                    if search_query.date_to:
                        date_filter["range"]["date"]["lte"] = search_query.date_to
                    search_body["query"]["bool"]["filter"] = [date_filter]
                
                # Execute search with this embedding field
                response = es.search(index=index_pattern, body=search_body)
                if response["hits"]["hits"]:  # If we got results
                    search_successful = True
                    logger.info(f"Search successful using embedding field: {embedding_field}")
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed with embedding field '{embedding_field}': {e}")
                continue
        
        if not search_successful:
            logger.error("All embedding field attempts failed")
            return []
        
        # Process results
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Extract themes from v2_themes (format: THEME_NAME,score;THEME_NAME,score...)
            themes = []
            if source.get("v2_themes"):
                theme_entries = source["v2_themes"].split(";")
                for theme_entry in theme_entries:
                    if "," in theme_entry:
                        theme_name = theme_entry.split(",")[0].strip()
                        if theme_name and theme_name not in themes:
                            themes.append(theme_name)
            if source.get("v1_themes"):
                v1_themes = source["v1_themes"].split(";")
                for theme in v1_themes:
                    theme = theme.strip()
                    if theme and theme not in themes:
                        themes.append(theme)
            themes = themes[:5]  # Top 5 unique themes
            
            # Extract organizations (if available)
            organizations = []
            if source.get("v2_organizations"):
                org_entries = source["v2_organizations"].split(";")
                for org_entry in org_entries:
                    if "," in org_entry:
                        org_name = org_entry.split(",")[0].strip()
                        if org_name and org_name not in organizations:
                            organizations.append(org_name)
            if source.get("v1_organizations"):
                v1_orgs = source["v1_organizations"].split(";")
                for org in v1_orgs:
                    org = org.strip()
                    if org and org not in organizations:
                        organizations.append(org)
            organizations = organizations[:5]  # Top 5 unique orgs
            
            # Extract sentiment from embedding_model field (contains sentiment info)
            sentiment = {}
            if source.get("embedding_model") and "finbert-sentiment" in source["embedding_model"]:
                # Extract sentiment from model name (e.g., "all-mpnet-base-v2+finbert-sentiment+negative")
                model_parts = source["embedding_model"].split("+")
                if len(model_parts) >= 3:
                    sentiment_label = model_parts[2]  # "negative", "positive", "neutral"
                    sentiment = {"label": sentiment_label, "score": 0.0}  # No score available in model name
            
            results.append(SearchResult(
                id=hit["_id"],
                score=hit["_score"],
                title=source.get("news_title", "No title available"),
                summary=source.get("news_summary", "No summary available"),
                full_text=source.get("news_body", "")[:1000] + "..." if len(source.get("news_body", "")) > 1000 else source.get("news_body", ""),
                url=source.get("url", ""),
                date=source.get("date", source.get("published_dt", "")),
                published_dt=source.get("published_dt", ""),
                rag_doc_url=f"https://my-elasticsearch-project-a901ed.kb.asia-south1.gcp.elastic.cloud/app/discover#/doc/{hit['_index']}/{hit['_index']}?id={hit['_id']}",
                sentiment=sentiment,
                themes=themes,
                organizations=organizations
            ))
        
        logger.info(f"Returning {len(results)} search results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.post("/search_embedding", response_model=List[SearchResult])
async def similarity_search_with_embedding(search_query: EmbeddingSearchQuery):
    """Perform similarity search using pre-computed embeddings"""
    try:
        logger.info(f"Processing search with embedding vector of dimension: {len(search_query.embedding)}")
        
        # Validate embedding dimension
        if len(search_query.embedding) != 384:
            raise HTTPException(
                status_code=400, 
                detail=f"Embedding dimension must be 384, got {len(search_query.embedding)}"
            )
        
        es = get_elasticsearch_client()
        
        # Determine which index to search
        if search_query.source_index:
            index_pattern = search_query.source_index
        else:
            # Search in available indices by default (prioritize finbert embeddings)
            index_pattern = "news_finbert_embeddings,*processed*,*news*"
        
        # Try different embedding field names
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        search_successful = False
        response = None
        
        for embedding_field in embedding_fields:
            try:
                # Build search query
                search_body = {
                    "size": search_query.limit,
                    "min_score": search_query.min_score,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": f"cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0",
                                            "params": {"query_vector": search_query.embedding}
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "_source": [
                        "news_title", "news_summary", "news_body", "url", "date", 
                        "v2_themes", "v1_themes", "v2_organizations", "v1_organizations",
                        "author", "source_common_name", "published_dt", "embedding_model"
                    ]
                }
                
                # Add date range filter if specified
                if search_query.date_from or search_query.date_to:
                    date_filter = {"range": {"date": {}}}
                    if search_query.date_from:
                        date_filter["range"]["date"]["gte"] = search_query.date_from
                    if search_query.date_to:
                        date_filter["range"]["date"]["lte"] = search_query.date_to
                    search_body["query"]["bool"]["filter"] = [date_filter]
                
                # Execute search with this embedding field
                response = es.search(index=index_pattern, body=search_body)
                if response["hits"]["hits"]:  # If we got results
                    search_successful = True
                    logger.info(f"Embedding search successful using field: {embedding_field}")
                    break
                    
            except Exception as e:
                logger.warning(f"Embedding search failed with field '{embedding_field}': {e}")
                continue
        
        if not search_successful:
            logger.error("All embedding field attempts failed in embedding search")
            return []
        
        # Process results (same as regular search)
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Extract themes from v2_themes (format: THEME_NAME,score;THEME_NAME,score...)
            themes = []
            if source.get("v2_themes"):
                theme_entries = source["v2_themes"].split(";")
                for theme_entry in theme_entries:
                    if "," in theme_entry:
                        theme_name = theme_entry.split(",")[0].strip()
                        if theme_name and theme_name not in themes:
                            themes.append(theme_name)
            if source.get("v1_themes"):
                v1_themes = source["v1_themes"].split(";")
                for theme in v1_themes:
                    theme = theme.strip()
                    if theme and theme not in themes:
                        themes.append(theme)
            themes = themes[:5]  # Top 5 unique themes
            
            # Extract organizations (if available)
            organizations = []
            if source.get("v2_organizations"):
                org_entries = source["v2_organizations"].split(";")
                for org_entry in org_entries:
                    if "," in org_entry:
                        org_name = org_entry.split(",")[0].strip()
                        if org_name and org_name not in organizations:
                            organizations.append(org_name)
            if source.get("v1_organizations"):
                v1_orgs = source["v1_organizations"].split(";")
                for org in v1_orgs:
                    org = org.strip()
                    if org and org not in organizations:
                        organizations.append(org)
            organizations = organizations[:5]  # Top 5 unique orgs
            
            # Extract sentiment from embedding_model field (contains sentiment info)
            sentiment = {}
            if source.get("embedding_model") and "finbert-sentiment" in source["embedding_model"]:
                # Extract sentiment from model name (e.g., "all-mpnet-base-v2+finbert-sentiment+negative")
                model_parts = source["embedding_model"].split("+")
                if len(model_parts) >= 3:
                    sentiment_label = model_parts[2]  # "negative", "positive", "neutral"
                    sentiment = {"label": sentiment_label, "score": 0.0}  # No score available in model name
            
            results.append(SearchResult(
                id=hit["_id"],
                score=hit["_score"],
                title=source.get("news_title", "No title available"),
                summary=source.get("news_summary", "No summary available"),
                full_text=source.get("news_body", "")[:1000] + "..." if len(source.get("news_body", "")) > 1000 else source.get("news_body", ""),
                url=source.get("url", ""),
                date=source.get("date", source.get("published_dt", "")),
                published_dt=source.get("published_dt", ""),
                rag_doc_url=f"https://my-elasticsearch-project-a901ed.kb.asia-south1.gcp.elastic.cloud/app/discover#/doc/{hit['_index']}/{hit['_index']}?id={hit['_id']}",
                sentiment=sentiment,
                themes=themes,
                organizations=organizations
            ))
        
        logger.info(f"Returning {len(results)} search results from embedding search")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding search error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding search failed: {e}")

class EmbeddingRequest(BaseModel):
    text: str

@app.post("/generate_embedding")
async def generate_embedding(request: EmbeddingRequest):
    """Generate embedding for given text"""
    try:
        logger.info(f"Generating embedding for text: '{request.text[:100]}...'")
        
        model = get_sentence_model()
        embedding = model.encode(request.text).tolist()
        
        return {
            "text": request.text,
            "embedding": embedding,
            "dimension": len(embedding)
        }
        
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

@app.get("/indices")
async def list_indices():
    """List available indices (limited by readonly permissions)"""
    try:
        es = get_elasticsearch_client()
        
        # Try cat API first (may fail with readonly)
        try:
            indices = es.cat.indices(index="*gdelt*,*processed*", format="json")
            return [{"name": idx["index"], "docs": int(idx["docs.count"]), "size": idx["store.size"]} for idx in indices]
        except Exception:
            # Fallback: try known index patterns with count
            result = []
            patterns = ["*processed*", "*gdelt*", "*news*", "news_finbert_embeddings"]
            
            for pattern in patterns:
                try:
                    count_result = es.count(index=pattern)
                    if count_result["count"] > 0:
                        result.append({
                            "name": pattern,
                            "docs": count_result["count"],
                            "size": "N/A (readonly)"
                        })
                except Exception:
                    continue
                    
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing indices: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)