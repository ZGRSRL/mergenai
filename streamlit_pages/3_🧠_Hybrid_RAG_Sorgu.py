#!/usr/bin/env python3
"""
Streamlit Pages - Hybrid RAG Query
Semantic search on 172K chunks
"""

import streamlit as st
import requests
import os
from typing import Dict, Any

# Configuration
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8001")

@st.cache_resource
def get_rag_client():
    """Initialize RAG API client"""
    class RAGClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
        
        def hybrid_search(self, query: str, alpha: float = 0.6, topk: int = 10):
            """Hybrid search"""
            try:
                endpoint = f"{self.base_url}/api/rag/hybrid_search"
                params = {
                    "query": query,
                    "alpha": alpha,
                    "topk": topk
                }
                response = requests.post(endpoint, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e), "results": []}
    
    return RAGClient(RAG_API_URL)

st.title("🧠 Hybrid RAG Sorgu Motoru")
st.markdown("### 172,402 Geçmiş Fırsat Üzerinde Anlamsal Arama")

# Controls
col_query, col_control = st.columns([3, 1])

with col_control:
    st.markdown("##### ⚙️ Hybrid Ayarlar")
    hybrid_alpha = st.slider(
        "FTS Ağırlığı (α)",
        0.0, 1.0, 0.7, 0.1,
        help="0.0: Semantic, 1.0: Keyword"
    )
    min_quality = st.slider(
        "Min. Kalite Skoru",
        0.0, 1.0, 0.5, 0.1
    )
    top_k = st.slider(
        "Chunk Sayısı (Top-K)",
        5, 20, 10, 1
    )

with col_query:
    user_query = st.text_input(
        "Arama Sorgunuz:",
        value="military base conference room services için tipik gereksinimler"
    )
    search_button = st.button("🔍 Hybrid Arama Yap", type="primary", use_container_width=True)

if search_button and user_query:
    with st.spinner("Hybrid Search Motoru çalışıyor..."):
        try:
            rag_client = get_rag_client()
            response = rag_client.hybrid_search(
                query=user_query,
                alpha=hybrid_alpha,
                topk=top_k
            )
            
            if response.get('status') == 'error':
                st.error(f"❌ RAG API Hatası: {response.get('message', 'Bilinmeyen hata')}")
                st.info(f"💡 API URL: {RAG_API_URL}")
            else:
                results = response.get('results', [])
                total = response.get('total', len(results))
                
                st.success(f"✅ Bulunan {total} Alakalı Chunk")
                
                for idx, item in enumerate(results, 1):
                    chunk_source = item.get('chunk_source', item.get('chunk_type', 'UNKNOWN'))
                    source_icon = "📄" if chunk_source == 'DOCUMENT' else "📰"
                    
                    hybrid_score = item.get('hybrid_score', item.get('similarity', 0))
                    quality_score = item.get('text_quality_score', item.get('quality', 0))
                    
                    if quality_score < min_quality:
                        continue
                    
                    st.markdown(f"""
                    **[{idx}] {source_icon} Skor: {hybrid_score:.3f} | {item.get('title', item.get('opportunity_id', 'N/A'))}**
                    
                    ⭐ Kalite: {quality_score:.2f} | Tür: {chunk_source}
                    """)
                    
                    content = item.get('content', item.get('text', ''))[:500]
                    st.text(content + "..." if len(content) == 500 else content)
                    
                    with st.expander(f"📋 Metadata - Chunk {idx}"):
                        metadata_items = {
                            'Opportunity ID': item.get('opportunity_id', 'N/A'),
                            'Chunk Type': item.get('chunk_type', 'N/A'),
                            'Similarity Score': f"{hybrid_score:.4f}",
                            'Quality Score': f"{quality_score:.2f}",
                            'Content Length': len(item.get('content', item.get('text', '')))
                        }
                        st.json(metadata_items)
                    
                    st.markdown("---")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ RAG API Hatası: Servise Ulaşılamıyor. Kontrol Edin: {RAG_API_URL}")
            st.exception(e)
        except Exception as e:
            st.error(f"Beklenmeyen hata: {e}")
            st.exception(e)

# Example queries
st.markdown("---")
st.subheader("💡 Örnek Sorgular")

example_queries = [
    "conference room requirements for military base",
    "hotel lodging services compliance requirements",
    "AV equipment specifications for government events"
]

cols = st.columns(3)
for i, example in enumerate(example_queries):
    with cols[i % 3]:
        if st.button(f"📝 {example[:40]}...", key=f"example_{i}", use_container_width=True):
            st.session_state.rag_query = example
            st.rerun()

