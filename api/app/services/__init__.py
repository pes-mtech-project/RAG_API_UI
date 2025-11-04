"""
Services package initialization
"""

from .elasticsearch_service import ElasticsearchService
from .embedding_service import EmbeddingService
from .search_service import SearchService
from .model_preloader import ModelPreloader
from .search_config_service import (
    list_configs,
    get_config,
    create_config,
    update_config,
    add_tags,
    remove_tag,
    add_phrases,
    update_phrase,
    remove_phrase,
    delete_config,
)
from .sector_news_service import search_sector_news

# Create service instances
elasticsearch_service = ElasticsearchService()
embedding_service = EmbeddingService()
search_service = SearchService()

__all__ = [
    'ElasticsearchService',
    'EmbeddingService',
    'SearchService',
    'ModelPreloader',
    'elasticsearch_service',
    'embedding_service',
    'search_service',
    'list_configs',
    'get_config',
    'create_config',
    'update_config',
    'add_tags',
    'remove_tag',
    'add_phrases',
    'update_phrase',
    'remove_phrase',
    'delete_config',
    'search_sector_news',
]
