#!/usr/bin/env python3
"""
Streamlit Pages - LLM Agent Chat
AutoGen-based chat interface
"""

import streamlit as st
import requests
import os

# Configuration
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8001")

@st.cache_resource
def get_rag_client():
    """Initialize RAG API client"""
    class RAGClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
        
        def generate_proposal(self, query: str, notice_id: str = None, alpha: float = 0.6, topk: int = 15):
            """Generate proposal"""
            try:
                endpoint = f"{self.base_url}/api/rag/generate_proposal"
                data = {
                    "query": query,
                    "notice_id": notice_id,
                    "hybrid_alpha": alpha,
                    "topk": topk
                }
                response = requests.post(endpoint, json=data, timeout=120)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e), "result": None}
    
    return RAGClient(RAG_API_URL)

st.title("🤖 AutoGen LLM Ajanı (Canlı Sohbet)")
st.markdown("### Teklif Taslağı Oluşturma ve Stratejik Destek")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Merhaba! Geçmiş 172K fırsat verisine dayanarak size nasıl yardımcı olabilirim?\n\nBen şunları yapabilirim:\n- 📋 Teklif taslağı oluşturma\n- 🔍 Geçmiş fırsatlarda arama\n- 📊 Stratejik analiz\n- ✅ Compliance kontrolü"
        }
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if prompt := st.chat_input("Teklif sorunuzu veya analiz isteğinizi girin..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("AutoGen Ajanları muhakeme ediyor... (Bu işlem birkaç dakika sürebilir)"):
            try:
                rag_client = get_rag_client()
                
                response = rag_client.generate_proposal(
                    query=prompt,
                    alpha=0.7,
                    topk=15
                )
                
                if response.get('status') == 'error':
                    assistant_response = f"Üzgünüm, bir hata oluştu: {response.get('message', 'Bilinmeyen hata')}\n\nLütfen RAG API'nin çalıştığından emin olun: {RAG_API_URL}"
                else:
                    result = response.get('result', response.get('proposal', ''))
                    sources = response.get('sources', [])
                    
                    if result:
                        assistant_response = f"{result}\n\n"
                    else:
                        assistant_response = "Elbette. Hibrit RAG motorumuz, en alakalı dokümanları inceleyerek yanıt oluşturuyor.\n\n"
                    
                    if sources:
                        assistant_response += "\n**Kaynaklar:**\n"
                        for i, source in enumerate(sources[:5], 1):
                            assistant_response += f"- [{i}] {source.get('title', 'N/A')} (Similarity: {source.get('similarity', 0):.3f})\n"
                
                st.write(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            except Exception as e:
                error_msg = f"Bir hata oluştu: {e}\n\nLütfen tekrar deneyin veya RAG API'yi kontrol edin."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Quick actions
st.markdown("---")
st.subheader("⚡ Hızlı Aksiyonlar")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Teklif Taslağı İste", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "Bir teklif taslağı oluştur. Conference room services için tipik gereksinimler nelerdir?"
        })
        st.rerun()

with col2:
    if st.button("🔍 Benzer Fırsatlar", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "Geçmiş başarılı tekliflerden benzer örnekler bul."
        })
        st.rerun()

with col3:
    if st.button("📊 Stratejik Analiz", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "Bu fırsat için rekabet analizi ve kazanma stratejisi öner."
        })
        st.rerun()

# Clear chat
if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Sohbet temizlendi. Size nasıl yardımcı olabilirim?"
        }
    ]
    st.rerun()

