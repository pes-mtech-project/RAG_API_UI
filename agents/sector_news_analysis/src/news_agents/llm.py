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
