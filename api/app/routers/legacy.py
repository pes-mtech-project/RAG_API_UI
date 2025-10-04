"""
Legacy API router
Maintains compatibility with existing API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from ..models.schemas import SearchQuery, HealthResponse, StatsResponse
from ..services import elasticsearch_service, search_service, embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["legacy"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", summary="API Information")
async def root():
    """Get basic API information"""
    return {
        "message": "FinBERT News RAG API", 
        "version": "2.0.0", 
        "status": "operational",
        "features": [
            "Multi-dimensional embedding search",
            "Cosine similarity search",
            "Enhanced financial embeddings",
            "Modular architecture"
        ]
    }

@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Comprehensive health check for the API and its dependencies
    """
    try:
        # Check Elasticsearch health
        es_health = elasticsearch_service.health_check()
        
        return HealthResponse(
            status="healthy",
            api="operational",
            elasticsearch=es_health.get("status", "unknown"),
            timestamp=str(datetime.utcnow().isoformat())
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.get("/stats", response_model=StatsResponse, summary="Cluster Statistics")
async def get_stats():
    """
    Get comprehensive Elasticsearch cluster statistics
    """
    try:
        stats = elasticsearch_service.get_cluster_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")

@router.post("/search", summary="Legacy Search Endpoint")
async def legacy_search(query: SearchQuery):
    """
    Legacy search endpoint for backward compatibility.
    Defaults to 384d embedding search.
    
    **Note:** This endpoint is maintained for compatibility.
    For new applications, use the specific cosine similarity endpoints:
    - `/search/cosine/embedding384d/`
    - `/search/cosine/embedding768d/` 
    - `/search/cosine/embedding1155d/`
    """
    try:
        logger.info(f"Processing legacy search query: '{query.query}'")
        # Default to 384d for backward compatibility
        result = search_service.search_with_cosine_similarity(query, "384d")
        
        # Convert to legacy format (list of dictionaries)
        legacy_results = []
        for item in result.results:
            legacy_results.append(item.dict())
        
        return legacy_results
    except Exception as e:
        logger.error(f"Legacy search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/generate_embedding", summary="Legacy Embedding Generation")
async def legacy_generate_embedding(
    text: str = Query(..., description="Text to generate embedding for")
):
    """
    Legacy embedding generation endpoint.
    Defaults to 384d embedding for backward compatibility.
    
    **Note:** For new applications, use `/search/generate-embedding/` 
    with explicit embedding type specification.
    """
    try:
        logger.info(f"Generating legacy embedding for text: '{text[:50]}...'")
        
        result = embedding_service.generate_embedding(text, "384d")
        
        return {
            "text": text,
            "embedding": result["embedding"],
            "dimension": result["dimension"]
        }
    except Exception as e:
        logger.error(f"Legacy embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.get("/debug_search", summary="Debug Search Information")
async def debug_search():
    """
    Debug endpoint to show available search capabilities
    """
    try:
        # Get available fields
        fields = elasticsearch_service.get_available_fields("news_finbert_embeddings,*processed*,*news*")
        
        # Get embedding compatibility
        embedding_types = search_service.get_available_embedding_types()
        
        return {
            "available_fields": fields[:20],  # Limit for readability
            "embedding_compatibility": embedding_types,
            "indices_info": "Searches across: news_finbert_embeddings, *processed*, *news*",
            "search_methods": [
                "POST /search/cosine/embedding384d/ - Fast 384d semantic search",
                "POST /search/cosine/embedding768d/ - High-quality 768d search", 
                "POST /search/cosine/embedding1155d/ - Enhanced financial search"
            ]
        }
    except Exception as e:
        logger.error(f"Debug search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

# Import datetime for health check
from datetime import datetime