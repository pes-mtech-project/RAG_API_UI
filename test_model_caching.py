#!/usr/bin/env python3
"""
Comprehensive test script to demonstrate model caching solution
Tests the new modular API endpoints and shows model download behavior
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health Check: PASSED")
            return True
        else:
            print(f"❌ Health Check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health Check: ERROR - {e}")
        return False

def test_search_endpoint(endpoint: str, query: str, embedding_type: str):
    """Test a specific search endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    payload = {"query": query, "limit": 3}
    
    print(f"\n🔍 Testing {embedding_type} Search:")
    print(f"   URL: {endpoint}")
    print(f"   Query: '{query}'")
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)  # Longer timeout for model downloads
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"   Total hits: {data.get('total_hits', 0)}")
            print(f"   Embedding field: {data.get('embedding_field', 'unknown')}")
            
            # Show sample results
            results = data.get('results', [])
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. [{result.get('score', 0):.3f}] {result.get('title', 'No title')[:60]}...")
            
            return True, response_time
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, response_time
            
    except Exception as e:
        response_time = time.time() - start_time
        print(f"❌ Error: {e}")
        return False, response_time

def test_cache_info():
    """Test the model cache info endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/search/model-cache-info/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n📁 Model Cache Info:")
            cache_info = data.get('cache_info', {})
            print(f"   Cache Directory: {cache_info.get('cache_directory', 'unknown')}")
            print(f"   Cached Models: {cache_info.get('cached_models', [])}")
            print(f"   Loaded Models: {cache_info.get('model_types_loaded', [])}")
            return True
        else:
            print(f"❌ Cache Info Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cache Info Error: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("=" * 70)
    print("    FINBERT RAG API - MODEL CACHING TEST")
    print("=" * 70)
    
    # Health check first
    if not test_health_check():
        print("❌ Health check failed. Exiting.")
        return
    
    # Wait for startup
    print("\n⏳ Waiting for API to fully initialize...")
    time.sleep(15)
    
    # Test endpoints - First call will download models, second call should be cached
    endpoints = [
        ("/search/cosine/embedding384d/", "technology stocks financial news", "384d"),
        ("/search/cosine/embedding768d/", "artificial intelligence investment", "768d"),
    ]
    
    print("\n" + "=" * 50)
    print("TESTING MODEL DOWNLOAD AND CACHING")
    print("=" * 50)
    
    # First round - models will download
    print("\n🚀 FIRST ROUND: Model downloads expected")
    first_round_times = {}
    
    for endpoint, query, embedding_type in endpoints:
        success, response_time = test_search_endpoint(endpoint, query, embedding_type)
        first_round_times[embedding_type] = response_time
        time.sleep(2)  # Brief pause between tests
    
    # Check cache info after first round
    test_cache_info()
    
    # Second round - models should be cached
    print("\n🔄 SECOND ROUND: Cached models expected (faster response)")
    second_round_times = {}
    
    for endpoint, query, embedding_type in endpoints:
        success, response_time = test_search_endpoint(endpoint, query, embedding_type)
        second_round_times[embedding_type] = response_time
        time.sleep(2)
    
    # Performance comparison
    print("\n" + "=" * 50)
    print("CACHING PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    for embedding_type in ["384d", "768d"]:
        if embedding_type in first_round_times and embedding_type in second_round_times:
            first_time = first_round_times[embedding_type]
            second_time = second_round_times[embedding_type]
            speedup = first_time / second_time if second_time > 0 else 0
            
            print(f"\n{embedding_type.upper()} Model Performance:")
            print(f"  First call (with download): {first_time:.2f}s")
            print(f"  Second call (cached):       {second_time:.2f}s")
            print(f"  Speedup factor:             {speedup:.1f}x")
            
            if speedup > 2:
                print(f"  ✅ Caching appears to be working!")
            else:
                print(f"  ⚠️  Caching may not be working optimally")
    
    # Final cache info
    print("\n" + "=" * 50)
    print("FINAL CACHE STATUS")
    print("=" * 50)
    test_cache_info()
    
    print("\n✅ Test completed!")
    print("\nIf you see significant speedup between first and second calls,")
    print("the model caching solution is working correctly!")

if __name__ == "__main__":
    main()