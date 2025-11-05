#!/usr/bin/env python3
"""
ZGR SAM/PROP - Streamlit Yönetim Paneli
Modern, analitik ve aksiyon odaklı tasarım
"""

import os
import json
import datetime as dt
from pathlib import Path
import streamlit as st
import sys
from dotenv import load_dotenv
import pandas as pd
import requests
from typing import Dict, Any, Optional, List
import time
import traceback

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append('.')
sys.path.append('./api')

# --- Configuration & Globals ---
# RAG API URL - Docker içinde rag_api:8000, host makinede localhost:8001
# Environment variable'dan al, ama Docker içi adres (rag_api:8000) ise localhost'a çevir
env_url = os.getenv("RAG_API_URL", "http://localhost:8001")
if "rag_api:8000" in env_url or ("rag_api" in env_url and "localhost" not in env_url):
    # Host makineden çalışıyoruz, localhost kullan
    RAG_API_URL = "http://localhost:8001"
else:
    RAG_API_URL = env_url

DB_DSN = os.getenv("DB_DSN", "dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432")

# --- Utility Functions for RAG/DB ---

@st.cache_data(ttl=300)
def get_platform_stats() -> Dict[str, Any]:
    """Platform istatistiklerini DB'den çeker - Her iki opportunities tablosunu da kontrol eder."""
    try:
        import psycopg2
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        stats = {}
        
        # Total chunks from sam_chunks - Her iki tablodan da opportunity_id'leri kontrol et
        try:
            # Önce hotel_opportunities_new'den chunks
            cur.execute("""
                SELECT COUNT(*) FROM sam_chunks 
                WHERE opportunity_id IN (
                    SELECT notice_id FROM hotel_opportunities_new
                    UNION
                    SELECT opportunity_id FROM opportunities WHERE opportunity_id IS NOT NULL
                )
            """)
            total_chunks = cur.fetchone()[0]
        except Exception:
            # Fallback: sadece hotel_opportunities_new
            try:
                cur.execute("SELECT COUNT(*) FROM sam_chunks WHERE opportunity_id IN (SELECT notice_id FROM hotel_opportunities_new)")
                total_chunks = cur.fetchone()[0]
            except Exception:
                total_chunks = 0
        
        # Opportunities count - Her iki tabloyu da say
        hotel_opp_count = 0
        sam_opp_count = 0
        
        try:
            cur.execute("SELECT COUNT(*) FROM hotel_opportunities_new")
            hotel_opp_count = cur.fetchone()[0]
        except Exception:
            pass
        
        try:
            cur.execute("SELECT COUNT(*) FROM opportunities")
            sam_opp_count = cur.fetchone()[0]
        except Exception:
            pass
        
        total_opportunities = hotel_opp_count + sam_opp_count
        
        # SOW analyses
        try:
            cur.execute("SELECT COUNT(*) FROM sow_analysis WHERE is_active = true")
            sow_analyses = cur.fetchone()[0]
        except Exception:
            sow_analyses = 0
        
        # Recent analyses
        try:
            cur.execute("""
                SELECT COUNT(*) FROM sow_analysis 
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)
            recent_analyses = cur.fetchone()[0]
        except Exception:
            recent_analyses = 0
        
        conn.close()
        return {
            'total_chunks': total_chunks,
            'opportunities': total_opportunities,
            'hotel_opportunities': hotel_opp_count,
            'sam_opportunities': sam_opp_count,
            'sow_analyses': sow_analyses,
            'recent_analyses': recent_analyses
        }
    except Exception as e:
        # DB bağlantısı başarısız olursa default istatistikleri göster
        return {
            'total_chunks': 172402,
            'opportunities': 9605,
            'hotel_opportunities': 9605,
            'sam_opportunities': 0,
            'sow_analyses': 0,
            'recent_analyses': 0
        }

@st.cache_data(ttl=3600)
def fetch_opportunity_title(notice_id: str) -> Optional[str]:
    """
    Notice ID'den başlığı getir - Veritabanı ve SAM API'den kontrol eder
    
    Args:
        notice_id: SAM.gov Notice ID
        
    Returns:
        Başlık string veya None
    """
    if not notice_id or not notice_id.strip():
        return None
    
    # ADIM 1: Veritabanından ara (hotel_opportunities_new)
    try:
        import psycopg2
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT title FROM hotel_opportunities_new 
                WHERE notice_id = %s
                LIMIT 1
            """, (notice_id,))
            result = cur.fetchone()
            if result and result[0]:
                conn.close()
                return result[0]
        except Exception:
            pass
        
        # ADIM 2: Veritabanından ara (opportunities)
        try:
            cur.execute("""
                SELECT title FROM opportunities 
                WHERE opportunity_id = %s
                LIMIT 1
            """, (notice_id,))
            result = cur.fetchone()
            if result and result[0]:
                conn.close()
                return result[0]
        except Exception:
            pass
        
        conn.close()
    except Exception:
        pass
    
    # ADIM 3: SAM API'den çek (fallback) - Yeni ilanlar için
    try:
        from sam_api_client import SAMAPIClient
        
        # API key'i doğru şekilde al
        api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
        if api_key:
            sam_client = SAMAPIClient(public_api_key=api_key, mode="public")
        else:
            sam_client = SAMAPIClient(mode="auto")
        
        # Önce direkt Notice ID ile dene
        opportunity = sam_client.get_opportunity_details(notice_id)
        
        # Eğer bulunamazsa ve Notice ID kısa format (örn: W50S6U26QA010) ise,
        # UUID formatına çevirmeyi deneyebiliriz, ama şimdilik sadece direkt aramayı yapıyoruz
        if not opportunity and len(notice_id) < 32:
            # Kısa format Notice ID - API'den geniş arama yap
            try:
                from datetime import datetime, timedelta
                today = datetime.now()
                posted_from = (today - timedelta(days=30)).strftime('%m/%d/%Y')
                posted_to = today.strftime('%m/%d/%Y')
                
                result = sam_client.search_opportunities(
                    posted_from=posted_from,
                    posted_to=posted_to,
                    limit=500
                )
                
                opportunities = result.get('opportunitiesData', [])
                for opp in opportunities:
                    opp_notice_id = str(opp.get('noticeId', '') or '')
                    opp_solicitation = str(opp.get('solicitationNumber', '') or '')
                    
                    if notice_id in opp_notice_id or notice_id in opp_solicitation:
                        opportunity = opp
                        break
            except Exception:
                pass
        
        if opportunity:
            # API response farklı formatlarda gelebilir
            title = opportunity.get('title') or opportunity.get('Title') or opportunity.get('opportunityTitle')
            if title:
                return title
    except Exception as e:
        # API hatası sessizce geçilir, kullanıcıya bilgi mesajı gösterilir
        pass
    
    return None

@st.cache_data(ttl=3600)  # 1 saat cache
def fetch_daily_opportunities():
    """SAM API'den bugün yayınlanan ilanları çek - Sadece Hotel sektörü (NAICS 721110)"""
    try:
        from sam_api_client import SAMAPIClient
        from datetime import datetime
        
        # API key'i al
        api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
        if not api_key:
            return {'error': 'SAM_API_KEY bulunamadı', 'opportunities': []}
        
        # Bugünün tarihi
        today = datetime.now()
        posted_from = today.strftime('%m/%d/%Y')
        posted_to = today.strftime('%m/%d/%Y')
        
        # SAM API client
        sam_client = SAMAPIClient(public_api_key=api_key, mode="public")
        
        # Bugünkü ilanları çek - Hotel sektörü için NAICS 721110 filtrele
        result = sam_client.search_opportunities(
            posted_from=posted_from,
            posted_to=posted_to,
            limit=100,  # Daha fazla çek, sonra filtrele
            naicsCode='721110'  # Hotels (except casino hotels) and motels
        )
        
        opportunities = result.get('opportunitiesData', [])
        
        # Ek filtreleme: NAICS 721110 içerenleri kontrol et (API bazen tam eşleşme yapmıyor)
        hotel_opportunities = []
        for opp in opportunities:
            naics_code = str(opp.get('naicsCode', '') or '')
            # NAICS 721110 ile ilgili olanları al (tam eşleşme veya içeriyor mu kontrol et)
            if '721110' in naics_code or naics_code == '721110':
                hotel_opportunities.append(opp)
        
        return {
            'success': True,
            'opportunities': hotel_opportunities,
            'count': len(hotel_opportunities),
            'date': today.strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'opportunities': [],
            'count': 0
        }

@st.cache_resource
def get_rag_client():
    """RAG API Client (FastAPI) başlatır."""
    class RAGClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
            
        def hybrid_search(self, query: str, alpha: float = 0.6, topk: int = 10):
            """Hibrit arama endpoint'ini çağırır."""
            endpoint = f"{self.base_url}/api/rag/hybrid_search"
            try:
                # POST method as per API definition
                response = requests.post(endpoint, params={"query": query, "alpha": alpha, "topk": topk}, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"status": "error", "message": f"Hybrid Search API hatası: {e}", "results": []}
        
        def generate_proposal(self, query: str, notice_id: Optional[str] = None, hybrid_alpha: float = 0.7, topk: int = 20):
            """Teklif oluşturma endpoint'ini çağırır."""
            endpoint = f"{self.base_url}/api/rag/generate_proposal"
            # API accepts: query, notice_id, hybrid_alpha, topk (target_agency is not in API)
            data = {
                "query": query,
                "notice_id": notice_id,
                "hybrid_alpha": hybrid_alpha,
                "topk": topk
            }
            try:
                response = requests.post(endpoint, json=data, timeout=180)  # Uzun LLM süresi için 180s
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"status": "error", "message": f"Proposal API hatası: {e}"}
                
    return RAGClient(RAG_API_URL)

def jdump(x): 
    """JSON dump with proper encoding"""
    return json.dumps(x, ensure_ascii=False, indent=2)

# --- Page Configuration ---
st.set_page_config(
    page_title="ZGR SAM/PROP - Yönetim Paneli",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (Keep the user's modern styling)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .result-box {
        background-color: #f7f7f7;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("🏆 ZGR SAM/PROP")
    st.caption("Hybrid RAG Intelligence Platform")
    
    # Load Stats into sidebar
    stats = get_platform_stats()
    
    st.metric("Total Chunks", f"{stats['total_chunks']:,}")
    st.metric("Opportunities", f"{stats['opportunities']:,}")
    
    # Show breakdown if available
    if stats.get('hotel_opportunities', 0) > 0 or stats.get('sam_opportunities', 0) > 0:
        with st.expander("📊 Detay"):
            st.write(f"Hotel: {stats.get('hotel_opportunities', 0):,}")
            st.write(f"SAM: {stats.get('sam_opportunities', 0):,}")
    
    st.metric("SOW Analyses", stats['sow_analyses'])
    st.metric("Son 7 Gün", stats['recent_analyses'])
    
    st.markdown("---")

    menu = st.radio(
        "Menü Seçin",
        [
            "🏆 Ana Sayfa",
            "🔍 İlan Analizi",
            "📊 SOW Analizi (LLM Teklif)",
            "🧠 Hybrid RAG Sorgu",
            "🤖 LLM Ajanı (Chat)",
            "📁 Dosya Yönetimi",
            "🔗 SAM API Test",
            "⚙️ Ayarlar"
        ],
        index=0
    )
    st.caption("Optimized • 172K Chunks")

# Helper function to get database connection
def get_db_connection_for_page():
    try:
        import psycopg2
        return psycopg2.connect(DB_DSN)
    except Exception as e:
        st.error(f"Database bağlantı hatası: {e}")
        return None

# --- MAIN CONTENT AREA ---

# 1. Ana Sayfa
if menu == "🏆 Ana Sayfa":
    st.markdown('<div class="main-header">🏆 Ana Sayfa / Genel Bakış</div>', unsafe_allow_html=True)
    st.markdown("### Stratejik Zeka ve Anlık Performans Metrikleri")
    
    # Stats Grid
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
    
    # Recent Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Platform Durumu")
        
        # Chunk distribution - Her iki tabloyu da kontrol et
        try:
            import psycopg2
            conn = psycopg2.connect(DB_DSN)
            cur = conn.cursor()
            
            # Try with both tables (UNION)
            try:
                cur.execute("""
                    SELECT chunk_type, COUNT(*) 
                    FROM sam_chunks 
                    WHERE opportunity_id IN (
                        SELECT notice_id FROM hotel_opportunities_new
                        UNION
                        SELECT opportunity_id FROM opportunities WHERE opportunity_id IS NOT NULL
                    )
                    GROUP BY chunk_type
                """)
            except Exception:
                # Fallback 1: only hotel_opportunities_new
                try:
                    cur.execute("""
                        SELECT chunk_type, COUNT(*) 
                        FROM sam_chunks 
                        WHERE opportunity_id IN (SELECT notice_id FROM hotel_opportunities_new)
                        GROUP BY chunk_type
                    """)
                except Exception:
                    # Fallback 2: all chunks (no filter)
                    cur.execute("""
                        SELECT chunk_type, COUNT(*) 
                        FROM sam_chunks 
                        GROUP BY chunk_type
                    """)
            
            chunks_data = dict(cur.fetchall())
            conn.close()
            
            if chunks_data:
                df_chunks = pd.DataFrame({
                    'Type': list(chunks_data.keys()),
                    'Count': list(chunks_data.values())
                })
                st.bar_chart(df_chunks.set_index('Type'))
        except Exception as e:
            st.info(f"Grafik verisi yüklenemedi: {str(e)[:50]}")
    
    with col2:
        st.subheader("🎯 Hızlı Aksiyonlar")
        
        if st.button("🔄 Verileri Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📊 Detaylı Rapor", use_container_width=True):
            st.info("Rapor oluşturuluyor...")
        
        if st.button("⚙️ Sistem Ayarları", use_container_width=True):
            st.info("Ayarlar sayfasına gidin")
    
    st.markdown("---")
    
    # Quick Links
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
    
    st.markdown("---")
    
    # Günlük İlanlar Akışı
    st.subheader("📰 Günlük İlanlar Akışı")
    st.caption("Bugün SAM.gov'da yayınlanan yeni ilanlar - Sadece Hotel Sektörü (NAICS 721110)")
    
    # Günlük ilanları getir
    with st.spinner("Günlük ilanlar yükleniyor..."):
        daily_data = fetch_daily_opportunities()
    
    if daily_data.get('success'):
        opportunities = daily_data.get('opportunities', [])
        count = daily_data.get('count', 0)
        
        if count > 0:
            st.success(f"✅ Bugün **{count}** yeni ilan bulundu ({daily_data.get('date', 'N/A')})")
            
            # Filtreleme seçenekleri
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                filter_keyword = st.text_input("🔍 Anahtar Kelime Filtre", "", key="daily_filter_keyword")
            
            with col_filter2:
                filter_agency = st.text_input("🏛️ Kurum Filtre", "", key="daily_filter_agency")
            
            with col_filter3:
                filter_naics = st.text_input("📊 NAICS Filtre", "", key="daily_filter_naics")
            
            # Filtreleme
            filtered_opps = opportunities
            if filter_keyword:
                filtered_opps = [opp for opp in filtered_opps if filter_keyword.lower() in str(opp.get('title', '')).lower() or filter_keyword.lower() in str(opp.get('description', '')).lower()]
            if filter_agency:
                filtered_opps = [opp for opp in filtered_opps if filter_agency.lower() in str(opp.get('department', '')).lower() or filter_agency.lower() in str(opp.get('fullParentPathName', '')).lower()]
            if filter_naics:
                filtered_opps = [opp for opp in filtered_opps if filter_naics in str(opp.get('naicsCode', ''))]
            
            st.info(f"📋 Filtrelenmiş sonuç: **{len(filtered_opps)}** ilan")
            
            # İlanları akış formatında göster
            for idx, opp in enumerate(filtered_opps[:20], 1):  # İlk 20 ilan
                notice_id = opp.get('noticeId', opp.get('notice_id', 'N/A'))
                title = opp.get('title', 'Başlık Yok')
                agency = opp.get('department', opp.get('fullParentPathName', 'N/A'))
                posted_date = opp.get('postedDate', opp.get('posted_date', 'N/A'))
                naics_code = opp.get('naicsCode', opp.get('naics_code', 'N/A'))
                description = opp.get('description', '')[:200] + "..." if len(str(opp.get('description', ''))) > 200 else opp.get('description', '')
                
                # İlan kartı
                st.markdown("---")  # Border yerine separator
                with st.container():
                    col_left, col_right = st.columns([4, 1])
                    
                    with col_left:
                        st.markdown(f"### [{idx}] {title}")
                        st.caption(f"📅 {posted_date} | 🏛️ {agency} | 📊 NAICS: {naics_code}")
                        
                        if description:
                            st.write(description)
                        
                        # Butonlar
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        with col_btn1:
                            if st.button("🔍 Analiz Et", key=f"analyze_daily_{notice_id}_{idx}", use_container_width=True):
                                st.session_state["selected_notice"] = notice_id
                                st.session_state[f'title_{notice_id}'] = title
                                st.success(f"✅ {notice_id} seçildi - İlan Analizi sekmesine geçin")
                        
                        with col_btn2:
                            sam_url = f"https://sam.gov/workspace/contract/opp/{notice_id}/view"
                            st.markdown(f'<a href="{sam_url}" target="_blank"><button style="width:100%">🌐 SAM.gov\'da Aç</button></a>', unsafe_allow_html=True)
                        
                        with col_btn3:
                            if st.button("📋 Detay", key=f"detail_daily_{notice_id}_{idx}", use_container_width=True):
                                st.session_state[f"show_detail_{notice_id}"] = not st.session_state.get(f"show_detail_{notice_id}", False)
                    
                    with col_right:
                        st.markdown(f"**Notice ID:**")
                        st.code(notice_id[:20] + "..." if len(notice_id) > 20 else notice_id, language=None)
                        
                        # Hızlı metrikler
                        if opp.get('responseDeadLine'):
                            st.caption(f"⏰ Son Tarih: {opp.get('responseDeadLine')}")
                    
                    # Detay gösterimi
                    if st.session_state.get(f"show_detail_{notice_id}", False):
                        with st.expander(f"📋 Tam Detay: {notice_id}", expanded=True):
                            st.json(opp)
            
            if len(filtered_opps) > 20:
                st.info(f"💡 Toplam {len(filtered_opps)} ilan bulundu. İlk 20 ilan gösteriliyor.")
            
            # Yenile butonu
            if st.button("🔄 Günlük İlanları Yenile", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        else:
            st.info("ℹ️ Bugün henüz yeni ilan yayınlanmamış veya filtre kriterlerinize uygun ilan bulunamadı.")
            if st.button("🔄 Tekrar Dene", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
    
    else:
        error_msg = daily_data.get('error', 'Bilinmeyen hata')
        st.warning(f"⚠️ Günlük ilanlar yüklenemedi: {error_msg}")
        
        if "SAM_API_KEY" in error_msg or "API" in error_msg:
            st.info("💡 Lütfen .env dosyasında SAM_API_KEY veya SAM_PUBLIC_API_KEY'in doğru ayarlandığından emin olun.")
        
        if st.button("🔄 Tekrar Dene", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# 2. İlan Analizi
elif menu == "🔍 İlan Analizi":
    st.markdown('<div class="main-header">🔍 Canlı İlan Analizi</div>', unsafe_allow_html=True)
    st.markdown("### SAM.gov İlanlarını Analiz Et ve RAG Sistemine Hazırla")
    
    # Notice ID Search Section
    st.markdown("### 🔍 Notice ID / Solicitation Number Arama")
    
    search_tab1, search_tab2 = st.tabs(["📝 Direkt Giriş", "🔎 API Arama"])
    
    with search_tab1:
        # Direct input
        col1, col2 = st.columns([2, 1])
        
        with col1:
            notice_id = st.text_input(
                "SAM.gov Notice ID veya Solicitation Number",
                value=st.session_state.get("selected_notice", "086008536ec84226ad9de043dc738d06"),
                help="UUID format: 086008536ec84226ad9de043738d06 veya Public format: W50S6U26QA010",
                key="notice_id_input"
            )
            
            # Başlığı getir ve göster
            if notice_id and notice_id.strip():
                opportunity_title = fetch_opportunity_title(notice_id)
                if opportunity_title:
                    st.markdown(f"**📋 İlan Başlığı:** {opportunity_title}")
                    st.session_state[f'title_{notice_id}'] = opportunity_title
                else:
                    st.info("ℹ️ Başlık bulunamadı - Veritabanında ve SAM API'de arama yapıldı. Bu yeni bir ilan olabilir veya API erişimi sınırlı olabilir.")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_button = st.button("🚀 İlanı Analiz Et", type="primary", use_container_width=True)
    
    with search_tab2:
        # API Search
        st.markdown("**SAM.gov API ile Geniş Arama**")
        
        col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
        
        with col_search1:
            search_term = st.text_input(
                "Arama Terimi (Notice ID, Solicitation Number, veya Anahtar Kelime)",
                placeholder="W50S6U26QA010 veya hotel services",
                key="api_search_term"
            )
        
        with col_search2:
            search_days = st.number_input("Son N Gün", min_value=1, max_value=365, value=30, key="search_days")
        
        with col_search3:
            st.markdown("<br>", unsafe_allow_html=True)
            search_button = st.button("🔍 Ara", type="primary", use_container_width=True)
        
        if search_button and search_term:
            with st.spinner("SAM.gov API'de aranıyor..."):
                try:
                    from sam_api_client import SAMAPIClient
                    from datetime import datetime, timedelta
                    
                    api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
                    sam_client = SAMAPIClient(public_api_key=api_key, mode="public")
                    
                    today = datetime.now()
                    posted_from = (today - timedelta(days=search_days)).strftime('%m/%d/%Y')
                    posted_to = today.strftime('%m/%d/%Y')
                    
                    # OPTIMIZE: Manuel arama için küçük limit
                    result = sam_client.search_opportunities(
                        posted_from=posted_from,
                        posted_to=posted_to,
                        limit=50,  # 100'den 50'ye düşürüldü
                        naicsCode='721110'
                    )
                    
                    opportunities = result.get('opportunitiesData', [])
                    
                    # Filter by search term
                    filtered_opps = []
                    search_lower = search_term.lower()
                    for opp in opportunities:
                        title = str(opp.get('title', '')).lower()
                        notice_id_val = str(opp.get('noticeId', '')).lower()
                        solicitation = str(opp.get('solicitationNumber', '')).lower()
                        description = str(opp.get('description', '')).lower()
                        
                        if (search_lower in title or 
                            search_lower in notice_id_val or 
                            search_lower in solicitation or
                            search_lower in description):
                            filtered_opps.append(opp)
                    
                    if filtered_opps:
                        st.success(f"✅ {len(filtered_opps)} fırsat bulundu")
                        
                        for idx, opp in enumerate(filtered_opps[:20], 1):
                            opp_notice_id = opp.get('noticeId', 'N/A')
                            opp_title = opp.get('title', 'N/A')
                            opp_date = opp.get('postedDate', 'N/A')
                            
                            with st.expander(f"[{idx}] {opp_title[:60]}...", expanded=False):
                                col_opp1, col_opp2 = st.columns([3, 1])
                                
                                with col_opp1:
                                    st.markdown(f"**Notice ID:** `{opp_notice_id}`")
                                    st.markdown(f"**Posted Date:** {opp_date}")
                                    st.markdown(f"**NAICS:** {opp.get('naicsCode', 'N/A')}")
                                    st.markdown(f"**Agency:** {opp.get('department', 'N/A')}")
                                
                                with col_opp2:
                                    if st.button("📋 Seç ve Analiz Et", key=f"select_opp_{idx}", use_container_width=True):
                                        st.session_state["selected_notice"] = opp_notice_id
                                        st.session_state[f'title_{opp_notice_id}'] = opp_title
                                        st.success(f"✅ {opp_notice_id} seçildi! Yukarıdaki 'Direkt Giriş' sekmesine geçin.")
                                        st.rerun()
                    else:
                        st.warning(f"⚠️ '{search_term}' için sonuç bulunamadı.")
                        st.info("💡 İpucu: Notice ID (UUID veya Public format), Solicitation Number veya anahtar kelime ile arayabilirsiniz.")
                
                except Exception as e:
                    st.error(f"❌ Arama hatası: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Settings
    with st.expander("⚙️ Ayarlar"):
        use_llm = st.checkbox("LLM ile Gereksinim Çıkarımı", value=True)
        download_dir = st.text_input("Download Dizini", value="./downloads")
    
    # Get notice_id from session state or input (for workflow execution)
    notice_id_for_analysis = st.session_state.get("selected_notice") or st.session_state.get("notice_id_input", "")
    
    if analyze_button and notice_id:
        with st.spinner("İlan analizi yapılıyor... Bu işlem birkaç dakika sürebilir."):
            try:
                from analyze_opportunity_workflow import OpportunityAnalysisWorkflow
                
                workflow = OpportunityAnalysisWorkflow(
                    download_dir=download_dir,
                    use_llm=use_llm
                )
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.info("Workflow başlatılıyor...")
                progress_bar.progress(10)
                
                # Use the notice_id from the input field
                result = workflow.run(notice_id.strip())
                
                progress_bar.progress(100)
                status_text.empty()
                
                if result.success:
                    # Başlık gösterimi (varsa)
                    if notice_id and f'title_{notice_id}' in st.session_state:
                        st.markdown(f"### 📋 {st.session_state[f'title_{notice_id}']}")
                    
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
                st.code(traceback.format_exc())
    
    # Stored Analyses
    st.markdown("---")
    st.subheader("📊 Kayıtlı Analiz Sonuçları")
    
    try:
        # Safe import with fallback
        try:
            from sow_analysis_manager import SOWAnalysisManager
            SOW_MANAGER_AVAILABLE = True
        except ImportError as import_err:
            st.warning(f"⚠️ sow_analysis_manager import edilemedi: {import_err}")
            SOW_MANAGER_AVAILABLE = False
            SOWAnalysisManager = None
        
        if SOW_MANAGER_AVAILABLE and SOWAnalysisManager:
            sow_manager = SOWAnalysisManager()
            all_sow = sow_manager.get_all_active_sow()
        else:
            all_sow = []
        
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

# 3. SOW Analizi (LLM Teklif)
elif menu == "📊 SOW Analizi (LLM Teklif)":
    st.header("📊 SOW Analizi ve Teklif Oluşturma")
    st.subheader("🤖 AutoGen ile Geçmiş Verilere Dayalı Teklif Taslağı")
    
    rag_client = get_rag_client()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📋 Teklif Parametreleri")
        rag_notice_id = st.text_input("Hedef Notice ID", value="086008536ec84226ad9de043dc738d06", key="rag_notice_id")
        
        # Başlığı getir ve göster
        if rag_notice_id and rag_notice_id.strip():
            opportunity_title = fetch_opportunity_title(rag_notice_id)
            if opportunity_title:
                st.markdown(f"**📋 İlan Başlığı:** {opportunity_title}")
                st.session_state[f'title_{rag_notice_id}'] = opportunity_title
            else:
                st.info("ℹ️ Başlık bulunamadı - Veritabanında ve SAM API'de arama yapıldı. Bu yeni bir ilan olabilir veya API erişimi sınırlı olabilir.")
        
        rag_query = st.text_area(
            "Soru/Talimat (LLM'e Gidecek)",
            value="Bu fırsat için ana teknik gereksinimler nelerdir ve geçmiş benzer fırsatlardan öğrenilen başarı faktörleri nelerdir? Profesyonel bir teklif taslağı formatında yaz.",
            height=120,
            key="rag_query_area"
        )
        
        hybrid_alpha = st.slider("RAG Ağırlığı", 0.0, 1.0, 0.7, 0.1, key="prop_alpha_main")
        
        if st.button("🚀 RAG ile Teklif Oluştur", type="primary", use_container_width=True):
            if rag_query:
                with st.spinner("AutoGen Ajanları RAG verisini kullanarak teklif taslağı oluşturuyor... (Bu işlem 2-3 dakika sürebilir)"):
                    result = rag_client.generate_proposal(
                        query=rag_query,
                        notice_id=rag_notice_id if rag_notice_id else None,
                        hybrid_alpha=hybrid_alpha,
                        topk=20
                    )
                    
                    if result.get("status") == "success":
                        # Başlık gösterimi (varsa)
                        if rag_notice_id and f'title_{rag_notice_id}' in st.session_state:
                            st.markdown(f"### 📋 {st.session_state[f'title_{rag_notice_id}']}")
                        
                        proposal_data = result.get('result', {})
                        st.session_state.proposal_draft = proposal_data.get('proposal_draft', '')
                        st.session_state.proposal_sources = result.get('sources', [])
                        st.success("✅ Teklif başarıyla oluşturuldu!")
                    else:
                        error_msg = result.get('message', 'API\'den beklenmeyen hata')
                        st.session_state.proposal_draft = f"❌ Hata: {error_msg}"
                        st.error(st.session_state.proposal_draft)
            else:
                st.warning("⚠️ Lütfen bir soru/talimat girin.")

    with col2:
        st.info("""
        **ZGRPROP Hotel Intelligence Köprüsü**

        Bu modül, 172K chunk'lık geçmiş veriyi (ZgrProp) kullanır ve sonuçları LLM (AutoGen) aracılığıyla yapılandırılmış bir teklif taslağına dönüştürür.
        
        - **Hedef:** Belirli bir Opportunity ID için geçmiş Best Practices'i uygulamak.
        """)
        
        # Display Proposal Draft
        if 'proposal_draft' in st.session_state and st.session_state.proposal_draft:
            st.subheader("📄 Oluşturulan Teklif Taslağı")
            st.text_area(
                "Teklif İçeriği",
                value=st.session_state.proposal_draft,
                height=400,
                key="proposal_draft_view"
            )
            
            if 'proposal_sources' in st.session_state and st.session_state.proposal_sources:
                st.subheader(f"📚 Kaynaklar ({len(st.session_state.proposal_sources)} adet)")
                sources_df = pd.DataFrame(st.session_state.proposal_sources)
                if not sources_df.empty:
                    st.dataframe(sources_df.head(5), hide_index=True)

# 4. Hybrid RAG Query
elif menu == "🧠 Hybrid RAG Sorgu":
    st.markdown('<div class="main-header">🧠 Hybrid RAG Sorgu Motoru</div>', unsafe_allow_html=True)
    st.markdown("### 172,402 Geçmiş Fırsat Üzerinde En Derin Aramayı Yapın")
    
    rag_client = get_rag_client()
    
    col_query, col_control = st.columns([3, 1])
    
    with col_control:
        st.markdown("##### ⚙️ Hybrid Ayarlar")
        hybrid_alpha = st.slider("FTS Ağırlığı (α)", 0.0, 1.0, 0.7, 0.1, help="0.0: Semantic, 1.0: Keyword", key="rag_alpha")
        top_k = st.slider("Chunk Sayısı (Top-K)", 5, 20, 10, 1, key="rag_topk")
        
    with col_query:
        # Initialize example query selector if not exists
        if 'selected_example_query' not in st.session_state:
            st.session_state.selected_example_query = None
        
        # Use selected example query if available, otherwise use default
        # This is set before widget creation, so it works
        if st.session_state.selected_example_query:
            default_query = st.session_state.selected_example_query
            # Clear it after using so next time it uses the default
            st.session_state.selected_example_query = None
        else:
            default_query = "military base conference room services için tipik gereksinimler"
        
        user_query = st.text_input(
            "Arama Sorgunuz:",
            value=default_query,
            key="rag_query"
        )
        
        search_button = st.button("🔍 Hybrid Arama Yap", type="primary", use_container_width=True)
    
    if search_button and user_query:
        with st.spinner("Hybrid Search Motoru çalışıyor..."):
            response = rag_client.hybrid_search(query=user_query, alpha=hybrid_alpha, topk=top_k)
            
            if response.get('status') == 'error':
                st.error(f"❌ RAG API Hatası: {response.get('message', 'Bilinmeyen hata')}")
                st.info(f"💡 API URL: {RAG_API_URL}")
            else:
                results = response.get('results', [])
                total = response.get('total', len(results))
                
                st.success(f"✅ Bulunan {total} Alakalı Chunk")
                
                for idx, item in enumerate(results, 1):
                    chunk_source = item.get('chunk_source', item.get('chunk_type', 'UNKNOWN'))
                    hybrid_score = item.get('hybrid_score', item.get('similarity', 0))
                    
                    with st.expander(f"[{idx}] Skor: {hybrid_score:.3f} | {item.get('title', item.get('opportunity_id', 'N/A'))}"):
                        st.markdown(f"**Kaynak:** {'📄 DOKÜMAN' if chunk_source == 'DOCUMENT' else '📰 SAM ÖZETİ'}")
                        content = item.get('content', item.get('text', 'İçerik yüklenemedi.'))
                        st.text(content[:800] + "..." if len(content) > 800 else content)
                        st.caption(f"Opportunity ID: {item.get('opportunity_id', 'N/A')}")
                        
                        # Metadata
                        metadata_items = {
                            'Similarity Score': f"{hybrid_score:.4f}",
                            'Chunk Type': chunk_source,
                            'Content Length': len(content)
                        }
                        st.json(metadata_items)
    
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
                # Use a different approach: directly set the query in a way that works
                # We'll use a query parameter or just update the input field by rerunning
                st.session_state.selected_example_query = example
                st.rerun()

# 5. LLM Agent Chat
elif menu == "🤖 LLM Ajanı (Chat)":
    st.markdown('<div class="main-header">🤖 AutoGen LLM Ajanı (Canlı Sohbet)</div>', unsafe_allow_html=True)
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
                        result = response.get('result', {})
                        proposal_draft = result.get('proposal_draft', '')
                        sources = response.get('sources', [])
                        
                        if proposal_draft:
                            assistant_response = f"{proposal_draft}\n\n"
                        else:
                            assistant_response = "Elbette. Hibrit RAG motorumuz, en alakalı dokümanları inceleyerek yanıt oluşturuyor.\n\n"
                        
                        if sources:
                            assistant_response += "\n**Kaynaklar:**\n"
                            for i, source in enumerate(sources[:5], 1):
                                similarity = source.get('similarity', 0)
                                assistant_response += f"- [{i}] {source.get('title', 'N/A')} (Similarity: {similarity:.3f})\n"
                    
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

# 6. Dosya Yönetimi
elif menu == "📁 Dosya Yönetimi":
    st.header("📁 Dosya Yönetimi")
    st.markdown("İndirilen dokümanları görüntüle ve yönet")
    
    download_dir = st.text_input("Download Dizini", value="./downloads", key="file_mgmt_dir")
    downloads_path = Path(download_dir)
    
    if downloads_path.exists():
        # Opportunity klasörlerini listele
        opp_dirs = [d for d in downloads_path.iterdir() if d.is_dir()]
        
        if opp_dirs:
            selected_opp = st.selectbox(
                "Opportunity seçin",
                options=[d.name for d in opp_dirs],
                key="file_opp_select"
            )
            
            if selected_opp:
                opp_dir = downloads_path / selected_opp
                files = list(opp_dir.rglob('*'))
                files = [f for f in files if f.is_file()]
                
                st.info(f"📁 {selected_opp} için {len(files)} dosya bulundu")
                
                for i, file_path in enumerate(files[:20], 1):  # İlk 20
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

# 7. SAM API Test
elif menu == "🔗 SAM API Test":
    st.header("🔍 SAM API Test")
    st.markdown("SAM.gov API bağlantısını ve arama işlevlerini test edin")
    
    try:
        from sam_api_client import SAMAPIClient
        
        api_client = SAMAPIClient()
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_notice_id = st.text_input("Test Notice ID", value="086008536ec84226ad9de043dc738d06", key="test_notice")
            
            if st.button("🔍 Metadata Çek", use_container_width=True):
                with st.spinner("Metadata çekiliyor..."):
                    try:
                        metadata = api_client.get_opportunity_metadata(test_notice_id)
                        if metadata:
                            st.success("✅ Metadata başarıyla çekildi")
                            st.json(metadata)
                        else:
                            st.warning("⚠️ Metadata bulunamadı")
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")
            
            if st.button("📥 Resource Links Çek", use_container_width=True):
                with st.spinner("Resource links çekiliyor..."):
                    try:
                        resource_links = api_client.get_resource_links(test_notice_id)
                        if resource_links:
                            st.success(f"✅ {len(resource_links)} resource link bulundu")
                            st.json(resource_links[:5])  # İlk 5
                        else:
                            st.warning("⚠️ Resource link bulunamadı")
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")
        
        with col2:
            st.info("""
            **SAM API Test Özellikleri:**
            
            - Metadata çekme
            - Resource links çekme
            - Document download test
            """)
            
    except ImportError:
        st.warning("⚠️ sam_api_client modülü bulunamadı")
    except Exception as e:
        st.error(f"❌ API test hatası: {e}")

# 8. Ayarlar
elif menu == "⚙️ Ayarlar":
    st.header("⚙️ Ayarlar")
    st.markdown("Sistem konfigürasyonu ve ortam değişkenleri")
    
    # Database status
    st.subheader("🔧 Database Durumu")
    try:
        import psycopg2
        conn = get_db_connection_for_page()
        if conn:
            st.success("✅ Database bağlantısı başarılı (ZGR_AI)")
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sow_analysis")
                count = cursor.fetchone()[0]
                st.info(f"📊 SOW analiz sayısı: {count}")
            conn.close()
        else:
            st.error("❌ Database bağlantısı başarısız. Lütfen DB_DSN ayarlarını kontrol edin.")
    except Exception as e:
        st.error(f"❌ Database bağlantısı başarısız: {e}")
    
    st.markdown("---")
    
    # API/Files status
    st.subheader("🔗 API/Files Durumu")
    if RAG_API_URL:
        st.success(f"✅ RAG API URL mevcut: {RAG_API_URL}")
        
        # Test API connection
        if st.button("🔍 RAG API Test", use_container_width=True):
            with st.spinner("API test ediliyor..."):
                try:
                    rag_client = get_rag_client()
                    test_response = rag_client.hybrid_search(query="test", alpha=0.7, topk=1)
                    if test_response.get('status') != 'error':
                        st.success("✅ RAG API bağlantısı başarılı")
                    else:
                        st.error(f"❌ RAG API hatası: {test_response.get('message')}")
                except Exception as e:
                    st.error(f"❌ RAG API bağlantı hatası: {e}")
    else:
        st.error("⚠️ RAG API URL yok.")
    
    st.markdown("---")
    
    # Environment variables
    st.subheader("📋 Ortam Değişkenleri")
    
    env_vars = {
        "RAG_API_URL": RAG_API_URL,
        "DB_DSN": "*** (güvenlik için gizli)" if DB_DSN else "Ayarlanmamış"
    }
    
    st.json(env_vars)
    
    st.markdown("---")
    
    # Cache management
    st.subheader("🗑️ Cache Yönetimi")
    if st.button("🔄 Tüm Cache'i Temizle", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ Cache temizlendi")
        st.rerun()

# Final check
if __name__ == "__main__":
    # Streamlit automatically runs this
    pass
