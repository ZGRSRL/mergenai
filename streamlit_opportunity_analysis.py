#!/usr/bin/env python3
"""
Streamlit İlan Analizi Yönetim Paneli
Kritik workflow'u Streamlit üzerinden yönetmek için
"""

import os
import sys
import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

# Add current directory to path
sys.path.append('.')

# Page config
st.set_page_config(
    page_title="İlan Analizi - ZGR SAM",
    page_icon="📋",
    layout="wide"
)

# Title
st.title("📋 İlan Analizi Yönetim Paneli")
st.markdown("SAM.gov ilanlarını analiz edip RAG sistemine hazır hale getirin")

# Sidebar
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    use_llm = st.checkbox("LLM ile Gereksinim Çıkarımı", value=True)
    download_dir = st.text_input("Download Dizini", value="./downloads")
    
    st.markdown("---")
    st.info("""
    **Workflow Adımları:**
    1. Metadata çekme
    2. Doküman indirme
    3. Gereksinim çıkarımı
    4. SOW analizi
    5. Veritabanı kaydı
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 İlan Analizi",
    "📊 Analiz Sonuçları",
    "📁 Doküman Yönetimi",
    "🔗 RAG Entegrasyonu"
])

# TAB 1: İlan Analizi
with tab1:
    st.header("Yeni İlan Analizi")
    
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
                from analyze_opportunity_workflow import OpportunityAnalysisWorkflow
                
                # Workflow oluştur
                workflow = OpportunityAnalysisWorkflow(
                    download_dir=download_dir,
                    use_llm=use_llm
                )
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # İlerleme bilgisi
                status_text.info("Workflow başlatılıyor...")
                progress_bar.progress(10)
                
                # Workflow çalıştır
                result = workflow.run(notice_id)
                
                progress_bar.progress(100)
                status_text.empty()
                
                # Sonuçları göster
                if result.success:
                    st.success(f"✅ Analiz başarıyla tamamlandı!")
                    
                    # Sonuç özeti
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Metadata", "✅" if result.metadata else "❌")
                    with col2:
                        st.metric("Dosyalar", len(result.downloaded_files or []))
                    with col3:
                        st.metric("Gereksinimler", "✅" if result.extracted_requirements else "❌")
                    with col4:
                        st.metric("Analysis ID", result.analysis_id or "N/A")
                    
                    # Detaylı sonuçlar
                    with st.expander("📋 Detaylı Sonuçlar", expanded=True):
                        # Metadata
                        if result.metadata:
                            st.subheader("Metadata")
                            st.json(result.metadata)
                        
                        # Gereksinimler
                        if result.extracted_requirements:
                            st.subheader("Çıkarılan Gereksinimler")
                            st.json(result.extracted_requirements)
                        
                        # SOW Analizi
                        if result.sow_analysis:
                            st.subheader("SOW Analizi")
                            st.json(result.sow_analysis)
                        
                        # İndirilen Dosyalar
                        if result.downloaded_files:
                            st.subheader(f"İndirilen Dosyalar ({len(result.downloaded_files)})")
                            for i, file_path in enumerate(result.downloaded_files, 1):
                                st.write(f"{i}. {Path(file_path).name}")
                    
                    # Hatalar varsa göster
                    if result.errors:
                        st.warning("⚠️ Bazı hatalar oluştu:")
                        for error in result.errors:
                            st.error(error)
                    
                    # Sonuçları session state'e kaydet
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

# TAB 2: Analiz Sonuçları
with tab2:
    st.header("Kayıtlı Analiz Sonuçları")
    
    try:
        from sow_analysis_manager import SOWAnalysisManager
        
        sow_manager = SOWAnalysisManager()
        all_sow = sow_manager.get_all_active_sow()
        
        if all_sow:
            st.info(f"📊 Toplam {len(all_sow)} aktif analiz bulundu")
            
            # Tablo görünümü
            df_data = []
            for sow in all_sow[:20]:  # İlk 20
                sow_payload = sow.get('sow_payload', {}) or {}
                metadata = sow_payload.get('metadata', {}) or {}
                
                df_data.append({
                    'Notice ID': sow.get('notice_id', 'N/A'),
                    'Title': metadata.get('title', 'N/A')[:50],
                    'Agency': metadata.get('agency', 'N/A'),
                    'Created': sow.get('created_at', 'N/A'),
                    'Analysis ID': sow.get('analysis_id', 'N/A')
                })
            
            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # Detay görüntüleme
                selected_notice = st.selectbox(
                    "Detay görüntülemek için Notice ID seçin",
                    options=[sow.get('notice_id') for sow in all_sow]
                )
                
                if selected_notice:
                    selected_sow = next((s for s in all_sow if s.get('notice_id') == selected_notice), None)
                    if selected_sow:
                        st.subheader(f"Analiz Detayları: {selected_notice}")
                        st.json(selected_sow)
        else:
            st.info("Henüz analiz yapılmamış. İlan Analizi sekmesinden yeni analiz başlatın.")
    
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")

# TAB 3: Doküman Yönetimi
with tab3:
    st.header("İndirilen Dokümanlar")
    
    downloads_path = Path(download_dir)
    
    if downloads_path.exists():
        # Opportunity klasörlerini listele
        opp_dirs = [d for d in downloads_path.iterdir() if d.is_dir()]
        
        if opp_dirs:
            selected_opp = st.selectbox(
                "Opportunity seçin",
                options=[d.name for d in opp_dirs]
            )
            
            if selected_opp:
                opp_dir = downloads_path / selected_opp
                files = list(opp_dir.rglob('*'))
                files = [f for f in files if f.is_file()]
                
                st.info(f"📁 {selected_opp} için {len(files)} dosya bulundu")
                
                for i, file_path in enumerate(files[:10], 1):  # İlk 10
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 {file_path.name}")
                    with col2:
                        file_size = file_path.stat().st_size
                        st.write(f"{file_size / 1024:.1f} KB")
                    with col3:
                        if st.button("Görüntüle", key=f"view_{i}"):
                            st.info(f"Dosya yolu: {file_path}")
        else:
            st.info("Henüz doküman indirilmemiş.")
    else:
        st.warning(f"Download dizini bulunamadı: {downloads_path}")

# TAB 4: RAG Entegrasyonu
with tab4:
    st.header("RAG Sistemi Entegrasyonu")
    
    st.markdown("""
    ### 📚 RAG Sistemi Durumu
    
    İlan analizi tamamlandıktan sonra:
    1. **Semantic Search:** 172,402 chunk'tan benzer fırsatları bul
    2. **Best Practices:** Geçmiş tekliflerden öğren
    3. **Teklif Taslağı:** Analiz + RAG ile teklif oluştur
    """)
    
    notice_id_rag = st.text_input(
        "RAG Analizi için Notice ID",
        value="086008536ec84226ad9de043dc738d06"
    )
    
    if st.button("🔍 RAG ile Analiz Et"):
        with st.spinner("RAG semantic search yapılıyor..."):
            try:
                # RAG search test_final_rag.py'den
                sys.path.append('../Zgrprop')
                from test_final_rag import semantic_search
                
                # Metadata'dan query oluştur
                query = f"hotel lodging conference requirements {notice_id_rag}"
                
                relevant_chunks = semantic_search(query, limit=10)
                
                if relevant_chunks:
                    st.success(f"✅ {len(relevant_chunks)} ilgili chunk bulundu")
                    
                    # Top chunks göster
                    for i, chunk in enumerate(relevant_chunks[:5], 1):
                        with st.expander(f"[{i}] {chunk['chunk_type'].upper()} - Similarity: {chunk['similarity']:.3f}"):
                            st.write(f"**Opportunity ID:** {chunk['opportunity_id']}")
                            st.write(f"**Content:**")
                            st.text(chunk['content'][:500])
                else:
                    st.warning("İlgili chunk bulunamadı")
            
            except Exception as e:
                st.error(f"RAG analizi hatası: {e}")
    
    # Teklif oluşturma
    st.markdown("---")
    st.subheader("Teklif Taslağı Oluştur")
    
    if st.button("📝 Teklif Taslağı Oluştur"):
        st.info("Teklif oluşturma özelliği yakında eklenecek...")
        # Burada teklif_raporu_olustur.py entegre edilebilir

if __name__ == "__main__":
    # Streamlit otomatik çalıştırır
    pass

