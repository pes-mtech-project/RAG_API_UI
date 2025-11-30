#!/usr/bin/env python3
"""
Test script for troubleshooting FinBERT News RAG API search functionality
This script tests various search endpoints and provides detailed diagnostics
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
# API_BASE_URL = "http://finber-finbe-mlc1emju4jnw-1497871200.ap-south-1.elb.amazonaws.com"
API_BASE_URL = "http://localhost:8000"  # Use this for local testing

def test_health_check():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/_cat/indices?v", timeout=10)
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_stats_endpoint():
    """Test the stats endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=30)
        print(f"✅ Stats Endpoint: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total Documents: {stats.get('total_documents', 'N/A')}")
            print(f"   Total Indices: {stats.get('total_indices', 'N/A')}")
            print(f"   Cluster Health: {stats.get('cluster_health', 'N/A')}")
            if stats.get('indices'):
                print("   Available Indices:")
                for idx in stats['indices']:
                    print(f"     - {idx['index_name']}: {idx['doc_count']} docs")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Stats Endpoint Failed: {e}")
        return False

def test_debug_search():
    """Test the debug search endpoint"""
    try:
        payload = {
            "query": "HDFC Bank Finance",
            "limit": 5,
            "min_score": 0.2,
            "source_index": "news_finbert_embeddings"
        }
        
        response = requests.post(f"{API_BASE_URL}/debug_search", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f"✅ Debug Search: {response.status_code}")
        if response.status_code == 200:
            debug_info = response.json()
            print(f"   Query: {debug_info.get('query')}")
            print(f"   Embedding Dimension: {debug_info.get('embedding_dimension')}")
            print(f"   Index Pattern: {debug_info.get('index_pattern')}")
            print(f"   Tested Fields: {debug_info.get('embedding_fields_tested')}")
            print(f"   Successful Field: {debug_info.get('successful_field')}")
            print(f"   Last Error: {debug_info.get('last_error')}")
        else:
            print(f"   Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Debug Search Failed: {e}")
        return False

def test_pregenerated_search():
    """Test the test search endpoint with pregenerated embeddings"""
    try:
        payload = {
            "use_pregenerated": True
        }
        
        response = requests.post(f"{API_BASE_URL}/test_search", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f"✅ Pregenerated Test Search: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}:")
                print(f"     Title: {result.get('title', 'N/A')[:60]}...")
                print(f"     Score: {result.get('score', 'N/A')}")
                print(f"     ID: {result.get('id', 'N/A')}")
        else:
            print(f"   Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Pregenerated Test Search Failed: {e}")
        return False

def test_original_search():
    """Test the original search endpoint that's failing"""
    try:
        payload = {
            "query": "HDFC Bank Finance",
            "limit": 5,
            "min_score": 0.2,
            "source_index": "news_finbert_embeddings"
        }
        
        response = requests.post(f"{API_BASE_URL}/search", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f"✅ Original Search: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results[:2]):
                print(f"   Result {i+1}:")
                print(f"     Title: {result.get('title', 'N/A')[:60]}...")
                print(f"     Score: {result.get('score', 'N/A')}")
        else:
            print(f"   Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Original Search Failed: {e}")
        return False

def test_custom_search():
    """Test search with different parameters"""
    try:
        payload = {
            "use_pregenerated": False,
            "custom_query": "financial news banking"
        }
        
        response = requests.post(f"{API_BASE_URL}/test_search", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f"✅ Custom Test Search: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {len(results)} results")
        else:
            print(f"   Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Custom Test Search Failed: {e}")
        return False

def run_curl_test():
    """Run the exact curl command that was failing"""
    print("\n🔄 Running equivalent of failing curl command...")
    
    import subprocess
    
    curl_command = [
        'curl', '--location', f'{API_BASE_URL}/search',
        '--header', 'Content-Type: application/json',
        '--data', json.dumps({
            "query": "HDFC Bank Finance",
            "limit": 5,
            "min_score": 0.2,
            "source_index": "news_finbert_embeddings"
        })
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        print(f"Curl Exit Code: {result.returncode}")
        print(f"Curl Response: {result.stdout}")
        if result.stderr:
            print(f"Curl Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Curl Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 FinBERT News RAG API - Search Troubleshooting")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Stats Endpoint", test_stats_endpoint),
        ("Debug Search", test_debug_search),
        ("Pregenerated Test Search", test_pregenerated_search),
        ("Original Search (Failing)", test_original_search),
        ("Custom Test Search", test_custom_search),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 40)
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        results[test_name] = {
            'success': success,
            'duration': round(end_time - start_time, 2)
        }
        print(f"   Duration: {results[test_name]['duration']}s")
    
    # Run curl test separately
    print("\n🔍 Testing: Curl Command")
    print("-" * 40)
    curl_success = run_curl_test()
    results["Curl Command"] = {'success': curl_success, 'duration': 0}
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{test_name:25} {status:8} ({result['duration']}s)")
    
    # Recommendations
    print("\n💡 Troubleshooting Recommendations")
    print("=" * 60)
    
    if not results["Health Check"]['success']:
        print("❌ API is not responding - check deployment status")
    elif not results["Stats Endpoint"]['success']:
        print("❌ Elasticsearch connection issues - check credentials/network")
    elif not results["Original Search (Failing)"]['success']:
        if results["Pregenerated Test Search"]['success']:
            print("✅ Pregenerated search works - issue is likely with embedding field mapping")
        else:
            print("❌ All search methods failing - check Elasticsearch index structure")
    else:
        print("✅ All tests passed - the issue may have been resolved!")
    
    print("\n🔧 Next Steps:")
    print("1. Check the debug search output for specific error details")
    print("2. Verify Elasticsearch index mappings for embedding fields")
    print("3. Consider using the /test_search endpoint as a workaround")
    print("4. Monitor CloudWatch logs for detailed error information")

if __name__ == "__main__":
    main()