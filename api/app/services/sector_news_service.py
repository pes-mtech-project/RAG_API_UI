"""
Sector news retrieval service leveraging hybrid search
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Optional, Set

from elasticsearch import NotFoundError

from .elasticsearch_service import elasticsearch_service
from .search_service import search_service
from .search_config_service import get_config
from ..models import SectorNewsResult, SectorNewsResponse, SectorNewsQueryInfo


async def search_sector_news(
    sector: str,
    *,
    limit: int = 10,
    min_score: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> SectorNewsResponse:
    """Execute hybrid search for a given sector"""

    if limit <= 0:
        raise ValueError("limit must be positive")

    config = get_config(sector)
    client = elasticsearch_service.get_client()
    date_from_dt = _parse_datetime(date_from) if date_from else None
    date_to_dt = _parse_datetime(date_to) if date_to else None

    start_time = time.perf_counter()

    semantic_hits: Dict[str, Dict] = {}
    semantic_max = 0.0
    phrase_texts: List[str] = []

    semantic_search_fn = _resolve_semantic_search_fn(config.semantic_field)
    semantic_search_limit = min(max(limit * 3, 20), 100)

    # Semantic search per phrase
    for phrase in config.phrases:
        if phrase.status != "ready":
            continue
        phrase_texts.append(phrase.text)
        try:
            results = await semantic_search_fn(
                phrase.text,
                limit=semantic_search_limit,
                min_score=0.0,
                indices=config.index_pattern,
            )
        except Exception:
            continue

        for result in results:
            if not _within_date_range(result, date_from_dt, date_to_dt):
                continue
            doc_id = result.get("id")
            if not doc_id:
                continue
            score = result.get("score", 0.0)
            # Apply per-phrase semantic threshold when configured
            try:
                min_thr = getattr(phrase, 'min_semantic_score', None)
            except Exception:
                min_thr = None
            if min_thr is not None and score < float(min_thr):
                continue
            entry = semantic_hits.setdefault(
                doc_id,
                {
                    "semantic_score": 0.0,
                    "bm25_score": 0.0,
                    "source": {},
                    "phrase_matches": set(),
                    "tags_matched": set(),
                },
            )
            if score > entry["semantic_score"]:
                entry["semantic_score"] = score
                entry["source"] = _extract_base_from_result(result)
            entry["phrase_matches"].add(phrase.text)
            semantic_max = max(semantic_max, score)

    # Keyword search using tags
    bm25_max = 0.0
    if config.tags:
        try:
            response = client.search(
                index=config.index_pattern,
                body=_bm25_query(config.tags_field, config.tags, size=min(limit * 3, 100)),
            )
        except NotFoundError:
            response = {}

        for hit in response.get("hits", {}).get("hits", []):
            doc_id = hit.get("_id")
            if not doc_id:
                continue
            score = hit.get("_score", 0.0)
            base_info = _extract_base_from_hit(hit)
            if not _within_date_range(base_info, date_from_dt, date_to_dt):
                continue
            entry = semantic_hits.setdefault(
                doc_id,
                {
                    "semantic_score": 0.0,
                    "bm25_score": 0.0,
                    "source": base_info,
                    "phrase_matches": set(),
                    "tags_matched": set(),
                },
            )
            entry["bm25_score"] = max(entry["bm25_score"], score)
            entry["tags_matched"].update(_infer_tags(hit, config.tags_field, config.tags))
            if not entry["source"]:
                entry["source"] = base_info
            bm25_max = max(bm25_max, score)

    results = _blend_results(semantic_hits, semantic_max, bm25_max, limit, min_score)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    query_info = SectorNewsQueryInfo(
        index_pattern=config.index_pattern,
        semantic_field=config.semantic_field,
        tags_field=config.tags_field,
        phrases=phrase_texts,
        tags=config.tags,
    )

    return SectorNewsResponse(
        sector=sector,
        config_summary=query_info,
        results=results,
        total_hits=len(results),
        search_duration_ms=elapsed_ms,
        warnings=[],
    )


def _bm25_query(field: str, tags: List[str], *, size: int) -> Dict:
    should_clauses = [{"match": {field: tag}} for tag in tags]
    body = {
        "size": size,
        "query": {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1 if should_clauses else 0,
            }
        },
    }
    return body


def _infer_tags(hit: Dict, field: str, candidate_tags: List[str]) -> Set[str]:
    tags_present: Set[str] = set()
    source = hit.get("_source", {})
    stored = source.get(field)
    if isinstance(stored, list):
        lower_values = {str(v).lower() for v in stored}
        for tag in candidate_tags:
            if tag.lower() in lower_values:
                tags_present.add(tag)
    elif isinstance(stored, str):
        value = stored.lower()
        for tag in candidate_tags:
            if tag.lower() in value:
                tags_present.add(tag)
    return tags_present


def _blend_results(
    doc_hits: Dict[str, Dict],
    semantic_max: float,
    bm25_max: float,
    limit: int,
    min_score: Optional[float],
) -> List[SectorNewsResult]:
    results: List[SectorNewsResult] = []

    semantic_max = semantic_max or 1.0
    bm25_max = bm25_max or 1.0

    for doc_id, data in doc_hits.items():
        base = _coerce_base_info(data.get("source"))
        semantic_score = data.get("semantic_score", 0.0)
        bm25_score = data.get("bm25_score", 0.0)

        semantic_norm = semantic_score / semantic_max if semantic_max else 0.0
        bm25_norm = bm25_score / bm25_max if bm25_max else 0.0

        final_score = 0.7 * semantic_norm + 0.3 * bm25_norm

        if min_score is not None and final_score < min_score:
            continue

        result = SectorNewsResult(
            id=doc_id,
            score=final_score,
            semantic_score=semantic_score,
            bm25_score=bm25_score,
            title=base.get("title"),
            summary=base.get("summary"),
            full_text=base.get("full_text"),
            url=base.get("url"),
            date=base.get("date"),
            published_dt=base.get("published_dt"),
            source_index=base.get("source_index"),
            tags_matched=sorted(data.get("tags_matched") or []),
            phrase_matches=sorted(data.get("phrase_matches") or []),
        )
        results.append(result)

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


def _extract_base_from_result(result: Dict) -> Dict:
    return {
        "title": result.get("title"),
        "summary": result.get("summary"),
        "full_text": result.get("full_text"),
        "url": result.get("url"),
        "date": result.get("date"),
        "published_dt": result.get("published_dt"),
        "source_index": result.get("source_index"),
    }


def _extract_base_from_hit(hit: Dict) -> Dict:
    source = hit.get("_source", {})
    return {
        "title": source.get("news_title") or source.get("title"),
        "summary": source.get("news_summary") or source.get("summary"),
        "full_text": source.get("news_body") or source.get("full_text"),
        "url": source.get("url"),
        "date": source.get("date"),
        "published_dt": source.get("published_dt"),
        "source_index": hit.get("_index"),
    }


def _coerce_base_info(raw: Optional[Dict]) -> Dict:
    if not raw:
        return {}
    if "title" in raw or "summary" in raw or "full_text" in raw:
        return raw
    if "_source" in raw:
        return _extract_base_from_hit(raw)
    return raw


def _parse_datetime(value: str) -> Optional[datetime]:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:
        pass

    # Handle compact YYYYMMDD or YYYYMMDDHHMMSS formats commonly stored in ES docs
    digits_only = "".join(ch for ch in value if ch.isdigit())
    try:
        if len(digits_only) == 14:
            return datetime.strptime(digits_only, "%Y%m%d%H%M%S")
        if len(digits_only) == 8:
            return datetime.strptime(digits_only, "%Y%m%d")
    except Exception:
        pass

    try:
        return datetime.fromisoformat(value[:10])
    except Exception:
        return None


def _within_date_range(entry: Dict, date_from: Optional[datetime], date_to: Optional[datetime]) -> bool:
    if not (date_from or date_to):
        return True
    if not entry:
        return True
    raw_value = entry.get("date") or entry.get("published_dt")
    if not raw_value:
        return True
    parsed = _parse_datetime(raw_value)
    if parsed is None:
        return True
    if date_from and parsed < date_from:
        return False
    if date_to and parsed > date_to:
        return False
    return True


def _resolve_semantic_search_fn(semantic_field: str):
    mapping = {
        "embedding_384d": search_service.search_with_embedding_384d,
        "embedding_768d": search_service.search_with_embedding_768d,
        "embedding_enhanced": search_service.search_with_embedding_enhanced,
    }
    return mapping.get(semantic_field, search_service.search_with_embedding_768d)
