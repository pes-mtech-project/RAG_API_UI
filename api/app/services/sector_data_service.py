"""
Service to combine sector news results and sector market data
"""

from __future__ import annotations

import json
import time
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import copy

from fastapi import HTTPException

from .elasticsearch_service import elasticsearch_service, build_rag_filters
from .sector_news_service import search_sector_news


def _load_mapping() -> Dict[str, str]:
    # Locate mapping file relative to package root (api/app/)
    try:
        from pathlib import Path

        base = Path(__file__).resolve().parents[1]
        path = base / "sector_market_mapping.json"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _parse_date(value: Optional[str]) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            # fallback to date-only
            return datetime.strptime(value[:10], '%Y-%m-%d')
    return datetime.utcnow()


async def search_sector_data(
    sector_name: str,
    *,
    date: Optional[str] = None,
    window: int = 5,
    limit: int = 3,
    min_score: Optional[float] = None,
    bypass_cache: bool = False,
) -> Dict:
    """Return combined news and market data for `sector_name`.

    - `date` is an ISO date string (default: today)
    - `window` is number of days inclusive ending at `date` (default: 5)
    """
    if window <= 0:
        raise ValueError("window must be positive")

    # sanitize incoming sector_name to avoid hidden/unicode char issues
    def _clean_sector_name(name: str) -> str:
        if not isinstance(name, str):
            return name
        # Normalize unicode and remove common invisible characters
        s = unicodedata.normalize('NFKC', name)
        # remove zero-width and other invisible marks
        s = re.sub(r'[\u200B-\u200F\uFEFF\u2060-\u2064]', '', s)
        s = s.strip()
        return s

    sector_name_clean = _clean_sector_name(sector_name)

    mapping = _load_mapping()
    # perform case-insensitive lookup using cleaned name
    mapping_ci = {k.lower(): v for k, v in mapping.items()}
    if sector_name_clean.lower() not in mapping_ci:
        raise ValueError(f"Unknown sector_name: {sector_name_clean}")
    market_sector = mapping_ci[sector_name_clean.lower()]

    end_dt = _parse_date(date)
    start_dt = end_dt - timedelta(days=(window - 1))

    date_from = start_dt.date().isoformat()
    date_to = end_dt.date().isoformat()

    start_time = time.perf_counter()

    # --- In-memory cache (TTL = 3 hours) ---
    CACHE_TTL = 3 * 60 * 60
    global _SECTOR_DATA_CACHE, _SECTOR_DATA_CACHE_LOCK
    try:
        _SECTOR_DATA_CACHE
    except NameError:
        _SECTOR_DATA_CACHE = {}
        _SECTOR_DATA_CACHE_LOCK = threading.Lock()

    def _make_cache_key() -> str:
        # include bypass flag in key to keep behavior explicit
        return f"{sector_name_clean}|{date or ''}|{window}|{limit}|{min_score or ''}"

    cache_key = _make_cache_key()
    if not bypass_cache:
        with _SECTOR_DATA_CACHE_LOCK:
            cached = _SECTOR_DATA_CACHE.get(cache_key)
            if cached:
                ts, payload = cached
                if (time.time() - ts) < CACHE_TTL:
                    return copy.deepcopy(payload)
                else:
                    # expired
                    del _SECTOR_DATA_CACHE[cache_key]

    # Get news via internal service (no external HTTP)
    news_resp = await search_sector_news(
        sector_name_clean,
        limit=limit,
        min_score=min_score,
        date_from=date_from,
        date_to=date_to,
    )

    news_elapsed = news_resp.search_duration_ms

    # Query Elasticsearch for market data
    client = elasticsearch_service.get_client()
    es_index = "sector_market_data"
    # Build ES query: match sector. Don't require a top-level `date` field
    # because many documents store time-series inside `last_window_data`.
    # Try multiple matching strategies so we return both per-day docs and
    # aggregated documents that store series in `last_window_data`.
    body = {
        "size": max(window * 6, 30),
        "query": {
            "bool": {
                "should": [
                    {"term": {"sector.keyword": market_sector}},
                    {"term": {"sector": market_sector}},
                    {"match": {"sector": {"query": market_sector, "operator": "and"}}}
                ],
                "minimum_should_match": 1
            }
        }
    }

    # Use a flexible index pattern in case the index is suffixed or aliased
    index_pattern = "sector_market_data*"
    try:
        resp = client.search(index=index_pattern, body=body)
    except Exception:
        # As a last resort try a simple match query without keyword/term
        try:
            fallback = {"query": {"match": {"sector": market_sector}}, "size": 20}
            resp = client.search(index=index_pattern, body=fallback)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Market data query failed: {exc}")

    price_history: List[Dict] = []
    # Support two storage patterns in ES:
    # 1) documents per date with fields: date, open, high, low, close, volume
    # 2) aggregated documents with `last_window_data` array (as in example-response.json)
    for hit in resp.get("hits", {}).get("hits", []):
        src = hit.get("_source", {})

        # Case: aggregated time-series stored in `last_window_data` or similar
        lw = src.get("last_window_data") or src.get("last_window")
        if isinstance(lw, list) and lw:
            for entry in lw:
                entry_date = entry.get("date") or entry.get("dt")
                if not entry_date:
                    continue
                # normalize to YYYY-MM-DD for comparison
                try:
                    ed = str(entry_date)[:10]
                except Exception:
                    continue
                if ed < date_from or ed > date_to:
                    continue
                price_history.append(
                    {
                        "date": ed,
                        "open": entry.get("open"),
                        "high": entry.get("high"),
                        "low": entry.get("low"),
                        "close": entry.get("close"),
                        "volume": entry.get("volume"),
                    }
                )
            continue

        # Fallback: individual documents per day
        doc_date = src.get("date") or src.get("dt")
        if doc_date:
            dd = str(doc_date)[:10]
            if dd >= date_from and dd <= date_to:
                price_history.append(
                    {
                        "date": dd,
                        "open": src.get("open"),
                        "high": src.get("high"),
                        "low": src.get("low"),
                        "close": src.get("close"),
                        "volume": src.get("volume"),
                    }
                )

    market_data = {
        "date_range": {"start_date": date_from, "end_date": date_to},
        "sector": sector_name_clean,
        "market_sector": market_sector,
        "price_history": price_history,
    }

    total_elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    result = {
        "sector": sector_name_clean,
        "config_summary": news_resp.config_summary.dict() if hasattr(news_resp, "config_summary") else {},
        "news_results": [r.dict() for r in getattr(news_resp, "results", [])],
        "market_data": market_data,
        "total_hits": getattr(news_resp, "total_hits", len(getattr(news_resp, "results", []))),
        "market_data_days": len(price_history),
        "search_duration_ms": int(news_elapsed or 0) + total_elapsed_ms,
        "warnings": getattr(news_resp, "warnings", []),
        "generated_at": getattr(news_resp, "generated_at", datetime.utcnow()).isoformat(),
    }

    # store result in cache for future identical requests
    if not bypass_cache:
        try:
            with _SECTOR_DATA_CACHE_LOCK:
                _SECTOR_DATA_CACHE[cache_key] = (time.time(), copy.deepcopy(result))
        except Exception:
            # cache failures shouldn't break API
            pass

    return result

