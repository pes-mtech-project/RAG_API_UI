from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from .types import Agent1Record, recency_decay

class Agent2:
    def decide(self, items: List[Agent1Record], now_iso: Optional[str] = None,
               up_threshold: float = 0.8, down_threshold: float = -0.8, min_consensus: float = 0.6):
        now = datetime.fromisoformat(now_iso.replace("Z","+00:00")) if now_iso else datetime.now(timezone.utc)
        weighted_sum, total_w = 0.0, 0.0
        weights = []
        for r in items:
            w = r.confidence * recency_decay(0.0)
            weights.append(w); total_w += w
            s = r.adjusted_sentiment if r.adjusted_sentiment is not None else r.sentiment_score
            weighted_sum += w * s
        if total_w == 0:
            return {"label":"NO_IMPACT","weighted_mean":0.0,"consensus":0.0,"confidence":0.2,"rationale":"Insufficient evidence.","top_signals":[]}
        wm = weighted_sum/total_w
        pos_w = sum(w for (r,w) in zip(items,weights) if (r.adjusted_sentiment or r.sentiment_score) > 0 and wm>0)
        neg_w = sum(w for (r,w) in zip(items,weights) if (r.adjusted_sentiment or r.sentiment_score) < 0 and wm<0)
        consensus = (pos_w if wm>0 else (neg_w if wm<0 else 0.0))/total_w
        label = "UP" if wm>=up_threshold and consensus>=min_consensus else ("DOWN" if wm<=down_threshold and consensus>=min_consensus else "NO_IMPACT")
        confidence = min(0.9, total_w / (total_w + 1.0))
        top_ids = [r.news_id for r in sorted(items, key=lambda x: abs((x.adjusted_sentiment or x.sentiment_score)), reverse=True)[:3]]
        return {"label":label,"weighted_mean":round(wm,3),"consensus":round(consensus,3),"confidence":round(confidence,3),
                "rationale":"Direction inferred from weighted mean and consensus of adjusted sentiment.","top_signals":top_ids}
