"""
Search router with new cosine similarity endpoints
Implements the new API endpoints for different embedding dimensions
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List

from ..models.schemas import SearchQuery, SearchResponse, EmbeddingResponse
from ..services import search_service, embedding_service, ModelPreloader

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

@router.post("/cosine/embedding384d/", 
            response_model=SearchResponse,
            summary="Search using 384-dimensional embeddings with cosine similarity")
async def search_cosine_384d(query: SearchQuery):
    """
    Perform vector search using 384-dimensional embeddings with cosine similarity.
    
    Uses the all-MiniLM-L6-v2 model for embedding generation and searches
    the embedding_384d field in Elasticsearch indices.
    """
    try:
        logger.info(f"Processing 384d cosine search query: '{query.query}'")
        
        results = await search_service.search_with_embedding_384d(
            query=query.query,
            limit=query.limit,
            min_score=query.min_score
        )
        
        return SearchResponse(
            results=results,
            total_hits=len(results),
            query=query.query,
            embedding_field="embedding_384d",
            search_time_ms=0.0  # Will be calculated properly later
        )
        
    except Exception as e:
        logger.error(f"384d search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/cosine/embedding768d/", 
            response_model=SearchResponse,
            summary="Search using 768-dimensional embeddings with cosine similarity")
async def search_cosine_768d(query: SearchQuery):
    """
    Perform vector search using 768-dimensional embeddings with cosine similarity.
    
    Uses the all-mpnet-base-v2 model for embedding generation and searches
    the embedding_768d field in Elasticsearch indices.
    """
    try:
        logger.info(f"Processing 768d cosine search query: '{query.query}'")
        
        results = await search_service.search_with_embedding_768d(
            query=query.query,
            limit=query.limit,
            min_score=query.min_score
        )
        
        return SearchResponse(
            results=results,
            total_hits=len(results),
            query=query.query,
            embedding_field="embedding_768d",
            search_time_ms=0.0  # Will be calculated properly later
        )
        
    except Exception as e:
        logger.error(f"768d search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/cosine/embedding1155d/", 
            response_model=SearchResponse,
            summary="Search using 1155-dimensional enhanced embeddings with cosine similarity")
async def search_cosine_1155d(query: SearchQuery):
    """
    Perform vector search using 1155-dimensional enhanced embeddings with cosine similarity.
    
    Uses the enhanced embedding field that combines 384d + 768d + 3d sentiment vectors.
    """
    try:
        logger.info(f"Processing 1155d enhanced cosine search query: '{query.query}'")
        
        results = await search_service.search_with_embedding_enhanced(
            query=query.query,
            limit=query.limit,
            min_score=query.min_score
        )
        
        return SearchResponse(
            results=results,
            total_hits=len(results),
            query=query.query,
            embedding_field="embedding_enhanced",
            search_time_ms=0.0  # Will be calculated properly later
        )
        
    except Exception as e:
        logger.error(f"1155d enhanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/embedding-compatibility/",
           summary="Get embedding compatibility information")
async def embedding_compatibility():
    """
    Get information about available embedding endpoints and their compatibility.
    """
    try:
        return {
            "status": "operational",
            "available_endpoints": {
                "384d": {
                    "endpoint": "/search/cosine/embedding384d/",
                    "model": "all-MiniLM-L6-v2",
                    "dimensions": 384,
                    "description": "Fast semantic search",
                    "use_case": "Quick queries and real-time search"
                },
                "768d": {
                    "endpoint": "/search/cosine/embedding768d/", 
                    "model": "all-mpnet-base-v2",
                    "dimensions": 768,
                    "description": "High-quality semantic search",
                    "use_case": "Accurate semantic matching"
                },
                "1155d": {
                    "endpoint": "/search/cosine/embedding1155d/",
                    "model": "enhanced (384d + 768d + 3d sentiment)",
                    "dimensions": 1155,
                    "description": "Financial-enhanced search with sentiment",
                    "use_case": "Advanced financial analysis and sentiment-aware search"
                }
            },
            "supported_operations": ["cosine_similarity"],
            "api_version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Failed to get embedding compatibility: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility info retrieval failed: {str(e)}")

@router.get("/model-cache-info/",
           summary="Get model cache information")
async def get_model_cache_info():
    """
    Get information about cached models and cache status.
    """
    try:
        preloader = ModelPreloader()
        cache_info = preloader.get_model_cache_info()
        return {
            "status": "success",
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        raise HTTPException(status_code=500, detail=f"Cache info retrieval failed: {str(e)}")