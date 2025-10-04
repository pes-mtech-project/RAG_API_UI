#!/usr/bin/env python3
"""
Startup script for FinBERT RAG API with Model Preloading
Supports both legacy and modular architectures
"""

import os
import sys
import logging
import asyncio

# Add current directory to Python path
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the modular app first, fallback to legacy
try:
    from app.main import create_app
    from app.services import ModelPreloader
    
    logger.info("🚀 Starting modular FinBERT RAG API with model preloading")
    
    # Create app with model preloading
    app = create_app()
    
    @app.on_event("startup")
    async def preload_models():
        """Preload all embedding models during startup"""
        logger.info("🔄 Initializing model preloader...")
        preloader = ModelPreloader()
        
        # Preload models
        success = await preloader.preload_all_models()
        
        if success:
            logger.info("✅ All models preloaded successfully")
        else:
            logger.warning("⚠️ Some models may not be cached - will download on first use")
        
        # Log cache info
        cache_info = preloader.get_model_cache_info()
        logger.info(f"📁 Model cache info: {cache_info}")
    
except ImportError as e:
    logger.warning(f"⚠️  Modular import failed: {e}")
    try:
        from main import app
        logger.info("🔄 Falling back to legacy main.py")
    except ImportError as e2:
        logger.error(f"❌ Both modular and legacy imports failed: {e2}")
        sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info"
    )