"""Router for sector combined data endpoint"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models import SectorDataResponse
from ..services import search_sector_data


router = APIRouter(prefix="", tags=["sector-data"])


@router.get("/sector_data/{sector_name}", response_model=SectorDataResponse)
async def get_sector_data(
    sector_name: str,
    date: Optional[str] = None,
    window: int = Query(5, ge=1, le=30),
    limit: int = Query(3, ge=1, le=50),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    bypass_cache: bool = Query(False, description="Bypass in-memory cache and query Elasticsearch directly"),
) -> SectorDataResponse:
    """Return news + market data for a sector over a date window ending at `date`"""
    try:
        # validate ISO date if provided
        if date:
            datetime.fromisoformat(date)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid date: {exc}") from exc

    try:
        data = await search_sector_data(
            sector_name, date=date, window=window, limit=limit, min_score=min_score, bypass_cache=bypass_cache
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Convert generated_at to ISO if string
    if isinstance(data.get("generated_at"), str):
        generated_at = data["generated_at"]
    else:
        generated_at = datetime.utcnow().isoformat()

    return {
        "sector": data.get("sector"),
        "config_summary": data.get("config_summary"),
        "news_results": data.get("news_results"),
        "market_data": data.get("market_data"),
        "total_hits": data.get("total_hits"),
        "market_data_days": data.get("market_data_days"),
        "search_duration_ms": data.get("search_duration_ms"),
        "warnings": data.get("warnings") or [],
        "generated_at": generated_at,
    }
