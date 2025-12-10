"""
Routers package initialization
"""

from .search import router as search_router
from .legacy import router as legacy_router
from .config import router as config_router
from .news import router as news_router
from .general_search import router as general_search_router
from .sector_data import router as sector_data_router

__all__ = ['search_router', 'legacy_router', 'config_router', 'news_router', 'general_search_router', 'sector_data_router']
