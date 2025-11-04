#!/usr/bin/env python3
"""
RAG API Client for fetching news data from external endpoint.
Converts RAG API responses to news_all.json format compatible with existing pipeline.
"""

import json
import os
import requests
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

# Optional spaCy import - will use fallback if not available
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    print("Warning: spaCy not available. Using keyword-based region detection.")

try:
    from .types import NewsItem
    from .utils import iso_to_datekey
except ImportError:
    from news_agents.types import NewsItem
    from news_agents.utils import iso_to_datekey


@dataclass
class RagConfig:
    """Configuration for RAG API client"""
    base_url: str = os.getenv("SECTOR_AGENT_RAG_BASE_URL", os.getenv("FINBERT_RAG_BASE_URL", "http://localhost:8000"))
    endpoint: str = os.getenv("SECTOR_AGENT_RAG_ENDPOINT", "/search/cosine/embedding1155d/")
    min_score: float = 0.5
    max_results_per_query: int = 25
    max_results_per_sector: int = 25  # New: limit per sector
    timeout: int = 30
    region: str = "IN"
    retry_attempts: int = 3  # New: retry logic
    retry_delay: float = 2.0  # New: delay between retries
    rate_limit_delay: float = 1.0  # New: delay between requests


# Predefined sector queries - configurable
DEFAULT_SECTOR_QUERIES = {
    "Banks": [
        "banking sector interest rates monetary policy RBI",
        "credit growth loan disbursement NPAs asset quality",
        "digital payments fintech banking regulations"
    ],
    "Energy": [
        "crude oil prices OPEC production energy sector",
        "renewable energy solar wind power generation",
        "natural gas pipeline oil refinery petroleum"
    ],
    "Auto": [
        "automobile sector car sales electric vehicles",
        "semiconductor chips automotive supply chain",
        "festive season demand passenger vehicles commercial"
    ],
    "FMCG": [
        "consumer goods rural demand monsoon agriculture",
        "commodity prices palm oil inflation margins",
        "FMCG brands market share consumer spending"
    ],
    "IT": [
        "information technology software services exports",
        "US visa H1B IT sector offshore development",
        "digital transformation cloud computing AI"
    ],
    "Pharma": [
        "pharmaceutical drugs USFDA approvals exports",
        "generic medicines patent expiry price controls",
        "healthcare sector medical devices regulations"
    ],
    "Telecom": [
        "telecommunications 5G spectrum auction TRAI",
        "mobile subscribers tariff hikes telecom operators",
        "fiber optic network digital infrastructure"
    ],
    "Cement": [
        "cement sector construction infrastructure demand",
        "raw material costs coal power cement prices",
        "housing real estate construction activity"
    ],
    "Infrastructure": [
        "infrastructure projects roads highways metro",
        "government capex budget allocation infra spending",
        "construction sector EPC contractors order book"
    ]
}


class RegionDetector:
    """NLP-based region detection using spaCy"""

    def __init__(self):
        self.nlp = None
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy English model not found. Using keyword-based region detection.")
                self.nlp = None
        else:
            print("spaCy not available. Using keyword-based region detection.")

    # Regional indicators for different markets
    REGION_INDICATORS = {
        "IN": [
            # Countries
            "india", "indian", "bharat", "hindustan",
            # Cities
            "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata", "hyderabad",
            "pune", "ahmedabad", "surat", "jaipur", "lucknow", "kanpur", "nagpur", "gurgaon",
            "noida", "kochi", "coimbatore", "bhubaneswar", "thiruvananthapuram",
            # Institutions
            "rbi", "reserve bank of india", "sebi", "nse", "bse", "sensex", "nifty",
            "lic", "sbi", "hdfc", "icici", "axis", "kotak", "bajaj", "tata", "reliance",
            "infosys", "tcs", "wipro", "bharti", "airtel", "jio", "adani",
            # Regions/States
            "maharashtra", "karnataka", "tamil nadu", "gujarat", "rajasthan", "uttar pradesh",
            "west bengal", "telangana", "andhra pradesh", "kerala", "punjab", "haryana",
            # Currency/Economic
            "rupee", "inr", "crore", "lakh", "gst", "demonetization", "jan dhan", "upi",
            "aadhaar", "pmo", "modi", "amit shah", "nirmala sitharaman", "shaktikanta das"
        ],
        "US": [
            # Countries
            "usa", "united states", "america", "american",
            # Cities
            "new york", "washington", "chicago", "los angeles", "san francisco", "boston",
            "seattle", "atlanta", "miami", "dallas", "houston", "philadelphia", "detroit",
            # Institutions
            "fed", "federal reserve", "wall street", "nasdaq", "nyse", "s&p", "dow jones",
            "treasury", "sec", "fdic", "jpmorgan", "goldman sachs", "morgan stanley",
            "bank of america", "wells fargo", "citigroup", "apple", "microsoft", "google",
            "amazon", "tesla", "facebook", "meta",
            # Currency/Economic
            "dollar", "usd", "trillion", "billion", "fed funds rate", "fomc", "jerome powell"
        ],
        "GB": [
            # Countries
            "uk", "united kingdom", "britain", "british", "england", "scotland", "wales",
            # Cities
            "london", "manchester", "birmingham", "glasgow", "edinburgh", "liverpool",
            # Institutions
            "boe", "bank of england", "lse", "ftse", "lloyds", "barclays", "hsbc", "rbs",
            # Currency
            "pound", "sterling", "gbp", "pence"
        ],
        "CN": [
            # Countries
            "china", "chinese", "mainland china", "prc",
            # Cities
            "beijing", "shanghai", "shenzhen", "guangzhou", "hong kong", "macau",
            # Institutions
            "pboc", "people's bank of china", "shanghai stock exchange", "shenzhen stock exchange",
            "alibaba", "tencent", "baidu", "huawei", "xiaomi",
            # Currency
            "yuan", "rmb", "renminbi", "cny"
        ]
    }

    def detect_region(self, headline: str, summary: str) -> str:
        """
        Detect region based on headline and summary content using NLP

        Args:
            headline: News headline
            summary: News summary

        Returns:
            Region code (IN, US, GB, CN, etc.) or "IN" as default
        """
        text = f"{headline} {summary}".lower()

        # Simple keyword-based detection first
        region_scores = {}
        for region, indicators in self.REGION_INDICATORS.items():
            score = 0
            for indicator in indicators:
                if indicator.lower() in text:
                    # Weight longer phrases higher
                    weight = len(indicator.split())
                    score += weight
            region_scores[region] = score

        # If we have clear indicators, return the highest scoring region
        if region_scores and max(region_scores.values()) > 0:
            return max(region_scores, key=region_scores.get)

        # Enhanced NLP-based detection if spaCy is available
        if self.nlp:
            try:
                doc = self.nlp(f"{headline} {summary}")

                # Extract named entities (countries, cities, organizations)
                entities = [ent.text.lower() for ent in doc.ents
                           if ent.label_ in ["GPE", "ORG", "MONEY"]]

                # Re-score based on entities
                for region, indicators in self.REGION_INDICATORS.items():
                    for entity in entities:
                        for indicator in indicators:
                            if indicator in entity or entity in indicator:
                                region_scores[region] = region_scores.get(region, 0) + 2

                if region_scores and max(region_scores.values()) > 0:
                    return max(region_scores, key=region_scores.get)

            except Exception as e:
                print(f"NLP region detection failed: {e}")

        # Default to India if no clear indicators
        return "IN"


class RagApiClient:
    """Client for interacting with RAG API endpoint"""

    def __init__(self, config: Optional[RagConfig] = None):
        self.config = config or RagConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RAG-News-Agents/1.0'
        })
        self.region_detector = RegionDetector()

    def search(self, query: str, size: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute search query against RAG API with retry logic

        Args:
            query: Search query string
            size: Maximum number of results (defaults to config)

        Returns:
            RAG API response as dict
        """
        if size is None:
            size = self.config.max_results_per_query

        url = f"{self.config.base_url}{self.config.endpoint}"
        payload = {
            "query": query,
            "size": size
        }

        last_exception = None

        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_exception = e
                if response.status_code == 429:  # Rate limit
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limited. Retrying in {delay}s (attempt {attempt + 1}/{self.config.retry_attempts})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"HTTP error {response.status_code} for query '{query}': {e}")
                    break

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    print(f"Request failed. Retrying in {delay}s (attempt {attempt + 1}/{self.config.retry_attempts}): {e}")
                    time.sleep(delay)
                    continue
                else:
                    break

        print(f"RAG API request failed after {self.config.retry_attempts} attempts for query '{query}': {last_exception}")
        return {"results": []}

    def _extract_rag_id(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract ID from RAG API response"""
        # Try various possible ID fields from RAG response
        for id_field in ["id", "_id", "doc_id", "document_id", "news_id"]:
            if id_field in result and result[id_field]:
                return str(result[id_field])
        return None

    def _generate_news_id(self, text: str, sector: str) -> str:
        """Generate consistent ID from content as fallback"""
        content = f"{text}_{sector}"
        return hashlib.md5(content.encode()).hexdigest()[:8].upper()

    def _extract_headline_summary(self, text: str) -> tuple[str, str]:
        """
        Extract headline and summary from RAG response text.
        Uses simple heuristics - first sentence as headline, rest as summary.
        """
        sentences = text.split('. ')
        if len(sentences) >= 2:
            headline = sentences[0].strip()
            summary = '. '.join(sentences[1:]).strip()
        else:
            # Fallback: split at reasonable length
            if len(text) > 80:
                headline = text[:80].strip()
                summary = text[80:].strip()
            else:
                headline = text.strip()
                summary = text.strip()

        # Clean up
        if not headline.endswith('.'):
            headline = headline.rstrip('.')
        if summary and not summary.endswith('.'):
            summary += '.'

        return headline, summary

    def convert_to_news_items(self, rag_response: Dict[str, Any], sector: str, source_query: str) -> List[NewsItem]:
        """
        Convert RAG API response to NewsItem objects

        Args:
            rag_response: Response from RAG API
            sector: Target sector for these results
            source_query: Original query used

        Returns:
            List of NewsItem objects
        """
        news_items = []
        results = rag_response.get("results", [])
        current_time = datetime.now(timezone.utc)

        for i, result in enumerate(results):
            # Filter by score threshold
            score = result.get("score", 0.0)
            if score < self.config.min_score:
                continue

            # Extract text content - try multiple fields
            text = result.get("full_text", "") or result.get("text", "") or result.get("summary", "")
            text = text.strip()
            if not text:
                continue

            # Generate headline and summary
            headline, summary = self._extract_headline_summary(text)

            # Use RAG API ID if available, otherwise generate one
            rag_id = self._extract_rag_id(result)
            if rag_id:
                news_id = rag_id
            else:
                news_id = f"{sector[:2].upper()}_{self._generate_news_id(text, sector)}"

            # Extract datetime from RAG API response
            published_dt = result.get("published_dt", "").strip()
            if not published_dt:
                # Fallback to current time if published_dt is missing
                published_dt = current_time.isoformat()

            # Detect region using NLP
            detected_region = self.region_detector.detect_region(headline, summary)

            # Create NewsItem using RAG API's published_dt and detected region
            news_item = NewsItem(
                id=news_id,
                headline=headline,
                summary=summary,
                datetime=published_dt,
                source=f"RAG-API (score: {score:.3f})",
                region=detected_region,
                sector=sector,
                date_key=iso_to_datekey(published_dt)
            )

            news_items.append(news_item)

        return news_items

    def fetch_news_for_sector(self, sector: str, queries: List[str]) -> List[NewsItem]:
        """
        Fetch news for a specific sector using multiple queries

        Args:
            sector: Target sector name
            queries: List of search queries for this sector

        Returns:
            Combined list of NewsItem objects (limited to max_results_per_sector)
        """
        all_news = []
        seen_texts = set()  # Deduplicate similar results
        seen_ids = set()    # Deduplicate by ID

        for query in queries:
            # Stop if we've reached the sector limit
            if len(all_news) >= self.config.max_results_per_sector:
                break

            print(f"Fetching {sector} news with query: {query}")

            # Execute search
            response = self.search(query)

            # Convert to news items
            news_items = self.convert_to_news_items(response, sector, query)

            # Deduplicate by ID and text similarity
            for item in news_items:
                if len(all_news) >= self.config.max_results_per_sector:
                    break

                # Check for duplicate IDs
                if item.id in seen_ids:
                    continue

                # Check for similar headlines
                text_key = item.headline.lower()[:50]
                if text_key in seen_texts:
                    continue

                seen_ids.add(item.id)
                seen_texts.add(text_key)
                all_news.append(item)

            # Rate limiting between requests
            time.sleep(self.config.rate_limit_delay)

        print(f"Collected {len(all_news)} unique news items for {sector}")
        return all_news

    def fetch_all_sectors(self, sector_queries: Optional[Dict[str, List[str]]] = None) -> List[NewsItem]:
        """
        Fetch news for all configured sectors

        Args:
            sector_queries: Custom sector query mapping (defaults to DEFAULT_SECTOR_QUERIES)

        Returns:
            Combined list of all NewsItem objects
        """
        if sector_queries is None:
            sector_queries = DEFAULT_SECTOR_QUERIES

        all_news = []

        print(f"Starting RAG API data collection for {len(sector_queries)} sectors...")

        for sector, queries in sector_queries.items():
            try:
                sector_news = self.fetch_news_for_sector(sector, queries)
                all_news.extend(sector_news)
                print(f"✓ {sector}: {len(sector_news)} items")

            except Exception as e:
                print(f"✗ {sector}: Failed - {e}")
                continue

        print(f"Total collected: {len(all_news)} news items")
        return all_news


def save_news_to_json(news_items: List[NewsItem], output_path: str) -> None:
    """Save news items to JSON file in news_all.json format"""
    news_dicts = [asdict(item) for item in news_items]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(news_dicts, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(news_items)} news items to {output_path}")


def main():
    """CLI entry point for RAG data collection"""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch news from RAG API")
    parser.add_argument("--output", "-o", default=".cache/news_rag.json",
                       help="Output JSON file path")
    parser.add_argument("--min-score", type=float, default=0.5,
                       help="Minimum RAG score threshold")
    parser.add_argument("--max-per-query", type=int, default=25,
                       help="Maximum results per query")
    parser.add_argument("--sectors", nargs="+",
                       help="Specific sectors to fetch (default: all)")

    args = parser.parse_args()

    # Configure client
    config = RagConfig(
        min_score=args.min_score,
        max_results_per_query=args.max_per_query
    )

    client = RagApiClient(config)

    # Filter sectors if specified
    sector_queries = DEFAULT_SECTOR_QUERIES
    if args.sectors:
        sector_queries = {
            sector: queries for sector, queries in DEFAULT_SECTOR_QUERIES.items()
            if sector in args.sectors
        }

    # Fetch data
    news_items = client.fetch_all_sectors(sector_queries)

    # Save results
    save_news_to_json(news_items, args.output)

    print("\n✅ RAG data collection complete!")
    print(f"   Output: {args.output}")
    print(f"   Items: {len(news_items)}")


if __name__ == "__main__":
    main()
