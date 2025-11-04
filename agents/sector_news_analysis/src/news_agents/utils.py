from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import math

DATE_FMT = "%Y-%m-%d"


def iso_to_datekey(iso_str: str) -> str:
    """
    Convert an ISO8601 timestamp (e.g., '2025-09-26T10:15:00Z') to a date key 'YYYY-MM-DD'.
    If the input already looks like a date string, return the first 10 chars.
    """
    if not iso_str:
        return ""
    # Common fast-path
    if len(iso_str) >= 10 and iso_str[4] == "-" and iso_str[7] == "-":
        return iso_str[:10]
    # Fallback split
    return iso_str.split("T", 1)[0]


def recency_decay(date_key: str, today: Optional[str] = None, half_life_days: float = 7.0) -> float:
    """
    Exponential time decay weight based on how old a (sector, date_key) signal is.
    weight = 0.5 ** (days_delta / half_life_days)
    - date_key: 'YYYY-MM-DD'
    - today: optional 'YYYY-MM-DD'; if None, uses current UTC date
    """
    try:
        d = datetime.strptime((date_key or "")[:10], DATE_FMT).date()
    except Exception:
        return 1.0  # if bad date, don't penalize

    try:
        t = (
            datetime.strptime((today or "")[:10], DATE_FMT).date()
            if today
            else datetime.now(timezone.utc).date()
        )
    except Exception:
        t = datetime.now(timezone.utc).date()

    days = (t - d).days
    if days <= 0:
        return 1.0
    return math.pow(0.5, days / float(half_life_days or 7.0))
