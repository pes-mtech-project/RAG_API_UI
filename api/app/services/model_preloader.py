"""
Model preloader service
Downloads and caches all required models during startup
"""

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ModelPreloader:
    """
    Service to preload and cache all embedding models during startup
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.model_types = ["384d", "768d"]  # Models to preload
    
    async def preload_all_models(self) -> bool:
        """
        Preload all embedding models concurrently
        
        Returns:
            bool: True if all models loaded successfully
        """
        logger.info("🔄 Starting model preloading...")
        
        try:
            # Use thread pool to load models concurrently
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                
                for model_type in self.model_types:
                    future = executor.submit(self._preload_model, model_type)
                    futures.append(future)
                
                # Wait for all models to load
                results = []
                for future in futures:
                    results.append(future.result())
                
                success = all(results)
                if success:
                    logger.info("✅ All models preloaded successfully")
                else:
                    logger.warning("⚠️ Some models failed to preload")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ Model preloading failed: {e}")
            return False
    
    def _preload_model(self, model_type: str) -> bool:
        """
        Preload a specific model type
        
        Args:
            model_type: Type of model to preload
            
        Returns:
            bool: True if model loaded successfully
        """
        try:
            logger.info(f"⏳ Preloading {model_type} model...")
            
            # Generate a test embedding to ensure model is fully loaded
            test_text = "test preload"
            
            if model_type == "384d":
                self.embedding_service.generate_embedding_384d(test_text)
            elif model_type == "768d":
                self.embedding_service.generate_embedding_768d(test_text)
            
            logger.info(f"✅ {model_type} model preloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to preload {model_type} model: {e}")
            return False
    
    def get_model_cache_info(self) -> dict:
        """
        Get information about cached models
        
        Returns:
            dict: Cache information
        """
        cache_info = {
            "cache_directory": str(self.embedding_service.cache_dir),
            "cached_models": [],
            "model_types_loaded": list(self.embedding_service._models.keys())
        }
        
        # Check which models are cached on disk
        if self.embedding_service.cache_dir.exists():
            cached_models = [d.name for d in self.embedding_service.cache_dir.iterdir() if d.is_dir()]
            cache_info["cached_models"] = cached_models
        
        return cache_info