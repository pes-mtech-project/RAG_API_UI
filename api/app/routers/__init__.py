"""
Routers package initialization
"""

from .search import router as search_router
from .legacy import router as legacy_router

__all__ = ['search_router', 'legacy_router']