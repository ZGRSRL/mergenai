#!/usr/bin/env python3
"""
Karşılaştırma/Compliance Sayfası
"""

import streamlit as st
import pandas as pd
from ui_components import page_header, sticky_action_bar, metric_card, status_badge, empty_state, skeleton_loader

def karsilastirma_compliance_page():
    """Karşılaştırma/Compliance sayfası"""
    
    # Page header
    page_header("⚖️ Karşılaştırma/Compliance", "2 notice seç → SOW farklarını ve teklif uyum boşluklarını çıkar")
    
    # Sticky action bar
    sticky_action_bar(
        ("📊 CSV İndir", "btn_csv", "secondary"),
        ("📄 PDF İndir", "btn_pdf", "secondary"),
        ("🔄 Yeniden Karşılaştır", "btn_rerun", "primary"),
        ("💾 Sonucu Kaydet", "btn_save", "secondary")
    )
    
    # Notice seçimi
    st.markdown("### 📋 Notice Seçimi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mock notice listesi
        choices = ["70LART26QPFB00001", "140D0424P0066", "31c170b76f4d", "DEMO-001", "TEST-002"]
        nid_a = st.selectbox("Notice A", choices, key="notice_a")
    
    with col2:
        nid_b = st.selectbox("Notice B", choices, key="notice_b")
    
    # Karşılaştır butonu
    if st.button("🔄 Karşılaştır", use_container_width=True):
        if nid_a and nid_b and nid_a != nid_b:
            with st.spinner("Karşılaştırma yapılıyor..."):
                # Mock compliance matrix
                mx = generate_compliance_matrix(nid_a, nid_b)
                
                if mx["status"] == "success":
                    st.success("✅ Karşılaştırma tamamlandı!")
                    
                    # Delta highlight
                    st.markdown("### 📊 Delta Analizi")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        metric_card("Oda/Gece Δ", f"{mx['delta']['room_block']:+}", "oda")
                    with col2:
                        metric_card("Kapasite Δ", f"{mx['delta']['capacity']:+}", "kişi")
                    with col3:
                        metric_card("A/V Δ", f"{mx['delta']['av_equipment']:+}", "kalem")
                    with col4:
                        metric_card("Tarih Δ", f"{mx['delta']['date_shift']:+}", "gün")
                    
                    # Compliance matrix
                    st.markdown("### 📋 Compliance Matrisi")
                    df = pd.DataFrame(mx["matrix"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Export butonları
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📊 CSV İndir",
                            mx["csv_bytes"],
                            "compliance_matrix.csv",
                            mime="text/csv"
                        )
                    with col2:
                        st.download_button(
                            "📄 PDF İndir",
                            open(mx["pdf_path"], "rb").read(),
                            "compliance_matrix.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error(f"❌ Karşılaştırma hatası: {mx.get('error', 'Bilinmeyen hata')}")
        else:
            st.warning("⚠️ Lütfen farklı iki notice seçin.")
    
    # Önceki karşılaştırmalar
    st.markdown("---")
    st.markdown("### 📚 Önceki Karşılaştırmalar")
    
    # Mock önceki karşılaştırmalar
    previous_comparisons = [
        {"notice_a": "70LART26QPFB00001", "notice_b": "140D0424P0066", "date": "2025-01-18", "status": "Tamamlandı"},
        {"notice_a": "DEMO-001", "notice_b": "TEST-002", "date": "2025-01-17", "status": "Tamamlandı"},
    ]
    
    if previous_comparisons:
        for comp in previous_comparisons:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{comp['notice_a']}**")
            with col2:
                st.write(f"**{comp['notice_b']}**")
            with col3:
                st.write(comp['date'])
            with col4:
                status_badge(comp['status'], "ok")
    else:
        empty_state(
            icon="📚",
            title="Önceki karşılaştırma yok",
            description="Henüz hiç karşılaştırma yapılmamış.",
            action_text="İlk Karşılaştırmayı Yap",
            action_key="first_comparison"
        )

def generate_compliance_matrix(nid_a, nid_b):
    """Mock compliance matrix generator"""
    import io
    import json
    from datetime import datetime
    
    # Mock delta data
    delta = {
        "room_block": 15,
        "capacity": -20,
        "av_equipment": 3,
        "date_shift": 5
    }
    
    # Mock compliance matrix
    matrix = [
        {"requirement": "Oda/Gece", "proposal_coverage": "85%", "gap": "15 oda eksik", "priority": "Yüksek"},
        {"requirement": "Genel Oturum Kapasitesi", "proposal_coverage": "90%", "gap": "20 kişi eksik", "priority": "Orta"},
        {"requirement": "A/V Ekipman", "proposal_coverage": "100%", "gap": "Yok", "priority": "Düşük"},
        {"requirement": "Breakout Odalar", "proposal_coverage": "75%", "gap": "2 oda eksik", "priority": "Yüksek"},
        {"requirement": "Catering", "proposal_coverage": "95%", "gap": "5% eksik", "priority": "Orta"},
    ]
    
    # CSV bytes
    df = pd.DataFrame(matrix)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    # Mock PDF path
    pdf_path = f"compliance_matrix_{nid_a}_{nid_b}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return {
        "status": "success",
        "delta": delta,
        "matrix": matrix,
        "csv_bytes": csv_bytes,
        "pdf_path": pdf_path
    }

