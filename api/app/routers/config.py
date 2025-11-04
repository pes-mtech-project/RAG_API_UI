"""
API routes for managing sector search configurations
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..models import (
    SectorConfigCreate,
    SectorConfigUpdate,
    SectorConfigResponse,
    SectorConfigSummary,
    PhraseCreateRequest,
    PhraseUpdateRequest,
    TagUpdateRequest,
)
from ..services import (
    list_configs,
    get_config,
    create_config,
    update_config,
    add_tags,
    remove_tag,
    add_phrases,
    update_phrase,
    remove_phrase,
    delete_config,
)

router = APIRouter(
    prefix="/config/sectors",
    tags=["search-configurations"],
)


@router.get("", response_model=list[SectorConfigSummary])
def list_sector_configs():
    """List all configured sectors with summary data"""
    return list_configs()


@router.get("/{sector}", response_model=SectorConfigResponse)
def get_sector_config(sector: str):
    """Retrieve full configuration for a sector"""
    try:
        return get_config(sector)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=SectorConfigResponse, status_code=status.HTTP_201_CREATED)
def create_sector_config(payload: SectorConfigCreate):
    """Create a new sector configuration"""
    try:
        return create_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{sector}", response_model=SectorConfigResponse)
def update_sector_config(sector: str, payload: SectorConfigUpdate):
    """Update top-level configuration values"""
    try:
        return update_config(sector, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{sector}/phrases", response_model=SectorConfigResponse)
def add_sector_phrases(sector: str, payload: PhraseCreateRequest):
    """Add semantic search phrases and generate embeddings"""
    try:
        return add_phrases(sector, payload.phrases)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{sector}/phrases/{phrase_id}", response_model=SectorConfigResponse)
def update_sector_phrase(sector: str, phrase_id: str, payload: PhraseUpdateRequest):
    """Update phrase text and regenerate embedding"""
    try:
        return update_phrase(sector, phrase_id, payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{sector}/phrases/{phrase_id}", response_model=SectorConfigResponse)
def delete_sector_phrase(sector: str, phrase_id: str):
    """Remove a phrase from configuration"""
    try:
        return remove_phrase(sector, phrase_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{sector}/tags", response_model=SectorConfigResponse)
def add_sector_tags(sector: str, payload: TagUpdateRequest):
    """Add tags used for BM25 matching"""
    try:
        return add_tags(sector, payload.tags)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{sector}/tags/{tag}", response_model=SectorConfigResponse)
def remove_sector_tag(sector: str, tag: str):
    """Remove a tag from the configuration"""
    try:
        return remove_tag(sector, tag)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{sector}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sector(sector: str):
    """Delete a sector configuration entirely"""
    try:
        delete_config(sector)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
