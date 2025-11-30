"""
Search service layer
Orchestrates embedding generation and vector search operations
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .elasticsearch_service import elasticsearch_service
from .embedding_service import embedding_service
from ..models.schemas import SearchQuery, SearchResult, SearchResponse
from ..config import embedding_config

logger = logging.getLogger(__name__)

class SearchService:
    """
    High-level search service that orchestrates embedding and search operations
    Implements the Facade pattern to provide a simple interface for complex operations
    """
    
    def __init__(self):
        self.es_service = elasticsearch_service
        self.embedding_service = embedding_service
    
    async def search_with_embedding_384d(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.5,
        indices: Optional[str] = None,
    ):
        """Search using 384-dimensional embeddings"""
        return await self._search_with_embedding(
            query,
            "384d",
            "embedding_384d",
            limit,
            min_score,
            indices=indices,
        )
    
    async def search_with_embedding_768d(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.5,
        indices: Optional[str] = None,
    ):
        """Search using 768-dimensional embeddings"""
        return await self._search_with_embedding(
            query,
            "768d",
            "embedding_768d",
            limit,
            min_score,
            indices=indices,
        )
    
    async def search_with_embedding_enhanced(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.5,
        indices: Optional[str] = None,
    ):
        """Search using enhanced 1155-dimensional embeddings"""
        return await self._search_with_embedding(
            query,
            "1155d",
            "embedding_enhanced",
            limit,
            min_score,
            indices=indices,
        )
    
    async def _search_with_embedding(
        self,
        query: str,
        model_type: str,
        field_name: str,
        limit: int,
        min_score: float,
        *,
        indices: Optional[str] = None,
    ):
        """Internal method to perform embedding-based search"""
        try:
            # Generate embedding for query
            if model_type == "384d":
                embedding = self.embedding_service.generate_embedding_384d(query)
            elif model_type == "768d":
                embedding = self.embedding_service.generate_embedding_768d(query)
            elif model_type == "1155d":
                embedding = self.embedding_service.generate_embedding_1155d(query)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Perform Elasticsearch k-NN search
            results = await self.es_service.search_by_embedding_async(
                query_vector=embedding,
                field_name=field_name,
                size=limit,
                min_score=min_score,
                indices=indices or "news_finbert_embeddings*,*processed*,*news*",
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for {model_type}: {e}")
            raise
    
    def search_with_cosine_similarity(self, 
                                    query: SearchQuery, 
                                    embedding_type: str) -> SearchResponse:
        """
        Perform search using cosine similarity with specified embedding type
        
        Args:
            query: Search query parameters
            embedding_type: Type of embedding to use (384d, 768d, 1155d)
            
        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()
        
        try:
            # Generate query embedding
            # Note: embedding_service.generate_embedding expects 'model_type' kwarg
            embedding_result = self.embedding_service.generate_embedding(
                text=query.query,
                model_type=embedding_type
            )
            query_vector = embedding_result["embedding"]
            
            # Get appropriate embedding field
            embedding_field = self.embedding_service.get_embedding_field(embedding_type)
            
            # Determine indices to search
            indices = query.source_index or "news_finbert_embeddings*,*processed*,*news*"
            
            # Perform vector search
            es_response = self.es_service.vector_search(
                query_vector=query_vector,
                embedding_field=embedding_field,
                indices=indices,
                size=query.limit,
                min_score=query.min_score
            )
            
            # Convert Elasticsearch results to SearchResult objects
            search_results = self._convert_es_results(es_response['hits']['hits'])
            
            # Apply date filtering if specified
            if query.date_from or query.date_to:
                search_results = self._filter_by_date(search_results, query.date_from, query.date_to)
            
            search_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Search completed: {len(search_results)} results in {search_time_ms:.2f}ms")
            
            return SearchResponse(
                results=search_results,
                total_hits=es_response['hits']['total']['value'],
                query=query.query,
                embedding_field=embedding_field,
                search_time_ms=search_time_ms
            )
        
        except Exception as e:
            logger.error(f"Search failed for {embedding_type} embedding: {e}")
            raise
    
    def _convert_es_results(self, hits: List[Dict]) -> List[SearchResult]:
        """Convert Elasticsearch hits to SearchResult objects"""
        results = []
        
        for hit in hits:
            source = hit.get('_source', {})
            
            # Extract fields with fallbacks
            result = SearchResult(
                id=hit.get('_id', ''),
                score=hit.get('_score', 0.0),
                title=source.get('news_title') or source.get('title'),
                summary=source.get('news_summary') or source.get('summary'),
                full_text=source.get('news_body') or source.get('full_text'),
                url=source.get('url'),
                date=source.get('date') or source.get('DATE'),
                published_dt=source.get('published_dt') or source.get('published_at'),
                rag_doc_url=self._generate_rag_doc_url(hit.get('_id', ''), hit.get('_index', '')),
                sentiment=source.get('sentiment', {"label": "negative", "score": 0.0}),
                themes=self._parse_list_field(source.get('V2Themes') or source.get('v2_themes') or source.get('themes', [])),
                organizations=self._parse_list_field(source.get('V2Organizations') or source.get('organizations', []))
            )
            
            results.append(result)
        
        return results
    
    def _parse_list_field(self, field_value) -> List[str]:
        """Parse field that might be a string, list, or None into a proper list"""
        if isinstance(field_value, list):
            return field_value
        elif isinstance(field_value, str):
            # Split by common separators and clean up
            if ',' in field_value:
                return [item.strip() for item in field_value.split(',') if item.strip()]
            elif ';' in field_value:
                return [item.strip() for item in field_value.split(';') if item.strip()]
            else:
                return [field_value.strip()] if field_value.strip() else []
        else:
            return []
    
    def _generate_rag_doc_url(self, doc_id: str, index: str) -> str:
        """Generate RAG document URL for Kibana/Elasticsearch viewing"""
        base_url = "https://my-elasticsearch-project-a901ed.kb.asia-south1.gcp.elastic.cloud"
        return f"{base_url}/app/discover#/doc/{index}/{index}?id={doc_id}"
    
    def _filter_by_date(self, 
                       results: List[SearchResult], 
                       date_from: Optional[str], 
                       date_to: Optional[str]) -> List[SearchResult]:
        """Filter results by date range (client-side filtering)"""
        if not date_from and not date_to:
            return results
        
        filtered = []
        for result in results:
            result_date = result.date or result.published_dt
            if not result_date:
                continue
            
            try:
                # Parse date (handle different formats)
                if len(str(result_date)) == 14:  # YYYYMMDDHHMMSS format
                    parsed_date = datetime.strptime(str(result_date)[:8], '%Y%m%d')
                else:
                    # Try ISO format
                    parsed_date = datetime.fromisoformat(str(result_date).replace('Z', '+00:00'))
                
                # Check date range
                if date_from:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d')
                    if parsed_date < from_date:
                        continue
                
                if date_to:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d')
                    if parsed_date > to_date:
                        continue
                
                filtered.append(result)
            except Exception as e:
                logger.warning(f"Date parsing failed for {result_date}: {e}")
                # Include result if date parsing fails
                filtered.append(result)
        
        return filtered
    
    def test_embedding_compatibility(self, embedding_type: str) -> Dict[str, Any]:
        """
        Test if the specified embedding type works with available data
        
        Args:
            embedding_type: Type of embedding to test (384d, 768d, 1155d)
            
        Returns:
            Test results dictionary
        """
        embedding_field = None
        try:
            # Get embedding field name and dimension
            embedding_field = self.embedding_service.get_embedding_field(embedding_type)
            dimension = getattr(embedding_config, f"dim_{embedding_type}")
            
            # Test the field directly with Elasticsearch
            field_works = self.es_service.test_embedding_field(embedding_field, dimension)
            
            if field_works:
                return {
                    "compatible": True,
                    "embedding_field": embedding_field,
                    "test_results": 1,
                    "dimension": dimension
                }
            else:
                return {
                    "compatible": False,
                    "error": f"Field {embedding_field} exists but k-NN search failed",
                    "embedding_field": embedding_field
                }
            
        except Exception as e:
            logger.error(f"Compatibility test failed for {embedding_type}: {e}")
            return {
                "compatible": False,
                "error": str(e),
                "embedding_field": embedding_field
            }
    
    def get_available_embedding_types(self) -> List[Dict[str, Any]]:
        """Get list of available embedding types with their compatibility status"""
        embedding_types = ["384d", "768d", "1155d"]
        results = []
        
        for embedding_type in embedding_types:
            test_result = self.test_embedding_compatibility(embedding_type)
            
            results.append({
                "type": embedding_type,
                "dimension": getattr(embedding_config, f"dim_{embedding_type}", None),
                "field": self.embedding_service.get_embedding_field(embedding_type),
                "compatible": test_result.get("compatible", False),
                "error": test_result.get("error")
            })
        
        return results

# Global service instance
search_service = SearchService()
