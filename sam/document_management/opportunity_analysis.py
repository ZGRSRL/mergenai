#!/usr/bin/env python3
"""
Fırsat Analiz Merkezi - Kapsamlı İlan Analiz Sayfası
Streamlit tabanlı, AutoGen destekli SAM.gov ilan analizi

Bu modül şunları yapar:
1. SAM API'den metadata çekme
2. Dokümanları indirme ve görüntüleme
3. AutoGen ile gereksinim çıkarımı ve SOW analizi
4. ZGR_AI veritabanına kaydetme
"""

import streamlit as st
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add paths
sys.path.append('.')
sys.path.append('..')
sys.path.append('../../')

# Imports
try:
    from sam_api_client import SAMAPIClient
    from analyze_opportunity_workflow import OpportunityAnalysisWorkflow, AnalysisWorkflowResult
    from sow_analysis_manager import SOWAnalysisManager
    SAM_AVAILABLE = True
except ImportError as e:
    SAM_AVAILABLE = False
    st.warning(f"⚠️ Bazı modüller import edilemedi: {e}")

# Page Configuration
st.set_page_config(
    page_title="Fırsat Analiz Merkezi - ZGR SAM/PROP",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .status-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    .document-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🎯 Fırsat Analiz Merkezi</div>', unsafe_allow_html=True)
st.markdown("### Canlı İlan Analizi ve Gereksinim Çıkarımı - AutoGen Destekli")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Analiz Ayarları")
    
    # LLM Configuration
    use_llm = st.checkbox("🤖 LLM ile Gereksinim Çıkarımı", value=True, help="AutoGen ajanları kullanılsın mı?")
    
    # LLM Provider Selection
    if use_llm:
        llm_provider = st.selectbox(
            "LLM Provider",
            ["OpenAI (GPT-4)", "Ollama (Local)", "Auto (Auto-detect)"],
            index=2,
            help="LLM sağlayıcısı seçin"
        )
    else:
        llm_provider = "None"
    
    # Download Directory
    download_dir = st.text_input(
        "📁 Download Dizini",
        value=os.getenv("DOWNLOAD_PATH", "./downloads"),
        help="Dokümanların indirileceği dizin"
    )
    
    st.markdown("---")
    
    # System Status
    st.subheader("📊 Sistem Durumu")
    
    # SAM API Status
    if SAM_AVAILABLE:
        st.success("✅ SAM API Client hazır")
    else:
        st.error("❌ SAM API Client yüklenemedi")
    
    # Database Status
    try:
        import psycopg2
        db_dsn = os.getenv("DB_DSN", "dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432")
        conn = psycopg2.connect(db_dsn)
        conn.close()
        st.success("✅ Database bağlantısı OK")
    except Exception as e:
        st.error(f"❌ Database: {str(e)[:50]}")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("🔗 Hızlı Erişim")
    
    if st.button("📋 Kayıtlı Analizler", use_container_width=True):
        st.session_state.show_saved = True
    
    if st.button("🔄 Sayfayı Yenile", use_container_width=True):
        st.rerun()

# Main Content Area

# Tab Structure
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Yeni İlan Analizi",
    "📄 Doküman Yönetimi",
    "📊 Analiz Sonuçları",
    "🤖 AutoGen Agent Logs"
])

# TAB 1: Yeni İlan Analizi
with tab1:
    st.subheader("SAM.gov İlan Analizi")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        notice_id = st.text_input(
            "SAM.gov Notice ID",
            value="086008536ec84226ad9de043dc738d06",
            help="Analiz edilecek ilanın Notice ID'si",
            key="notice_id_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🚀 İlanı Analiz Et", type="primary", use_container_width=True)
    
    if analyze_button and notice_id:
        if not SAM_AVAILABLE:
            st.error("❌ SAM API Client yüklenemedi. Lütfen gerekli modülleri kontrol edin.")
        else:
            # Initialize progress tracking
            progress_container = st.container()
            status_container = st.container()
            results_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # Initialize Workflow
                status_text.info("🔄 Workflow başlatılıyor...")
                progress_bar.progress(5)
                
                workflow = OpportunityAnalysisWorkflow(
                    download_dir=download_dir,
                    use_llm=use_llm
                )
                
                # Run Analysis
                status_text.info("📥 SAM.gov'dan metadata çekiliyor...")
                progress_bar.progress(10)
                
                result = workflow.run(notice_id)
                
                progress_bar.progress(100)
                status_text.empty()
                
                # Display Results
                with results_container:
                    if result.success:
                        st.markdown('<div class="status-success">✅ Analiz başarıyla tamamlandı!</div>', unsafe_allow_html=True)
                        
                        # Metrics Row
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("📋 Metadata", "✅" if result.metadata else "❌")
                        
                        with col2:
                            file_count = len(result.downloaded_files or [])
                            st.metric("📄 Dosyalar", file_count)
                        
                        with col3:
                            st.metric("🔍 Gereksinimler", "✅" if result.extracted_requirements else "❌")
                        
                        with col4:
                            st.metric("📊 SOW Analizi", "✅" if result.sow_analysis else "❌")
                        
                        with col5:
                            st.metric("💾 Analysis ID", result.analysis_id or "N/A")
                        
                        st.markdown("---")
                        
                        # Detailed Results in Expanders
                        details_col1, details_col2 = st.columns(2)
                        
                        with details_col1:
                            # Metadata
                            if result.metadata:
                                with st.expander("📋 Metadata Detayları", expanded=True):
                                    st.json(result.metadata)
                            
                            # Extracted Requirements
                            if result.extracted_requirements:
                                with st.expander("🔍 Çıkarılan Gereksinimler", expanded=True):
                                    st.json(result.extracted_requirements)
                            
                            # SOW Analysis
                            if result.sow_analysis:
                                with st.expander("📊 SOW Analizi", expanded=True):
                                    st.json(result.sow_analysis)
                        
                        with details_col2:
                            # Downloaded Files
                            if result.downloaded_files:
                                with st.expander(f"📄 İndirilen Dosyalar ({len(result.downloaded_files)})", expanded=True):
                                    for i, file_path in enumerate(result.downloaded_files, 1):
                                        file_path_obj = Path(file_path)
                                        if file_path_obj.exists():
                                            file_size = file_path_obj.stat().st_size
                                            st.markdown(f"""
                                            <div class="document-card">
                                                <strong>{i}. {file_path_obj.name}</strong><br>
                                                <small>Boyut: {file_size / 1024:.1f} KB</small><br>
                                                <small>Yol: {file_path}</small>
                                            </div>
                                            """, unsafe_allow_html=True)
                            
                            # Errors (if any)
                            if result.errors:
                                with st.expander("⚠️ Hatalar ve Uyarılar", expanded=True):
                                    for error in result.errors:
                                        st.error(error)
                        
                        # Save to session state
                        st.session_state[f'analysis_{notice_id}'] = result
                        st.session_state['last_analysis'] = result
                        
                        # Success notification
                        st.balloons()
                        
                    else:
                        st.markdown('<div class="status-error">❌ Analiz başarısız oldu</div>', unsafe_allow_html=True)
                        
                        if result.errors:
                            for error in result.errors:
                                st.error(f"❌ {error}")
            
            except Exception as e:
                status_text.empty()
                st.markdown('<div class="status-error">❌ Workflow hatası oluştu</div>', unsafe_allow_html=True)
                st.error(f"Hata: {e}")
                st.code(traceback.format_exc())

# TAB 2: Doküman Yönetimi
with tab2:
    st.subheader("📄 İndirilen Dokümanlar")
    
    # Select Opportunity
    download_path = Path(download_dir)
    
    if download_path.exists():
        # Get opportunity directories
        opp_dirs = [d for d in download_path.iterdir() if d.is_dir()]
        
        if opp_dirs:
            selected_opp = st.selectbox(
                "Opportunity seçin",
                options=[d.name for d in opp_dirs],
                key="doc_opp_select"
            )
            
            if selected_opp:
                opp_dir = download_path / selected_opp
                files = list(opp_dir.rglob('*'))
                files = [f for f in files if f.is_file()]
                
                st.info(f"📁 **{selected_opp}** için **{len(files)}** dosya bulundu")
                
                # File List
                st.markdown("---")
                st.subheader("📋 Dosya Listesi")
                
                for i, file_path in enumerate(files[:50], 1):  # İlk 50 dosya
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{i}. {file_path.name}**")
                    
                    with col2:
                        file_size = file_path.stat().st_size
                        st.write(f"{file_size / 1024:.1f} KB")
                    
                    with col3:
                        file_ext = file_path.suffix.upper()
                        st.write(file_ext if file_ext else "NO EXT")
                    
                    with col4:
                        if st.button("📄 Görüntüle", key=f"view_{i}"):
                            st.session_state[f'view_file_{i}'] = file_path
                
                # File Preview
                if any(k.startswith('view_file_') for k in st.session_state.keys()):
                    for key in st.session_state.keys():
                        if key.startswith('view_file_'):
                            file_to_view = st.session_state[key]
                            st.markdown("---")
                            st.subheader(f"📄 Dosya Önizleme: {file_to_view.name}")
                            
                            try:
                                # Text files
                                if file_to_view.suffix.lower() in ['.txt', '.md', '.json']:
                                    with open(file_to_view, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    st.text_area("İçerik", content, height=400)
                                
                                # PDF files (basic info)
                                elif file_to_view.suffix.lower() == '.pdf':
                                    st.info(f"PDF dosyası: {file_to_view.name}")
                                    st.write(f"Boyut: {file_to_view.stat().st_size / 1024:.1f} KB")
                                    st.write("PDF içeriği görüntülemek için external viewer kullanın.")
                                
                                # Other files
                                else:
                                    st.info(f"Dosya türü: {file_to_view.suffix}")
                                    st.write(f"Boyut: {file_to_view.stat().st_size / 1024:.1f} KB")
                            
                            except Exception as e:
                                st.error(f"Dosya okuma hatası: {e}")
        else:
            st.info("Henüz doküman indirilmemiş.")
    else:
        st.warning(f"Download dizini bulunamadı: {download_path}")

# TAB 3: Analiz Sonuçları
with tab3:
    st.subheader("📊 Kayıtlı Analiz Sonuçları")
    
    try:
        from sow_analysis_manager import SOWAnalysisManager
        
        sow_manager = SOWAnalysisManager()
        all_sow = sow_manager.get_all_active_sow()
        
        if all_sow:
            st.success(f"✅ **{len(all_sow)}** aktif analiz bulundu")
            
            # Table View
            st.markdown("---")
            st.subheader("📋 Analiz Listesi")
            
            df_data = []
            for sow in all_sow[:50]:  # İlk 50
                sow_payload = sow.get('sow_payload', {}) or {}
                metadata = sow_payload.get('metadata', {}) or {}
                
                df_data.append({
                    'Notice ID': sow.get('notice_id', 'N/A'),
                    'Title': str(metadata.get('title', 'N/A'))[:60],
                    'Agency': str(metadata.get('agency', 'N/A')),
                    'Created': str(sow.get('created_at', 'N/A'))[:19],
                    'Updated': str(sow.get('updated_at', 'N/A'))[:19],
                    'Analysis ID': sow.get('analysis_id', 'N/A')
                })
            
            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Detail View
                st.markdown("---")
                st.subheader("🔍 Detaylı Görüntüleme")
                
                selected_notice = st.selectbox(
                    "Detay görüntülemek için Notice ID seçin",
                    options=[sow.get('notice_id') for sow in all_sow[:50]],
                    key="sow_detail_select"
                )
                
                if selected_notice:
                    selected_sow = next((s for s in all_sow if s.get('notice_id') == selected_notice), None)
                    if selected_sow:
                        with st.expander(f"📋 Analiz Detayları: {selected_notice}", expanded=True):
                            st.json(selected_sow)
        else:
            st.info("Henüz analiz yapılmamış. 'Yeni İlan Analizi' sekmesinden analiz başlatın.")
    
    except Exception as e:
        st.warning(f"Veritabanı bağlantı hatası: {e}")

# TAB 4: AutoGen Agent Logs
with tab4:
    st.subheader("🤖 AutoGen Agent Logs")
    st.markdown("LLM ajanlarının çalışma logları ve muhakeme süreçleri")
    
    if 'last_analysis' in st.session_state:
        last_analysis = st.session_state['last_analysis']
        
        if last_analysis and last_analysis.success:
            st.success("✅ Son analiz logları mevcut")
            
            # Analysis Summary
            st.markdown("---")
            st.subheader("📊 Analiz Özeti")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Notice ID:** {last_analysis.notice_id}")
                st.write(f"**Timestamp:** {last_analysis.timestamp}")
                st.write(f"**Analysis ID:** {last_analysis.analysis_id or 'N/A'}")
            
            with col2:
                st.write(f"**Metadata:** {'✅' if last_analysis.metadata else '❌'}")
                st.write(f"**Dosyalar:** {len(last_analysis.downloaded_files or [])}")
                st.write(f"**Gereksinimler:** {'✅' if last_analysis.extracted_requirements else '❌'}")
                st.write(f"**SOW Analizi:** {'✅' if last_analysis.sow_analysis else '❌'}")
            
            # Agent Activity
            if last_analysis.extracted_requirements:
                st.markdown("---")
                st.subheader("🤖 AutoGen Agent Aktivitesi")
                
                requirements = last_analysis.extracted_requirements
                
                if requirements.get('room_requirements'):
                    st.write("**🏨 Oda Gereksinimleri:**")
                    st.json(requirements['room_requirements'])
                
                if requirements.get('conference_requirements'):
                    st.write("**📅 Konferans Gereksinimleri:**")
                    st.json(requirements['conference_requirements'])
                
                if requirements.get('av_requirements'):
                    st.write("**🎥 AV Gereksinimleri:**")
                    st.json(requirements['av_requirements'])
                
                if requirements.get('catering_requirements'):
                    st.write("**🍽️ Catering Gereksinimleri:**")
                    st.json(requirements['catering_requirements'])
        else:
            st.info("Son analiz bulunamadı veya başarısız oldu.")
    else:
        st.info("Henüz analiz yapılmamış. 'Yeni İlan Analizi' sekmesinden analiz başlatın.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>🎯 Fırsat Analiz Merkezi - ZGR SAM/PROP Platform</small><br>
    <small>Powered by AutoGen Multi-Agent System & Hybrid RAG (172K Chunks)</small>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    # Streamlit automatically runs this
    pass
