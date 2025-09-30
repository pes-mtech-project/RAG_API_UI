#!/usr/bin/env python3
"""
Demo script showing how to use the FinBERT News RAG API programmatically
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"

def search_news(query, limit=5, min_score=0.5):
    """Search for news articles using similarity search"""
    search_data = {
        "query": query,
        "limit": limit,
        "min_score": min_score
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/search", json=search_data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Search failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def get_system_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Stats failed: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {}

def demo_search_queries():
    """Demonstrate various search queries"""
    
    queries = [
        "stock market crash",
        "technology earnings",
        "cryptocurrency regulation",
        "economic inflation",
        "merger and acquisition"
    ]
    
    print("🔍 Demo: Similarity Search Queries")
    print("=" * 50)
    
    for query in queries:
        print(f"\n📊 Searching for: '{query}'")
        results = search_news(query, limit=3, min_score=0.4)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['title'][:80]}...")
                print(f"      Score: {result['score']:.3f} | Date: {result['date']}")
                if result.get('sentiment'):
                    sentiment = result['sentiment']
                    if 'compound' in sentiment:
                        print(f"      Sentiment: {sentiment['compound']:.3f}")
        else:
            print("   No results found")

def demo_system_overview():
    """Show system overview"""
    print("📊 Demo: System Overview")
    print("=" * 50)
    
    stats = get_system_stats()
    
    if stats:
        print(f"📄 Total Documents: {stats['total_documents']:,}")
        print(f"📁 Total Indices: {stats['total_indices']}")
        print(f"⚡ Cluster Health: {stats['cluster_health']}")
        
        print(f"\n📂 Available Indices:")
        for idx in stats['indices'][:5]:  # Show top 5
            print(f"   • {idx['index_name']}: {idx['doc_count']:,} docs")
            print(f"     Date range: {idx['date_range']['from']} to {idx['date_range']['to']}")
    else:
        print("Unable to retrieve system stats")

def main():
    """Main demo function"""
    print("🚀 FinBERT News RAG API Demo")
    print("=" * 50)
    
    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Status: {health.get('status', 'unknown')}")
            print(f"✅ Elasticsearch: {health.get('elasticsearch', 'unknown')}")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure to run: ./run_api.sh")
        return
    
    print()
    
    # Run demos
    demo_system_overview()
    print()
    demo_search_queries()
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print("\n📱 Try the web interface:")
    print("1. Run: ./run_streamlit.sh")
    print("2. Open: http://localhost:8501")

if __name__ == "__main__":
    main()