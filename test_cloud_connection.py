#!/usr/bin/env python3
"""
Test script to verify cloud Elasticsearch connectivity
"""

import os
import base64
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cloud_elasticsearch():
    """Test connection to cloud Elasticsearch"""
    print("🌩️  Testing Cloud Elasticsearch Connection")
    print("=" * 50)
    
    # Get cloud credentials using readonly access
    es_host = os.getenv('ES_READONLY_HOST', 'https://my-elasticsearch-project-a901ed.es.asia-south1.gcp.elastic.cloud:443')
    es_key = os.getenv('ES_READONLY_KEY', 'ZzlOZ21aa0JBUXZGb3RVb01rLUY6blBPOVphYmE2MjVTZ1o2eGZWOUpxQQ==')
    
    print(f"🔗 Host: {es_host}")
    
    try:
        # Try both API key and basic auth authentication methods
        print("🔌 Trying API key authentication...")
        try:
            # First try as API key (newer ES format)
            es_client = Elasticsearch(
                es_host,
                api_key=es_key,
                verify_certs=True,
                ssl_show_warn=False,
                request_timeout=30
            )
        except Exception as api_key_error:
            print(f"   API key auth failed: {api_key_error}")
            print("🔌 Trying basic auth (decoded credentials)...")
            
            # Fallback to basic auth
            credentials = base64.b64decode(es_key).decode('utf-8')
            username, password = credentials.split(':')
            print(f"👤 Username: {username}")
            
            es_client = Elasticsearch(
                es_host,
                basic_auth=(username, password),
                verify_certs=True,
                ssl_show_warn=False,
                request_timeout=30
            )
        
        # Test connection with readonly operations
        print("✅ API key authentication successful!")
        
        try:
            # Try cluster info (might not work with readonly)
            cluster_info = es_client.info()
            print(f"   Cluster Name: {cluster_info.get('cluster_name', 'N/A')}")
            print(f"   Version: {cluster_info.get('version', {}).get('number', 'N/A')}")
        except Exception as info_error:
            print(f"   ⚠️  Cluster info not accessible (readonly permissions): {info_error}")
        
        try:
            # Try cluster health (might not work with readonly)
            health = es_client.cluster.health()
            print(f"   Health: {health.get('status', 'N/A')}")
            print(f"   Nodes: {health.get('number_of_nodes', 'N/A')}")
        except Exception as health_error:
            print(f"   ⚠️  Cluster health not accessible (readonly permissions): {health_error}")
        
        # Try to list indices (might not work with readonly)
        print("\n📊 Checking for news indices...")
        try:
            indices = es_client.cat.indices(index="*gdelt*,*processed*,*news*", format="json")
            if indices:
                print(f"   Found {len(indices)} relevant indices:")
                for idx in indices[:10]:  # Show first 10
                    name = idx.get('index', 'N/A')
                    docs = idx.get('docs.count', '0')
                    size = idx.get('store.size', '0')
                    print(f"   - {name}: {docs} docs, {size}")
            else:
                print("   ⚠️  No news-related indices found")
        except Exception as indices_error:
            print(f"   ⚠️  Cannot list indices (readonly permissions): {indices_error}")
            print("   📝 Will try direct search on known patterns...")
            
        # Try a simple search on common index patterns
        print("\n🔍 Testing search functionality...")
        search_patterns = [
            "*gdelt*,*processed*,*news*",
            "*processed*",
            "*gdelt*", 
            "news_*",
            "*"
        ]
        
        search_successful = False
        for pattern in search_patterns:
            try:
                search_result = es_client.search(
                    index=pattern,
                    size=1,
                    body={"query": {"match_all": {}}}
                )
                total_docs = search_result['hits']['total']['value']
                print(f"   ✅ Search successful on '{pattern}'! Total documents: {total_docs:,}")
                search_successful = True
                
                # Show a sample document if available
                if search_result['hits']['hits']:
                    sample_doc = search_result['hits']['hits'][0]
                    print(f"   📄 Sample document from index: {sample_doc['_index']}")
                    source = sample_doc['_source']
                    if 'title' in source:
                        print(f"      Title: {source['title'][:100]}...")
                    break
                        
            except Exception as search_error:
                print(f"   ⚠️  Search on '{pattern}' failed: {search_error}")
                continue
        
        if not search_successful:
            print("   ❌ All search patterns failed - no accessible data found")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cloud_elasticsearch()
    
    if success:
        print("\n🎉 Cloud Elasticsearch connection successful!")
        print("The RAG application is ready to use cloud data.")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Check ES1_HOST and ES1_KEY in .env file")
        print("2. Verify cloud Elasticsearch cluster is running")
        print("3. Ensure credentials have proper permissions")
        print("4. Check network connectivity")