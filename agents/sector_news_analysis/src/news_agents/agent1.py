from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import asdict
import itertools

from .types import NewsItem, Agent1Record, iso_to_datekey
from .config import AGENT1_SYSTEM_PROMPT, AGENT1_FEWSHOTS
from .llm import call_llm

NEWS_TYPE_MULTIPLIER = {"regulatory":1.2,"earnings":1.1,"legal":1.1,"geopolitical":1.0,"company":1.0,"supplychain":1.0,"M&A":1.0,"sector":0.95,"macro":0.9,"ESG":0.9}
def clamp(x,lo,hi): return max(lo,min(hi,x))
def _sign(x): return 1 if x>0 else (-1 if x<0 else 0)

class Agent1:
    def __init__(self, provider: str = "mock"):
        self.provider = provider
        self.system_prompt = AGENT1_SYSTEM_PROMPT
        self.few_shots = AGENT1_FEWSHOTS

    def run_llm(self, news_items: List[NewsItem], sector_map: Dict[str, List[str]], market: str, optional_hints=None) -> List[Agent1Record]:
        payload = {"news_items":[asdict(n) for n in news_items], "sector_map":sector_map, "market":market, "optional_hints": optional_hints or []}
        raw = call_llm(self.provider, self.system_prompt, payload, self.few_shots)
        nid_to_date = {n.id: iso_to_datekey(n.datetime) for n in news_items}
        out = []
        for r in raw:
            r["date_key"] = nid_to_date.get(r["news_id"])
            out.append(Agent1Record(**r))
        return out

    @staticmethod
    def aggregate_same_day(records: List[Agent1Record]):
        if not records: return 0.0, []
        raw_w = []
        for r in records:
            mag = 0.5 + 0.5 * min(1.0, abs(r.sentiment_score)/4.0)
            typ = NEWS_TYPE_MULTIPLIER.get(r.news_type, 1.0)
            raw_w.append(r.confidence * mag * typ)
        total = sum(raw_w) or 1e-9
        norm_w = [w/total for w in raw_w]
        day_score = 0.0
        for r, w in zip(records, norm_w):
            r.attribution_weight = round(w,6)
            day_score += w * r.sentiment_score
        return day_score, records

    @staticmethod
    def calibrate_to_next_day(day_score: float, next_day_pct: Optional[float]):
        if next_day_pct is None or day_score == 0 or _sign(day_score)==0: return day_score, "no_calibration_data_or_zero"
        if _sign(day_score) != _sign(next_day_pct) or abs(next_day_pct) < 0.3: return day_score, "no_calibration_mismatch_or_tiny_move"
        scale = clamp(abs(next_day_pct)/max(0.1, abs(day_score)), 0.5, 1.8)
        return day_score*scale, f"scaled_by_{round(scale,3)}"

    @staticmethod
    def redistribute(records: List[Agent1Record], original: float, calibrated: float):
        if original == 0:
            for r in records:
                r.adjusted_sentiment = r.sentiment_score
                r.calibration_note = "no_redistribution_zero_day_score"
            return records
        scale = calibrated/original
        for r in records:
            r.adjusted_sentiment = round(r.sentiment_score * scale, 4)
            r.calibration_note = f"redistributed_scale_{round(scale,3)}"
        return records

    def process_batch(self, agent1_outputs: List[Agent1Record], next_day_sector_change: Dict[Tuple[str,str], float]):
        result = {}
        agent1_outputs = [r for r in agent1_outputs if r.sector and r.date_key]
        agent1_outputs.sort(key=lambda r: (r.sector, r.date_key))
        for (sector, date_key), grp in itertools.groupby(agent1_outputs, key=lambda r: (r.sector, r.date_key)):
            recs = list(grp)
            raw, recs = self.aggregate_same_day(recs)
            cal = next_day_sector_change.get((sector, date_key))
            cald, note = self.calibrate_to_next_day(raw, cal)
            recs = self.redistribute(recs, raw, cald)
            for r in recs:
                if not r.calibration_note: r.calibration_note = note
            result[(sector, date_key)] = {"day_score_raw": round(raw,4), "day_score_calibrated": round(cald,4),
                                          "records": recs, "calibration_basis_next_day_pct": cal, "calibration_note": note}
        return result
