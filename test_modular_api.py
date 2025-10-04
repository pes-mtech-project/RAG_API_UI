#!/usr/bin/env python3
"""
Comprehensive test script for the new modular FinBERT RAG API
Tests all three embedding dimensions: 384d, 768d, and 1155d
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

# Test queries for different sectors
TEST_QUERIES = {
    "Finance": "Indian banks exposure to non-performing assets",
    "FMCG": "growth outlook of packaged foods and personal care products in India", 
    "Automotive": "electric vehicle adoption and subsidies in India",
    "Energy": "oil price fluctuations impact on Indian refiners",
    "IT": "cloud computing revenue growth for Indian IT services",
    "Healthcare": "pharmaceutical companies drug development pipeline",
    "Real_Estate": "commercial real estate investment trusts performance",
    "Agriculture": "agricultural commodity prices and farmer income support"
}

def test_health_check():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"✅ Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   API Status: {data.get('api', 'unknown')}")
            print(f"   Elasticsearch: {data.get('elasticsearch', 'unknown')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_embedding_compatibility():
    """Test embedding compatibility endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/search/embedding-compatibility/", timeout=15)
        print(f"✅ Embedding Compatibility Check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   Embedding Types Status:")
            for embedding in data.get('embedding_types', []):
                status = "✅" if embedding.get('compatible') else "❌"
                print(f"     {status} {embedding.get('type')}: {embedding.get('dimension')}d - {embedding.get('field')}")
                if embedding.get('error'):
                    print(f"        Error: {embedding.get('error')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Compatibility Check Failed: {e}")
        return False

def test_embedding_generation():
    """Test embedding generation for all types"""
    test_text = "Apple Inc. reported strong quarterly earnings driven by iPhone sales growth"
    embedding_types = ["384d", "768d", "1155d"]
    
    print("\n🧠 Testing Embedding Generation:")
    results = {}
    
    for emb_type in embedding_types:
        try:
            response = requests.post(
                f"{API_BASE_URL}/search/generate-embedding/",
                params={"text": test_text, "embedding_type": emb_type},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {emb_type}: Generated {data.get('dimension')}d embedding")
                results[emb_type] = {
                    "dimension": data.get('dimension'),
                    "embedding_length": len(data.get('embedding', []))
                }
            else:
                print(f"   ❌ {emb_type}: Failed with status {response.status_code}")
                results[emb_type] = {"error": response.text}
        except Exception as e:
            print(f"   ❌ {emb_type}: Exception - {e}")
            results[emb_type] = {"error": str(e)}
    
    return results

def test_cosine_search(embedding_type: str, query: str, sector: str) -> Dict[str, Any]:
    """Test cosine similarity search for specific embedding type"""
    endpoint_map = {
        "384d": f"{API_BASE_URL}/search/cosine/embedding384d/",
        "768d": f"{API_BASE_URL}/search/cosine/embedding768d/",
        "1155d": f"{API_BASE_URL}/search/cosine/embedding1155d/"
    }
    
    endpoint = endpoint_map.get(embedding_type)
    if not endpoint:
        return {"error": f"Unknown embedding type: {embedding_type}"}
    
    payload = {
        "query": query,
        "limit": 5,
        "min_score": 0.5
    }
    
    try:
        start_time = time.time()
        response = requests.post(endpoint, json=payload, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "results_count": len(data.get('results', [])),
                "total_hits": data.get('total_hits', 0),
                "response_time_ms": response_time,
                "search_time_ms": data.get('search_time_ms', 0),
                "embedding_field": data.get('embedding_field'),
                "top_score": data.get('results', [{}])[0].get('score', 0) if data.get('results') else 0,
                "results": data.get('results', [])[:2]  # Keep only top 2 for brevity
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "response_time_ms": response_time
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def run_comprehensive_tests():
    """Run all tests and generate comprehensive report"""
    print("=" * 80)
    print("         FINBERT RAG API - MODULAR ARCHITECTURE TEST SUITE")
    print("=" * 80)
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Health check
    print("🏥 Health Checks:")
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ API is not healthy. Stopping tests.")
        return
    
    # Compatibility check  
    print("\n🔧 Compatibility Checks:")
    compatibility_ok = test_embedding_compatibility()
    
    # Embedding generation tests
    embedding_results = test_embedding_generation()
    
    # Search tests for all embedding types
    print("\n🔍 Cosine Similarity Search Tests:")
    search_results = {}
    
    embedding_types = ["384d", "768d", "1155d"]
    
    for emb_type in embedding_types:
        print(f"\n   Testing {emb_type.upper()} Embeddings:")
        search_results[emb_type] = {}
        
        for sector, query in TEST_QUERIES.items():
            result = test_cosine_search(emb_type, query, sector)
            search_results[emb_type][sector] = result
            
            if result.get('success'):
                print(f"     ✅ {sector}: {result.get('results_count', 0)} results "
                      f"(top score: {result.get('top_score', 0):.3f}, "
                      f"time: {result.get('response_time_ms', 0):.0f}ms)")
            else:
                print(f"     ❌ {sector}: {result.get('error', 'Unknown error')}")
    
    # Performance comparison
    print("\n📊 Performance Analysis:")
    print("   " + "-" * 60)
    print("   Sector              384d      768d      1155d")
    print("   " + "-" * 60)
    
    for sector in TEST_QUERIES.keys():
        line = f"   {sector:<18}"
        for emb_type in embedding_types:
            result = search_results.get(emb_type, {}).get(sector, {})
            if result.get('success'):
                score = result.get('top_score', 0)
                time_ms = result.get('response_time_ms', 0)
                line += f"  {score:.2f}({time_ms:.0f}ms)"
            else:
                line += f"  {'FAIL':<8}"
        print(line)
    
    # Save detailed results
    test_results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "api_url": API_BASE_URL,
        "health_check": health_ok,
        "compatibility_check": compatibility_ok,
        "embedding_generation": embedding_results,
        "search_results": search_results,
        "test_queries": TEST_QUERIES
    }
    
    with open("modular_api_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: modular_api_test_results.json")
    
    # Summary
    print("\n📈 Test Summary:")
    total_tests = len(TEST_QUERIES) * len(embedding_types)
    successful_tests = sum(
        1 for emb_type in embedding_types 
        for sector in TEST_QUERIES.keys() 
        if search_results.get(emb_type, {}).get(sector, {}).get('success', False)
    )
    
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("   🎉 Overall Status: EXCELLENT")
    elif success_rate >= 60:
        print("   ✅ Overall Status: GOOD")
    else:
        print("   ⚠️  Overall Status: NEEDS ATTENTION")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_comprehensive_tests()