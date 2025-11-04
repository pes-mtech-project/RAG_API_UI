"""Router for sector news data endpoint"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models import SectorNewsResponse
from ..services import search_sector_news


router = APIRouter(prefix="", tags=["sector-news"])


@router.get("/news_data/{sector}", response_model=SectorNewsResponse)
async def get_sector_news(
    sector: str,
    limit: int = Query(10, ge=1, le=100),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> SectorNewsResponse:
    """Return blended semantic + BM25 results for a configured sector"""
    try:
        # Validate date strings if provided
        if date_from:
            datetime.fromisoformat(date_from)
        if date_to:
            datetime.fromisoformat(date_to)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return await search_sector_news(
            sector,
            limit=limit,
            min_score=min_score,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - fallback for unexpected errors
        raise HTTPException(status_code=500, detail=str(exc)) from exc
