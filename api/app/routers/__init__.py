"""
Routers package initialization
"""

from .search import router as search_router
from .legacy import router as legacy_router
from .config import router as config_router
from .news import router as news_router

__all__ = ['search_router', 'legacy_router', 'config_router', 'news_router']
