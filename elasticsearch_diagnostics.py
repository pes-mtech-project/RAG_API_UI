#!/usr/bin/env python3
"""
Elasticsearch Index Diagnostics for FinBERT News RAG
This script helps diagnose embedding field issues and provides solutions
"""

import requests
import json
import base64
from elasticsearch import Elasticsearch
import os
from typing import Dict, Any

def get_elasticsearch_client():
    """Initialize Elasticsearch client with credentials from environment or defaults"""
    # Use the same credentials as the API
    es_host = os.getenv('ES_READONLY_HOST', 'https://my-elasticsearch-project-a901ed.es.asia-south1.gcp.elastic.cloud:443')
    es_key = os.getenv('ES_READONLY_KEY', 'ZzlOZ21aa0JBUXZGb3RVb01rLUY6blBPOVphYmE2MjVTZ1o2eGZWOUpxQQ==')
    
    try:
        # Try as API key first
        es = Elasticsearch(
            es_host,
            api_key=es_key,
            verify_certs=True,
            ssl_show_warn=False,
            request_timeout=30
        )
        # Test connection
        es.info()
        return es
    except:
        # Fallback to basic auth
        try:
            credentials = base64.b64decode(es_key).decode('utf-8')
            username, password = credentials.split(':')
            
            es = Elasticsearch(
                es_host,
                basic_auth=(username, password),
                verify_certs=True,
                ssl_show_warn=False,
                request_timeout=30
            )
            # Test connection
            es.info()
            return es
        except Exception as e:
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            return None

def analyze_index_mappings(es: Elasticsearch):
    """Analyze index mappings to understand embedding field structure"""
    print("🔍 Analyzing Index Mappings")
    print("=" * 50)
    
    index_patterns = ["news_finbert_embeddings", "*processed*", "*news*", "*gdelt*"]
    
    for pattern in index_patterns:
        try:
            # Get indices matching pattern
            indices = es.cat.indices(index=pattern, format="json")
            
            if indices:
                print(f"\n📊 Pattern: {pattern}")
                print("-" * 30)
                
                for index_info in indices:
                    index_name = index_info['index']
                    doc_count = index_info.get('docs.count', '0')
                    print(f"  Index: {index_name} ({doc_count} docs)")
                    
                    try:
                        # Get mapping for this index
                        mapping = es.indices.get_mapping(index=index_name)
                        
                        if index_name in mapping and 'mappings' in mapping[index_name]:
                            properties = mapping[index_name]['mappings'].get('properties', {})
                            
                            # Look for embedding-related fields
                            embedding_fields = []
                            for field_name, field_props in properties.items():
                                if ('embedding' in field_name.lower() or 
                                    'vector' in field_name.lower() or
                                    field_props.get('type') == 'dense_vector'):
                                    embedding_fields.append({
                                        'name': field_name,
                                        'type': field_props.get('type', 'unknown'),
                                        'dims': field_props.get('dims', 'unknown')
                                    })
                            
                            if embedding_fields:
                                print("    🎯 Embedding Fields:")
                                for field in embedding_fields:
                                    print(f"      - {field['name']}: {field['type']} (dims: {field['dims']})")
                            else:
                                print("    ⚠️  No embedding fields found")
                                
                                # Show first few fields to understand structure
                                print("    📝 Available Fields (first 10):")
                                for i, (field_name, field_props) in enumerate(list(properties.items())[:10]):
                                    field_type = field_props.get('type', 'object')
                                    print(f"      - {field_name}: {field_type}")
                        
                    except Exception as e:
                        print(f"    ❌ Could not get mapping: {e}")
            else:
                print(f"📭 No indices found for pattern: {pattern}")
                
        except Exception as e:
            print(f"❌ Error analyzing pattern {pattern}: {e}")

def test_sample_document(es: Elasticsearch):
    """Get a sample document to understand the data structure"""
    print("\n🔍 Analyzing Sample Documents")
    print("=" * 50)
    
    index_patterns = ["news_finbert_embeddings", "*processed*"]
    
    for pattern in index_patterns:
        try:
            # Get a sample document
            result = es.search(
                index=pattern,
                body={
                    "size": 1,
                    "query": {"match_all": {}}
                }
            )
            
            if result['hits']['hits']:
                doc = result['hits']['hits'][0]
                source = doc['_source']
                
                print(f"\n📄 Sample from {doc['_index']}:")
                print(f"  Document ID: {doc['_id']}")
                
                # Look for embedding fields in the document
                embedding_fields = []
                for field_name, field_value in source.items():
                    if ('embedding' in field_name.lower() or 'vector' in field_name.lower()):
                        if isinstance(field_value, list) and len(field_value) > 0:
                            if isinstance(field_value[0], (int, float)):
                                embedding_fields.append({
                                    'name': field_name,
                                    'length': len(field_value),
                                    'sample': field_value[:5]
                                })
                
                if embedding_fields:
                    print("  🎯 Found Embedding Fields:")
                    for field in embedding_fields:
                        print(f"    - {field['name']}: {field['length']} dimensions")
                        print(f"      Sample values: {field['sample']}")
                else:
                    print("  ⚠️  No embedding vectors found in document")
                    print("  📝 Available fields:")
                    for field_name in list(source.keys())[:15]:
                        value = source[field_name]
                        if isinstance(value, str):
                            value = value[:50] + "..." if len(value) > 50 else value
                        print(f"    - {field_name}: {type(value).__name__} - {value}")
                
        except Exception as e:
            print(f"❌ Error getting sample from {pattern}: {e}")

def test_embedding_field_queries(es: Elasticsearch):
    """Test different embedding field queries"""
    print("\n🧪 Testing Embedding Field Queries")
    print("=" * 50)
    
    # Sample embedding vector (384 dimensions, normalized)
    test_vector = [0.1] * 384
    
    embedding_fields = ["embedding_384d", "embedding", "embeddings", "vector", "sentence_embedding"]
    index_patterns = ["news_finbert_embeddings", "*processed*"]
    
    for index_pattern in index_patterns:
        print(f"\n📊 Testing index pattern: {index_pattern}")
        
        for field in embedding_fields:
            try:
                query = {
                    "size": 1,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": f"cosineSimilarity(params.query_vector, '{field}') + 1.0",
                                "params": {"query_vector": test_vector}
                            }
                        }
                    }
                }
                
                result = es.search(index=index_pattern, body=query)
                if result['hits']['hits']:
                    score = result['hits']['hits'][0]['_score']
                    print(f"  ✅ {field}: Score {score:.3f}")
                else:
                    print(f"  📭 {field}: No results")
                    
            except Exception as e:
                error_type = "Unknown error"
                if "search_phase_execution_exception" in str(e):
                    error_type = "Field not found or type mismatch"
                elif "script_exception" in str(e):
                    error_type = "Script execution error"
                elif "runtime error" in str(e):
                    error_type = "Runtime script error"
                
                print(f"  ❌ {field}: {error_type}")

def generate_fix_suggestions():
    """Generate suggestions to fix the embedding search issues"""
    print("\n💡 Fix Suggestions")
    print("=" * 50)
    
    suggestions = [
        "1. 🔧 Update API to use the correct embedding field name found in mappings",
        "2. 🔄 Add field existence checks before running similarity queries", 
        "3. 🛡️ Implement graceful fallback to text search when embeddings fail",
        "4. 📊 Use the debug endpoints to monitor field availability",
        "5. 🔍 Consider re-indexing data if embedding fields are missing",
        "6. ⚡ Optimize queries with proper field type validation",
        "7. 📈 Monitor CloudWatch logs for detailed error patterns"
    ]
    
    for suggestion in suggestions:
        print(f"  {suggestion}")

def main():
    """Run comprehensive Elasticsearch diagnostics"""
    print("🔍 Elasticsearch Index Diagnostics for FinBERT News RAG")
    print("=" * 70)
    
    # Initialize Elasticsearch client
    es = get_elasticsearch_client()
    if not es:
        print("❌ Cannot proceed without Elasticsearch connection")
        return
    
    try:
        # Test connection
        cluster_info = es.info()
        print(f"✅ Connected to Elasticsearch cluster: {cluster_info.get('cluster_name', 'Unknown')}")
    except Exception as e:
        print(f"⚠️  Limited connection (readonly): {e}")
    
    # Run diagnostics
    analyze_index_mappings(es)
    test_sample_document(es)
    test_embedding_field_queries(es)
    generate_fix_suggestions()
    
    print("\n📋 Summary")
    print("=" * 50)
    print("1. Check the embedding fields found in your indices")
    print("2. Update the API to use the correct field names") 
    print("3. Test with the /debug_search and /test_search endpoints")
    print("4. Consider the fix suggestions above")

if __name__ == "__main__":
    main()