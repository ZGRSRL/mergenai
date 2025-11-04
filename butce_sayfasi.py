#!/usr/bin/env python3
"""
Bütçe Sayfası
"""

import streamlit as st
import pandas as pd
import json
from ui_components import page_header, sticky_action_bar, metric_card, status_badge, empty_state

def butce_sayfasi_page():
    """Bütçe sayfası"""
    
    # Page header
    page_header("💰 Bütçe", "SOW'dan otomatik 'light' bütçe tahmini + varsayımlar")
    
    # Sticky action bar
    sticky_action_bar(
        ("📊 CSV İndir", "btn_csv", "secondary"),
        ("📄 PDF İndir", "btn_pdf", "secondary"),
        ("🔄 Yeniden Hesapla", "btn_recalc", "primary"),
        ("💾 Kaydet", "btn_save", "secondary")
    )
    
    # Notice seçimi
    st.markdown("### 📋 Notice Seçimi")
    
    # Mock notice listesi
    choices = ["70LART26QPFB00001", "140D0424P0066", "31c170b76f4d", "DEMO-001", "TEST-002"]
    nid = st.selectbox("Notice ID", choices)
    
    # Bütçe tahmini oluştur
    if st.button("💰 Tahmin Oluştur", use_container_width=True):
        with st.spinner("Bütçe tahmini hesaplanıyor..."):
            b = estimate_budget(nid)
            
            if b["status"] == "success":
                st.success("✅ Bütçe tahmini oluşturuldu!")
                
                # Ana metrikler
                st.markdown("### 💰 Bütçe Özeti")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    metric_card("Toplam", f"${b['total']:,.2f}", "USD")
                with col2:
                    metric_card("Konaklama", f"${b['lodging']:,.2f}", "USD")
                with col3:
                    metric_card("A/V + Diğer", f"${b['av'] + b['other']:,.2f}", "USD")
                
                # Detaylı breakdown
                st.markdown("### 📊 Detaylı Breakdown")
                
                breakdown_data = [
                    {"Kategori": "Konaklama", "Miktar": f"${b['lodging']:,.2f}", "Açıklama": f"{b['parameters']['rooms_per_night']} oda × {b['parameters']['total_nights']} gece"},
                    {"Kategori": "A/V Ekipman", "Miktar": f"${b['av']:,.2f}", "Açıklama": f"{b['parameters']['duration_days']} gün"},
                    {"Kategori": "Catering", "Miktar": f"${b['catering']:,.2f}", "Açıklama": f"{b['parameters']['capacity']} kişi × {b['parameters']['duration_days']} gün"},
                    {"Kategori": "Toplantı Odaları", "Miktar": f"${b['meeting_rooms']:,.2f}", "Açıklama": f"{b['parameters']['breakout_rooms']} oda × {b['parameters']['duration_days']} gün"},
                    {"Kategori": "Kurulum", "Miktar": f"${b['setup']:,.2f}", "Açıklama": "Tek seferlik"},
                    {"Kategori": "Vergi", "Miktar": f"${b['tax']:,.2f}", "Açıklama": f"{b['pricing_rates']['tax_rate']*100:.1f}%"},
                ]
                
                df = pd.DataFrame(breakdown_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Varsayımlar
                with st.expander("🔧 Varsayımlar"):
                    st.json(b["assumptions"])
                
                # Export butonları
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📊 CSV İndir",
                        b["csv_bytes"],
                        "budget_estimate.csv",
                        mime="text/csv"
                    )
                with col2:
                    st.download_button(
                        "📄 PDF İndir",
                        open(b["pdf_path"], "rb").read(),
                        "budget_estimate.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error(f"❌ Bütçe tahmini hatası: {b.get('error', 'Bilinmeyen hata')}")
    
    # Önceki tahminler
    st.markdown("---")
    st.markdown("### 📚 Önceki Tahminler")
    
    # Mock önceki tahminler
    previous_estimates = [
        {"notice_id": "70LART26QPFB00001", "total": 35640.00, "date": "2025-01-18", "status": "Tamamlandı"},
        {"notice_id": "140D0424P0066", "total": 28950.00, "date": "2025-01-17", "status": "Tamamlandı"},
    ]
    
    if previous_estimates:
        for est in previous_estimates:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{est['notice_id']}**")
            with col2:
                st.write(f"**${est['total']:,.2f}**")
            with col3:
                st.write(est['date'])
            with col4:
                status_badge(est['status'], "ok")
    else:
        empty_state(
            icon="📚",
            title="Önceki tahmin yok",
            description="Henüz hiç bütçe tahmini yapılmamış.",
            action_text="İlk Tahmini Yap",
            action_key="first_estimate"
        )

def estimate_budget(notice_id):
    """Mock budget estimator"""
    import io
    from datetime import datetime
    
    # Mock parameters
    parameters = {
        "rooms_per_night": 80,
        "total_nights": 3,
        "capacity": 120,
        "duration_days": 3,
        "breakout_rooms": 4
    }
    
    # Mock pricing rates
    pricing_rates = {
        "room_rate_per_night": 150.0,
        "av_rate_per_day": 500.0,
        "catering_rate_per_person_per_day": 45.0,
        "meeting_room_rate_per_day": 200.0,
        "setup_fee": 1000.0,
        "tax_rate": 0.08
    }
    
    # Hesaplamalar
    lodging = parameters["rooms_per_night"] * parameters["total_nights"] * pricing_rates["room_rate_per_night"]
    av = parameters["duration_days"] * pricing_rates["av_rate_per_day"]
    catering = parameters["capacity"] * parameters["duration_days"] * pricing_rates["catering_rate_per_person_per_day"]
    meeting_rooms = parameters["breakout_rooms"] * parameters["duration_days"] * pricing_rates["meeting_room_rate_per_day"]
    setup = pricing_rates["setup_fee"]
    
    subtotal = lodging + av + catering + meeting_rooms + setup
    tax = subtotal * pricing_rates["tax_rate"]
    total = subtotal + tax
    
    # Breakdown items
    items = [
        {"Kategori": "Konaklama", "Miktar": lodging, "Açıklama": f"{parameters['rooms_per_night']} oda × {parameters['total_nights']} gece"},
        {"Kategori": "A/V Ekipman", "Miktar": av, "Açıklama": f"{parameters['duration_days']} gün"},
        {"Kategori": "Catering", "Miktar": catering, "Açıklama": f"{parameters['capacity']} kişi × {parameters['duration_days']} gün"},
        {"Kategori": "Toplantı Odaları", "Miktar": meeting_rooms, "Açıklama": f"{parameters['breakout_rooms']} oda × {parameters['duration_days']} gün"},
        {"Kategori": "Kurulum", "Miktar": setup, "Açıklama": "Tek seferlik"},
        {"Kategori": "Vergi", "Miktar": tax, "Açıklama": f"{pricing_rates['tax_rate']*100:.1f}%"},
    ]
    
    # CSV bytes
    df = pd.DataFrame(items)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    # Mock PDF path
    pdf_path = f"budget_estimate_{notice_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Assumptions
    assumptions = {
        "room_rate_source": "Ortalama piyasa fiyatı",
        "av_rate_source": "Standart A/V kiralama",
        "catering_rate_source": "Ortalama catering maliyeti",
        "tax_rate_source": "Yerel vergi oranı",
        "currency": "USD",
        "validity_period": "30 gün"
    }
    
    return {
        "status": "success",
        "total": total,
        "lodging": lodging,
        "av": av,
        "catering": catering,
        "meeting_rooms": meeting_rooms,
        "setup": setup,
        "tax": tax,
        "subtotal": subtotal,
        "parameters": parameters,
        "pricing_rates": pricing_rates,
        "items": items,
        "assumptions": assumptions,
        "csv_bytes": csv_bytes,
        "pdf_path": pdf_path
    }

