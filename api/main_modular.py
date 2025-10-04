"""
Entry point for the modular FinBERT News RAG API
"""

from app.main import app

# For backwards compatibility, expose the app at module level
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )