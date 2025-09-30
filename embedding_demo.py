#!/usr/bin/env python3
"""
Embedding API Demo for FinBERT News RAG Application
Demonstrates how to use the embedding generation and search endpoints
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def generate_embedding(text):
    """Generate embedding for given text"""
    try:
        response = requests.get(f"{API_BASE_URL}/generate_embedding", params={"text": text})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error generating embedding: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def search_with_embedding(embedding, limit=5, min_score=0.3):
    """Search using pre-computed embedding"""
    try:
        data = {
            "embedding": embedding,
            "limit": limit,
            "min_score": min_score
        }
        response = requests.post(f"{API_BASE_URL}/search_embedding", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error searching with embedding: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def main():
    """Demo the embedding workflow"""
    print("🧠 FinBERT News RAG - Embedding API Demo")
    print("=" * 50)
    
    # Example queries
    queries = [
        "artificial intelligence stock market trends",
        "cryptocurrency bitcoin price volatility",
        "federal reserve interest rate policy",
        "renewable energy investment opportunities"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📋 Demo {i}: '{query}'")
        print("-" * 40)
        
        # Step 1: Generate embedding
        print("🧠 Generating embedding...")
        embedding_result = generate_embedding(query)
        
        if not embedding_result:
            continue
            
        print(f"   ✅ Generated {embedding_result['dimension']}-dimensional embedding")
        
        # Step 2: Search with embedding
        print("🔍 Searching with embedding...")
        search_results = search_with_embedding(embedding_result['embedding'], limit=3)
        
        if search_results:
            print(f"   ✅ Found {len(search_results)} relevant documents:")
            
            for j, result in enumerate(search_results, 1):
                print(f"\n   📄 Result {j} (Score: {result['score']:.3f})")
                print(f"      Title: {result['title'][:80]}...")
                print(f"      Date: {result['date']}")
                if result.get('sentiment'):
                    sentiment_label = result['sentiment'].get('label', 'neutral')
                    sentiment_score = result['sentiment'].get('score', 0)
                    print(f"      Sentiment: {sentiment_label} ({sentiment_score:.2f})")
                if result.get('themes'):
                    print(f"      Themes: {', '.join(result['themes'][:3])}")
        else:
            print("   ❌ No results found")
    
    print("\n" + "=" * 50)
    print("🎉 Embedding demo completed!")
    print("\n💡 Use Cases:")
    print("• Generate embeddings once, store them, and reuse for multiple searches")
    print("• Compare document similarity using pre-computed embeddings")
    print("• Build custom search applications with your own embedding logic")
    print("• Integrate with external systems that provide embeddings")
    
    print("\n🔧 API Endpoints Used:")
    print("• GET  /generate_embedding?text=<query>  - Generate embedding for text")
    print("• POST /search_embedding                 - Search using pre-computed embedding")
    print("• POST /search                          - Traditional text-based search")

if __name__ == "__main__":
    main()