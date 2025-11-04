#!/usr/bin/env python3
"""
Streamlit Pages - İlan Analizi
Live opportunity analysis workflow
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys

sys.path.append('.')

# Import workflow
try:
    from analyze_opportunity_workflow import OpportunityAnalysisWorkflow
except ImportError:
    st.error("analyze_opportunity_workflow.py bulunamadı")
    st.stop()

st.title("🔍 Canlı İlan Analizi")
st.markdown("### SAM.gov İlanlarını Analiz Et ve RAG Sistemine Hazırla")

# Settings
use_llm = st.sidebar.checkbox("LLM ile Gereksinim Çıkarımı", value=True)
download_dir = st.sidebar.text_input("Download Dizini", value="./downloads")

# Input
col1, col2 = st.columns([2, 1])

with col1:
    notice_id = st.text_input(
        "SAM.gov Notice ID",
        value="086008536ec84226ad9de043dc738d06",
        help="Örnek: 086008536ec84226ad9de043dc738d06"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🚀 İlanı Analiz Et", type="primary", use_container_width=True)

if analyze_button and notice_id:
    with st.spinner("İlan analizi yapılıyor... Bu işlem birkaç dakika sürebilir."):
        try:
            workflow = OpportunityAnalysisWorkflow(
                download_dir=download_dir,
                use_llm=use_llm
            )
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.info("Workflow başlatılıyor...")
            progress_bar.progress(10)
            
            result = workflow.run(notice_id)
            
            progress_bar.progress(100)
            status_text.empty()
            
            if result.success:
                st.success(f"✅ Analiz başarıyla tamamlandı!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Metadata", "✅" if result.metadata else "❌")
                with col2:
                    st.metric("Dosyalar", len(result.downloaded_files or []))
                with col3:
                    st.metric("Gereksinimler", "✅" if result.extracted_requirements else "❌")
                with col4:
                    st.metric("Analysis ID", result.analysis_id or "N/A")
                
                with st.expander("📋 Detaylı Sonuçlar", expanded=True):
                    if result.metadata:
                        st.subheader("Metadata")
                        st.json(result.metadata)
                    
                    if result.extracted_requirements:
                        st.subheader("Çıkarılan Gereksinimler")
                        st.json(result.extracted_requirements)
                    
                    if result.sow_analysis:
                        st.subheader("SOW Analizi")
                        st.json(result.sow_analysis)
                    
                    if result.downloaded_files:
                        st.subheader(f"İndirilen Dosyalar ({len(result.downloaded_files)})")
                        for i, file_path in enumerate(result.downloaded_files, 1):
                            st.write(f"{i}. {Path(file_path).name}")
                
                if result.errors:
                    st.warning("⚠️ Bazı hatalar oluştu:")
                    for error in result.errors:
                        st.error(error)
                
                st.session_state[f'analysis_{notice_id}'] = result
            else:
                st.error("❌ Analiz başarısız oldu")
                if result.errors:
                    for error in result.errors:
                        st.error(error)
        
        except Exception as e:
            st.error(f"Workflow hatası: {e}")
            import traceback
            st.code(traceback.format_exc())

# Stored Analyses
st.markdown("---")
st.subheader("📊 Kayıtlı Analiz Sonuçları")

try:
    from sow_analysis_manager import SOWAnalysisManager
    
    sow_manager = SOWAnalysisManager()
    all_sow = sow_manager.get_all_active_sow()
    
    if all_sow:
        st.info(f"📊 Toplam {len(all_sow)} aktif analiz bulundu")
        
        df_data = []
        for sow in all_sow[:20]:
            sow_payload = sow.get('sow_payload', {}) or {}
            metadata = sow_payload.get('metadata', {}) or {}
            
            df_data.append({
                'Notice ID': sow.get('notice_id', 'N/A'),
                'Title': str(metadata.get('title', 'N/A'))[:50],
                'Agency': str(metadata.get('agency', 'N/A')),
                'Created': str(sow.get('created_at', 'N/A'))[:19],
                'Analysis ID': sow.get('analysis_id', 'N/A')
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            selected_notice = st.selectbox(
                "Detay görüntülemek için Notice ID seçin",
                options=[sow.get('notice_id') for sow in all_sow[:20]]
            )
            
            if selected_notice:
                selected_sow = next((s for s in all_sow if s.get('notice_id') == selected_notice), None)
                if selected_sow:
                    with st.expander(f"📋 Analiz Detayları: {selected_notice}", expanded=True):
                        st.json(selected_sow)
    else:
        st.info("Henüz analiz yapılmamış. Yukarıdan yeni analiz başlatın.")

except Exception as e:
    st.warning(f"Veritabanı bağlantı hatası (opsiyonel): {e}")

