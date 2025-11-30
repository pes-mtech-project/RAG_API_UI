"""
FinBERT News RAG API - Modular Application
Clean architecture following SOLID principles with enhanced embedding support
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import api_config
from .routers import search_router, legacy_router, config_router, news_router, general_search_router
from .services import elasticsearch_service, embedding_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Application factory following the Factory pattern
    Creates and configures the FastAPI application
    """
    app = FastAPI(
        title="FinBERT News RAG API",
        description="""
        Advanced API for financial news retrieval and analysis using multiple embedding dimensions.
        
        ## Features
        - **Multi-dimensional Embeddings**: 384d, 768d, and 1155d enhanced embeddings
        - **Cosine Similarity Search**: Precise vector similarity matching
        - **Financial Domain Optimization**: Specialized for financial news analysis
        - **Modular Architecture**: Clean, maintainable code following SOLID principles
        
        ## Embedding Types
        - **384d**: Fast semantic search using all-MiniLM-L6-v2
        - **768d**: High-quality search using all-mpnet-base-v2  
        - **1155d**: Enhanced embeddings with sentiment analysis (384d + 768d + 3d sentiment)
        
        ## Quick Start
        1. Use `/search/cosine/embedding384d/` for fast queries
        2. Use `/search/cosine/embedding768d/` for high accuracy
        3. Use `/search/cosine/embedding1155d/` for enhanced financial analysis
        """,
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(search_router)
    app.include_router(legacy_router)
    app.include_router(config_router)
    app.include_router(news_router)
    app.include_router(general_search_router)

    return app

# Application startup and shutdown events
app = create_app()

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("🚀 Starting up FinBERT News RAG API...")
    
    try:
        # Test Elasticsearch connection
        health = elasticsearch_service.health_check()
        logger.info(f"📊 Elasticsearch status: {health.get('status', 'unknown')}")
        
        # Pre-load 384d model for faster first requests
        logger.info("🤖 Pre-loading sentence transformer model...")
        embedding_service.generate_embedding("test query", "384d")
        logger.info("✅ 384d model loaded successfully")
        
        logger.info("🎉 API startup completed successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("🛑 Shutting down FinBERT News RAG API...")
    logger.info("✅ Shutdown completed")

# Health check for container/load balancer
@app.get("/health-simple")
async def simple_health():
    """Simple health endpoint for container health checks"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=api_config.api_host,
        port=api_config.api_port,
        reload=True,
        log_level="info"
    )
