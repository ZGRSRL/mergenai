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

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append('.')

def jdump(x): 
    """JSON dump with proper encoding"""
    return json.dumps(x, ensure_ascii=False, indent=2)

# Page configuration
st.set_page_config(
    page_title="SOW Analysis System", 
    page_icon="📊", 
    layout="wide"
)

# Environment variables
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))

# Sidebar navigation
with st.sidebar:
    st.title("📊 SOW Dashboard")
    menu = st.radio(
        "Menü Seçin",
        [
            "Sistem Durumu",
            "Dosya Yönetimi", 
            "SAM API Test",
            "Fırsat Analizi",
            "SOW Analizi",
            "AutoGen Analiz",
            "Ayarlar"
        ],
        index=0
    )
    st.caption("Optimized • Working Modules Only")

# Main content area
if menu == "Sistem Durumu":
    st.header("🔧 Sistem Durumu")
    
    # Database status
    st.subheader("Database Durumu")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='ZGR_AI',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'sarlio41'),
            port=os.getenv('DB_PORT', '5432')
        )
        st.success("✅ Database bağlantısı başarılı")
        
        # Test SOW analysis table
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sow_analysis")
            count = cursor.fetchone()[0]
            st.info(f"📊 SOW analiz sayısı: {count}")
        
        conn.close()
    except Exception as e:
        st.error(f"❌ Database bağlantısı başarısız: {e}")
    
    # SAM API status
    st.subheader("SAM API Durumu")
    api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
    if api_key:
        st.success(f"✅ SAM API Key mevcut: {api_key[:10]}...")
    else:
        st.warning("⚠️ SAM API Key bulunamadı")
    
    # File system status
    st.subheader("Dosya Sistemi Durumu")
    if DOWNLOAD_PATH.exists():
        st.success(f"✅ Downloads dizini mevcut: {DOWNLOAD_PATH.absolute()}")
        pdf_files = list(DOWNLOAD_PATH.rglob("*.pdf"))
        st.info(f"📁 Toplam PDF dosyası: {len(pdf_files)}")
        
        # Show opportunity directories
        opp_dirs = [d for d in DOWNLOAD_PATH.iterdir() if d.is_dir()]
        if opp_dirs:
            st.write("**Opportunity Dizinleri:**")
            for opp_dir in opp_dirs:
                pdf_count = len(list(opp_dir.glob("*.pdf")))
                st.write(f"- {opp_dir.name}: {pdf_count} PDF dosyası")
    else:
        st.warning("⚠️ Downloads dizini bulunamadı")

elif menu == "Dosya Yönetimi":
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

elif menu == "SAM API Test":
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

elif menu == "Ayarlar":
    st.header("⚙️ Ayarlar")
    
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
st.caption("SOW Analysis System - Optimized Version")
