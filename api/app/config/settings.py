"""
Configuration module for FinBERT News RAG API
Handles environment variables and application settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ElasticsearchConfig:
    """Elasticsearch configuration settings"""
    
    def __init__(self):
        # Prefer new ES_READONLY_* variables but fall back to legacy ES_CLOUD_* secrets and finally the legacy default.
        host_env = os.getenv('ES_READONLY_HOST') or os.getenv('ES_CLOUD_HOST')
        self.host = host_env or 'https://my-elasticsearch-project-a901ed.es.asia-south1.gcp.elastic.cloud:443'

        self.unrestricted_key = os.getenv('ES_UNRESTRICTED_KEY') or os.getenv('ES_CLOUD_KEY')

        readonly_key_env = os.getenv('ES_READONLY_KEY') or os.getenv('ES_CLOUD_KEY')
        self.readonly_key = readonly_key_env or 'ZzlOZ21aa0JBUXZGb3RVb01rLUY6blBPOVphYmE2MjVTZ1o2eGZWOUpxQQ=='
        self.search_config_index = os.getenv('SEARCH_CONFIG_INDEX', 'finbert-search-configs')
        
        # Determine if we're connecting to local Docker Elasticsearch
        self.is_local_docker = 'host.docker.internal' in self.host or 'localhost' in self.host
        
        # SSL configuration
        self.ssl_config = {
            'verify_certs': not self.is_local_docker,
            'ssl_show_warn': False,
            'request_timeout': 30
        }
        
    @property
    def api_key(self) -> str:
        """Get the appropriate API key"""
        return self.unrestricted_key or self.readonly_key

class APIConfig:
    """API configuration settings"""
    
    def __init__(self):
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', 8000))
        self.finbert_model_path = os.getenv('FINBERT_MODEL_PATH', '/app/models/finbert')
        self.cache_size = int(os.getenv('CACHE_SIZE', 1000))

class EmbeddingConfig:
    """Embedding model configuration"""
    
    def __init__(self):
        # Model configurations for different embedding dimensions
        self.model_384d = 'all-MiniLM-L6-v2'
        self.model_768d = 'all-mpnet-base-v2'
        
        # Field names in Elasticsearch
        self.field_384d = 'embedding_384d'
        self.field_768d = 'embedding_768d'
        self.field_1155d = 'embedding_enhanced'
        
        # Dimensions
        self.dim_384d = 384
        self.dim_768d = 768
        self.dim_1155d = 1155  # 384 + 768 + 3 (sentiment)

class RAGConfig:
    """Quality and gating settings for RAG retrieval"""

    def __init__(self):
        self.min_quality_score_for_rag = float(os.getenv("MIN_QUALITY_SCORE_FOR_RAG", 0.5))
        doc_types = os.getenv(
            "ALLOWED_DOC_TYPES_FOR_RAG",
            "news_article,press_release",
        )
        self.allowed_doc_types_for_rag = [t.strip() for t in doc_types.split(",") if t.strip()]
        self.usable_for_rag_field = os.getenv("USABLE_FOR_RAG_FIELD", "usable_for_rag")
        self.doc_type_field = os.getenv("DOC_TYPE_FIELD", "doc_type.keyword")
        self.quality_score_field = os.getenv("QUALITY_SCORE_FIELD", "quality_score")

# Global configuration instances
elasticsearch_config = ElasticsearchConfig()
api_config = APIConfig()
embedding_config = EmbeddingConfig()
rag_config = RAGConfig()
