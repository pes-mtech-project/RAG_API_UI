"""
Service for managing sector search configurations in Elasticsearch
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from elastic_transport import ObjectApiResponse
from elasticsearch import NotFoundError

from .elasticsearch_service import elasticsearch_service
from .embedding_service import embedding_service
from ..config import elasticsearch_config
from ..models import (
    SectorConfigCreate,
    SectorConfigUpdate,
    SectorConfigResponse,
    SectorConfigSummary,
    PhraseRepresentation,
)

CONFIG_INDEX = getattr(elasticsearch_config, "search_config_index", "finbert-search-configs")
MAX_SECTORS = 20


def _get_es_client():
    return elasticsearch_service.get_client()


def _ensure_index() -> None:
    client = _get_es_client()
    if client.indices.exists(index=CONFIG_INDEX):
        return
    mapping = {
        "mappings": {
            "properties": {
                "sector": {"type": "keyword"},
                "index_pattern": {"type": "keyword"},
                "semantic_field": {"type": "keyword"},
                "tags_field": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "phrases": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "embedding_model": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "updated_at": {"type": "date"},
                        "error": {"type": "text"},
                    },
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        }
    }
    client.indices.create(index=CONFIG_INDEX, body=mapping)


def list_configs() -> List[SectorConfigSummary]:
    _ensure_index()
    client = _get_es_client()
    response = client.search(
        index=CONFIG_INDEX,
        body={
            "size": MAX_SECTORS,
            "_source": ["sector", "index_pattern", "semantic_field", "tags_field", "phrases", "tags", "updated_at"],
            "sort": [{"updated_at": {"order": "desc"}}],
        },
    )

    summaries: List[SectorConfigSummary] = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        summaries.append(
            SectorConfigSummary(
                sector=source["sector"],
                index_pattern=source.get("index_pattern", ""),
                semantic_field=source.get("semantic_field", ""),
                tags_field=source.get("tags_field", ""),
                phrase_count=len(source.get("phrases") or []),
                tag_count=len(source.get("tags") or []),
                updated_at=datetime.fromisoformat(source["updated_at"]),
            )
        )
    return summaries


def _load_config(sector: str) -> Dict[str, Any]:
    _ensure_index()
    client = _get_es_client()
    try:
        response: ObjectApiResponse[Any] = client.get(index=CONFIG_INDEX, id=sector)
        return response["_source"]
    except NotFoundError as exc:
        raise ValueError(f"Sector '{sector}' not found") from exc


def get_config(sector: str) -> SectorConfigResponse:
    source = _load_config(sector)
    return _deserialize_config(source)


def create_config(payload: SectorConfigCreate) -> SectorConfigResponse:
    _ensure_index()
    client = _get_es_client()

    existing = client.count(index=CONFIG_INDEX)["count"]
    if existing >= MAX_SECTORS:
        raise ValueError(f"Cannot create more than {MAX_SECTORS} sector configurations")

    now = datetime.now(timezone.utc)
    document = {
        "sector": payload.sector,
        "index_pattern": payload.index_pattern,
        "semantic_field": payload.semantic_field,
        "tags_field": payload.tags_field,
        "phrases": [],
        "tags": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    client.index(index=CONFIG_INDEX, id=payload.sector, body=document, refresh="wait_for")
    return _deserialize_config(document)


def update_config(sector: str, payload: SectorConfigUpdate) -> SectorConfigResponse:
    config = _load_config(sector)
    config.update(
        {
            "index_pattern": payload.index_pattern,
            "semantic_field": payload.semantic_field,
            "tags_field": payload.tags_field,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_config(sector, config)
    return _deserialize_config(config)


def add_tags(sector: str, tags: List[str]) -> SectorConfigResponse:
    config = _load_config(sector)
    existing_tags = set(config.get("tags") or [])
    updated = existing_tags.union(tags)
    config["tags"] = sorted(updated)
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_config(sector, config)
    return _deserialize_config(config)


def remove_tag(sector: str, tag: str) -> SectorConfigResponse:
    config = _load_config(sector)
    config["tags"] = [t for t in (config.get("tags") or []) if t != tag]
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_config(sector, config)
    return _deserialize_config(config)


def add_phrases(sector: str, phrases: List[str]) -> SectorConfigResponse:
    config = _load_config(sector)
    existing = config.get("phrases") or []

    if len(existing) + len(phrases) > 100:
        raise ValueError("Cannot store more than 100 phrases per sector")

    for text in phrases:
        phrase_id = str(uuid.uuid4())
        phrase_record = _generate_phrase_record(text, config["semantic_field"])
        phrase_record["id"] = phrase_id
        existing.append(phrase_record)

    config["phrases"] = existing
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_config(sector, config)
    return _deserialize_config(config)


def update_phrase(sector: str, phrase_id: str, text: str) -> SectorConfigResponse:
    config = _load_config(sector)
    found = False
    new_phrases: List[Dict[str, Any]] = []
    for phrase in config.get("phrases") or []:
        if phrase["id"] == phrase_id:
            found = True
            updated_phrase = _generate_phrase_record(text, config["semantic_field"])
            updated_phrase["id"] = phrase_id
            new_phrases.append(updated_phrase)
        else:
            new_phrases.append(phrase)

    if not found:
        raise ValueError(f"Phrase {phrase_id} not found for sector {sector}")

    config["phrases"] = new_phrases
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_config(sector, config)
    return _deserialize_config(config)


def remove_phrase(sector: str, phrase_id: str) -> SectorConfigResponse:
    config = _load_config(sector)
    original_count = len(config.get("phrases") or [])
    config["phrases"] = [p for p in (config.get("phrases") or []) if p["id"] != phrase_id]
    if len(config["phrases"]) == original_count:
        raise ValueError(f"Phrase {phrase_id} not found for sector {sector}")
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_config(sector, config)
    return _deserialize_config(config)


def delete_config(sector: str) -> None:
    _ensure_index()
    client = _get_es_client()
    try:
        client.delete(index=CONFIG_INDEX, id=sector, refresh="wait_for")
    except NotFoundError as exc:
        raise ValueError(f"Sector '{sector}' not found") from exc


def _generate_phrase_record(text: str, semantic_field: str) -> Dict[str, Any]:
    model_type = _resolve_model_type(semantic_field)
    try:
        embedding_result = embedding_service.generate_embedding(text, model_type)
        embedding = embedding_result["embedding"]
        status = "ready"
        error: Optional[str] = None
    except Exception as exc:
        embedding = None
        status = "failed"
        error = str(exc)

    return {
        "text": text,
        "embedding_model": model_type,
        "embedding": embedding,
        "status": status,
        "error": error,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _resolve_model_type(semantic_field: str) -> str:
    field_to_model = {
        "embedding_384d": "384d",
        "embedding_768d": "768d",
        "embedding_enhanced": "1155d",
    }
    return field_to_model.get(semantic_field, "768d")


def _save_config(sector: str, document: Dict[str, Any]) -> None:
    client = _get_es_client()
    client.index(index=CONFIG_INDEX, id=sector, body=document, refresh="wait_for")


def _deserialize_config(document: Dict[str, Any]) -> SectorConfigResponse:
    phrases = [
        PhraseRepresentation(
            id=p["id"],
            text=p["text"],
            embedding_model=p.get("embedding_model", ""),
            status=p.get("status", "pending"),
            updated_at=datetime.fromisoformat(p["updated_at"]),
            embedding=p.get("embedding"),
            error=p.get("error"),
        )
        for p in document.get("phrases") or []
    ]

    return SectorConfigResponse(
        sector=document["sector"],
        index_pattern=document.get("index_pattern", ""),
        semantic_field=document.get("semantic_field", ""),
        tags_field=document.get("tags_field", ""),
        tags=document.get("tags") or [],
        phrases=phrases,
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
    )
