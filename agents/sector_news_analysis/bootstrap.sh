#!/usr/bin/env bash
set -euo pipefail
mkdir -p src/news_agents data/examples .cache

# .gitignore
cat > .gitignore <<'GIT'
.venv/
__pycache__/
.DS_Store
.env
.cache/
GIT

# README (short)
cat > README.md <<'MD'
# rag-news-agents
Two-agent pipeline for RAG news → (sector/ticker) sentiment → UP/DOWN/NO_IMPACT.
See CLI usage in this README and comments in code.
MD

# requirements
cat > requirements.txt <<'REQ'
typer==0.12.5
rich==13.7.1
pydantic==2.9.2
python-dotenv==1.0.1
pytest==8.3.2
tabulate==0.9.0
openai>=1.40.0
REQ

# example data
cat > data/examples/telecom_news.json <<'JSON'
[
  {"id":"N_te_1","headline":"TRAI trims 5G reserve prices by 18%","summary":"Regulator cuts reserve prices to accelerate 5G adoption.","datetime":"2025-09-26T10:15:00Z","source":"Economic Daily","region":"IN"},
  {"id":"N_te_2","headline":"AGR dues hearing scheduled next week","summary":"Court lists minor hearing; no immediate cash outflow expected.","datetime":"2025-09-26T12:00:00Z","source":"Biz Court Wire","region":"IN"},
  {"id":"N_te_3","headline":"Fiber outage impacts northern circle","summary":"Several hours of disruption reported; services restored.","datetime":"2025-09-26T13:40:00Z","source":"Telecom Log","region":"IN"}
]
JSON
cat > data/examples/sector_map.json <<'JSON'
{"Telecom":["BHARTIARTL.NS","RELIANCE.NS"],"Pharmaceuticals":["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],"Metals & Mining":["TATASTEEL.NS","JSWSTEEL.NS","JINDALSTEL.NS"]}
JSON
cat > data/examples/next_day_changes.json <<'JSON'
{"(Telecom,2025-09-26)": 1.2}
JSON

# package init
cat > src/news_agents/__init__.py <<'PY'
__all__ = ["config","agent1","agent2","llm","types","cli"]
PY

# types & small utils
cat > src/news_agents/types.py <<'PY'
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
PY

# prompts & few-shots (short)
cat > src/news_agents/config.py <<'PY'
AGENT1_SYSTEM_PROMPT = """You are the Sector/Ticker Sentiment Mapper.
Objective: From news summaries, output sector/ticker targets with price-impact sentiment_score in [-4.0, +4.0].
Inputs: news_items, sector_map, market, optional_hints.
Rules: One record per impacted sector/ticker; evidence phrases (1–4); near-neutral if unclear.
Output: JSON array only (no markdown).
"""
AGENT1_FEWSHOTS = [{
  "input":{"news_items":[{"id":"N1","headline":"TRAI trims 5G reserve prices by 18%","summary":"Regulator recommends an 18% cut to 5G spectrum reserve prices.","datetime":"2025-09-26T10:15:00Z","source":"Economic Daily","region":"IN"}],
            "sector_map":{"Telecom":["BHARTIARTL.NS","RELIANCE.NS"]},"market":"IN","optional_hints":[]},
  "output":[{"news_id":"N1","sector":"Telecom","tickers":["BHARTIARTL.NS","RELIANCE.NS"],"sentiment_score":2.6,"confidence":0.78,"impact_horizon":"short_term(1-4w)","news_type":"regulatory","rationale":"Lower spectrum costs boost margins.","evidence_phrases":["18% cut","reserve prices"]}]
}]
AGENT2_SYSTEM_PROMPT = """You are the Price-Impact Direction Aggregator.
Weight = confidence*exp(-age_days/7). Compute weighted_mean & consensus; decide UP/DOWN/NO_IMPACT by thresholds. Output JSON only.
"""
AGENT2_FEWSHOTS = []
PY

# LLM wrapper (mock + OpenAI)
cat > src/news_agents/llm.py <<'PY'
from __future__ import annotations
from typing import Dict, Any, List
import json, os
from dotenv import load_dotenv
load_dotenv()

def call_llm(provider: str, system_prompt: str, user_payload: Dict[str, Any], few_shots: List[Dict[str, Any]]):
    if provider == "mock":
        return _mock_agent1(user_payload)
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key: raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        messages = [{"role":"system","content":system_prompt}]
        for fs in (few_shots or []):
            messages += [{"role":"user","content":json.dumps(fs["input"])},
                         {"role":"assistant","content":json.dumps(fs["output"])}]
        messages.append({"role":"user","content":json.dumps(user_payload)})
        resp = client.chat.completions.create(model="gpt-4o-mini", temperature=0.2, messages=messages)
        txt = resp.choices[0].message.content
        try: return json.loads(txt)
        except Exception: return []
    raise ValueError(f"Unknown provider: {provider}")

def _mock_agent1(user_payload):
    items = user_payload.get("news_items", [])
    out = []
    for it in items:
        if it["id"] == "N_te_1":
            out.append({"news_id":it["id"],"sector":"Telecom","tickers":["BHARTIARTL.NS","RELIANCE.NS"],"sentiment_score":2.6,"confidence":0.78,"impact_horizon":"short_term(1-4w)","news_type":"regulatory","rationale":"Lower spectrum costs.","evidence_phrases":["18% cut","reserve prices"]})
        elif it["id"] == "N_te_2":
            out.append({"news_id":it["id"],"sector":"Telecom","tickers":["BHARTIARTL.NS"],"sentiment_score":-0.5,"confidence":0.55,"impact_horizon":"intraday","news_type":"legal","rationale":"Minor hearing.","evidence_phrases":["hearing"]})
        elif it["id"] == "N_te_3":
            out.append({"news_id":it["id"],"sector":"Telecom","tickers":[],"sentiment_score":-0.9,"confidence":0.6,"impact_horizon":"intraday","news_type":"company","rationale":"Temporary outage.","evidence_phrases":["outage","restored"]})
        else:
            out.append({"news_id":it["id"],"sector":"Unknown","tickers":[],"sentiment_score":0.0,"confidence":0.2,"impact_horizon":"intraday","news_type":"macro","rationale":"Insufficient info.","evidence_phrases":[]})
    return out
PY

# Agent-1 (incl. same-day aggregation + calibration)
cat > src/news_agents/agent1.py <<'PY'
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
PY

# Agent-2 (final direction)
cat > src/news_agents/agent2.py <<'PY'
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
PY

# CLI
cat > src/news_agents/cli.py <<'PY'
from __future__ import annotations
import json
from typing import Optional, List, Dict, Tuple
import typer
from rich import print
from .types import NewsItem, Agent1Record, iso_to_datekey
from .agent1 import Agent1
from .agent2 import Agent2

app = typer.Typer(help="CLI for news sentiment agents")

@app.command("agent1-run")
def agent1_run(news: str = typer.Option(...), sector_map: str = typer.Option(...),
               market: str = typer.Option("IN"), provider: str = typer.Option("mock"),
               out: str = typer.Option(".cache/agent1.json")):
    with open(news) as f: news_items = [NewsItem(**d) for d in json.load(f)]
    with open(sector_map) as f: sector_map_obj = json.load(f)
    for n in news_items: n.date_key = iso_to_datekey(n.datetime)
    a1 = Agent1(provider=provider)
    records = a1.run_llm(news_items, sector_map_obj, market)
    with open(out,"w") as f: json.dump([r.__dict__ for r in records], f, indent=2)
    print(f"[green]Wrote Agent-1 outputs → {out}[/green]")

@app.command("agent1-aggregate")
def agent1_aggregate(agent1_json: str = typer.Option(...),
                     next_day: Optional[str] = typer.Option(None),
                     out: str = typer.Option(".cache/agent1_adjusted.json")):
    with open(agent1_json) as f: recs = [Agent1Record(**d) for d in json.load(f)]
    next_day_map: Dict[Tuple[str,str], float] = {}
    if next_day:
        raw = json.load(open(next_day))
        for k, v in raw.items():
            sector, date = k.strip("()").split(",")
            next_day_map[(sector, date)] = float(v)
    from .agent1 import Agent1 as A1
    a1 = A1()
    daywise = a1.process_batch(recs, next_day_map)
    adjusted: List[Agent1Record] = []
    for _, blob in daywise.items(): adjusted.extend(blob["records"])
    with open(out, "w") as f: json.dump([r.__dict__ for r in adjusted], f, indent=2)
    print(f"[green]Wrote adjusted Agent-1 records → {out}[/green]")

@app.command("agent2-decide")
def agent2_decide(agent1_json: str = typer.Option(...),
                  level: str = typer.Option("sector"), name: str = typer.Option(""),
                  tickers: Optional[str] = typer.Option(None),
                  start_date: Optional[str] = typer.Option(None),
                  end_date: Optional[str] = typer.Option(None),
                  up_threshold: float = typer.Option(0.8),
                  down_threshold: float = typer.Option(-0.8),
                  min_consensus: float = typer.Option(0.6),
                  now_iso: Optional[str] = typer.Option(None),
                  out: str = typer.Option(".cache/decision.json")):
    with open(agent1_json) as f: recs = [Agent1Record(**d) for d in json.load(f)]
    if level == "sector":
        recs = [r for r in recs if r.sector == name]
    elif level == "tickers" and tickers:
        set_t = set([t.strip() for t in tickers.split(",")])
        recs = [r for r in recs if set_t.intersection(set(r.tickers))]
    if start_date: recs = [r for r in recs if r.date_key and r.date_key >= start_date]
    if end_date: recs = [r for r in recs if r.date_key and r.date_key <= end_date]
    a2 = Agent2()
    dec = a2.decide(recs, now_iso=now_iso, up_threshold=up_threshold, down_threshold=down_threshold, min_consensus=min_consensus)
    dec["target"] = {"level": level, "name": name, "tickers": (tickers.split(",") if tickers else [])}
    with open(out, "w") as f: json.dump(dec, f, indent=2)
    print(f"[green]Wrote decision → {out}[/green]")
    print(json.dumps(dec, indent=2))

if __name__ == "__main__":
    app()
PY

chmod +x bootstrap.sh
./bootstrap.sh
