#!/usr/bin/env python3
"""
Integrated RAG Pipeline for Sector News Analysis
1) Search vector DB for sector-specific news using RAG
2) Create CSV and JSON files from search results
3) Run Agent1 and Agent2 analysis
4) Generate comprehensive HTML report
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

# Import RAG search module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.news_agents.rag_search import RAGNewsSearch


CACHE = Path(".cache")
CACHE.mkdir(exist_ok=True)


def run(cmd):
    """Run shell command and return success status"""
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        print("❌ Error:\n" + p.stderr.strip())
        return False
    print(p.stdout.strip())
    return True


def run_rag_search(config_file: str = "rag_config.json") -> Dict[str, Any]:
    """Run RAG search to get news data"""
    print("🔍 Starting RAG news search...")

    try:
        rag_search = RAGNewsSearch(config_file)
        if not rag_search.collection:
            print("❌ Vector DB not available, using sample data instead")
            return {"csv_file": "data/news_all_sectors_sample.csv", "json_file": ".cache/news_all.json"}

        # Run full RAG search
        results = rag_search.run_full_search()

        print("✅ RAG search completed!")
        print(f"📊 Found {results['total_articles']} articles across {results['sectors_covered']} sectors")

        return {
            "csv_file": results["csv_file"],
            "json_file": results["json_file"],
            "total_articles": results["total_articles"],
            "sectors_covered": results["sectors_covered"]
        }

    except Exception as e:
        print(f"❌ RAG search failed: {e}")
        print("🔄 Falling back to sample data...")
        return {"csv_file": "data/news_all_sectors_sample.csv", "json_file": ".cache/news_all.json"}


def run_agent_analysis(csv_file: str, json_file: str, provider: str = "mock") -> bool:
    """Run Agent1 and Agent2 analysis"""
    print("🤖 Starting agent analysis...")

    # Convert CSV to JSON if needed
    if csv_file.endswith('.csv'):
        print("🔄 Converting CSV to JSON...")
        if not run(["python", "scripts/csv_to_newsjson.py", csv_file, json_file]):
            return False

    # 1) Agent1 analysis
    a1_out = CACHE / "agent1_rag.json"
    if not run([
        "python", "-m", "src.news_agents.cli", "agent1-run",
        "--news", json_file,
        "--sector-map", "data/sector_map_all.json",
        "--market", "IN",
        "--provider", provider,
        "--out", str(a1_out)
    ]):
        return False

    # 2) Aggregate Agent1 results
    a1_adj = CACHE / "agent1_adjusted_rag.json"
    if not run([
        "python", "-m", "src.news_agents.cli", "agent1-aggregate",
        "--agent1-json", str(a1_out),
        "--out", str(a1_adj)
    ]):
        return False

    # 3) Agent2 analysis for all sectors
    sector_map = json.load(open("data/sector_map_all.json", "r", encoding="utf-8"))
    summary = {}

    for sector in sector_map.keys():
        out_dec = CACHE / f"decision_{sector.lower()}_rag.json"
        print(f"🧭 Running Agent2 for sector: {sector}...")

        if not run([
            "python", "-m", "src.news_agents.cli", "agent2-decide",
            "--agent1-json", str(a1_adj),
            "--level", "sector",
            "--name", sector,
            "--out", str(out_dec)
        ]):
            print(f"❌ Failed to process sector: {sector}")
            continue

        try:
            summary[sector] = json.load(open(out_dec, "r", encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ Could not parse results for {sector}: {e}")

    # Save sector summary
    sum_path = CACHE / "sector_summary_rag.json"
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("✅ Agent analysis completed!")
    print(f"📊 Summary saved to: {sum_path}")

    return True


def generate_html_report(json_file: str, output_file: str, news_file: str) -> bool:
    """Generate HTML report from analysis results"""
    print("📄 Generating HTML report...")

    success = run([
        "python", "scripts/enhanced_html_generator.py",
        "--input", json_file,
        "--output", output_file,
        "--news", news_file,
        "--title", "RAG-Powered Sector News Analysis Report"
    ])

    if success:
        print(f"✅ HTML report generated: {output_file}")

    return success


def main():
    """Main RAG pipeline function"""
    parser = argparse.ArgumentParser(description="Run complete RAG pipeline for sector analysis")
    parser.add_argument("--config", default="rag_config.json", help="RAG configuration file")
    parser.add_argument("--provider", default="mock", choices=["openai", "mock"], help="AI provider for agents")
    parser.add_argument("--output-report", default="reports/rag_sector_analysis_report.html", help="Output HTML report file")
    parser.add_argument("--skip-rag", action="store_true", help="Skip RAG search and use sample data")

    args = parser.parse_args()

    print("🚀 Starting Integrated RAG Pipeline for Sector News Analysis")
    print("=" * 60)

    # Step 1: RAG Search for news
    if args.skip_rag:
        print("⏭️ Skipping RAG search, using sample data...")
        rag_results = {"csv_file": "data/news_all_sectors_sample.csv", "json_file": ".cache/news_all.json"}
    else:
        rag_results = run_rag_search(args.config)

    # Step 2: Agent Analysis
    if not run_agent_analysis(
        csv_file=rag_results["csv_file"],
        json_file=rag_results["json_file"],
        provider=args.provider
    ):
        print("❌ Pipeline failed at agent analysis stage")
        return

    # Step 3: Generate HTML Report
    summary_file = CACHE / "sector_summary_rag.json"
    if generate_html_report(
        json_file=str(summary_file),
        output_file=args.output_report,
        news_file=rag_results["json_file"]
    ):
        print("🎉 RAG Pipeline completed successfully!")
        print(f"📄 Final report: {args.output_report}")

        # Show summary if available
        if "total_articles" in rag_results:
            print(f"📊 Articles processed: {rag_results['total_articles']}")
            print(f"📊 Sectors covered: {rag_results['sectors_covered']}")
    else:
        print("❌ Pipeline failed at report generation stage")


if __name__ == "__main__":
    main()
