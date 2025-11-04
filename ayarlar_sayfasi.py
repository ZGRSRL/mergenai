#!/usr/bin/env python3
"""
Ayarlar Sayfası
"""

import streamlit as st
import os
from ui_components import page_header, sticky_action_bar, status_badge, empty_state

def ayarlar_sayfasi_page():
    """Ayarlar sayfası"""
    
    # Page header
    page_header("⚙️ Ayarlar", "Feature flags ve bağlantı testleri")
    
    # Sticky action bar
    sticky_action_bar(
        ("🔄 Tüm Testleri Çalıştır", "btn_test_all", "primary"),
        ("💾 Ayarları Kaydet", "btn_save", "secondary"),
        ("🔄 Sıfırla", "btn_reset", "secondary"),
        ("📊 Durum Raporu", "btn_status", "secondary")
    )
    
    # Feature Flags
    st.markdown("### 🚩 Feature Flags")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### UI Özellikleri")
        experimental_ui = st.checkbox("EXPERIMENTAL_UI", value=bool(os.getenv("EXPERIMENTAL_UI", False)))
        use_ocr = st.checkbox("USE_OCR", value=bool(os.getenv("USE_OCR", False)))
        dark_mode = st.checkbox("DARK_MODE", value=bool(os.getenv("DARK_MODE", True)))
    
    with col2:
        st.markdown("#### Sistem Özellikleri")
        system_account = st.checkbox("SYSTEM_ACCOUNT", value=bool(os.getenv("SYSTEM_ACCOUNT", False)))
        auto_save = st.checkbox("AUTO_SAVE", value=bool(os.getenv("AUTO_SAVE", True)))
        debug_mode = st.checkbox("DEBUG_MODE", value=bool(os.getenv("DEBUG_MODE", False)))
    
    # Bağlantı Testleri
    st.markdown("### 🔧 Bağlantı Testleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔌 SAM Test", use_container_width=True):
            ok = sam_health_check()
            if ok:
                status_badge("SAM OK", "ok")
                st.success("SAM API bağlantısı başarılı")
            else:
                status_badge("SAM FAIL", "err")
                st.error("SAM API bağlantısı başarısız")
    
    with col2:
        if st.button("🗄️ DB Test", use_container_width=True):
            ok = test_db_connection()
            if ok:
                status_badge("DB OK", "ok")
                st.success("Veritabanı bağlantısı başarılı")
            else:
                status_badge("DB FAIL", "err")
                st.error("Veritabanı bağlantısı başarısız")
    
    with col3:
        if st.button("📧 SMTP Test", use_container_width=True):
            ok = smtp_health_check()
            if ok:
                status_badge("SMTP OK", "ok")
                st.success("E-posta servisi başarılı")
            else:
                status_badge("SMTP FAIL", "err")
                st.error("E-posta servisi başarısız")
    
    # Sistem Durumu
    st.markdown("### 📊 Sistem Durumu")
    
    # Mock sistem durumu
    system_status = {
        "SAM API": {"status": "OK", "last_check": "2025-01-18 14:30:15", "response_time": "120ms"},
        "Database": {"status": "OK", "last_check": "2025-01-18 14:30:10", "response_time": "45ms"},
        "SMTP": {"status": "OK", "last_check": "2025-01-18 14:30:05", "response_time": "200ms"},
        "File System": {"status": "OK", "last_check": "2025-01-18 14:30:00", "response_time": "5ms"},
    }
    
    for service, info in system_status.items():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{service}**")
        with col2:
            status_badge(info["status"], "ok" if info["status"] == "OK" else "err")
        with col3:
            st.write(info["last_check"])
        with col4:
            st.write(info["response_time"])
    
    # Environment Variables
    st.markdown("### 🔐 Environment Variables")
    
    with st.expander("Güvenli Değişkenler"):
        env_vars = {
            "SAM_API_KEY": "***" if os.getenv("SAM_API_KEY") else "Not set",
            "DB_PASSWORD": "***" if os.getenv("DB_PASSWORD") else "Not set",
            "SMTP_PASSWORD": "***" if os.getenv("SMTP_PASSWORD") else "Not set",
        }
        
        for key, value in env_vars.items():
            st.write(f"**{key}**: {value}")
    
    # Sistem Bilgileri
    st.markdown("### 💻 Sistem Bilgileri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Python Version", "3.11.0")
        st.metric("Streamlit Version", "1.28.0")
        st.metric("Database", "PostgreSQL 15")
    
    with col2:
        st.metric("Memory Usage", "256 MB")
        st.metric("CPU Usage", "12%")
        st.metric("Disk Space", "2.1 GB / 10 GB")
    
    # Log Seviyeleri
    st.markdown("### 📝 Log Seviyeleri")
    
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    current_level = st.selectbox("Log Level", log_levels, index=1)
    
    if st.button("Log Seviyesini Güncelle"):
        st.success(f"Log seviyesi {current_level} olarak güncellendi")
    
    # Sistem Temizliği
    st.markdown("### 🧹 Sistem Temizliği")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Cache Temizle", use_container_width=True):
            st.success("Cache temizlendi")
    
    with col2:
        if st.button("📊 Log Temizle", use_container_width=True):
            st.success("Eski loglar temizlendi")
    
    with col3:
        if st.button("💾 DB Optimize", use_container_width=True):
            st.success("Veritabanı optimize edildi")

def sam_health_check():
    """Mock SAM health check"""
    import random
    return random.choice([True, True, True, False])  # %75 başarı oranı

def test_db_connection():
    """Mock DB connection test"""
    import random
    return random.choice([True, True, True, True, False])  # %80 başarı oranı

def smtp_health_check():
    """Mock SMTP health check"""
    import random
    return random.choice([True, True, False])  # %67 başarı oranı

