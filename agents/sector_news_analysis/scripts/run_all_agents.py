#!/usr/bin/env python3
# scripts/run_all_agents.py
"""
End-to-end runner:
1) (Optional) Convert CSV→news JSON if --csv provided.
2) Agent1 mapping & sentiment → .cache/agent1_openai.json
3) Aggregate → .cache/agent1_adjusted_openai.json
4) Run Agent2 for all sectors in the sector_map file and build sector_summary.json
"""

import argparse
import json
import subprocess
from pathlib import Path

CACHE = Path(".cache")
CACHE.mkdir(exist_ok=True)

def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        print("❌ Error:\n" + p.stderr.strip())
        return False
    print(p.stdout.strip())
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="Optional path to CSV input (will write .cache/news_all.json)")
    ap.add_argument("--news", help="News JSON path (default .cache/news_all.json)", default=str(CACHE / "news_all.json"))
    ap.add_argument("--sector-map", default="data/sector_map_all.json")
    ap.add_argument("--provider", default="openai", choices=["openai", "mock"])
    ap.add_argument("--market", default="IN")
    args = ap.parse_args()

    news_json = Path(args.news)

    if args.csv:
        out_json = str(CACHE / "news_all.json")
        print(f"\n🧩 Converting CSV → JSON ...")
        if not run(["python", "scripts/csv_to_newsjson.py", args.csv, out_json]):
            return
        print("✅ OK")
        news_json = Path(out_json)

    # 1) Agent1
    a1_out = CACHE / "agent1_openai.json"
    if not run([
        "python","-m","src.news_agents.cli","agent1-run",
        "--news", str(news_json),
        "--sector-map", args.sector_map,
        "--market", args.market,
        "--provider", args.provider,
        "--out", str(a1_out)
    ]):
        return

    # 2) Aggregate
    a1_adj = CACHE / "agent1_adjusted_openai.json"
    if not run([
        "python","-m","src.news_agents.cli","agent1-aggregate",
        "--agent1-json", str(a1_out),
        "--out", str(a1_adj)
    ]):
        return

    # 3) Agent2 across sectors from the sector_map file
    sector_map = json.load(open(args.sector_map, "r", encoding="utf-8"))
    summary = {}
    for sector in sector_map.keys():
        out_dec = CACHE / f"decision_{sector.lower()}.json"
        print(f"\n🧭 Running Agent2 for sector: {sector} ...")
        ok = run([
            "python","-m","src.news_agents.cli","agent2-decide",
            "--agent1-json", str(a1_adj),
            "--level","sector","--name", sector,
            "--out", str(out_dec)
        ])
        if not ok or not out_dec.exists():
            print(f"❌ No output for {sector}")
            continue
        try:
            summary[sector] = json.load(open(out_dec, "r", encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ Could not parse {out_dec}: {e}")

    sum_path = CACHE / "sector_summary.json"
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n📊 Sector Sentiment Summary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n✅ Summary saved to {sum_path}")

if __name__ == "__main__":
    main()
