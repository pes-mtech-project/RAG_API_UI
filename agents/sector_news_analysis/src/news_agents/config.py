AGENT1_SYSTEM_PROMPT = """You are the Sector/Ticker Sentiment Mapper.
Objective: From news summaries, output sector/ticker targets with price-impact sentiment_score in [-4.0, +4.0].
Inputs: news_items, sector_map, market, optional_hints.
Rules: One record per impacted sector/ticker; evidence phrases (1–4); near-neutral if unclear.
Output: JSON array only (no markdown).

Guidelines:
- sentiment_score: -4.0 (extremely negative) to +4.0 (extremely positive)
- confidence: 0.0 (no confidence) to 1.0 (complete confidence)
- impact_horizon: intraday, short_term(1-4w), medium_term(1-3m), long_term(3m+)
- news_type: regulatory, earnings, corporate, macro, sector, supplychain, policy, legal, etc.
- rationale: 1-2 sentence explanation of the price impact
- evidence_phrases: 1-4 key phrases from the news that support your analysis
"""
# Load comprehensive fewshots from the merged file
import json
import os

# Load the comprehensive fewshots from the data directory
FEWSHOTS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fewshots", "agent1_fewshots_merged.json")
try:
    with open(FEWSHOTS_FILE, 'r', encoding='utf-8') as f:
        AGENT1_FEWSHOTS = json.load(f)
    print(f"Loaded {len(AGENT1_FEWSHOTS)} fewshot examples from {FEWSHOTS_FILE}")
except Exception as e:
    print(f"Warning: Could not load fewshots from {FEWSHOTS_FILE}: {e}")
    # Fallback to basic examples
    AGENT1_FEWSHOTS = [
        {
            "input":{"news_items":[{"id":"N_TEL_1","headline":"TRAI trims 5G spectrum reserve prices by 18%","summary":"Regulator recommends an 18% cut to 5G spectrum reserve prices.","datetime":"2025-09-26T10:15:00Z","source":"Economic Daily","region":"IN"}],
                      "sector_map":{"Telecom":["BHARTIARTL.NS","RELIANCE.NS"]},"market":"IN","optional_hints":[]},
            "output":[{"news_id":"N_TEL_1","sector":"Telecom","tickers":["BHARTIARTL.NS","RELIANCE.NS"],"sentiment_score":2.6,"confidence":0.78,"impact_horizon":"short_term(1-4w)","news_type":"regulatory","rationale":"Lower spectrum costs improve 5G ROI and margins.","evidence_phrases":["18% cut","reserve prices"]}]
        }
    ]
AGENT2_SYSTEM_PROMPT = """You are the Price-Impact Direction Aggregator.
Objective: Aggregate multiple sentiment signals into sector/ticker direction with confidence.

Process:
1. For each signal, compute weight = confidence * recency_decay(age_days)
2. Calculate weighted_mean = sum(weight * sentiment_score) / sum(weight)
3. Calculate consensus = (sum of same-direction weights) / total_weight
4. Apply thresholds: UP (weighted_mean >= 0.8 and consensus >= 0.6), DOWN (weighted_mean <= -0.8 and consensus >= 0.6), else NO_IMPACT
5. Set confidence = min(0.9, total_weight / (total_weight + 1.0))

Output: JSON with label, weighted_mean, consensus, confidence, rationale, top_signals (3 signal IDs)
"""
AGENT2_FEWSHOTS = []
