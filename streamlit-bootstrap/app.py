#!/usr/bin/env python3
"""
Lightweight Bootstrap Streamlit UI for FinBERT RAG
Fast-loading minimal interface for production deployments
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, List, Any

# Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

st.set_page_config(
    page_title="FinBERT RAG - Bootstrap",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("💹 FinBERT RAG - Production Interface")
    st.markdown("**Fast Bootstrap UI** | Lightweight production interface for financial news analysis")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        st.code(f"API: {API_BASE_URL}")
        
        # Health check
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API Connected")
            else:
                st.error(f"❌ API Error: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection Failed: {str(e)[:50]}")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Financial News Search")
        
        # Search input
        query = st.text_input(
            "Enter your financial query:",
            placeholder="e.g., Tesla stock performance, inflation impact, market trends"
        )
        
        # Search options
        col_a, col_b = st.columns(2)
        with col_a:
            limit = st.selectbox("Results", [5, 10, 20, 50], index=1)
        with col_b:
            search_type = st.selectbox("Search Type", ["semantic", "keyword"], index=0)
        
        if st.button("🚀 Search", type="primary"):
            if query.strip():
                search_financial_news(query, limit, search_type)
            else:
                st.warning("Please enter a search query")
    
    with col2:
        st.subheader("📊 Quick Stats")
        
        # API stats
        try:
            stats_response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                st.metric("Total Documents", stats.get("total_documents", "N/A"))
                st.metric("Search Queries", stats.get("total_searches", "N/A"))
                st.metric("Avg Response Time", f"{stats.get('avg_response_time', 0):.2f}s")
            else:
                st.info("Stats unavailable")
        except:
            st.info("Stats loading...")

def search_financial_news(query: str, limit: int, search_type: str):
    """Perform financial news search via API"""
    
    with st.spinner(f"Searching for: {query}..."):
        try:
            # Prepare search payload
            payload = {
                "query": query,
                "limit": limit,
                "search_type": search_type
            }
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/search",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                display_search_results(results, query)
            else:
                st.error(f"Search failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Search timed out. Please try again.")
        except Exception as e:
            st.error(f"❌ Search error: {str(e)}")

def display_search_results(results: Dict[str, Any], query: str):
    """Display search results in a clean format"""
    
    if not results or "results" not in results:
        st.warning("No results found")
        return
    
    articles = results["results"]
    
    st.success(f"Found {len(articles)} results for: **{query}**")
    
    # Results metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Results", len(articles))
    with col2:
        st.metric("Response Time", f"{results.get('response_time', 0):.2f}s")
    with col3:
        st.metric("Search Type", results.get("search_type", "unknown").title())
    
    st.divider()
    
    # Display articles
    for i, article in enumerate(articles, 1):
        with st.container():
            # Article header
            col_title, col_score = st.columns([4, 1])
            
            with col_title:
                st.subheader(f"{i}. {article.get('title', 'Untitled')}")
            
            with col_score:
                if 'score' in article:
                    score = article['score']
                    if score > 0.8:
                        st.success(f"Score: {score:.3f}")
                    elif score > 0.6:
                        st.info(f"Score: {score:.3f}")
                    else:
                        st.warning(f"Score: {score:.3f}")
            
            # Article content
            st.markdown(f"**Content:** {article.get('content', 'No content available')[:300]}...")
            
            # Metadata
            col_date, col_source = st.columns(2)
            with col_date:
                if 'date' in article:
                    st.text(f"📅 {article['date']}")
            with col_source:
                if 'source' in article:
                    st.text(f"📰 {article['source']}")
            
            st.divider()

# Footer
def show_footer():
    st.markdown("---")
    st.markdown("""
    **FinBERT RAG Bootstrap UI** | 
    🚀 Production-ready | 
    ⚡ Fast-loading | 
    📊 Real-time search
    """)

if __name__ == "__main__":
    main()
    show_footer()