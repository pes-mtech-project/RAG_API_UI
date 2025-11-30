"""General search endpoints reusing sector hybrid logic"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import search_service as semantic_service
from ..services.sector_news_service import (
    _bm25_query, _blend_results, _coerce_base_info, _extract_base_from_hit,
)
from ..services.elasticsearch_service import elasticsearch_service


router = APIRouter(prefix="/search", tags=["search"])


class SimilarityRequest(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=100)
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source_index: Optional[str] = None


class TagsRequest(BaseModel):
    tags: List[str]
    limit: int = Field(10, ge=1, le=100)
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source_index: Optional[str] = None
    tags_field: str = "structured_context"


class HybridRequest(BaseModel):
    query: str = ""
    tags: List[str] = []
    limit: int = Field(10, ge=1, le=100)
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source_index: Optional[str] = None
    semantic_field: str = "embedding_768d"
    tags_field: str = "structured_context"


@router.post("/similarity")
async def similarity_search(payload: SimilarityRequest):
    try:
        # Reuse existing semantic search pipeline
        return await semantic_service.search_with_embedding_768d(
            query=payload.query,
            limit=payload.limit,
            min_score=payload.min_score or 0.0,
            indices=payload.source_index or "news_finbert_embeddings*,*processed*,*news*",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.post("/tags")
async def tags_search(payload: TagsRequest):
    """BM25-only over provided tags using same ES query helper as sector search."""
    client = elasticsearch_service.get_client()
    try:
        index = payload.source_index or "news_finbert_embeddings*"
        body = _bm25_query(payload.tags_field, payload.tags, size=min(payload.limit * 3, 100))
        es_resp = client.search(index=index, body=body)

        hits = es_resp.get("hits", {}).get("hits", [])
        # Convert to SectorNewsResult-like dicts using the same helpers
        results: List[Dict[str, Any]] = []
        bm25_max = max((h.get("_score", 0.0) for h in hits), default=1.0) or 1.0
        for hit in hits[: payload.limit]:
            bm25 = hit.get("_score", 0.0)
            base = _coerce_base_info(_extract_base_from_hit(hit))
            results.append(
                {
                    "id": hit.get("_id"),
                    "score": (bm25 / bm25_max),
                    "semantic_score": 0.0,
                    "bm25_score": bm25,
                    "title": base.get("title"),
                    "summary": base.get("summary"),
                    "full_text": base.get("full_text"),
                    "url": base.get("url"),
                    "date": base.get("date"),
                    "published_dt": base.get("published_dt"),
                    "source_index": base.get("source_index"),
                    "tags_matched": [],
                    "phrase_matches": [],
                }
            )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.post("/hybrid")
async def hybrid_search(payload: HybridRequest):
    """Blend semantic + BM25 using the exact blender from sector_news_service."""
    try:
        # Semantic side
        semantic_hits: Dict[str, Dict[str, Any]] = {}
        semantic_max = 0.0
        if payload.query:
            try:
                sem_results = await (
                    semantic_service.search_with_embedding_768d(
                        payload.query,
                        limit=min(max(payload.limit * 3, 20), 100),
                        min_score=0.0,
                        indices=payload.source_index or "news_finbert_embeddings*,*processed*,*news*",
                    )
                )
            except Exception:
                sem_results = []
            for r in sem_results:
                doc_id = r.get("id")
                if not doc_id:
                    continue
                score = r.get("score", 0.0)
                entry = semantic_hits.setdefault(
                    doc_id,
                    {"semantic_score": 0.0, "bm25_score": 0.0, "source": {}, "phrase_matches": set(), "tags_matched": set()},
                )
                if score > entry["semantic_score"]:
                    entry["semantic_score"] = score
                    entry["source"] = {
                        "title": r.get("title"),
                        "summary": r.get("summary"),
                        "full_text": r.get("full_text"),
                        "url": r.get("url"),
                        "date": r.get("date"),
                        "published_dt": r.get("published_dt"),
                        "source_index": r.get("source_index"),
                    }
                semantic_max = max(semantic_max, score)

        # BM25 side
        bm25_max = 0.0
        if payload.tags:
            client = elasticsearch_service.get_client()
            index = payload.source_index or "news_finbert_embeddings*"
            resp = client.search(index=index, body=_bm25_query(payload.tags_field, payload.tags, size=min(payload.limit * 3, 100)))
            for hit in resp.get("hits", {}).get("hits", []):
                doc_id = hit.get("_id")
                if not doc_id:
                    continue
                score = hit.get("_score", 0.0)
                base = _extract_base_from_hit(hit)
                entry = semantic_hits.setdefault(
                    doc_id,
                    {"semantic_score": 0.0, "bm25_score": 0.0, "source": base, "phrase_matches": set(), "tags_matched": set()},
                )
                entry["bm25_score"] = max(entry["bm25_score"], score)
                if not entry["source"]:
                    entry["source"] = base
                bm25_max = max(bm25_max, score)

        # Blend using shared blender
        blended = _blend_results(semantic_hits, semantic_max, bm25_max, payload.limit, payload.min_score)
        # Convert pydantic model list to plain dicts if needed
        return [r.dict() for r in blended]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

