"""
Embedding service layer
Handles embedding generation for different models and dimensions
"""

import logging
import time
import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

from ..config import embedding_config

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service class for embedding generation
    Supports multiple embedding models and dimensions
    """
    
    def __init__(self):
        self._models: Dict[str, SentenceTransformer] = {}
        self._model_loading_lock = False
        
        # Set up persistent model cache directory in user home
        self.cache_dir = Path.home() / ".cache" / "sentence_transformers"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variable for sentence transformers cache
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(self.cache_dir)
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        os.environ['HF_HOME'] = str(self.cache_dir / "huggingface")
        
        logger.info(f"📁 Model cache directory set to: {self.cache_dir}")
    
    def _get_model(self, model_type: str) -> SentenceTransformer:
        """
        Get or load embedding model with lazy initialization and caching
        
        Args:
            model_type: Type of model (384d, 768d)
            
        Returns:
            Loaded SentenceTransformer model
        """
        if model_type not in self._models:
            if self._model_loading_lock:
                # Wait for concurrent model loading to complete
                while self._model_loading_lock:
                    time.sleep(0.1)
            else:
                self._model_loading_lock = True
                try:
                    model_name = self._get_model_name(model_type)
                    cached_model_path = self.cache_dir / model_name.replace("/", "--")
                    
                    if cached_model_path.exists():
                        logger.info(f"📋 Loading cached {model_type} model from: {cached_model_path}")
                        self._models[model_type] = SentenceTransformer(str(cached_model_path))
                    else:
                        logger.info(f"⬇️ Downloading {model_type} embedding model: {model_name}")
                        self._models[model_type] = SentenceTransformer(model_name, cache_folder=str(self.cache_dir))
                        # Save to persistent location
                        self._models[model_type].save(str(cached_model_path))
                        logger.info(f"💾 Cached {model_type} model to: {cached_model_path}")
                    
                    logger.info(f"✅ {model_type} embedding model loaded successfully")
                finally:
                    self._model_loading_lock = False
        
        return self._models[model_type]
    
    def _get_model_name(self, model_type: str) -> str:
        """Get model name for given type"""
        model_map = {
            '384d': embedding_config.model_384d,
            '768d': embedding_config.model_768d,
        }
        
        if model_type not in model_map:
            raise ValueError(f"Unsupported model type: {model_type}. Supported: {list(model_map.keys())}")
        
        return model_map[model_type]
    
    def generate_embedding_384d(self, text: str) -> List[float]:
        """
        Generate 384-dimensional embedding using all-MiniLM-L6-v2
        
        Args:
            text: Input text
            
        Returns:
            384-dimensional embedding vector
        """
        model = self._get_model('384d')
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embedding_768d(self, text: str) -> List[float]:
        """
        Generate 768-dimensional embedding using all-mpnet-base-v2
        
        Args:
            text: Input text
            
        Returns:
            768-dimensional embedding vector
        """
        model = self._get_model('768d')
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embedding_1155d(self, text: str) -> List[float]:
        """
        Generate 1155-dimensional enhanced embedding (384d + 768d + 3d sentiment)
        This simulates the enhanced embedding structure from finbert-news-pipeline-daily
        
        Args:
            text: Input text
            
        Returns:
            1155-dimensional enhanced embedding vector
        """
        # Generate base embeddings
        embedding_384d = self.generate_embedding_384d(text)
        embedding_768d = self.generate_embedding_768d(text)
        
        # Generate mock sentiment vector (3 dimensions: positive, negative, neutral)
        # In production, this would use actual sentiment analysis
        sentiment_vector = self._generate_mock_sentiment(text)
        
        # Concatenate all embeddings: 384 + 768 + 3 = 1155
        enhanced_embedding = embedding_384d + embedding_768d + sentiment_vector
        
        return enhanced_embedding
    
    def _generate_mock_sentiment(self, text: str) -> List[float]:
        """
        Generate mock sentiment vector for enhanced embedding
        In production, this would use the actual FinBERT sentiment model
        
        Args:
            text: Input text
            
        Returns:
            3-dimensional sentiment vector [positive, negative, neutral]
        """
        # Simple heuristic-based mock sentiment
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'positive', 'growth', 'profit', 'success', 'gain']
        negative_words = ['bad', 'poor', 'decline', 'loss', 'negative', 'crisis', 'problem', 'fall']
        
        positive_score = sum(1 for word in positive_words if word in text_lower) / len(positive_words)
        negative_score = sum(1 for word in negative_words if word in text_lower) / len(negative_words)
        neutral_score = 1.0 - (positive_score + negative_score)
        
        # Normalize to sum to 1.0
        total = positive_score + negative_score + neutral_score
        if total > 0:
            return [positive_score/total, negative_score/total, neutral_score/total]
        else:
            return [0.33, 0.33, 0.34]  # Default neutral
    
    def generate_embedding(self, text: str, model_type: str = "384d") -> Dict[str, Any]:
        """
        Generate embedding for given text and model type
        
        Args:
            text: Input text
            model_type: Type of embedding (384d, 768d, 1155d)
            
        Returns:
            Dictionary with embedding and metadata
        """
        start_time = time.time()
        
        try:
            if model_type == "384d":
                embedding = self.generate_embedding_384d(text)
                dimension = embedding_config.dim_384d
            elif model_type == "768d":
                embedding = self.generate_embedding_768d(text)
                dimension = embedding_config.dim_768d
            elif model_type == "1155d":
                embedding = self.generate_embedding_1155d(text)
                dimension = embedding_config.dim_1155d
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            generation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.info(f"Generated {model_type} embedding for text: '{text[:50]}...' in {generation_time:.2f}ms")
            
            return {
                "embedding": embedding,
                "dimension": dimension,
                "embedding_model": model_type,
                "generation_time_ms": generation_time,
                "text_length": len(text)
            }
        except Exception as e:
            logger.error(f"Failed to generate {model_type} embedding: {e}")
            raise
    
    def get_embedding_field(self, model_type: str) -> str:
        """Get Elasticsearch field name for embedding type"""
        field_map = {
            "384d": embedding_config.field_384d,
            "768d": embedding_config.field_768d,
            "1155d": embedding_config.field_1155d,
        }
        
        if model_type not in field_map:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        return field_map[model_type]
    
    def validate_embedding_dimension(self, embedding: List[float], expected_type: str) -> bool:
        """Validate embedding dimension matches expected type"""
        dimension_map = {
            "384d": embedding_config.dim_384d,
            "768d": embedding_config.dim_768d,
            "1155d": embedding_config.dim_1155d,
        }
        
        expected_dim = dimension_map.get(expected_type)
        if expected_dim is None:
            return False
        
        return len(embedding) == expected_dim

# Global service instance
embedding_service = EmbeddingService()