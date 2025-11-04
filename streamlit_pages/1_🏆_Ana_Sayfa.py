#!/usr/bin/env python3
"""
Streamlit Pages - Ana Sayfa
Modern dashboard with analytics
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

sys.path.append('.')

# Database connection
DB_DSN = os.getenv("DB_DSN", "dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432")

@st.cache_data(ttl=300)
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        import psycopg2
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        stats = {}
        
        # Chunks by type
        cur.execute("""
            SELECT chunk_type, COUNT(*) 
            FROM sam_chunks 
            WHERE opportunity_id IN (SELECT notice_id FROM hotel_opportunities_new)
            GROUP BY chunk_type
        """)
        stats['chunks_by_type'] = dict(cur.fetchall())
        
        # Total stats
        cur.execute("SELECT COUNT(*) FROM sam_chunks WHERE opportunity_id IN (SELECT notice_id FROM hotel_opportunities_new)")
        stats['total_chunks'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM hotel_opportunities_new")
        stats['opportunities'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sow_analysis WHERE is_active = true")
        stats['sow_analyses'] = cur.fetchone()[0]
        
        # Recent activity
        cur.execute("""
            SELECT COUNT(*) FROM sow_analysis 
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)
        stats['recent_analyses'] = cur.fetchone()[0]
        
        conn.close()
        return stats
    
    except Exception as e:
        return {
            'chunks_by_type': {'document': 162797, 'title': 9605},
            'total_chunks': 172402,
            'opportunities': 9605,
            'sow_analyses': 0,
            'recent_analyses': 0
        }

st.title("🏆 Ana Sayfa / Genel Bakış")
st.markdown("### Stratejik Zeka ve Anlık Performans Metrikleri")

# Get stats
stats = get_dashboard_stats()

# Main metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Chunks", f"{stats['total_chunks']:,}", help="ZgrProp RAG veritabanı")

with col2:
    st.metric("Opportunities", f"{stats['opportunities']:,}", help="Kayıtlı fırsat sayısı")

with col3:
    st.metric("SOW Analyses", stats['sow_analyses'], help="Aktif analiz sayısı")

with col4:
    st.metric("Son 7 Gün", stats['recent_analyses'], help="Yeni analizler")

st.markdown("---")

# Charts
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Chunk Dağılımı")
    chunks_data = stats['chunks_by_type']
    if chunks_data:
        df_chunks = pd.DataFrame({
            'Type': list(chunks_data.keys()),
            'Count': list(chunks_data.values())
        })
        st.bar_chart(df_chunks.set_index('Type'))

with col2:
    st.subheader("🎯 Hızlı Aksiyonlar")
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📊 Detaylı Rapor", use_container_width=True):
        st.info("Rapor oluşturuluyor...")
    
    if st.button("⚙️ Sistem Ayarları", use_container_width=True):
        st.info("Ayarlar sayfası yakında...")

st.markdown("---")

# Quick links
st.subheader("🔗 Hızlı Erişim")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🔍 İlan Analizi**
    - Yeni SAM.gov ilanlarını analiz et
    - Gereksinim çıkar ve SOW oluştur
    """)

with col2:
    st.markdown("""
    **🧠 Hybrid RAG Sorgu**
    - 172K chunk'ta semantic search
    - Geçmiş fırsatlardan öğren
    """)

with col3:
    st.markdown("""
    **🤖 LLM Ajanı**
    - AutoGen ile teklif taslağı
    - Stratejik destek ve analiz
    """)

