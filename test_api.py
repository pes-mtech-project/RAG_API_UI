#!/usr/bin/env python3
"""
Test script for FinBERT News RAG Application
Verifies API functionality and system health
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint, method="GET", data=None, description=""):
    """Test a single API endpoint"""
    print(f"🧪 Testing {method} {endpoint} - {description}")
    
    try:
        url = f"{API_BASE_URL}{endpoint}"
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success ({elapsed:.2f}s)")
            return result
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Connection Error: Is the API running on port 8000?")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Run comprehensive API tests"""
    print("🧪 FinBERT News RAG API Test Suite")
    print("=" * 50)
    
    # Test 1: Root endpoint
    root_result = test_api_endpoint("/", description="Root endpoint")
    
    # Test 2: Health check
    health_result = test_api_endpoint("/health", description="Health check")
    
    # Test 3: System statistics
    stats_result = test_api_endpoint("/stats", description="System statistics")
    if stats_result:
        print(f"   📊 Total documents: {stats_result.get('total_documents', 0):,}")
        print(f"   📁 Total indices: {stats_result.get('total_indices', 0)}")
        print(f"   ⚡ Cluster health: {stats_result.get('cluster_health', 'unknown')}")
    
    # Test 4: List indices
    indices_result = test_api_endpoint("/indices", description="List indices")
    if indices_result:
        print(f"   📂 Found {len(indices_result)} indices")
    
    # Test 5: Search functionality
    search_data = {
        "query": "financial market volatility",
        "limit": 5,
        "min_score": 0.3
    }
    search_result = test_api_endpoint("/search", method="POST", data=search_data, description="Similarity search")
    if search_result:
        print(f"   🔍 Found {len(search_result)} results")
        if search_result:
            best_score = max(r['score'] for r in search_result)
            print(f"   🎯 Best match score: {best_score:.3f}")
    
    # Test 6: Embedding generation
    embedding_data = {"text": "artificial intelligence stock market"}
    embedding_result = test_api_endpoint("/generate_embedding", method="POST", data=embedding_data, description="Generate embedding")
    if embedding_result:
        print(f"   🧠 Generated embedding with dimension: {embedding_result.get('dimension', 0)}")
    
    # Test 7: Search with pre-computed embedding
    if embedding_result and embedding_result.get('embedding'):
        embedding_search_data = {
            "embedding": embedding_result['embedding'],
            "limit": 3,
            "min_score": 0.3
        }
        embedding_search_result = test_api_endpoint("/search_embedding", method="POST", data=embedding_search_data, description="Search with embedding")
        if embedding_search_result:
            print(f"   🎯 Embedding search found {len(embedding_search_result)} results")
    
    print("\n" + "=" * 50)
    
    # Summary
    tests = [root_result, health_result, stats_result, indices_result, search_result, embedding_result]
    if 'embedding_search_result' in locals():
        tests.append(embedding_search_result)
    successful_tests = sum(1 for test in tests if test is not None)
    
    print(f"📊 Test Summary: {successful_tests}/{len(tests)} tests passed")
    
    if successful_tests == len(tests):
        print("🎉 All tests passed! API is fully functional.")
        print("\n🚀 Next steps:")
        print("1. Start Streamlit app: ./run_streamlit.sh")
        print("2. Access web interface: http://localhost:8501")
    else:
        print("⚠️  Some tests failed. Check the API setup and Elasticsearch connection.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure FastAPI is running: ./run_api.sh")
        print("2. Check Elasticsearch is accessible")
        print("3. Verify .env configuration")

if __name__ == "__main__":
    main()