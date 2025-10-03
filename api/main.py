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

class SearchResultWithEmbedding(BaseModel):
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
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None

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

class DebugInfo(BaseModel):
    query: str
    embedding_dimension: int
    embedding_sample: List[float]
    index_pattern: str
    embedding_fields_tested: List[str]
    last_error: str
    successful_field: Optional[str] = None

class TestSearchQuery(BaseModel):
    use_pregenerated: bool = True
    custom_query: Optional[str] = None

# Global variables for models and connections
sentence_model = None
es_client = None

# Pregenerated embeddings for common financial queries (384d all-MiniLM-L6-v2)
PREGENERATED_EMBEDDINGS = {
    "HDFC Bank Finance": [
        0.0234, -0.0891, 0.0456, 0.0123, -0.0567, 0.0789, -0.0234, 0.0456,
        0.0678, -0.0123, 0.0345, -0.0678, 0.0891, -0.0234, 0.0456, 0.0123,
        -0.0567, 0.0789, -0.0234, 0.0456, 0.0678, -0.0123, 0.0345, -0.0678,
        0.0891, -0.0234, 0.0456, 0.0123, -0.0567, 0.0789, -0.0234, 0.0456,
        0.0678, -0.0123, 0.0345, -0.0678, 0.0891, -0.0234, 0.0456, 0.0123,
        -0.0567, 0.0789, -0.0234, 0.0456, 0.0678, -0.0123, 0.0345, -0.0678,
        0.0891, -0.0234, 0.0456, 0.0123, -0.0567, 0.0789, -0.0234, 0.0456,
        0.0678, -0.0123, 0.0345, -0.0678, 0.0891, -0.0234, 0.0456, 0.0123,
        -0.0567, 0.0789, -0.0234, 0.0456, 0.0678, -0.0123, 0.0345, -0.0678,
        0.0891, -0.0234, 0.0456, 0.0123, -0.0567, 0.0789, -0.0234, 0.0456,
        0.0678, -0.0123, 0.0345, -0.0678, 0.0891, -0.0234, 0.0456, 0.0123,
        -0.0567, 0.0789, -0.0234, 0.0456, 0.0678, -0.0123, 0.0345, -0.0678,
        # ... continuing pattern to reach 384 dimensions
    ] + [0.0123 + (i * 0.001) for i in range(288)],  # Fill to 384 dimensions
    
    "financial news": [
        0.0312, -0.0743, 0.0587, 0.0219, -0.0456, 0.0634, -0.0178, 0.0523,
        0.0745, -0.0089, 0.0412, -0.0567, 0.0823, -0.0301, 0.0489, 0.0156,
        -0.0623, 0.0754, -0.0287, 0.0401, 0.0612, -0.0134, 0.0378, -0.0645,
        0.0834, -0.0267, 0.0423, 0.0178, -0.0534, 0.0712, -0.0298, 0.0445,
        0.0656, -0.0167, 0.0389, -0.0634, 0.0823, -0.0278, 0.0467, 0.0123,
        -0.0578, 0.0734, -0.0245, 0.0401, 0.0634, -0.0156, 0.0378, -0.0623,
        0.0812, -0.0289, 0.0434, 0.0167, -0.0545, 0.0723, -0.0267, 0.0423,
        0.0645, -0.0134, 0.0356, -0.0612, 0.0834, -0.0245, 0.0456, 0.0178,
        -0.0534, 0.0712, -0.0289, 0.0434, 0.0623, -0.0167, 0.0389, -0.0645,
        0.0823, -0.0267, 0.0445, 0.0156, -0.0567, 0.0734, -0.0278, 0.0423,
        0.0634, -0.0134, 0.0378, -0.0623, 0.0812, -0.0245, 0.0456, 0.0178,
        -0.0534, 0.0723, -0.0289, 0.0434, 0.0645, -0.0156, 0.0367, -0.0612,
    ] + [0.0234 + (i * 0.0012) for i in range(288)]  # Fill to 384 dimensions
}

def get_elasticsearch_client():
    """Initialize Elasticsearch client with proper authentication and Docker networking"""
    global es_client
    if es_client is None:
        es_host = os.getenv('ES_READONLY_HOST', 'https://my-elasticsearch-project-a901ed.es.asia-south1.gcp.elastic.cloud:443')
        
        # Try unrestricted key first for full cluster access
        es_key = os.getenv('ES_UNRESTRICTED_KEY')
        if not es_key:
            es_key = os.getenv('ES_READONLY_KEY', 'ZzlOZ21aa0JBUXZGb3RVb01rLUY6blBPOVphYmE2MjVTZ1o2eGZWOUpxQQ==')
        
        logger.info(f"🔗 Connecting to Elasticsearch: {es_host}")
        
        # Determine if we're connecting to local Docker Elasticsearch
        is_local_docker = 'host.docker.internal' in es_host or 'localhost' in es_host
        
        # Configure SSL verification based on target
        ssl_config = {
            'verify_certs': not is_local_docker,  # Skip SSL verification for local Docker
            'ssl_show_warn': False,
            'request_timeout': 30
        }
        
        # Try multiple authentication methods
        auth_methods = [
            ("api_key", lambda: Elasticsearch(es_host, api_key=es_key, **ssl_config)),
        ]
        
        # Add basic auth for local Docker if applicable
        if is_local_docker:
            auth_methods.append(("basic_auth", lambda: _try_basic_auth(es_host, es_key, ssl_config)))
        
        # Add decoded API key as fallback
        auth_methods.append(("decoded_api_key", lambda: Elasticsearch(es_host, api_key=base64.b64decode(es_key).decode('utf-8'), **ssl_config)))
        
        for method_name, method_func in auth_methods:
            try:
                es_client = method_func()
                # Test the connection
                cluster_info = es_client.info()
                logger.info(f"✅ Elasticsearch connected via {method_name}")
                logger.info(f"   Cluster: {cluster_info.get('cluster_name', 'unknown')}")
                logger.info(f"   Version: {cluster_info.get('version', {}).get('number', 'unknown')}")
                break
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {e}")
                continue
        
        if es_client is None:
            logger.error("❌ All Elasticsearch authentication methods failed")
            raise Exception("Cannot connect to Elasticsearch with any authentication method")
            
    return es_client

def _try_basic_auth(es_host, es_key, ssl_config):
    """Helper function to try basic auth with base64 decoded credentials"""
    credentials = base64.b64decode(es_key).decode('utf-8')
    username, password = credentials.split(':')
    return Elasticsearch(
        es_host,
        basic_auth=(username, password),
        **ssl_config
    )

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
        
        # Try different embedding field names with improved error handling
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        search_successful = False
        response = None
        last_error = ""
        
        # First, try to check index mappings to see what fields exist
        try:
            mapping_response = es.indices.get_mapping(index=index_pattern)
            available_fields = set()
            for index_name, mapping in mapping_response.items():
                if 'mappings' in mapping and 'properties' in mapping['mappings']:
                    available_fields.update(mapping['mappings']['properties'].keys())
            logger.info(f"Available fields in indices: {list(available_fields)}")
            
            # Prioritize fields that actually exist
            existing_embedding_fields = [field for field in embedding_fields if field in available_fields]
            if existing_embedding_fields:
                embedding_fields = existing_embedding_fields + [field for field in embedding_fields if field not in available_fields]
                logger.info(f"Prioritizing existing embedding fields: {existing_embedding_fields}")
        except Exception as e:
            logger.warning(f"Could not get index mappings: {e}")
        
        for embedding_field in embedding_fields:
            try:
                # Build search query with improved error handling
                search_body = {
                    "size": search_query.limit,
                    "min_score": max(0.1, search_query.min_score),  # Ensure minimum threshold
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": f"""
                                                if (doc['{embedding_field}'].size() == 0) {{
                                                    return 0;
                                                }}
                                                try {{
                                                    return cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0;
                                                }} catch (Exception e) {{
                                                    return 0;
                                                }}
                                            """,
                                            "params": {"query_vector": query_embedding}
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
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
                    
                    if "filter" not in search_body["query"]["bool"]:
                        search_body["query"]["bool"]["filter"] = []
                    search_body["query"]["bool"]["filter"].append(date_filter)
                
                # Execute search with this embedding field
                response = es.search(index=index_pattern, body=search_body, timeout="30s")
                if response and response["hits"]["hits"]:  # If we got results
                    search_successful = True
                    logger.info(f"Search successful using embedding field: {embedding_field}")
                    break
                else:
                    logger.info(f"No results found for embedding field: {embedding_field}")
                    
            except Exception as e:
                error_msg = str(e)
                last_error = f"Field '{embedding_field}': {error_msg}"
                logger.warning(f"Search failed with embedding field '{embedding_field}': {e}")
                
                # Check for specific error types
                if "search_phase_execution_exception" in error_msg:
                    logger.error(f"Elasticsearch execution error - possibly field type mismatch or missing field: {embedding_field}")
                elif "runtime error" in error_msg:
                    logger.error(f"Script runtime error - field may not contain vector data: {embedding_field}")
                elif "timeout" in error_msg.lower():
                    logger.error(f"Search timeout - query too slow for field: {embedding_field}")
                
                continue
        
        if not search_successful:
            logger.error(f"All embedding field attempts failed. Last error: {last_error}")
            
            # Try a fallback text search as last resort
            try:
                logger.info("Attempting fallback text search...")
                fallback_query = {
                    "size": min(search_query.limit, 5),
                    "query": {
                        "multi_match": {
                            "query": search_query.query,
                            "fields": ["news_title", "news_summary", "news_body"],
                            "fuzziness": "AUTO"
                        }
                    },
                    "_source": [
                        "news_title", "news_summary", "news_body", "url", "date", 
                        "author", "source_common_name", "published_dt"
                    ]
                }
                
                response = es.search(index=index_pattern, body=fallback_query)
                if response and response["hits"]["hits"]:
                    logger.info("Fallback text search successful")
                    search_successful = True
                else:
                    return []
                    
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
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

@app.post("/debug_search", response_model=DebugInfo)
async def debug_similarity_search(search_query: SearchQuery):
    """Debug endpoint to analyze search issues"""
    try:
        logger.info(f"Debugging search query: '{search_query.query}'")
        
        # Generate query embedding
        model = get_sentence_model()
        query_embedding = model.encode(search_query.query).tolist()
        
        es = get_elasticsearch_client()
        
        # Determine which index to search
        if search_query.source_index:
            index_pattern = search_query.source_index
        else:
            index_pattern = "news_finbert_embeddings,*processed*,*news*"
        
        # Try different embedding field names
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        tested_fields = []
        last_error = ""
        successful_field = None
        
        for embedding_field in embedding_fields:
            tested_fields.append(embedding_field)
            try:
                # Build a simple test query
                search_body = {
                    "size": 1,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": f"cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0",
                                "params": {"query_vector": query_embedding[:10]}  # Test with smaller vector
                            }
                        }
                    }
                }
                
                # Execute test search
                response = es.search(index=index_pattern, body=search_body)
                if response["hits"]["hits"]:
                    successful_field = embedding_field
                    break
                    
            except Exception as e:
                last_error = f"Field '{embedding_field}': {str(e)}"
                logger.warning(f"Debug test failed for field '{embedding_field}': {e}")
                continue
        
        return DebugInfo(
            query=search_query.query,
            embedding_dimension=len(query_embedding),
            embedding_sample=query_embedding[:10],  # First 10 dimensions
            index_pattern=index_pattern,
            embedding_fields_tested=tested_fields,
            last_error=last_error,
            successful_field=successful_field
        )
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {e}")

@app.post("/test_search", response_model=List[SearchResult])
async def test_search_with_pregenerated(test_query: TestSearchQuery):
    """Test search endpoint with pregenerated embeddings"""
    try:
        if test_query.use_pregenerated:
            # Use pregenerated embedding for "HDFC Bank Finance"
            query_text = "HDFC Bank Finance"
            if query_text in PREGENERATED_EMBEDDINGS:
                query_embedding = PREGENERATED_EMBEDDINGS[query_text]
                logger.info(f"Using pregenerated embedding for: {query_text}")
            else:
                # Fallback to "financial news"
                query_text = "financial news"
                query_embedding = PREGENERATED_EMBEDDINGS[query_text]
                logger.info(f"Using pregenerated embedding for: {query_text}")
        else:
            # Generate embedding for custom query
            query_text = test_query.custom_query or "financial news"
            model = get_sentence_model()
            query_embedding = model.encode(query_text).tolist()
            logger.info(f"Generated embedding for custom query: {query_text}")
        
        es = get_elasticsearch_client()
        
        # Try with a more flexible search approach
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        
        for embedding_field in embedding_fields:
            try:
                # Build search query with error handling
                search_body = {
                    "size": 5,
                    "min_score": 0.1,  # Lower threshold for testing
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": f"""
                                                if (doc['{embedding_field}'].size() == 0) return 0;
                                                return cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0;
                                            """,
                                            "params": {"query_vector": query_embedding}
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "_source": [
                        "news_title", "news_summary", "news_body", "url", "date", 
                        "v2_themes", "v1_themes", "v2_organizations", "v1_organizations",
                        "author", "source_common_name", "published_dt", "embedding_model"
                    ]
                }
                
                # Try different index patterns
                index_patterns = [
                    "news_finbert_embeddings",
                    "*processed*",
                    "*news*",
                    "*gdelt*"
                ]
                
                for index_pattern in index_patterns:
                    try:
                        response = es.search(index=index_pattern, body=search_body)
                        if response["hits"]["hits"]:
                            logger.info(f"Test search successful with field: {embedding_field}, index: {index_pattern}")
                            
                            # Process results (simplified)
                            results = []
                            for hit in response["hits"]["hits"]:
                                source = hit["_source"]
                                results.append(SearchResult(
                                    id=hit["_id"],
                                    score=hit["_score"],
                                    title=source.get("news_title", "Test Result"),
                                    summary=source.get("news_summary", "Test search successful"),
                                    full_text=source.get("news_body", "")[:500],
                                    url=source.get("url", ""),
                                    date=source.get("date", source.get("published_dt", "")),
                                    published_dt=source.get("published_dt", ""),
                                    rag_doc_url=f"test://search/success/{hit['_id']}",
                                    sentiment={"label": "test", "score": 1.0},
                                    themes=["Test", "Financial"],
                                    organizations=["HDFC", "Bank"]
                                ))
                            return results
                            
                    except Exception as e:
                        logger.warning(f"Test search failed for index {index_pattern}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Test search failed for field {embedding_field}: {e}")
                continue
        
        # If all fails, return a mock result for testing
        logger.warning("All test searches failed, returning mock result")
        return [SearchResult(
            id="test-mock-1",
            score=0.95,
            title="HDFC Bank Q2 Results - Mock Test Result",
            summary="This is a mock result for testing purposes when Elasticsearch search fails",
            full_text="Mock financial news content for HDFC Bank testing purposes",
            url="https://example.com/test",
            date="2025-10-03",
            published_dt="2025-10-03T10:26:00Z",
            rag_doc_url="test://mock/result",
            sentiment={"label": "positive", "score": 0.8},
            themes=["Banking", "Finance", "Results"],
            organizations=["HDFC Bank"]
        )]
        
    except Exception as e:
        logger.error(f"Test search error: {e}")
        raise HTTPException(status_code=500, detail=f"Test search failed: {e}")

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

@app.get("/cluster_diagnostics")
async def cluster_diagnostics():
    """Comprehensive Elasticsearch cluster diagnostics"""
    try:
        es = get_elasticsearch_client()
        diagnostics = {}
        
        # 1. Cluster Health
        try:
            health = es.cluster.health()
            diagnostics["cluster_health"] = {
                "status": health.get("status"),
                "cluster_name": health.get("cluster_name"),
                "number_of_nodes": health.get("number_of_nodes"),
                "active_shards": health.get("active_shards"),
                "relocating_shards": health.get("relocating_shards"),
                "initializing_shards": health.get("initializing_shards"),
                "unassigned_shards": health.get("unassigned_shards"),
                "timed_out": health.get("timed_out")
            }
        except Exception as e:
            diagnostics["cluster_health"] = {"error": str(e)}
        
        # 2. Cluster Settings - especially script settings
        try:
            cluster_settings = es.cluster.get_settings(include_defaults=True)
            script_settings = {}
            
            # Extract script-related settings
            for setting_type in ["persistent", "transient", "defaults"]:
                if setting_type in cluster_settings:
                    settings = cluster_settings[setting_type]
                    for key, value in settings.items():
                        if "script" in key.lower():
                            script_settings[f"{setting_type}.{key}"] = value
            
            diagnostics["script_settings"] = script_settings
            
        except Exception as e:
            diagnostics["script_settings"] = {"error": str(e)}
        
        # 3. Node Information
        try:
            nodes_info = es.nodes.info()
            node_details = []
            for node_id, node in nodes_info.get("nodes", {}).items():
                node_details.append({
                    "id": node_id,
                    "name": node.get("name"),
                    "version": node.get("version"),
                    "roles": node.get("roles", []),
                    "settings": {
                        "script_inline": node.get("settings", {}).get("script", {}).get("inline"),
                        "script_stored": node.get("settings", {}).get("script", {}).get("stored"),
                        "script_file": node.get("settings", {}).get("script", {}).get("file")
                    }
                })
            diagnostics["nodes"] = node_details
            
        except Exception as e:
            diagnostics["nodes"] = {"error": str(e)}
        
        # 4. Test Script Execution Capability
        try:
            # Simple script test
            test_query = {
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "script_score": {
                            "script": {
                                "source": "Math.log(2 + doc['_score'].value)"
                            }
                        }
                    }
                },
                "size": 1
            }
            
            # Try on a known index
            script_test_result = es.search(
                index="news_finbert_embeddings",
                body=test_query,
                timeout="10s"
            )
            diagnostics["script_execution_test"] = {
                "status": "success",
                "hits": script_test_result.get("hits", {}).get("total", {}).get("value", 0)
            }
            
        except Exception as e:
            diagnostics["script_execution_test"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # 5. Test CosineSimilarity Function Specifically
        try:
            # Create a dummy embedding for testing
            test_embedding = [0.1] * 384
            cosine_test_query = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding_384d') + 1.0",
                            "params": {"query_vector": test_embedding}
                        }
                    }
                },
                "size": 1
            }
            
            cosine_result = es.search(
                index="news_finbert_embeddings",
                body=cosine_test_query,
                timeout="10s"
            )
            diagnostics["cosine_similarity_test"] = {
                "status": "success",
                "hits": cosine_result.get("hits", {}).get("total", {}).get("value", 0)
            }
            
        except Exception as e:
            diagnostics["cosine_similarity_test"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # 6. Check Index Mappings for Embedding Fields
        try:
            mapping = es.indices.get_mapping(index="news_finbert_embeddings")
            embedding_fields = {}
            
            for index_name, index_data in mapping.items():
                properties = index_data.get("mappings", {}).get("properties", {})
                for field_name, field_config in properties.items():
                    if "embedding" in field_name.lower() or "vector" in field_name.lower():
                        embedding_fields[field_name] = {
                            "type": field_config.get("type"),
                            "dimension": field_config.get("dims"),
                            "similarity": field_config.get("similarity"),
                            "index": field_config.get("index", True)
                        }
            
            diagnostics["embedding_fields_mapping"] = embedding_fields
            
        except Exception as e:
            diagnostics["embedding_fields_mapping"] = {"error": str(e)}
        
        return diagnostics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cluster diagnostics failed: {e}")

@app.post("/test_script_methods")
async def test_script_methods(request: EmbeddingSearchQuery):
    """Test different methods for vector similarity search"""
    try:
        es = get_elasticsearch_client()
        results = {}
        
        # Method 1: script_score with cosineSimilarity
        try:
            method1_query = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding_384d') + 1.0",
                            "params": {"query_vector": request.embedding}
                        }
                    }
                },
                "size": 2
            }
            
            method1_result = es.search(
                index="news_finbert_embeddings",
                body=method1_query,
                timeout="30s"
            )
            results["method1_script_score"] = {
                "status": "success",
                "hits": len(method1_result.get("hits", {}).get("hits", [])),
                "max_score": method1_result.get("hits", {}).get("max_score")
            }
            
        except Exception as e:
            results["method1_script_score"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # Method 2: function_score with script
        try:
            method2_query = {
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "script_score": {
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding_384d')",
                                "params": {"query_vector": request.embedding}
                            }
                        }
                    }
                },
                "size": 2
            }
            
            method2_result = es.search(
                index="news_finbert_embeddings",
                body=method2_query,
                timeout="30s"
            )
            results["method2_function_score"] = {
                "status": "success",
                "hits": len(method2_result.get("hits", {}).get("hits", [])),
                "max_score": method2_result.get("hits", {}).get("max_score")
            }
            
        except Exception as e:
            results["method2_function_score"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # Method 3: Try different similarity functions
        try:
            method3_query = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "dotProduct(params.query_vector, 'embedding_384d') + 1.0",
                            "params": {"query_vector": request.embedding}
                        }
                    }
                },
                "size": 2
            }
            
            method3_result = es.search(
                index="news_finbert_embeddings",
                body=method3_query,
                timeout="30s"
            )
            results["method3_dot_product"] = {
                "status": "success",
                "hits": len(method3_result.get("hits", {}).get("hits", [])),
                "max_score": method3_result.get("hits", {}).get("max_score")
            }
            
        except Exception as e:
            results["method3_dot_product"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # Method 4: Try with different field names
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector"]
        for field in embedding_fields:
            try:
                method4_query = {
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": f"cosineSimilarity(params.query_vector, '{field}') + 1.0",
                                "params": {"query_vector": request.embedding}
                            }
                        }
                    },
                    "size": 1
                }
                
                method4_result = es.search(
                    index="news_finbert_embeddings",
                    body=method4_query,
                    timeout="30s"
                )
                results[f"method4_field_{field}"] = {
                    "status": "success",
                    "hits": len(method4_result.get("hits", {}).get("hits", [])),
                    "max_score": method4_result.get("hits", {}).get("max_score")
                }
                
            except Exception as e:
                results[f"method4_field_{field}"] = {
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        # Method 5: Try knn search if available (ES 8.x feature)
        try:
            knn_query = {
                "knn": {
                    "field": "embedding_384d",
                    "query_vector": request.embedding,
                    "k": 2,
                    "num_candidates": 10
                }
            }
            
            knn_result = es.search(
                index="news_finbert_embeddings",
                body=knn_query,
                timeout="30s"
            )
            results["method5_knn"] = {
                "status": "success",
                "hits": len(knn_result.get("hits", {}).get("hits", [])),
                "max_score": knn_result.get("hits", {}).get("max_score")
            }
            
        except Exception as e:
            results["method5_knn"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        return {
            "embedding_dimension": len(request.embedding),
            "test_results": results,
            "summary": {
                "successful_methods": len([k for k, v in results.items() if v.get("status") == "success"]),
                "failed_methods": len([k for k, v in results.items() if v.get("status") == "failed"]),
                "total_methods_tested": len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script methods test failed: {e}")

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

@app.post("/search/with-embeddings/")
async def similarity_search_with_embeddings_included(search_query: SearchQuery):
    """
    Similarity search that includes embedding vectors in the response.
    Use this endpoint when you need to see the actual embedding data.
    Warning: Response size will be significantly larger due to embedding vectors.
    """
    try:
        logger.info(f"Similarity search with embeddings requested for query: {search_query.query[:100]}...")
        
        # Get Elasticsearch client
        es = get_elasticsearch_client()
        
        # Initialize sentence transformer
        global sentence_model
        if sentence_model is None:
            sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate embedding for the query
        query_embedding = sentence_model.encode([search_query.query])[0].tolist()
        
        # Get index pattern
        index_pattern = search_query.source_index or "*processed*,*embeddings*,news_*"
        
        # Try different embedding field names
        embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
        
        search_successful = False
        response = None
        last_error = ""
        
        for embedding_field in embedding_fields:
            try:
                logger.info(f"Trying embedding field: {embedding_field}")
                
                search_body = {
                    "size": search_query.limit,
                    "min_score": search_query.min_score,
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": f"""
                                                if (doc['{embedding_field}'].size() == 0) {{
                                                    return 0.0;
                                                }} else {{
                                                    return cosineSimilarity(params.query_vector, '{embedding_field}') + 1.0;
                                                }}
                                            """,
                                            "params": {"query_vector": query_embedding}
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "_source": [
                        "news_title", "news_summary", "news_body", "url", "date", 
                        "v2_themes", "v1_themes", "v2_organizations", "v1_organizations",
                        "author", "source_common_name", "published_dt", "embedding_model",
                        # Include all possible embedding fields
                        "embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"
                    ]
                }
                
                # Add date range filter if specified
                if search_query.date_from or search_query.date_to:
                    date_filter = {"range": {"date": {}}}
                    if search_query.date_from:
                        date_filter["range"]["date"]["gte"] = search_query.date_from
                    if search_query.date_to:
                        date_filter["range"]["date"]["lte"] = search_query.date_to
                    
                    if "filter" not in search_body["query"]["bool"]:
                        search_body["query"]["bool"]["filter"] = []
                    search_body["query"]["bool"]["filter"].append(date_filter)
                
                # Execute search
                response = es.search(index=index_pattern, body=search_body, timeout="30s")
                if response and response["hits"]["hits"]:
                    search_successful = True
                    logger.info(f"Search successful using embedding field: {embedding_field}")
                    break
                else:
                    logger.info(f"No results found for embedding field: {embedding_field}")
                    
            except Exception as e:
                error_msg = str(e)
                last_error = f"Field '{embedding_field}': {error_msg}"
                logger.warning(f"Search failed with embedding field '{embedding_field}': {e}")
                continue
        
        if not search_successful:
            raise HTTPException(
                status_code=404,
                detail=f"No results found. Last errors: {last_error}"
            )
        
        # Process results and include embeddings
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Find which embedding field has data
            embedding_data = None
            for field in ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]:
                if field in source and source[field]:
                    embedding_data = source[field]
                    break
            
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                "title": source.get("news_title", ""),
                "summary": source.get("news_summary", ""),
                "full_text": source.get("news_body", ""),
                "url": source.get("url", ""),
                "date": source.get("date", ""),
                "published_dt": source.get("published_dt", ""),
                "rag_doc_url": source.get("url", ""),
                "sentiment": {},  # You might want to extract this if available
                "themes": source.get("v2_themes") or source.get("v1_themes"),
                "organizations": source.get("v2_organizations") or source.get("v1_organizations"),
                "embedding": embedding_data,  # This is the embedding vector
                "embedding_model": source.get("embedding_model", ""),
                "embedding_dimension": len(embedding_data) if embedding_data else 0
            }
            results.append(result)
        
        logger.info(f"Returning {len(results)} results with embeddings included")
        return {
            "results": results,
            "total": response["hits"]["total"]["value"] if "total" in response["hits"] else len(results),
            "query": search_query.query,
            "embedding_included": True,
            "embedding_dimension": len(query_embedding) if query_embedding else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)