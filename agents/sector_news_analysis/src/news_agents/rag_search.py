#!/usr/bin/env python3
"""
RAG Search Module for News Retrieval
Connects to RAG API endpoint to search for sector-specific news articles
"""

import json
import csv
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import the RAG API client
from .rag_api_client import RagApiClient, RagConfig


class RAGNewsSearch:
    """RAG-powered news search for sector analysis using API"""

    def __init__(self, config_path: str = "rag_config.json"):
        """Initialize RAG search with configuration"""
        self.config = self._load_config(config_path)
        self.api_client = None
        self._setup_api_client()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load RAG configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found"""
        env_base_url = os.getenv("SECTOR_AGENT_RAG_BASE_URL", os.getenv("FINBERT_RAG_BASE_URL", "http://localhost:8000"))
        env_endpoint = os.getenv("SECTOR_AGENT_RAG_ENDPOINT", "/search/cosine/embedding1155d/")

        return {
            "api": {
                "base_url": env_base_url,
                "endpoint": env_endpoint,
                "min_score": 0.5,
                "max_results_per_query": 25,
                "max_results_per_sector": 15,
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 2.0,
                "rate_limit_delay": 1.0
            },
            "sectors": {
                "Energy": ["oil", "gas", "petroleum", "crude", "energy sector", "refinery", "fuel"],
                "Banks": ["banking", "banks", "financial", "lending", "credit", "NPA", "RBI"],
                "Auto": ["automotive", "cars", "vehicles", "EV", "electric vehicle", "automobile"],
                "Cement": ["cement", "construction", "building materials", "infrastructure"],
                "IT": ["information technology", "software", "IT services", "tech", "digital"],
                "Pharma": ["pharmaceutical", "drugs", "medicine", "healthcare", "biotech"],
                "Telecom": ["telecommunication", "mobile", "wireless", "broadband", "5G"],
                "FMCG": ["consumer goods", "FMCG", "retail", "consumer", "household"],
                "Infrastructure": ["infrastructure", "construction", "roads", "highways", "railways"]
            },
            "output": {
                "csv_file": "data/news_rag_results.csv",
                "json_file": ".cache/news_rag.json",
                "include_metadata": True,
                "max_news_per_sector": 15
            }
        }

    def _setup_api_client(self):
        """Setup RAG API client connection"""
        try:
            api_config = self.config.get("api", {})
            base_url = os.getenv("SECTOR_AGENT_RAG_BASE_URL", os.getenv("FINBERT_RAG_BASE_URL", api_config.get("base_url", "http://localhost:8000")))
            endpoint = os.getenv("SECTOR_AGENT_RAG_ENDPOINT", api_config.get("endpoint", "/search/cosine/embedding1155d/"))

            rag_config = RagConfig(
                base_url=base_url,
                endpoint=endpoint,
                min_score=api_config.get("min_score", 0.5),
                max_results_per_query=api_config.get("max_results_per_query", 25),
                max_results_per_sector=api_config.get("max_results_per_sector", 15),
                timeout=api_config.get("timeout", 30),
                retry_attempts=api_config.get("retry_attempts", 3),
                retry_delay=api_config.get("retry_delay", 2.0),
                rate_limit_delay=api_config.get("rate_limit_delay", 1.0)
            )

            # Initialize API client
            self.api_client = RagApiClient(rag_config)

            print(f"✅ Connected to RAG API: {rag_config.base_url}")
            print(f"✅ Endpoint: {rag_config.endpoint}")
            print(f"✅ Min score threshold: {rag_config.min_score}")

        except Exception as e:
            print(f"❌ Error setting up RAG API client: {e}")
            self.api_client = None

    def search_by_sector(self, sector: str, limit: int = None) -> List[Dict[str, Any]]:
        """Search for news articles by sector using RAG API"""
        if not self.api_client:
            print("❌ RAG API client not available")
            return []

        # Get sector queries from config
        sector_queries = self.config["sectors"].get(sector, [])
        if not sector_queries:
            print(f"❌ No queries found for sector: {sector}")
            return []

        print(f"🔍 Searching RAG API for sector: {sector}")

        try:
            # Use the API client to fetch news for this sector
            news_items = self.api_client.fetch_news_for_sector(sector, sector_queries)

            # Convert NewsItem objects to dict format for compatibility
            results = []
            for item in news_items:
                result_dict = {
                    "id": item.id,
                    "headline": item.headline,
                    "summary": item.summary,
                    "datetime": item.datetime,
                    "source": item.source,
                    "region": item.region,
                    "sector": item.sector,
                    "url": item.source_url if hasattr(item, 'source_url') else "",
                    "similarity_score": 0.8,  # Default score since API doesn't provide this
                    "search_keyword": "sector_query",
                    "date_key": item.date_key
                }
                results.append(result_dict)

            print(f"✅ Found {len(results)} relevant articles for {sector}")
            return results

        except Exception as e:
            print(f"❌ Error searching RAG API for sector '{sector}': {e}")
            return []

    def search_all_sectors(self) -> Dict[str, List[Dict[str, Any]]]:
        """Search for news across all sectors using RAG API"""
        if not self.api_client:
            print("❌ RAG API client not available")
            return {}

        print("🔍 Searching RAG API for all sectors...")

        try:
            # Use the API client to fetch news for all sectors
            all_news_items = self.api_client.fetch_all_sectors()

            # Group by sector
            all_sector_results = {}
            for item in all_news_items:
                sector = item.sector
                if sector not in all_sector_results:
                    all_sector_results[sector] = []

                # Convert NewsItem to dict format
                result_dict = {
                    "id": item.id,
                    "headline": item.headline,
                    "summary": item.summary,
                    "datetime": item.datetime,
                    "source": item.source,
                    "region": item.region,
                    "sector": item.sector,
                    "url": item.source_url if hasattr(item, 'source_url') else "",
                    "similarity_score": 0.8,
                    "search_keyword": "sector_query",
                    "date_key": item.date_key
                }
                all_sector_results[sector].append(result_dict)

            print(f"✅ RAG API search completed for {len(all_sector_results)} sectors")
            return all_sector_results

        except Exception as e:
            print(f"❌ Error in RAG API search: {e}")
            return {}

    def create_csv_output(self, all_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create CSV file from search results"""
        csv_file = self.config["output"]["csv_file"]

        # Flatten results for CSV
        csv_rows = []
        for sector, results in all_results.items():
            for result in results:
                csv_rows.append({
                    "id": result["id"],
                    "headline": result["headline"],
                    "summary": result["summary"],
                    "datetime": result["datetime"],
                    "source": result["source"],
                    "region": result["region"],
                    "sector": result["sector"],
                    "url": result["url"],
                    "similarity_score": result["similarity_score"],
                    "search_keyword": result["search_keyword"]
                })

        # Create CSV
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if csv_rows:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)

        print(f"✅ Created CSV file: {csv_file} ({len(csv_rows)} articles)")
        return csv_file

    def create_json_output(self, all_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create JSON file from search results"""
        json_file = self.config["output"]["json_file"]

        # Convert to news format expected by agents
        news_articles = []
        for sector, results in all_results.items():
            for result in results:
                news_articles.append({
                    "id": result["id"],
                    "headline": result["headline"],
                    "summary": result["summary"],
                    "datetime": result["datetime"],
                    "source": result["source"],
                    "region": result["region"],
                    "sector": result["sector"],
                    "source_url": result["url"],
                    "date_key": result["date_key"]
                })

        # Create JSON
        os.makedirs(os.path.dirname(json_file), exist_ok=True)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(news_articles, f, indent=2, ensure_ascii=False)

        print(f"✅ Created JSON file: {json_file} ({len(news_articles)} articles)")
        return json_file

    def run_full_search(self) -> Dict[str, Any]:
        """Run complete RAG search pipeline"""
        print("🚀 Starting RAG news search pipeline...")

        # Search all sectors
        all_results = self.search_all_sectors()

        # Create output files
        csv_file = self.create_csv_output(all_results)
        json_file = self.create_json_output(all_results)

        # Summary
        total_articles = sum(len(results) for results in all_results.values())

        return {
            "total_articles": total_articles,
            "sectors_covered": len(all_results),
            "csv_file": csv_file,
            "json_file": json_file,
            "results_by_sector": {sector: len(results) for sector, results in all_results.items()}
        }


def main():
    """Main function for RAG search"""
    import argparse

    parser = argparse.ArgumentParser(description="RAG-powered news search for sector analysis")
    parser.add_argument("--config", default="rag_config.json", help="RAG configuration file")
    parser.add_argument("--sector", help="Search specific sector only")
    parser.add_argument("--output-csv", help="Output CSV file path")
    parser.add_argument("--output-json", help="Output JSON file path")

    args = parser.parse_args()

    # Initialize RAG search
    rag_search = RAGNewsSearch(args.config)

    if not rag_search.api_client:
        print("❌ Cannot proceed without RAG API connection")
        return

    # Run search
    if args.sector:
        print(f"🔍 Searching for sector: {args.sector}")
        results = rag_search.search_by_sector(args.sector)
        print(f"✅ Found {len(results)} articles for {args.sector}")

        # Create single sector output
        all_results = {args.sector: results}
    else:
        print("🔍 Searching all sectors...")
        all_results = rag_search.search_all_sectors()

    # Create output files
    csv_file = rag_search.create_csv_output(all_results)
    json_file = rag_search.create_json_output(all_results)

    print("\n🎉 RAG search completed!")
    print(f"📄 CSV: {csv_file}")
    print(f"📋 JSON: {json_file}")

    # Summary
    total_articles = sum(len(results) for results in all_results.values())
    print(f"\n📊 Summary: {total_articles} articles across {len(all_results)} sectors")


if __name__ == "__main__":
    main()
