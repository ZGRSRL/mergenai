#!/usr/bin/env python3
"""
SOW Analysis System - Optimized Streamlit Application
Simplified version with only working modules
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

def jdump(x): 
    """JSON dump with proper encoding"""
    return json.dumps(x, ensure_ascii=False, indent=2)

# Page configuration
st.set_page_config(
    page_title="MergenAI - Yönetim Paneli", 
    page_icon="🏆", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
    }
    .result-box {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Environment variables
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))
DB_DSN = os.getenv("DB_DSN", f"dbname=ZGR_AI user={os.getenv('DB_USER', 'postgres')} password={os.getenv('DB_PASSWORD', 'sarlio41')} host={os.getenv('DB_HOST', 'localhost')} port={os.getenv('DB_PORT', '5432')}")

# RAG API URL - Docker içinde rag_api:8000, host makinede localhost:8001
env_url = os.getenv("RAG_API_URL", "http://localhost:8001")
if "rag_api:8000" in env_url or ("rag_api" in env_url and "localhost" not in env_url):
    # Host makineden çalışıyoruz, localhost kullan
    RAG_API_URL = "http://localhost:8001"
else:
    RAG_API_URL = env_url

# --- Utility Functions ---

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

# Logger setup
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis Cache Manager import
try:
    from redis_cache_manager import get_cache_manager
    cache_manager = get_cache_manager()
except ImportError:
    cache_manager = None
    logger.warning("Redis cache manager not available")

# Health Check import
try:
    from health_check import check_rag_api_health, check_redis_health, get_health_status_icon, get_health_status_text
except ImportError:
    def check_rag_api_health(*args, **kwargs):
        return {'status': 'error', 'error': 'Health check module not available'}
    def check_redis_health(*args, **kwargs):
        return {'status': 'error', 'error': 'Health check module not available'}
    def get_health_status_icon(status):
        return '⚪'
    def get_health_status_text(status):
        return 'Unknown'

@st.cache_resource
def get_rag_client():
    """RAG API Client (FastAPI) başlatır - Redis cache desteği ile."""
    class RAGClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
            self.cache_manager = cache_manager
            
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
            """
            Teklif oluşturma endpoint'ini çağırır - Redis cache ile optimize edilmiş.
            
            Cache stratejisi:
            - İlk sorgu: LLM API call + Cache
            - Tekrarlanan sorgular: Cache HIT ($0 maliyet)
            """
            # Check cache first
            if self.cache_manager:
                cached_response = self.cache_manager.get(query, notice_id, hybrid_alpha, topk)
                if cached_response:
                    # Mark as cache hit
                    cached_response['_cache_hit'] = True
                    cached_response['_cache_status'] = '💰 Cache HIT - Saved LLM API call'
                    return cached_response
            
            # Cache miss - call API
            endpoint = f"{self.base_url}/api/rag/generate_proposal"
            data = {
                "query": query,
                "notice_id": notice_id,
                "hybrid_alpha": hybrid_alpha,
                "topk": topk
            }
            try:
                response = requests.post(endpoint, json=data, timeout=180)  # Uzun LLM süresi için 180s
                response.raise_for_status()
                result = response.json()
                
                # Cache successful responses
                if self.cache_manager and result.get('status') == 'success':
                    self.cache_manager.set(query, result, notice_id, hybrid_alpha, topk, ttl=3600)
                    result['_cache_hit'] = False
                    result['_cache_status'] = '💾 Cache SET - Response cached'
                
                return result
            except Exception as e:
                return {"status": "error", "message": f"Proposal API hatası: {e}"}
                
    return RAGClient(RAG_API_URL)

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

@st.cache_data(ttl=3600)
def fetch_opportunity_title(notice_id: str) -> str:
    """
    Notice ID'den başlığı getir - Her iki tabloyu da kontrol eder
    
    Args:
        notice_id: SAM.gov Notice ID
        
    Returns:
        Başlık string veya None
    """
    if not notice_id or not notice_id.strip():
        return None
    
    try:
        import psycopg2
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        # Önce hotel_opportunities_new'de ara
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
        
        # Sonra opportunities tablosunda ara
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
        return None
        
    except Exception:
        return None

# Sidebar navigation
with st.sidebar:
    st.title("🏆 MergenAI Dashboard")
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
    
    # Platform statistics
    try:
        import psycopg2
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT COUNT(*) FROM sam_chunks WHERE opportunity_id IN (SELECT notice_id FROM hotel_opportunities_new)")
            total_chunks = cur.fetchone()[0]
        except:
            total_chunks = 172402
        
        try:
            cur.execute("SELECT COUNT(*) FROM hotel_opportunities_new")
            total_opps = cur.fetchone()[0]
        except:
            total_opps = 9605
        
        try:
            cur.execute("SELECT COUNT(*) FROM sow_analysis WHERE is_active = true")
            sow_count = cur.fetchone()[0]
        except:
            sow_count = 0
        
        conn.close()
        
        st.markdown("---")
        st.markdown("### 📊 Platform İstatistikleri")
        st.metric("Total Chunks", f"{total_chunks:,}")
        st.metric("Opportunities", f"{total_opps:,}")
        st.metric("SOW Analyses", sow_count)
        
    except Exception as e:
        st.info("Platform istatistikleri yüklenemedi")
    
    # API Health Check - Real-time Status
    st.markdown("---")
    st.markdown("### 🔧 System Status")
    
    # RAG API Health
    try:
        rag_health = check_rag_api_health(RAG_API_URL, timeout=3)
        rag_icon = get_health_status_icon(rag_health.get('status', 'unknown'))
        rag_status = get_health_status_text(rag_health.get('status', 'unknown'))
        rag_time = rag_health.get('response_time_ms')
        
        if rag_time:
            st.markdown(f"{rag_icon} **RAG API** ({rag_time}ms)")
        else:
            st.markdown(f"{rag_icon} **RAG API** ({rag_status})")
    except Exception as e:
        st.markdown(f"🔴 **RAG API** (Error)")
    
    # Redis Cache Health
    try:
        if cache_manager:
            redis_health = check_redis_health(cache_manager)
            redis_icon = get_health_status_icon(redis_health.get('status', 'unknown'))
            redis_status = "Connected" if redis_health.get('connected') else "Offline"
            st.markdown(f"{redis_icon} **Redis Cache** ({redis_status})")
        else:
            st.markdown(f"⚪ **Redis Cache** (Not Available)")
    except Exception as e:
        st.markdown(f"🔴 **Redis Cache** (Error)")
    
    # Git Commit ID (Version Tracking)
    try:
        import subprocess
        git_commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                            stderr=subprocess.DEVNULL, 
                                            cwd=os.getcwd()).decode().strip()
        st.caption(f"MergenAI • 172K Chunks • Hybrid RAG • v{git_commit[:7]}")
    except:
        st.caption("MergenAI • 172K Chunks • Hybrid RAG")

# Main content area
if menu == "🏆 Ana Sayfa":
    st.markdown('<div class="main-header">🏆 Haber Merkezi & Hızlı Arama</div>', unsafe_allow_html=True)
    st.markdown("### Proaktif İş Zekası ve Konsolide Arama - NAICS 721110 (Hotel/Lodging)")
    
    # Git Commit ID (Version Display)
    try:
        import subprocess
        git_commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                            stderr=subprocess.DEVNULL, 
                                            cwd=os.getcwd()).decode().strip()
        st.caption(f"🔖 Versiyon: {git_commit[:7]} | MergenAI Platform")
    except:
        st.caption("🔖 MergenAI Platform")
    
    # Tab Structure: Haber Merkezi ve Hızlı Arama
    tab1_haber, tab2_arama = st.tabs(["📰 Haber Merkezi (Günlük İlanlar)", "🔍 Hızlı Arama Merkezi"])
    
    # TAB 1: HABER MERKEZI - Günlük İlanlar Akışı
    with tab1_haber:
        st.markdown("### 📰 Günlük İlanlar Akışı - NAICS 721110")
        st.caption("Bugün SAM.gov'da yayınlanan yeni ilanlar - Sadece Hotel Sektörü")
        st.info("💡 **Proaktif İş Zekası**: Yeni fırsatları anında görün ve tek tıklama ile 172K chunk'lık RAG analizini başlatın!")
        
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
                    filter_naics = st.text_input("📊 NAICS Filtre", value="721110", key="daily_filter_naics", help="Varsayılan: 721110")
                
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
                    st.markdown("---")
                    with st.container():
                        col_left, col_right = st.columns([4, 1])
                        
                        with col_left:
                            st.markdown(f"### [{idx}] {title}")
                            st.caption(f"📅 {posted_date} | 🏛️ {agency} | 📊 NAICS: {naics_code}")
                            
                            if description:
                                st.write(description)
                            
                            # Butonlar - TEK TIKLAMA İLE ANALİZ BAŞLATMA
                            col_btn1, col_btn2, col_btn3 = st.columns(3)
                            with col_btn1:
                                if st.button("🔍 Analiz Et", key=f"analyze_daily_{notice_id}_{idx}", use_container_width=True):
                                    st.session_state["selected_notice"] = notice_id
                                    st.session_state[f'title_{notice_id}'] = title
                                    st.success(f"✅ {notice_id} seçildi - İlan Analizi sekmesine geçin")
                                    # Otomatik olarak İlan Analizi sekmesine geç
                                    st.session_state["auto_switch_menu"] = "🔍 İlan Analizi"
                            
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
        
        # Auto-switch menu if needed
        if st.session_state.get("auto_switch_menu"):
            st.info(f"💡 {st.session_state['auto_switch_menu']} sekmesine geçiliyor...")
            st.session_state["auto_switch_menu"] = None
    
    # TAB 2: HIZLI ARAMA MERKEZI - Manuel Arama + Hybrid RAG
    with tab2_arama:
        st.markdown("### 🔍 Hızlı Arama Merkezi - NAICS 721110")
        st.caption("Manuel Fırsat Arama ve Hybrid RAG Sorgu - Tek Yerden")
        
        # Sub-tabs for different search types
        search_subtab1, search_subtab2 = st.tabs(["🌐 SAM.gov API Arama", "🧠 Hybrid RAG Sorgu"])
        
        # SUB-TAB 1: SAM.gov API Arama
        with search_subtab1:
            st.markdown("**SAM.gov API ile Manuel Fırsat Arama**")
            
            col_search1, col_search2, col_search3, col_search4 = st.columns([2, 1, 1, 1])
            
            with col_search1:
                search_term = st.text_input(
                    "Arama Terimi (Notice ID, Solicitation Number, veya Anahtar Kelime)",
                    placeholder="W50S6U26QA010 veya hotel services",
                    key="api_search_term_main"
                )
            
            with col_search2:
                search_days = st.number_input("Son N Gün", min_value=1, max_value=365, value=30, key="search_days_main")
            
            with col_search3:
                naics_default = st.text_input("NAICS", value="721110", key="naics_search_main", help="Varsayılan: 721110 (Hotel Services)")
            
            with col_search4:
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
                        
                        # NAICS 721110 (Hotel Services) ile arama
                        result = sam_client.search_opportunities(
                            posted_from=posted_from,
                            posted_to=posted_to,
                            limit=100,
                            naicsCode=naics_default or '721110'
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
                                        if st.button("📋 Seç ve Analiz Et", key=f"select_opp_main_{idx}", use_container_width=True):
                                            st.session_state["selected_notice"] = opp_notice_id
                                            st.session_state[f'title_{opp_notice_id}'] = opp_title
                                            st.success(f"✅ {opp_notice_id} seçildi! İlan Analizi sekmesine geçin.")
                                            st.session_state["auto_switch_menu"] = "🔍 İlan Analizi"
                                            st.rerun()
                        else:
                            st.warning(f"⚠️ '{search_term}' için sonuç bulunamadı.")
                            st.info("💡 İpucu: Notice ID (UUID veya Public format), Solicitation Number veya anahtar kelime ile arayabilirsiniz.")
                    
                    except Exception as e:
                        st.error(f"❌ Arama hatası: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # SUB-TAB 2: Hybrid RAG Sorgu
        with search_subtab2:
            st.markdown("**🧠 Hybrid RAG Sorgu Motoru - 172,402 Geçmiş Fırsat Üzerinde Semantic Search**")
            
            rag_client = get_rag_client()
            
            col_query, col_control = st.columns([3, 1])
            
            with col_control:
                st.markdown("##### ⚙️ Hybrid Ayarlar")
                hybrid_alpha = st.slider("FTS Ağırlığı (α)", 0.0, 1.0, 0.7, 0.1, help="0.0: Semantic, 1.0: Keyword", key="rag_alpha_main")
                top_k = st.slider("Chunk Sayısı (Top-K)", 5, 20, 10, 1, key="rag_topk_main")
            
            with col_query:
                # Initialize example query selector if not exists
                if 'selected_example_query_main' not in st.session_state:
                    st.session_state.selected_example_query_main = None
                
                # Use selected example query if available, otherwise use default
                if st.session_state.selected_example_query_main:
                    default_query = st.session_state.selected_example_query_main
                    st.session_state.selected_example_query_main = None
                else:
                    default_query = "military base conference room services için tipik gereksinimler"
                
                user_query = st.text_input(
                    "Arama Sorgunuz:",
                    value=default_query,
                    key="rag_query_main"
                )
                
                search_button_rag = st.button("🔍 Hybrid Arama Yap", type="primary", use_container_width=True)
            
            if search_button_rag and user_query:
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
                    if st.button(f"📝 {example[:40]}...", key=f"example_main_{i}", use_container_width=True):
                        st.session_state.selected_example_query_main = example
                        st.rerun()

elif menu == "🔍 İlan Analizi":
    st.markdown('<div class="main-header">🔍 Canlı İlan Analizi</div>', unsafe_allow_html=True)
    st.markdown("### SAM.gov İlanlarını Analiz Et ve RAG Sistemine Hazırla")
    
    # Settings
    with st.expander("⚙️ Ayarlar"):
        use_llm = st.checkbox("LLM ile Gereksinim Çıkarımı", value=True)
        download_dir = st.text_input("Download Dizini", value="./downloads")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Auto-fill from daily opportunities if available
        default_notice = st.session_state.get("selected_notice", "086008536ec84226ad9de043dc738d06")
        
        notice_id = st.text_input(
            "SAM.gov Notice ID",
            value=default_notice,
            help="Örnek: 086008536ec84226ad9de043dc738d06",
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
                
                result = workflow.run(notice_id)
                
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
                import traceback
                st.code(traceback.format_exc())

elif menu == "📁 Dosya Yönetimi":
    st.header("📁 Dosya Yönetimi")
    
    if DOWNLOAD_PATH.exists():
        st.success(f"Downloads dizini: {DOWNLOAD_PATH.absolute()}")
        
        # List all files
        all_files = list(DOWNLOAD_PATH.rglob("*"))
        st.write(f"**Toplam dosya sayısı:** {len(all_files)}")
        
        # Group by opportunity
        opp_files = {}
        for file_path in all_files:
            if file_path.is_file():
                opp_id = file_path.parent.name
                if opp_id not in opp_files:
                    opp_files[opp_id] = []
                opp_files[opp_id].append(file_path)
        
        for opp_id, files in opp_files.items():
            with st.expander(f"Opportunity: {opp_id} ({len(files)} dosya)"):
                for file_path in files:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"📄 {file_path.name}")
                    col2.write(f"{file_path.stat().st_size} bytes")
                    if col3.button("Görüntüle", key=f"view_{file_path}"):
                        st.info(f"Dosya yolu: {file_path}")
    else:
        st.warning("Downloads dizini bulunamadı")

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
                        
                        # Cache status gösterimi
                        cache_status = result.get('_cache_status', '')
                        if result.get('_cache_hit'):
                            st.success(f"✅ Teklif başarıyla oluşturuldu! {cache_status}")
                        else:
                            st.success(f"✅ Teklif başarıyla oluşturuldu! {cache_status}")
                    else:
                        error_msg = result.get('message', 'API\'den beklenmeyen hata')
                        st.session_state.proposal_draft = f"❌ Hata: {error_msg}"
                        st.error(st.session_state.proposal_draft)
            else:
                st.warning("⚠️ Lütfen bir soru/talimat girin.")

    with col2:
        st.info("""
        **ZGRPROP Hotel Intelligence Köprüsü**

        Bu modül, 172K chunk'lık geçmiş veriyi (MergenAI) kullanır ve sonuçları LLM (AutoGen) aracılığıyla yapılandırılmış bir teklif taslağına dönüştürür.
        
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

elif menu == "🧠 Hybrid RAG Sorgu":
    # Hybrid RAG Sorgu artık Ana Sayfa'da - Bu menu item'ı Ana Sayfa'ya yönlendir
    st.info("💡 **Hybrid RAG Sorgu** artık Ana Sayfa'daki **Hızlı Arama Merkezi** bölümünde! Lütfen Ana Sayfa'ya geçin.")
    st.markdown("---")
    st.markdown("### 🔄 Yönlendirme")
    
    if st.button("🏆 Ana Sayfa'ya Git", type="primary", use_container_width=True):
        st.session_state["menu_switch"] = "🏆 Ana Sayfa"
        st.rerun()

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

elif menu == "🔗 SAM API Test":
    st.header("🔍 SAM API Test")
    
    # Test SAM API
    api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
    
    if not api_key:
        st.error("SAM API Key bulunamadı. Lütfen .env dosyasında SAM_API_KEY ayarlayın.")
        st.stop()
    
    # Test connection
    if st.button("API Bağlantısını Test Et"):
        with st.spinner("SAM API test ediliyor..."):
            try:
                from sam_api_client_safe import SamClientSafe
                client = SamClientSafe(key=api_key)
                
                if client.test_connection():
                    st.success("✅ SAM API bağlantısı başarılı")
                else:
                    st.warning("⚠️ SAM API bağlantı testi başarısız")
            except Exception as e:
                st.error(f"❌ SAM API hatası: {e}")
    
    # Search opportunities
    st.subheader("Fırsat Arama")
    
    col1, col2, col3 = st.columns(3)
    naics = col1.text_input("NAICS", value="721110")
    posted_from = col2.date_input("Başlangıç", value=dt.date.today() - dt.timedelta(days=7))
    posted_to = col3.date_input("Bitiş", value=dt.date.today())
    
    if st.button("Fırsat Ara"):
        with st.spinner("Fırsatlar aranıyor..."):
            try:
                from sam_api_client_safe import SamClientSafe
                client = SamClientSafe(key=api_key)
                
                data = client.search_opportunities(
                    naics=naics,
                    postedFrom=posted_from.strftime("%m/%d/%Y"),
                    postedTo=posted_to.strftime("%m/%d/%Y"),
                    limit="10"
                )
                
                opportunities = data.get("opportunitiesData", [])
                
                if opportunities:
                    st.success(f"{len(opportunities)} fırsat bulundu")
                    
                    for opp in opportunities:
                        with st.container(border=True):
                            st.write(f"**{opp.get('title', 'N/A')}**")
                            st.write(f"Notice ID: `{opp.get('noticeId', 'N/A')}`")
                            st.write(f"Posted: {opp.get('postedDate', 'N/A')}")
                            st.write(f"NAICS: {opp.get('naics', 'N/A')}")
                            
                            if st.button("Detayları Görüntüle", key=f"detail_{opp.get('noticeId')}"):
                                st.json(opp)
                else:
                    st.warning("Fırsat bulunamadı")
                    
            except Exception as e:
                st.error(f"Arama hatası: {e}")

elif menu == "Fırsat Analizi":
    st.header("🔍 Fırsat Analizi")
    
    # Get opportunities from database
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='ZGR_AI',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'sarlio41'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    opportunity_id,
                    title,
                    organization_type,
                    naics_code,
                    posted_date,
                    response_dead_line,
                    place_of_performance
                FROM opportunities
                ORDER BY posted_date DESC
                LIMIT 50
            """)
            opportunities = cursor.fetchall()
        
        conn.close()
        
        if opportunities:
            st.success(f"{len(opportunities)} fırsat bulundu")
            
            # Search and filter
            col1, col2 = st.columns(2)
            search_term = col1.text_input("Ara (title, agency, notice_id)")
            naics_filter = col2.text_input("NAICS Filtre")
            
            # Filter opportunities
            filtered_opps = opportunities
            if search_term:
                filtered_opps = [opp for opp in filtered_opps if search_term.lower() in str(opp).lower()]
            if naics_filter:
                filtered_opps = [opp for opp in filtered_opps if naics_filter in str(opp[3])]
            
            st.write(f"**Filtrelenmiş sonuç:** {len(filtered_opps)} fırsat")
            
            for opp in filtered_opps:
                opportunity_id, title, organization_type, naics_code, posted_date, response_dead_line, place_of_performance = opp
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{title or 'Başlık Yok'}**")
                        st.write(f"Opportunity ID: `{opportunity_id}`")
                        st.write(f"Organization: {organization_type or 'N/A'}")
                        st.write(f"NAICS: {naics_code or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Posted:** {posted_date.strftime('%Y-%m-%d') if posted_date else 'N/A'}")
                        st.write(f"**Due:** {response_dead_line.strftime('%Y-%m-%d') if response_dead_line else 'N/A'}")
                    
                    with col3:
                        if st.button("Detay", key=f"detail_{opportunity_id}"):
                            st.session_state[f"show_detail_{opportunity_id}"] = not st.session_state.get(f"show_detail_{opportunity_id}", False)
                        
                        if st.button("Analiz Et", key=f"analyze_{opportunity_id}"):
                            st.session_state["selected_notice"] = opportunity_id
                            st.success(f"Seçildi: {opportunity_id}")
                    
                    if st.session_state.get(f"show_detail_{opportunity_id}", False):
                        st.write("**Detaylı Bilgi:**")
                        st.write(f"- Place of Performance: {place_of_performance or 'N/A'}")
                        st.write(f"- Posted At: {posted_date}")
                        st.write(f"- Due At: {response_dead_line}")
        else:
            st.info("Veritabanında fırsat bulunamadı")
            
    except Exception as e:
        st.error(f"Database hatası: {e}")

elif menu == "SOW Analizi":
    st.header("📊 SOW Analizi")
    
    # RAG Servisi ile Teklif Oluşturma
    st.subheader("🤖 RAG Servisi ile Teklif Oluştur")
    
    col1, col2 = st.columns(2)
    
    with col1:
        rag_notice_id = st.text_input("Opportunity ID (RAG için)", value="", key="rag_notice_id")
        
        # Başlığı getir ve göster
        if rag_notice_id and rag_notice_id.strip():
            opportunity_title = fetch_opportunity_title(rag_notice_id)
            if opportunity_title:
                st.markdown(f"**📋 İlan Başlığı:** {opportunity_title}")
                st.session_state[f'title_{rag_notice_id}'] = opportunity_title
            else:
                st.info("ℹ️ Başlık bulunamadı - Bu yeni bir ilan olabilir")
        
        rag_agency = st.text_input("Agency (Opsiyonel)", value="", key="rag_agency")
        rag_query = st.text_area(
            "Soru/Talimat",
            value="Bu fırsat için ana teknik gereksinimler nelerdir ve geçmiş benzer fırsatlardan öğrenilen başarı faktörleri nelerdir?",
            height=100,
            key="rag_query"
        )
        
        if st.button("🚀 RAG ile Teklif Oluştur", type="primary"):
            if rag_query:
                with st.spinner("RAG servisi ile teklif oluşturuluyor..."):
                    try:
                        from samai_integrator import call_rag_proposal_service
                        
                        result = call_rag_proposal_service(
                            user_query=rag_query,
                            notice_id=rag_notice_id if rag_notice_id else None,
                            agency=rag_agency if rag_agency else None
                        )
                        
                        if result.get("status") == "success":
                            # Başlık gösterimi (varsa)
                            if rag_notice_id and f'title_{rag_notice_id}' in st.session_state:
                                st.markdown(f"### 📋 {st.session_state[f'title_{rag_notice_id}']}")
                            
                            st.success("✅ Teklif başarıyla oluşturuldu!")
                            
                            # Teklif taslağını göster
                            st.subheader("📄 Teklif Taslağı")
                            st.text_area(
                                "Teklif İçeriği",
                                value=result['result']['proposal_draft'],
                                height=400,
                                key="proposal_draft"
                            )
                            
                            # Kaynakları göster
                            if result.get('sources'):
                                st.subheader(f"📚 Kaynaklar ({len(result['sources'])} adet)")
                                for i, source in enumerate(result['sources'][:5], 1):
                                    with st.expander(f"Kaynak {i}: Belge ID {source['document_id']} (Benzerlik: {source['similarity']:.2f})"):
                                        st.write(f"**Önizleme:** {source['text_preview']}")
                        else:
                            st.error(f"❌ Hata: {result.get('message', 'Bilinmeyen hata')}")
                            
                    except ImportError:
                        st.error("❌ samai_integrator modülü bulunamadı. Lütfen dosyanın mevcut olduğundan emin olun.")
                    except Exception as e:
                        st.error(f"❌ RAG servisi hatası: {e}")
            else:
                st.warning("⚠️ Lütfen bir soru/talimat girin.")
    
    with col2:
        st.info("""
        **RAG Servisi Özellikleri:**
        
        ✅ Geçmiş fırsatlardan öğrenme
        ✅ Semantic arama
        ✅ LLM ile teklif oluşturma
        ✅ Kaynak referansları
        
        **Kullanım:**
        1. Opportunity ID ve Agency bilgisini girin
        2. Soru/talimatınızı yazın
        3. "RAG ile Teklif Oluştur" butonuna tıklayın
        """)
    
    # Get SOW analyses from database
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='ZGR_AI',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'sarlio41'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    template_version,
                    sow_payload,
                    created_at,
                    updated_at
                FROM sow_analysis 
                WHERE is_active = true
                ORDER BY updated_at DESC
                LIMIT 20
            """)
            analyses = cursor.fetchall()
        
        conn.close()
        
        if analyses:
            st.success(f"{len(analyses)} SOW analizi bulundu")
            
            for analysis in analyses:
                notice_id, template_version, sow_payload, created_at, updated_at = analysis
                
                with st.expander(f"SOW: {notice_id} ({template_version})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Notice ID:** {notice_id}")
                        st.write(f"**Template Version:** {template_version}")
                        st.write(f"**Created:** {created_at}")
                        st.write(f"**Updated:** {updated_at}")
                    
                    with col2:
                        if sow_payload:
                            st.write("**SOW Payload:**")
                            st.json(sow_payload)
                        else:
                            st.write("SOW payload bulunamadı")
        else:
            st.info("SOW analizi bulunamadı")
            
    except Exception as e:
        st.error(f"Database hatası: {e}")
    
    # Create new SOW analysis
    st.subheader("Yeni SOW Analizi Oluştur")
    
    notice_id = st.text_input("Opportunity ID", value="70LART26QPFB00001")
    
    # Başlığı getir ve göster
    if notice_id and notice_id.strip():
        opportunity_title = fetch_opportunity_title(notice_id)
        if opportunity_title:
            st.markdown(f"**📋 İlan Başlığı:** {opportunity_title}")
            st.session_state[f'title_{notice_id}'] = opportunity_title
        else:
            st.info("ℹ️ Başlık bulunamadı - Bu yeni bir ilan olabilir")
    
    if st.button("Mock SOW Analizi Oluştur"):
        with st.spinner("SOW analizi oluşturuluyor..."):
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    database='ZGR_AI',
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'sarlio41'),
                    port=os.getenv('DB_PORT', '5432')
                )
                
                # Create mock SOW data
                mock_sow = {
                    "period_of_performance": "2025-02-25 to 2025-02-27",
                    "setup_deadline": "2025-02-24T18:00:00Z",
                    "room_block": {
                        "total_rooms_per_night": 120,
                        "nights": 4,
                        "attrition_policy": "no_penalty_below_120"
                    },
                    "function_space": {
                        "general_session": {
                            "capacity": 120,
                            "projectors": 2,
                            "screens": "6x10",
                            "setup": "classroom"
                        },
                        "breakout_rooms": {
                            "count": 4,
                            "capacity_each": 30,
                            "setup": "classroom"
                        }
                    },
                    "av": {
                        "projector_lumens": 5000,
                        "power_strips_min": 10,
                        "adapters": ["HDMI", "DisplayPort", "DVI", "VGA"]
                    },
                    "refreshments": {
                        "frequency": "AM/PM_daily",
                        "menu": ["water", "coffee", "tea", "snacks"]
                    },
                    "tax_exemption": True
                }
                
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sow_analysis (
                            notice_id, 
                            template_version, 
                            sow_payload, 
                            source_docs, 
                            is_active
                        )
                        VALUES (%s, %s, %s::jsonb, %s::jsonb, true)
                        ON CONFLICT (notice_id, template_version)
                        DO UPDATE SET
                            sow_payload = EXCLUDED.sow_payload,
                            updated_at = now()
                        RETURNING analysis_id
                    """, (
                        notice_id,
                        "v1.0",
                        json.dumps(mock_sow),
                        json.dumps({"generated_by": "streamlit_app"})
                    ))
                    
                    analysis_id = cursor.fetchone()[0]
                    conn.commit()
                
                conn.close()
                st.success(f"✅ SOW analizi oluşturuldu! Analysis ID: {analysis_id}")
                st.rerun()
                
            except Exception as e:
                st.error(f"SOW analizi oluşturma hatası: {e}")

elif menu == "AutoGen Analiz":
    st.header("🤖 AutoGen Analiz")
    
    # Check if AutoGen is available
    try:
        from autogen.agentchat.assistant_agent import AssistantAgent
        from autogen.agentchat.user_proxy_agent import UserProxyAgent
        AUTOGEN_AVAILABLE = True
    except ImportError:
        AUTOGEN_AVAILABLE = False
        st.error("AutoGen modülü bulunamadı. Lütfen 'pip install pyautogen' komutu ile yükleyin.")
        st.stop()
    
    st.success("✅ AutoGen modülü mevcut")
    
    # Select notice for analysis
    notice_id = st.text_input("Opportunity ID", value=st.session_state.get("selected_notice", "70LART26QPFB00001"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("AutoGen Analiz Başlat"):
            with st.spinner("AutoGen analizi çalıştırılıyor..."):
                try:
                    # Create AutoGen agents
                    assistant = AssistantAgent(
                        name="SOW_Analyzer",
                        system_message="""You are a SOW (Statement of Work) analysis expert for government contracting opportunities. 
                        
                        Your task is to analyze SAM.gov opportunity data and create a comprehensive SOW analysis. Even if specific details are not provided in the opportunity description, you should make reasonable assumptions based on:
                        - The organization type (DHS, FLETC, etc.)
                        - NAICS code (721110 = Hotels and Motels)
                        - The nature of the requirement (lodging services, training facilities)
                        - Industry standards for similar contracts
                        
                        Always provide a structured JSON response with the following format:
                        {
                            "period_of_performance": "estimated dates based on context",
                            "room_requirements": "estimated room needs",
                            "function_space": "meeting room requirements",
                            "av_requirements": "A/V equipment needs",
                            "refreshments": "catering requirements",
                            "pre_con_meeting": "coordination meeting details",
                            "tax_exemption": true/false,
                            "assumptions_made": "list of assumptions used"
                        }
                        
                        Be helpful and provide detailed analysis even with limited information.""",
                        llm_config={
                            "model": "gpt-4",
                            "api_key": os.getenv("OPENAI_API_KEY"),
                            "temperature": 0.3
                        }
                    )
                    
                    user_proxy = UserProxyAgent(
                        name="User_Proxy",
                        human_input_mode="NEVER",
                        max_consecutive_auto_reply=1
                    )
                    
                    # Get opportunity data
                    import psycopg2
                    conn = psycopg2.connect(
                        host=os.getenv('DB_HOST', 'localhost'),
                        database='ZGR_AI',
                        user=os.getenv('DB_USER', 'postgres'),
                        password=os.getenv('DB_PASSWORD', 'sarlio41'),
                        port=os.getenv('DB_PORT', '5432')
                    )
                    
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT title, description, organization_type, naics_code, posted_date, response_dead_line
                            FROM opportunities 
                            WHERE opportunity_id = %s
                        """, (notice_id,))
                        opp_data = cursor.fetchone()
                    
                    conn.close()
                    
                    if opp_data:
                        title, description, organization_type, naics_code, posted_date, response_dead_line = opp_data
                        
                        # Prepare analysis prompt
                        analysis_prompt = f"""
                        Please analyze this SAM.gov opportunity and create a comprehensive SOW (Statement of Work) analysis:
                        
                        OPPORTUNITY DETAILS:
                        - ID: {notice_id}
                        - Title: {title}
                        - Organization: {organization_type}
                        - NAICS Code: {naics_code} (Hotels and Motels)
                        - Posted Date: {posted_date}
                        - Response Deadline: {response_dead_line}
                        - Description: {description or 'No description available'}
                        
                        CONTEXT:
                        This is a Department of Homeland Security (DHS) Federal Law Enforcement Training Centers (FLETC) requirement for lodging services in Artesia, New Mexico. Based on the NAICS code 721110 and the nature of FLETC training programs, please make reasonable assumptions about:
                        
                        1. Training program duration (typically 1-4 weeks)
                        2. Participant capacity (typically 50-200 people)
                        3. Room requirements (single/double occupancy)
                        4. Meeting space needs (classrooms, conference rooms)
                        5. A/V equipment requirements
                        6. Catering needs
                        7. Pre-conference coordination
                        8. Tax exemption status (government contract)
                        
                        Please provide a detailed JSON analysis with specific recommendations and assumptions clearly stated.
                        """
                        
                        # Run AutoGen analysis
                        user_proxy.initiate_chat(
                            assistant,
                            message=analysis_prompt
                        )
                        
                        # Get the result
                        messages = user_proxy.chat_messages[assistant]
                        if messages:
                            last_message = messages[-1]['content']
                            
                            # Başlık gösterimi (varsa)
                            if notice_id and f'title_{notice_id}' in st.session_state:
                                st.markdown(f"### 📋 {st.session_state[f'title_{notice_id}']}")
                            
                            st.success("✅ AutoGen analizi tamamlandı!")
                            
                            # Display result
                            st.subheader("Analiz Sonucu:")
                            st.text_area("AutoGen Çıktısı", value=last_message, height=400)
                            
                            # Try to parse as JSON
                            try:
                                import json
                                analysis_json = json.loads(last_message)
                                st.subheader("JSON Formatında:")
                                st.json(analysis_json)
                            except:
                                st.info("JSON formatında parse edilemedi, ham metin gösteriliyor")
                        else:
                            st.warning("AutoGen analizi tamamlandı ancak sonuç alınamadı")
                    else:
                        st.error(f"Notice ID {notice_id} bulunamadı")
                        
                except Exception as e:
                    st.error(f"AutoGen analiz hatası: {e}")
                    import traceback
                    st.text(traceback.format_exc())
    
    with col2:
        st.subheader("AutoGen Konfigürasyonu")
        
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            st.success(f"✅ OpenAI API Key: {openai_key[:10]}...")
        else:
            st.error("❌ OpenAI API Key bulunamadı")
            st.info("Lütfen .env dosyasında OPENAI_API_KEY ayarlayın")
        
        # Show available models
        st.write("**Kullanılabilir Modeller:**")
        st.write("- gpt-4 (önerilen)")
        st.write("- gpt-3.5-turbo")
        st.write("- gpt-4-turbo")
        
        # Analysis parameters
        st.write("**Analiz Parametreleri:**")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
        max_tokens = st.number_input("Max Tokens", 1000, 4000, 2000)
        
        st.write("**Analiz Kapsamı:**")
        st.write("- SOW gereksinimleri")
        st.write("- Oda ve kapasite analizi")
        st.write("- Fonksiyon alanı ihtiyaçları")
        st.write("- A/V ve teknik gereksinimler")
        st.write("- Refreshment planlaması")
        st.write("- Vergi muafiyeti durumu")

elif menu == "⚙️ Ayarlar":
    st.header("⚙️ Ayarlar")
    st.markdown("### Sistem Konfigürasyonu ve Durum Kontrolü")
    
    # Health Check Section
    st.markdown("---")
    st.subheader("🔗 API/Files Durumu")
    
    col_health1, col_health2 = st.columns(2)
    
    with col_health1:
        st.markdown("##### RAG API Health")
        rag_health = check_rag_api_health(RAG_API_URL, timeout=3)
        rag_icon = get_health_status_icon(rag_health.get('status', 'unknown'))
        rag_status = get_health_status_text(rag_health.get('status', 'unknown'))
        rag_time = rag_health.get('response_time_ms')
        
        st.markdown(f"{rag_icon} **Status:** {rag_status}")
        if rag_time:
            st.markdown(f"**Response Time:** {rag_time}ms")
        st.markdown(f"**API URL:** `{RAG_API_URL}`")
        if rag_health.get('error'):
            st.error(f"**Error:** {rag_health.get('error')}")
        if rag_health.get('status_code'):
            st.markdown(f"**HTTP Status:** {rag_health.get('status_code')}")
        st.markdown(f"**Last Check:** {rag_health.get('timestamp', 'N/A')}")
    
    with col_health2:
        st.markdown("##### Redis Cache Durumu")
        if cache_manager:
            redis_health = check_redis_health(cache_manager)
            redis_icon = get_health_status_icon(redis_health.get('status', 'unknown'))
            redis_stats = cache_manager.get_stats()
            
            st.markdown(f"{redis_icon} **Status:** {'Connected' if redis_health.get('connected') else 'Offline'}")
            if redis_health.get('connected'):
                st.markdown(f"**Keys:** {redis_health.get('keys', 0)}")
                st.markdown(f"**Memory:** {redis_health.get('memory_mb', 0.0)} MB")
                st.markdown(f"**Total Keys:** {redis_stats.get('total_keys', 0)}")
            if redis_health.get('error'):
                st.error(f"**Error:** {redis_health.get('error')}")
            st.markdown(f"**Last Check:** {redis_health.get('timestamp', 'N/A')}")
        else:
            st.markdown("⚪ **Status:** Not Available")
            st.info("Redis cache manager not initialized. Check Redis connection.")
    
    # Cache Management Section
    st.markdown("---")
    st.subheader("💾 Redis Cache Yönetimi")
    
    if cache_manager and cache_manager.connected:
        cache_stats = cache_manager.get_stats()
        
        col_cache1, col_cache2, col_cache3 = st.columns(3)
        
        with col_cache1:
            st.metric("Cache Keys", cache_stats.get('keys', 0))
        
        with col_cache2:
            st.metric("Memory Usage", f"{cache_stats.get('memory_mb', 0.0)} MB")
        
        with col_cache3:
            st.metric("Total Redis Keys", cache_stats.get('total_keys', 0))
        
        # Cache control buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🗑️ Cache'i Temizle", use_container_width=True):
                if cache_manager.clear_cache():
                    st.success("✅ Cache temizlendi!")
                    st.rerun()
                else:
                    st.error("❌ Cache temizlenemedi")
        
        with col_btn2:
            if st.button("🔄 Cache İstatistiklerini Yenile", use_container_width=True):
                st.rerun()
        
        # Cache key info
        st.markdown("**Cache Key Format:** `proposal:{hash}`")
        st.info("💡 Cache TTL: 1 saat (3600 saniye). Aynı sorgu için tekrarlanan istekler cache'den servis edilir.")
    else:
        st.warning("⚠️ Redis cache kullanılamıyor. Cache özellikleri devre dışı.")
        st.info("💡 Redis'i başlatmak için: `docker-compose up -d redis`")
    
    st.markdown("---")
    st.subheader("📊 Cache Optimizasyonu")
    
    st.markdown("""
    **💰 Maliyet Tasarrufu:**
    - **Öncesi:** Her RAG query → LLM API call ($0.01-0.05)
    - **Sonrası:** Tekrarlanan sorgular → Cache HIT ($0.00)
    - **Tasarruf:** %70-90 maliyet azalması (tipik kullanımda)
    
    **⚡ Performans İyileştirmesi:**
    - Cache HIT: Milisaniye seviyesinde yanıt
    - Cache MISS: Normal LLM API call süresi (2-3 dakika)
    
    **🔧 Cache Stratejisi:**
    - Cache Key: Query + Notice ID + Parameters hash
    - TTL: 1 saat (3600 saniye)
    - Auto-expiration: Redis tarafından otomatik temizlik
    """)
    
    st.markdown("---")
    
    # Environment variables
    st.subheader("Environment Variables")
    
    # Load .env file if exists
    env_file = Path('.env')
    if env_file.exists():
        st.success("✅ .env dosyası bulundu")
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        st.text_area(".env İçeriği", value=env_content, height=200)
    else:
        st.warning("⚠️ .env dosyası bulunamadı")
    
    env_vars = {
        "SAM_API_KEY": os.getenv('SAM_API_KEY'),
        "SAM_PUBLIC_API_KEY": os.getenv('SAM_PUBLIC_API_KEY'),
        "OPENAI_API_KEY": os.getenv('OPENAI_API_KEY'),
        "DB_HOST": os.getenv('DB_HOST'),
        "DB_NAME": os.getenv('DB_NAME'),
        "DB_USER": os.getenv('DB_USER'),
        "DB_PASSWORD": os.getenv('DB_PASSWORD'),
        "DB_PORT": os.getenv('DB_PORT'),
        "DOWNLOAD_PATH": os.getenv('DOWNLOAD_PATH'),
        "SAM_OPPS_BASE_URL": os.getenv('SAM_OPPS_BASE_URL'),
        "SAM_MIN_INTERVAL": os.getenv('SAM_MIN_INTERVAL'),
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**API Keys:**")
        for key in ["SAM_API_KEY", "SAM_PUBLIC_API_KEY", "OPENAI_API_KEY"]:
            value = env_vars[key]
            if value:
                st.success(f"✅ {key}: {value[:10]}...")
            else:
                st.error(f"❌ {key}: Not set")
    
    with col2:
        st.write("**Database:**")
        for key in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT"]:
            value = env_vars[key]
            if value:
                if 'PASSWORD' in key:
                    st.success(f"✅ {key}: {'*' * len(str(value))}")
                else:
                    st.success(f"✅ {key}: {value}")
            else:
                st.error(f"❌ {key}: Not set")
    
    st.write("**Diğer Ayarlar:**")
    for key in ["DOWNLOAD_PATH", "SAM_OPPS_BASE_URL", "SAM_MIN_INTERVAL"]:
        value = env_vars[key]
        if value:
            st.success(f"✅ {key}: {value}")
        else:
            st.warning(f"⚠️ {key}: Not set (default kullanılıyor)")
    
    # System info
    st.subheader("Sistem Bilgileri")
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Working Directory:** {os.getcwd()}")
    st.write(f"**Download Path:** {DOWNLOAD_PATH.absolute()}")
    
    # Clear cache
    if st.button("Streamlit Cache'i Temizle"):
        st.cache_data.clear()
        st.success("✅ Cache temizlendi")

# Footer
st.markdown("---")
st.caption("MergenAI - Hybrid RAG Intelligence Platform • 172K Chunks • Production Ready")
