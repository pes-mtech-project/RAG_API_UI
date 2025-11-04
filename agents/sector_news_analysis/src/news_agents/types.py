from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone
import math

@dataclass
class NewsItem:
    id: str
    headline: str
    summary: str
    datetime: str
    source: str
    region: str
    sector: Optional[str] = None
    date_key: Optional[str] = None

@dataclass
class Agent1Record:
    news_id: str
    sector: str
    tickers: List[str]
    sentiment_score: float
    confidence: float
    impact_horizon: str
    news_type: str
    rationale: str
    evidence_phrases: List[str]
    date_key: Optional[str] = None
    attribution_weight: Optional[float] = None
    adjusted_sentiment: Optional[float] = None
    calibration_note: Optional[str] = None

def iso_to_datekey(ts: str) -> str:
    return datetime.fromisoformat(ts.replace("Z","+00:00")).date().isoformat()

def recency_decay(age_days: float) -> float:
    return math.exp(-age_days / 7.0)
