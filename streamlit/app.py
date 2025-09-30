"""
Streamlit frontend for FinBERT News RAG System
Simple UI with two tabs: Data Summary and Similarity Search
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

# Configure Streamlit page
st.set_page_config(
    page_title="FinBERT News RAG",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = "http://localhost:8000"

def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API calls to FastAPI backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return {}
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API. Please ensure the FastAPI server is running on port 8000.")
        return {}
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return {}

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def display_data_summary():
    """Display data summary tab"""
    st.header("📊 Data Summary")
    
    # API Health Check
    with st.spinner("Checking API health..."):
        health = call_api("/health")
    
    if health:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("API Status", "🟢 Healthy")
        with col2:
            st.metric("Elasticsearch", f"🟢 {health.get('elasticsearch', 'Unknown')}")
        with col3:
            st.metric("Last Check", health.get('timestamp', 'Unknown')[:19])
    
    st.divider()
    
    # System Statistics
    with st.spinner("Loading system statistics..."):
        stats = call_api("/stats")
    
    if stats:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Total Documents", f"{stats['total_documents']:,}")
        with col2:
            st.metric("🗂️ Total Indices", stats['total_indices'])
        with col3:
            st.metric("⚡ Cluster Health", f"🟢 {stats['cluster_health']}")
        with col4:
            total_size = sum(idx['size_in_bytes'] for idx in stats['indices'] if isinstance(idx['size_in_bytes'], (int, float)))
            if total_size > 0:
                st.metric("💾 Total Size", format_bytes(total_size))
            else:
                st.metric("💾 Total Size", "N/A (readonly)")
        
        st.divider()
        
        # Indices Details
        st.subheader("📈 Index Details")
        
        if stats['indices']:
            # Create DataFrame for better display
            indices_data = []
            for idx in stats['indices']:
                # Handle size display for readonly permissions
                if isinstance(idx['size_in_bytes'], (int, float)) and idx['size_in_bytes'] > 0:
                    size_display = format_bytes(idx['size_in_bytes'])
                else:
                    size_display = "N/A (readonly)"
                
                indices_data.append({
                    'Index Name': idx['index_name'],
                    'Documents': f"{idx['doc_count']:,}",
                    'Size': size_display,
                    'Date From': idx['date_range']['from'],
                    'Date To': idx['date_range']['to'],
                    'Type': 'Processed' if 'processed' in idx['index_name'] else 'Pattern'
                })
            
            df = pd.DataFrame(indices_data)
            st.dataframe(df, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Document count by index
                fig_docs = px.bar(
                    x=[idx['index_name'] for idx in stats['indices']],
                    y=[idx['doc_count'] for idx in stats['indices']],
                    title="Documents by Index",
                    labels={'x': 'Index', 'y': 'Document Count'}
                )
                fig_docs.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_docs, use_container_width=True)
            
            with col2:
                # Document count distribution (instead of size for readonly)
                if any(idx['size_in_bytes'] > 0 for idx in stats['indices']):
                    # Use size if available
                    fig_size = px.pie(
                        values=[idx['size_in_bytes'] for idx in stats['indices']],
                        names=[idx['index_name'].split('-')[-1] if '-' in idx['index_name'] else idx['index_name'] for idx in stats['indices']],
                        title="Storage Distribution by Index"
                    )
                else:
                    # Use document count if size not available (readonly)
                    fig_size = px.pie(
                        values=[idx['doc_count'] for idx in stats['indices']],
                        names=[idx['index_name'].split('-')[-1] if '-' in idx['index_name'] else idx['index_name'] for idx in stats['indices']],
                        title="Document Distribution by Index"
                    )
                st.plotly_chart(fig_size, use_container_width=True)
    
    else:
        st.warning("Unable to load system statistics. Please check if the API is running.")

def display_similarity_search():
    """Display similarity search tab"""
    st.header("🔍 Similarity Search")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Search Query",
                placeholder="Enter your search query (e.g., 'market volatility', 'technology stocks', 'financial crisis')",
                help="Enter natural language queries to find similar news articles"
            )
        
        with col2:
            limit = st.number_input("Results Limit", min_value=1, max_value=50, value=10)
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_score = st.slider("Minimum Similarity Score", 0.0, 1.0, 0.5, 0.1)
            
            with col2:
                date_from = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
            
            with col3:
                date_to = st.date_input("To Date", value=datetime.now())
            
            # Index selection
            indices = call_api("/indices")
            if indices:
                index_options = ["All Indices"] + [idx["name"] for idx in indices]
                selected_index = st.selectbox("Search in Index", index_options)
                source_index = None if selected_index == "All Indices" else selected_index
            else:
                source_index = None
        
        # Search button
        search_clicked = st.form_submit_button("🔍 Search", type="primary")
    
    # Perform search
    if search_clicked and query:
        search_data = {
            "query": query,
            "limit": limit,
            "min_score": min_score,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "source_index": source_index
        }
        
        with st.spinner("🔍 Searching for similar articles..."):
            results = call_api("/search", method="POST", data=search_data)
        
        if results:
            st.success(f"Found {len(results)} similar articles")
            
            # Display results
            for i, result in enumerate(results, 1):
                with st.expander(f"📰 {i}. {result['title'][:100]}... (Score: {result['score']:.3f})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Title:** {result['title']}")
                        st.markdown(f"**Summary:** {result['summary']}")
                        st.markdown(f"**URL:** {result['url']}")
                        
                        # Show full text preview
                        if st.checkbox(f"Show full text", key=f"fulltext_{i}"):
                            st.text_area("Full Text", result['full_text'], height=200, key=f"text_{i}")
                    
                    with col2:
                        st.markdown(f"**Date:** {result['date']}")
                        st.markdown(f"**Similarity Score:** {result['score']:.3f}")
                        
                        # Sentiment
                        if result.get('sentiment') and isinstance(result['sentiment'], dict):
                            sentiment = result['sentiment']
                            st.markdown("**Sentiment:**")
                            for key, value in sentiment.items():
                                if isinstance(value, (int, float)):
                                    st.markdown(f"- {key}: {value:.3f}")
                                elif isinstance(value, str):
                                    st.markdown(f"- {key}: {value}")
                        
                        # Themes
                        if result.get('themes') and isinstance(result['themes'], list):
                            st.markdown("**Themes:**")
                            for theme in result['themes'][:3]:
                                if theme and isinstance(theme, str):
                                    st.markdown(f"- {theme}")
                        
                        # Organizations
                        if result.get('organizations') and isinstance(result['organizations'], list):
                            st.markdown("**Organizations:**")
                            for org in result['organizations'][:3]:
                                if org and isinstance(org, str):
                                    st.markdown(f"- {org}")
            
            # Results summary
            st.divider()
            scores = [r['score'] for r in results]
            st.markdown(f"**Search Statistics:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Score", f"{sum(scores)/len(scores):.3f}")
            with col2:
                st.metric("Best Match", f"{max(scores):.3f}")
            with col3:
                st.metric("Score Range", f"{min(scores):.3f} - {max(scores):.3f}")
        
        else:
            st.warning("No results found. Try adjusting your search query or parameters.")
    
    elif search_clicked and not query:
        st.warning("Please enter a search query.")

def main():
    """Main Streamlit application"""
    # Sidebar
    with st.sidebar:
        st.title("📰 FinBERT News RAG")
        st.markdown("### Navigation")
        
        # API Status
        st.markdown("**API Status:**")
        health = call_api("/health")
        if health:
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
        
        st.divider()
        
        # Quick stats
        st.markdown("**Quick Info:**")
        stats = call_api("/stats")
        if stats:
            st.markdown(f"📄 {stats['total_documents']:,} documents")
            st.markdown(f"🗂️ {stats['total_indices']} indices")
            st.markdown(f"⚡ {stats['cluster_health']} cluster")
        
        st.divider()
        st.markdown("**About:**")
        st.markdown("This app provides access to FinBERT-processed news data with semantic search capabilities.")
    
    # Main content tabs
    tab1, tab2 = st.tabs(["📊 Data Summary", "🔍 Similarity Search"])
    
    with tab1:
        display_data_summary()
    
    with tab2:
        display_similarity_search()

if __name__ == "__main__":
    main()