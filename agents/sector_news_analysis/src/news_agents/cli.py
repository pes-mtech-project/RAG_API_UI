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
