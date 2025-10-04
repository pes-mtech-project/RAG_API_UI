"""
Services package initialization
"""

from .elasticsearch_service import ElasticsearchService
from .embedding_service import EmbeddingService
from .search_service import SearchService
from .model_preloader import ModelPreloader

# Create service instances
elasticsearch_service = ElasticsearchService()
embedding_service = EmbeddingService()
search_service = SearchService()

__all__ = ['ElasticsearchService', 'EmbeddingService', 'SearchService', 'ModelPreloader', 
           'elasticsearch_service', 'embedding_service', 'search_service']

__all__ = ['elasticsearch_service', 'embedding_service', 'search_service']