"""
Streamlit frontend for FinBERT News RAG System
Simple UI with two tabs: Data Summary and Similarity Search
"""

import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="FinBERT News RAG",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def call_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Any]:
    """Make API calls to FastAPI backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        kwargs: Dict[str, Any] = {"timeout": 30}
        if method.upper() == "GET":
            if data:
                kwargs["params"] = data
        else:
            if data is not None:
                kwargs["json"] = data
        response = requests.request(method.upper(), url, **kwargs)

        if response.status_code in (200, 201):
            if not response.content:
                return {}
            return response.json()
        if response.status_code == 204:
            return {}

        try:
            detail = response.json().get('detail')
        except Exception:
            detail = response.text
        st.error(f"API Error ({response.status_code}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API. Please ensure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return None

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
    """Unified search tab supporting Similarity, Tags, and Hybrid"""
    st.header("🔎 Search")
    
    # Search form
    with st.form("search_form"):
        col0, col1, col2 = st.columns([1.4, 3, 1])

        with col0:
            mode = st.selectbox("Mode", ["Similarity", "Tags", "Hybrid"], help="Choose search algorithm")

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

            # Tags input for Tags and Hybrid modes
            tags = []
            if mode in ("Tags", "Hybrid"):
                tags_text = st.text_input(
                    "Tags (comma-separated)",
                    value="",
                    placeholder="e.g., energy, oil, renewables",
                    help="Enter one or more tags separated by commas"
                )
                tags = [t.strip() for t in tags_text.split(',') if t.strip()]

            tags = []
            if mode in ("Tags", "Hybrid"):
                tags_text = st.text_input("Tags (comma-separated)", value="energy, oil, renewables")
                tags = [t.strip() for t in tags_text.split(',') if t.strip()]
        
        # Search button
        search_clicked = st.form_submit_button("🔍 Search", type="primary")
    
    # Perform search
    if search_clicked:
        results = None
        if mode == "Similarity":
            if not query:
                st.warning("Please enter a query for similarity search.")
            else:
                search_data = {
                    "query": query,
                    "limit": limit,
                    "min_score": min_score,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "source_index": source_index,
                }
                with st.spinner("🔍 Running similarity search..."):
                    # Prefer new endpoint; fallback to legacy /search
                    results = call_api("/search/similarity", method="POST", data=search_data)
                    if results is None:
                        results = call_api("/search", method="POST", data=search_data)
        elif mode == "Tags":
            if not tags:
                st.warning("Please provide at least one tag.")
            else:
                with st.spinner("🏷️ Running tags search (BM25)..."):
                    results = call_api("/search/tags", method="POST", data={
                        "tags": tags,
                        "limit": limit,
                        "min_score": min_score,
                        "date_from": date_from.isoformat() if date_from else None,
                        "date_to": date_to.isoformat() if date_to else None,
                        "source_index": source_index,
                        "tags_field": "structured_context",
                    })
        else:  # Hybrid
            with st.spinner("🔀 Running hybrid search..."):
                results = call_api("/search/hybrid", method="POST", data={
                    "query": query or "",
                    "tags": tags,
                    "limit": limit,
                    "min_score": min_score,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "source_index": source_index,
                    "semantic_field": "embedding_768d",
                    "tags_field": "structured_context",
                })
        
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


def display_search_configurations():
    """Display sector search configuration management UI"""
    st.header("⚙️ Search Configurations")

    configs = call_api("/config/sectors")
    if configs is None:
        return
    if not isinstance(configs, list):
        st.warning("Unexpected response while fetching configurations")
        return

    st.caption(f"{len(configs)} / 20 sectors configured")

    can_create = len(configs) < 20
    with st.expander("➕ Add new sector configuration", expanded=can_create and len(configs) == 0):
        with st.form("create_sector_form"):
            sector = st.text_input(
                "Sector key",
                placeholder="e.g. banking",
                help="Lowercase, max 64 characters (letters, numbers, hyphen, underscore)",
            )
            index_pattern = st.text_input("Index pattern", value="news_finbert_embedding*")
            semantic_field = st.text_input("Semantic embedding field", value="embedding_768d")
            tags_field = st.text_input("Tags field", value="structured_context")
            submitted = st.form_submit_button("Create sector", disabled=not can_create)
            if submitted:
                if not sector.strip():
                    st.warning("Sector key is required")
                else:
                    payload = {
                        "sector": sector.strip().lower(),
                        "index_pattern": index_pattern.strip(),
                        "semantic_field": semantic_field.strip(),
                        "tags_field": tags_field.strip(),
                    }
                    result = call_api("/config/sectors", method="POST", data=payload)
                    if result is not None:
                        st.success(f"Sector '{payload['sector']}' created")
                        st.experimental_rerun()

    if not configs:
        st.info("No sector configurations defined yet. Create one to get started.")
        return

    for summary in configs:
        sector = summary.get("sector")
        header = f"{sector} • {summary.get('phrase_count', 0)} phrases / {summary.get('tag_count', 0)} tags"
        with st.expander(header, expanded=False):
            details = call_api(f"/config/sectors/{sector}")
            if details is None:
                continue

            st.subheader("Base configuration")
            with st.form(f"update_sector_{sector}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    index_pattern = st.text_input(
                        "Index pattern",
                        value=details.get("index_pattern", ""),
                        key=f"idx_{sector}",
                    )
                with col2:
                    semantic_field = st.text_input(
                        "Semantic field",
                        value=details.get("semantic_field", ""),
                        key=f"sem_{sector}",
                    )
                with col3:
                    tags_field = st.text_input(
                        "Tags field",
                        value=details.get("tags_field", ""),
                        key=f"tags_{sector}",
                    )
                update_clicked = st.form_submit_button("Save settings")
                if update_clicked:
                    payload = {
                        "index_pattern": index_pattern.strip(),
                        "semantic_field": semantic_field.strip(),
                        "tags_field": tags_field.strip(),
                    }
                    result = call_api(f"/config/sectors/{sector}", method="PUT", data=payload)
                    if result is not None:
                        st.success("Settings updated")
                        st.experimental_rerun()

            st.markdown("---")
            st.subheader("Semantic search phrases")

            with st.form(f"add_phrase_{sector}"):
                new_phrase = st.text_input(
                    "Add phrase",
                    key=f"new_phrase_{sector}",
                    placeholder="Enter a semantic search phrase",
                )
                add_phrase = st.form_submit_button("Add phrase")
                if add_phrase:
                    cleaned = new_phrase.strip()
                    if not cleaned:
                        st.warning("Phrase cannot be empty")
                    else:
                        result = call_api(
                            f"/config/sectors/{sector}/phrases",
                            method="POST",
                            data={"phrases": [cleaned]},
                        )
                        if result is not None:
                            st.success("Phrase added")
                            st.experimental_rerun()

            for phrase in details.get("phrases", []):
                status_icon = {
                    "ready": "🟢",
                    "pending": "🕒",
                    "failed": "🔴",
                }.get(phrase.get("status"), "⚪")
                with st.form(f"phrase_form_{sector}_{phrase['id']}"):
                    st.text_input(
                        "Phrase",
                        value=phrase.get("text", ""),
                        key=f"phrase_text_{sector}_{phrase['id']}",
                    )
                    # Per-phrase semantic threshold control
                    min_thr_val = float(phrase.get("min_semantic_score", 0.0))
                    st.slider(
                        "Min semantic score (per-phrase)",
                        0.0, 1.0, min_thr_val, 0.05,
                        key=f"phrase_thr_{sector}_{phrase['id']}"
                    )
                    status_line = f"{status_icon} Status: {phrase.get('status', 'unknown')}"
                    if phrase.get("embedding_model"):
                        status_line += f" • Model: {phrase['embedding_model']}"
                    st.caption(status_line)
                    if phrase.get("error"):
                        st.error(phrase["error"])
                    col_u, col_d = st.columns(2)
                    if col_u.form_submit_button("Update phrase"):
                        updated_text = st.session_state.get(
                            f"phrase_text_{sector}_{phrase['id']}", ""
                        ).strip()
                        if not updated_text:
                            st.warning("Phrase cannot be empty")
                        else:
                            updated_thr = st.session_state.get(f"phrase_thr_{sector}_{phrase['id']}")
                            result = call_api(
                                f"/config/sectors/{sector}/phrases/{phrase['id']}",
                                method="PATCH",
                                data={"text": updated_text, "min_semantic_score": updated_thr},
                            )
                            if result is not None:
                                st.success("Phrase updated")
                                st.experimental_rerun()
                    if col_d.form_submit_button("Remove", help="Remove phrase"):
                        result = call_api(
                            f"/config/sectors/{sector}/phrases/{phrase['id']}",
                            method="DELETE",
                        )
                        if result is not None:
                            st.success("Phrase removed")
                            st.experimental_rerun()

            st.markdown("---")
            st.subheader("Tags for BM25 search")
            with st.form(f"add_tag_{sector}"):
                new_tag = st.text_input(
                    "Add tag",
                    key=f"new_tag_{sector}",
                    placeholder="e.g. liquidity",
                )
                add_tag = st.form_submit_button("Add tag")
                if add_tag:
                    cleaned_tag = new_tag.strip()
                    if not cleaned_tag:
                        st.warning("Tag cannot be empty")
                    else:
                        result = call_api(
                            f"/config/sectors/{sector}/tags",
                            method="POST",
                            data={"tags": [cleaned_tag]},
                        )
                        if result is not None:
                            st.success("Tag added")
                            st.experimental_rerun()

            tags = details.get("tags", [])
            if tags:
                for tag in tags:
                    col_tag, col_remove = st.columns([4, 1])
                    col_tag.markdown(f"- `{tag}`")
                    if col_remove.button("Remove", key=f"remove_tag_{sector}_{tag}"):
                        result = call_api(
                            f"/config/sectors/{sector}/tags/{tag}",
                            method="DELETE",
                        )
                        if result is not None:
                            st.success("Tag removed")
                            st.experimental_rerun()
            else:
                st.info("No tags configured yet.")

            st.markdown("---")
            st.markdown("#### Delete sector configuration")
            with st.form(f"delete_sector_{sector}"):
                confirmation = st.text_input(
                    "Type the sector key to confirm deletion",
                    key=f"confirm_delete_{sector}",
                )
                delete_clicked = st.form_submit_button("Delete sector", help="This action cannot be undone")
                if delete_clicked:
                    if confirmation.strip().lower() != sector:
                        st.warning("Sector key confirmation does not match")
                    else:
                        result = call_api(f"/config/sectors/{sector}", method="DELETE")
                        if result is not None:
                            st.success(f"Sector '{sector}' deleted")
                            st.experimental_rerun()


def display_sector_search():
    """Display sector-focused hybrid search"""
    st.header("📈 Sector News Search")

    configs = call_api("/config/sectors")
    if configs is None:
        return
    if not configs:
        st.info("No sector configurations defined yet. Create a configuration first.")
        return

    sector_names = [cfg.get("sector") for cfg in configs]
    with st.form("sector_search_form"):
        sector = st.selectbox("Sector", sector_names)
        col1, col2, col3 = st.columns(3)
        with col1:
            limit = st.number_input("Results limit", min_value=1, max_value=100, value=10)
        with col2:
            min_score = st.slider("Min score", 0.0, 1.0, 0.0, 0.05)
        with col3:
            use_score_filter = st.checkbox("Apply min score filter", value=False)

        col4, col5 = st.columns(2)
        with col4:
            date_from = st.text_input("Date from (YYYY-MM-DD)", value="")
        with col5:
            date_to = st.text_input("Date to (YYYY-MM-DD)", value="")

        submitted = st.form_submit_button("Run sector search", type="primary")

    if not submitted:
        return

    params: Dict[str, Any] = {"limit": limit}
    if use_score_filter:
        params["min_score"] = min_score
    if date_from.strip():
        params["date_from"] = date_from.strip()
    if date_to.strip():
        params["date_to"] = date_to.strip()

    response = call_api(f"/news_data/{sector}", method="GET", data=params)
    if response is None:
        return

    results = response.get("results", [])
    st.success(
        f"Retrieved {len(results)} results in {response.get('search_duration_ms', 0)} ms"
    )
    summary = response.get("config_summary", {})
    st.caption(
        f"Index pattern: {summary.get('index_pattern')} | "
        f"Semantic field: {summary.get('semantic_field')} | "
        f"Tags field: {summary.get('tags_field')}"
    )

    for idx, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled"
        with st.expander(f"{idx}. {title} (Score {result.get('score', 0):.3f})"):
            st.markdown(f"**URL:** {result.get('url') or 'N/A'}")
            st.markdown(f"**Date:** {result.get('date') or result.get('published_dt') or 'N/A'}")
            st.markdown(
                f"**Scores** – Semantic: {result.get('semantic_score', 0):.3f} | BM25: {result.get('bm25_score', 0):.3f}"
            )
            st.markdown(f"**Source index:** {result.get('source_index')}")
            if result.get("phrase_matches"):
                st.markdown("**Phrase matches:** " + ", ".join(result["phrase_matches"]))
            if result.get("tags_matched"):
                st.markdown("**Tag matches:** " + ", ".join(result["tags_matched"]))
            if result.get("summary"):
                st.markdown(f"**Summary:** {result['summary']}")
            if result.get("full_text"):
                st.text_area("Full text", result["full_text"], height=200, key=f"sector_ft_{sector}_{idx}")


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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Data Summary",
        "🔍 Search",
        "⚙️ Search Configurations",
        "📈 Sector News",
    ])
    
    with tab1:
        display_data_summary()
    
    with tab2:
        display_similarity_search()

    with tab3:
        display_search_configurations()

    with tab4:
        display_sector_search()

if __name__ == "__main__":
    main()
