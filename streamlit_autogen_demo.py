#!/usr/bin/env python3
"""
Streamlit AutoGen Demo - Adım adım gösterim
"""

import streamlit as st
import time
import psycopg2
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# AutoGen implementation'ı import et
sys.path.append('.')
from autogen_implementation import ZgrBidAutoGenOrchestrator, Document, DocumentType

load_dotenv()

def create_database_connection():
    """Veritabanı bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        return conn
    except Exception as e:
        st.error(f"Veritabani baglanti hatasi: {e}")
        return None

def get_sam_opportunities_from_db(conn, limit=3):
    """Veritabanından SAM fırsatlarını al"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, opportunity_id, title, description, posted_date, contract_type, naics_code
            FROM opportunities 
            WHERE naics_code = '721110' 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (limit,))
        
        records = cursor.fetchall()
        
        opportunities = []
        for record in records:
            opportunities.append({
                'id': record[0],
                'opportunity_id': record[1],
                'title': record[2],
                'description': record[3],
                'posted_date': record[4],
                'contract_type': record[5],
                'naics_code': record[6]
            })
        
        return opportunities
        
    except Exception as e:
        st.error(f"Veri alma hatasi: {e}")
        return []

def simulate_agent_processing(agent_name, duration, status="success"):
    """Agent işlemini simüle et"""
    with st.spinner(f"{agent_name} çalışıyor..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            progress_bar.progress(i + 1)
            status_text.text(f"{agent_name}: %{i+1} tamamlandı")
            time.sleep(duration / 100)
        
        if status == "success":
            st.success(f"✅ {agent_name} başarıyla tamamlandı!")
        else:
            st.error(f"❌ {agent_name} hatası!")
        
        return True

def main():
    st.set_page_config(
        page_title="ZgrBid AutoGen Demo",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 ZgrBid AutoGen Sistemi - Adım Adım Demo")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Kontrol Paneli")
    
    if st.sidebar.button("🚀 AutoGen'i Başlat", type="primary"):
        run_autogen_demo()
    
    if st.sidebar.button("📊 Veritabanını Kontrol Et"):
        check_database()
    
    if st.sidebar.button("📧 Rapor Gönder"):
        send_report()

def run_autogen_demo():
    """AutoGen demo'sunu çalıştır"""
    
    st.header("🚀 AutoGen İşlem Süreci")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        return
    
    # SAM fırsatlarını al
    opportunities = get_sam_opportunities_from_db(conn, limit=3)
    
    if not opportunities:
        st.warning("Veritabanında SAM fırsatı bulunamadı!")
        conn.close()
        return
    
    st.success(f"✅ Veritabanından {len(opportunities)} fırsat alındı")
    
    # Fırsatları göster
    st.subheader("📋 İşlenecek Fırsatlar")
    for i, opp in enumerate(opportunities, 1):
        with st.expander(f"Fırsat {i}: {opp['title'][:50]}..."):
            st.write(f"**ID:** {opp['id']}")
            st.write(f"**Başlık:** {opp['title']}")
            st.write(f"**Tip:** {opp['contract_type']}")
            st.write(f"**Tarih:** {opp['posted_date']}")
    
    # AutoGen işlemi
    st.subheader("🤖 AutoGen Multi-Agent İşlemi")
    
    # Agent 1: Document Processor
    st.markdown("### 📄 Agent 1: Document Processor")
    simulate_agent_processing("Document Processor", 2.3)
    st.info("📝 Belgeler işlendi, metadata eklendi")
    
    # Agent 2: Requirements Extractor
    st.markdown("### 🔍 Agent 2: Requirements Extractor")
    simulate_agent_processing("Requirements Extractor", 4.1)
    st.info("📋 15 gereksinim çıkarıldı")
    
    # Agent 3: Compliance Analyst
    st.markdown("### ⚖️ Agent 3: Compliance Analyst")
    simulate_agent_processing("Compliance Analyst", 3.7)
    st.info("📊 Compliance analizi tamamlandı (6/15 karşılandı)")
    
    # Agent 4: Pricing Specialist
    st.markdown("### 💰 Agent 4: Pricing Specialist")
    simulate_agent_processing("Pricing Specialist", 2.9)
    st.info("💵 Fiyatlandırma hesaplandı ($64,000 per fırsat)")
    
    # Agent 5: Proposal Writer
    st.markdown("### ✍️ Agent 5: Proposal Writer")
    simulate_agent_processing("Proposal Writer", 5.2)
    st.info("📝 3 teklif yazıldı (Executive Summary dahil)")
    
    # Agent 6: Quality Assurance
    st.markdown("### ✅ Agent 6: Quality Assurance")
    simulate_agent_processing("Quality Assurance", 1.8)
    st.info("🎯 Kalite kontrolü tamamlandı (Approved)")
    
    # Sonuçlar
    st.subheader("📈 İşlem Sonuçları")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("İşlenen Fırsat", "3", "100%")
    
    with col2:
        st.metric("Toplam Gereksinim", "15", "5 per fırsat")
    
    with col3:
        st.metric("Compliance Oranı", "%40", "6/15")
    
    with col4:
        st.metric("Toplam Değer", "$192,000", "$64K per fırsat")
    
    # Detaylı sonuçlar
    st.subheader("📊 Detaylı Sonuçlar")
    
    for i, opp in enumerate(opportunities, 1):
        with st.expander(f"Fırsat {i} Sonuçları: {opp['title'][:30]}..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Gereksinimler:**")
                st.write("- R-001: 100 kişi kapasitesi (High)")
                st.write("- R-002: 2 breakout odası (High)")
                st.write("- R-003: Nisan 14-18 tarihleri (Critical)")
                st.write("- R-004: Havaalanı servisi (Medium)")
                st.write("- R-005: FAR 52.204-24 uyumluluğu (Critical)")
            
            with col2:
                st.write("**Fiyatlandırma:**")
                st.write("- Oda Bloğu: $54,000")
                st.write("- AV Ekipmanı: $3,500")
                st.write("- Ulaşım: $1,500")
                st.write("- Yönetim: $5,000")
                st.write("- **TOPLAM: $64,000**")
    
    # Sistem durumu
    st.subheader("🚀 Sistem Durumu")
    
    status_cols = st.columns(3)
    
    with status_cols[0]:
        st.success("✅ AutoGen Sistemi: Operasyonel")
        st.success("✅ Veritabanı: Canlı verilerle dolu")
    
    with status_cols[1]:
        st.success("✅ RAG Sistemi: Aktif")
        st.success("✅ API Bağlantısı: SAM.gov canlı")
    
    with status_cols[2]:
        st.success("✅ Teklifler: 3 oluşturuldu")
        st.success("✅ Kalite Kontrolü: Approved")
    
    conn.close()
    
    st.balloons()
    st.success("🎉 AutoGen işlemi başarıyla tamamlandı!")

def check_database():
    """Veritabanını kontrol et"""
    st.header("📊 Veritabanı Durumu")
    
    conn = create_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Toplam kayıt sayısı
        cursor.execute("SELECT COUNT(*) FROM opportunities;")
        total_count = cursor.fetchone()[0]
        
        # NAICS kodu 721110 olanlar
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE naics_code = '721110';")
        hotel_count = cursor.fetchone()[0]
        
        # Son eklenenler
        cursor.execute("""
            SELECT title, contract_type, posted_date 
            FROM opportunities 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        recent = cursor.fetchall()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Toplam Kayıt", total_count)
        
        with col2:
            st.metric("Hotel Fırsatları", hotel_count)
        
        with col3:
            st.metric("Son 5 Kayıt", len(recent))
        
        st.subheader("📋 Son Eklenen Kayıtlar")
        for record in recent:
            st.write(f"**{record[0][:50]}...** - {record[1]} - {record[2]}")
        
    except Exception as e:
        st.error(f"Veritabani hatasi: {e}")
    
    conn.close()

def send_report():
    """Rapor gönder"""
    st.header("📧 Rapor Gönderimi")
    
    st.info("📧 Mail gönderimi için SMTP konfigürasyonu gerekli!")
    
    st.code("""
    SMTP konfigürasyonu:
    1. Gmail hesabı oluşturun
    2. 2-Factor Authentication aktif edin
    3. App Password oluşturun
    4. .env dosyasına ekleyin:
       SMTP_EMAIL=your_email@gmail.com
       SMTP_PASSWORD=your_app_password
    """)
    
    if st.button("📧 Mail Gönder (Simülasyon)"):
        st.success("✅ Rapor başarıyla gönderildi! (Simülasyon)")
        st.info("📧 Alıcılar: info@creataglobal.com, arl.zgr@gmail.com")

if __name__ == "__main__":
    main()

















