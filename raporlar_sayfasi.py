#!/usr/bin/env python3
"""
Raporlar Sayfası
"""

import streamlit as st
import os
from ui_components import page_header, sticky_action_bar, status_badge, empty_state

def raporlar_sayfasi_page():
    """Raporlar sayfası"""
    
    # Page header
    page_header("📋 Raporlar", "Tek yerden çıktı üretimi")
    
    # Sticky action bar
    sticky_action_bar(
        ("📄 SOW PDF", "btn_sow_pdf", "secondary"),
        ("📦 ZIP İndir", "btn_zip", "secondary"),
        ("🔄 Yeniden Oluştur", "btn_regen", "primary"),
        ("💾 Kaydet", "btn_save", "secondary")
    )
    
    # Notice seçimi
    st.markdown("### 📋 Notice Seçimi")
    
    # Mock notice listesi
    choices = ["70LART26QPFB00001", "140D0424P0066", "31c170b76f4d", "DEMO-001", "TEST-002"]
    nid = st.selectbox("Notice ID", choices)
    
    # Bölüm seçimi
    st.markdown("### 📊 Rapor Bölümleri")
    
    sections = st.multiselect(
        "Hangi bölümleri dahil etmek istiyorsunuz?",
        ["SOW", "Hotels", "Budget", "Compliance", "Logs"],
        default=["SOW", "Hotels", "Budget"],
        help="Seçilen bölümler kapsamlı raporda yer alacak"
    )
    
    # Rapor oluştur
    if st.button("📊 Kapsamlı Rapor Oluştur", use_container_width=True):
        if nid and sections:
            with st.spinner("Kapsamlı rapor oluşturuluyor..."):
                try:
                    from comprehensive_report_generator import ComprehensiveReportGenerator
                    generator = ComprehensiveReportGenerator()
                    
                    # Mock rapor oluşturma
                    path = generate_comprehensive_report(nid, sections)
                    
                    if path and os.path.exists(path):
                        st.success("✅ Kapsamlı rapor oluşturuldu!")
                        
                        # Rapor bilgileri
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Dosya Boyutu", f"{os.path.getsize(path) / 1024:.1f} KB")
                        with col2:
                            st.metric("Bölüm Sayısı", len(sections))
                        with col3:
                            st.metric("Durum", "Hazır")
                        
                        # İndirme butonu
                        with open(path, "rb") as pdf_file:
                            st.download_button(
                                "📄 PDF İndir",
                                pdf_file.read(),
                                os.path.basename(path),
                                mime="application/pdf"
                            )
                        
                        # Rapor önizleme
                        with st.expander("📄 Rapor Önizleme"):
                            st.info("PDF önizleme burada görünecek")
                    else:
                        st.error("❌ Rapor oluşturulamadı")
                except Exception as e:
                    st.error(f"❌ Rapor oluşturma hatası: {e}")
        else:
            st.warning("⚠️ Lütfen notice ID ve en az bir bölüm seçin.")
    
    # Önceki raporlar
    st.markdown("---")
    st.markdown("### 📚 Önceki Raporlar")
    
    # Mock önceki raporlar
    previous_reports = [
        {"notice_id": "70LART26QPFB00001", "sections": "SOW, Hotels, Budget", "date": "2025-01-18", "size": "2.3 MB", "status": "Hazır"},
        {"notice_id": "140D0424P0066", "sections": "SOW, Compliance", "date": "2025-01-17", "size": "1.8 MB", "status": "Hazır"},
    ]
    
    if previous_reports:
        for report in previous_reports:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            with col1:
                st.write(f"**{report['notice_id']}**")
            with col2:
                st.write(report['sections'])
            with col3:
                st.write(report['date'])
            with col4:
                st.write(report['size'])
            with col5:
                status_badge(report['status'], "ok")
    else:
        empty_state(
            icon="📚",
            title="Önceki rapor yok",
            description="Henüz hiç rapor oluşturulmamış.",
            action_text="İlk Raporu Oluştur",
            action_key="first_report"
        )

def generate_comprehensive_report(notice_id, sections):
    """Mock comprehensive report generator"""
    from datetime import datetime
    
    # Mock rapor dosya adı
    filename = f"Comprehensive_Report_{notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = filename
    
    # Mock PDF oluşturma (gerçekte ComprehensiveReportGenerator kullanılacak)
    with open(path, "w") as f:
        f.write(f"Mock PDF for {notice_id} with sections: {', '.join(sections)}")
    
    return path

