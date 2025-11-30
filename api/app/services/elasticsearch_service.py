"""
Elasticsearch service layer
Handles all Elasticsearch operations following Single Responsibility Principle
"""

import logging
import base64
from typing import Optional, List, Dict, Any, Tuple
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError

from ..config import elasticsearch_config

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """
    Service class for Elasticsearch operations
    Implements Repository pattern for data access
    """
    
    def __init__(self):
        self._client: Optional[Elasticsearch] = None
        self._connection_verified = False
    
    def get_client(self) -> Elasticsearch:
        """
        Get Elasticsearch client with lazy initialization
        Implements Singleton pattern for connection management
        """
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    def _initialize_client(self) -> Elasticsearch:
        """Initialize and test Elasticsearch connection"""
        config = elasticsearch_config
        
        logger.info(f"🔗 Connecting to Elasticsearch: {config.host}")
        
        # Try multiple authentication methods
        auth_methods = [
            ("api_key", lambda: Elasticsearch(config.host, api_key=config.api_key, **config.ssl_config)),
        ]
        
        # Add basic auth for local Docker if applicable
        if config.is_local_docker:
            auth_methods.append(("basic_auth", lambda: self._try_basic_auth(config)))
        
        # Add decoded API key as fallback
        auth_methods.append(("decoded_api_key", 
                           lambda: Elasticsearch(config.host, 
                                               api_key=base64.b64decode(config.api_key).decode('utf-8'), 
                                               **config.ssl_config)))
        
        for method_name, method_func in auth_methods:
            try:
                client = method_func()
                # Test the connection
                cluster_info = client.info()
                logger.info(f"✅ Elasticsearch connected via {method_name}")
                logger.info(f"   Cluster: {cluster_info.get('cluster_name', 'unknown')}")
                logger.info(f"   Version: {cluster_info.get('version', {}).get('number', 'unknown')}")
                self._connection_verified = True
                return client
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {e}")
                continue
        
        raise ConnectionError("Failed to connect to Elasticsearch with any authentication method")
    
    def _try_basic_auth(self, config) -> Elasticsearch:
        """Try basic authentication for local Docker setup"""
        basic_auth_configs = [
            ("elastic", "elastic"),
            ("elastic", "changeme"),
        ]
        
        for username, password in basic_auth_configs:
            try:
                return Elasticsearch(
                    config.host,
                    basic_auth=(username, password),
                    **config.ssl_config
                )
            except:
                continue
        
        raise ConnectionError("Basic auth failed for local Docker")
    
    def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        try:
            client = self.get_client()
            health = client.cluster.health()
            return {
                "status": health.get("status", "unknown"),
                "cluster_name": health.get("cluster_name", "unknown"),
                "number_of_nodes": health.get("number_of_nodes", 0),
                "active_primary_shards": health.get("active_primary_shards", 0),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "red", "error": str(e)}
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get comprehensive cluster statistics"""
        try:
            client = self.get_client()
            
            # Get indices stats
            indices_stats = {}
            index_patterns = ["*news*", "*gdelt*", "*processed*", "news_finbert_embeddings*"]
            
            total_documents = 0
            for pattern in index_patterns:
                try:
                    count_response = client.count(index=pattern)
                    doc_count = count_response.get('count', 0)
                    indices_stats[pattern] = {
                        "doc_count": doc_count,
                        "size_in_bytes": 0,  # Would need indices API for actual size
                        "date_range": {"from": "N/A", "to": "N/A"}
                    }
                    total_documents += doc_count
                except Exception as e:
                    logger.warning(f"Failed to get stats for {pattern}: {e}")
                    indices_stats[pattern] = {"doc_count": 0, "size_in_bytes": 0, 
                                            "date_range": {"from": "N/A", "to": "N/A"}}
            
            health = self.health_check()
            
            return {
                "total_documents": total_documents,
                "total_indices": len(indices_stats),
                "indices": [{"index_name": k, **v} for k, v in indices_stats.items()],
                "cluster_health": health.get("status", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to get cluster stats: {e}")
            raise
    
    def get_available_fields(self, indices: str) -> List[str]:
        """Get available fields from specified indices"""
        try:
            client = self.get_client()
            mapping_response = client.indices.get_mapping(index=indices)
            
            all_fields = set()
            for index_name, index_data in mapping_response.items():
                properties = index_data.get('mappings', {}).get('properties', {})
                all_fields.update(properties.keys())
            
            return sorted(list(all_fields))
        except Exception as e:
            logger.error(f"Failed to get fields for {indices}: {e}")
            return []
    
    def vector_search(self, 
                     query_vector: List[float], 
                     embedding_field: str,
                     indices: str = "news_finbert_embeddings*,*processed*,*news*",
                     size: int = 10,
                     min_score: float = 0.5) -> Dict[str, Any]:
        """
        Perform vector similarity search using cosine similarity
        
        Args:
            query_vector: Query embedding vector
            embedding_field: Field name containing embeddings
            indices: Comma-separated index names or patterns
            size: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            Search results dictionary
        """
        try:
            client = self.get_client()
            
            # Build k-NN search query with cosine similarity
            # Use the knn parameter at top level (Elasticsearch 8.x format)
            search_body = {
                "knn": {
                    "field": embedding_field,
                    "query_vector": query_vector,
                    "k": size,
                    "num_candidates": size * 3  # For better recall
                },
                "size": size,
                "min_score": min_score,
                "_source": {
                    "excludes": [embedding_field]  # Exclude large embedding field from results
                }
            }
            
            logger.info(f"Attempting k-NN search with field '{embedding_field}' on indices '{indices}'")
            
            response = client.search(
                index=indices,
                body=search_body,
                request_timeout=30
            )
            
            logger.info(f"✅ k-NN search successful using embedding field: {embedding_field}")
            logger.info(f"Found {len(response['hits']['hits'])} results")
            
            return response
        except Exception as e:
            logger.error(f"Vector search failed for field {embedding_field}: {e}")
            raise
    
    def test_embedding_field(self, field_name: str, dimension: int = 384, index: str = "news_finbert_embeddings*") -> bool:
        """Test if an embedding field exists and works for k-NN search"""
        try:
            # Use a test vector with correct dimension
            test_vector = [0.1] * dimension
            
            response = self.vector_search(
                query_vector=test_vector,
                embedding_field=field_name,
                indices=index,
                size=1,
                min_score=0.0
            )
            
            return len(response['hits']['hits']) > 0
        except Exception as e:
            logger.warning(f"Test failed for field {field_name}: {e}")
            return False
    
    async def search_by_embedding_async(self, 
                                      query_vector: List[float],
                                      field_name: str,
                                      size: int = 10,
                                      min_score: float = 0.5,
                                      indices: str = "news_finbert_embeddings*,*processed*,*news*") -> List[Dict[str, Any]]:
        """
        Perform asynchronous k-NN search using embedding vector
        
        Args:
            query_vector: The embedding vector to search with
            field_name: The field containing embeddings (e.g., embedding_384d)
            size: Number of results to return
            min_score: Minimum similarity score
            indices: Comma-separated list of indices to search
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            client = self.get_client()
            
            # Construct k-NN search body for Elasticsearch 8.x
            search_body = {
                "knn": {
                    "field": field_name,
                    "query_vector": query_vector,
                    "k": size,
                    "num_candidates": size * 5
                },
                "size": size,
                "_source": True
            }
            
            if min_score > 0:
                search_body["min_score"] = min_score
            
            # Execute search
            response = client.search(
                index=indices,
                body=search_body
            )
            
            # Parse results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                
                # Convert result to consistent format
                result = {
                    "id": hit.get('_id', 'unknown'),
                    "score": hit.get('_score', 0.0),
                    "title": source.get('news_title') or source.get('title', 'No title'),
                    "summary": source.get('news_summary') or source.get('summary', 'No summary available'),
                    "full_text": source.get('news_body') or source.get('full_text', source.get('content', '')),
                    "url": source.get('url', ''),
                    "date": source.get('date') or source.get('published_date', ''),
                    "published_dt": source.get('published_dt', ''),
                    "rag_doc_url": f"https://my-elasticsearch-project-a901ed.kb.asia-south1.gcp.elastic.cloud/app/discover#/doc/news_finbert_embeddings/news_finbert_embeddings?id={hit.get('_id', '')}",
                    "sentiment": source.get('sentiment', {"label": "neutral", "score": 0.0}),
                    "themes": self._safe_list_conversion(source.get('v2_themes') or source.get('themes', [])),
                    "organizations": self._safe_list_conversion(source.get('organizations', [])),
                    "source_index": hit.get('_index', '')
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"k-NN search failed: {e}")
            raise
    
    def _safe_list_conversion(self, value) -> List[str]:
        """Convert various types to list of strings safely"""
        if isinstance(value, str):
            return [value] if value.strip() else []
        elif isinstance(value, list):
            return [str(item) for item in value if item]
        else:
            return []

# Global service instance
elasticsearch_service = ElasticsearchService()
