#!/usr/bin/env python3

import os
import json
from elasticsearch import Elasticsearch

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    # Get credentials
    es_host = os.getenv('ES_READONLY_HOST')
    es_key = os.getenv('ES_READONLY_KEY')
    
    if not es_host or not es_key:
        print("Missing ES credentials in .env file")
        print(f"ES_READONLY_HOST: {es_host}")
        print(f"ES_READONLY_KEY: {'*' * len(es_key) if es_key else 'None'}")
        return
    
    print(f"Connecting to: {es_host}")
    print(f"Using API Key: {'*' * len(es_key)}")
    
    # Connect to Elasticsearch
    es = Elasticsearch(
        [es_host],
        api_key=es_key,
        verify_certs=True,
        ssl_show_warn=False
    )
    
    try:
        # Get a sample document to see its structure
        response = es.search(
            index='news_finbert_embeddings',
            body={
                'size': 1,
                'query': {'match_all': {}},
                '_source': ['*']  # Get all fields
            }
        )
        
        if response['hits']['hits']:
            doc = response['hits']['hits'][0]['_source']
            doc_id = response['hits']['hits'][0]['_id']
            
            print(f"\n=== DOCUMENT ID: {doc_id} ===")
            print(f"=== TOTAL FIELDS: {len(doc)} ===\n")
            
            for key, value in sorted(doc.items()):
                if isinstance(value, str):
                    if len(value) > 200:
                        display_value = value[:200] + "..."
                    else:
                        display_value = value
                    print(f"{key:25}: \"{display_value}\"")
                elif isinstance(value, list):
                    print(f"{key:25}: [list with {len(value)} items]")
                    if value and len(value) > 0:
                        sample = str(value[0])[:100] + "..." if len(str(value[0])) > 100 else str(value[0])
                        print(f"{' ':25}   Sample: {sample}")
                elif isinstance(value, dict):
                    print(f"{key:25}: {{dict with {len(value)} keys}}")
                    if value:
                        keys_sample = list(value.keys())[:5]
                        print(f"{' ':25}   Keys: {keys_sample}")
                else:
                    print(f"{key:25}: {type(value).__name__} = {value}")
                    
        else:
            print('No documents found in news_finbert_embeddings index')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()