#!/usr/bin/env python3
"""
Teklif Raporu Sayfası - Streamlit UI
"""

import streamlit as st
import json
import pandas as pd
from ui_components import page_header, sticky_action_bar, status_badge, empty_state, metric_card
from teklif_raporu_olustur import teklif_raporu_olustur

def teklif_raporu_sayfasi():
    """Teklif Raporu sayfası"""
    
    # Page header
    page_header("📋 Teklif Raporu", "SOW analizi + Otel önerileri + Bütçe + Compliance = Detaylı teklif raporu")
    
    # Sticky action bar
    sticky_action_bar(
        ("🔄 Yeniden Oluştur", "btn_regen", "primary"),
        ("📊 Özet Görünüm", "btn_summary", "secondary"),
        ("💾 JSON İndir", "btn_download", "secondary"),
        ("📄 PDF Oluştur", "btn_pdf", "secondary")
    )
    
    # Notice ID seçimi
    st.markdown("### 📋 Notice ID Seçimi")
    
    # Mock notice listesi
    choices = ["70LART26QPFB00001", "140D0424P0066", "31c170b76f4d", "DEMO-001", "TEST-002"]
    nid = st.selectbox("Notice ID", choices, key="teklif_notice_id")
    
    # Teklif raporu oluştur
    if st.button("📋 Teklif Raporu Oluştur", use_container_width=True):
        if nid:
            with st.spinner("Teklif raporu oluşturuluyor..."):
                try:
                    result = teklif_raporu_olustur(nid)
                    
                    if result.get("status") == "success":
                        st.success("✅ Teklif raporu başarıyla oluşturuldu!")
                        
                        # Raporu session state'e kaydet
                        st.session_state[f"teklif_raporu_{nid}"] = result
                        
                        # Ana metrikler
                        rapor = result['rapor']
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Otel Önerisi", rapor['hotel_recommendations']['total_found'])
                        with col2:
                            st.metric("Toplam Maliyet", f"${rapor['budget_analysis']['total_estimated_cost']:,.2f}")
                        with col3:
                            st.metric("Compliance Skoru", f"{rapor['compliance_matrix']['overall_score']:.1f}%")
                        with col4:
                            st.metric("Kritik Gereksinim", len(rapor['proposal_recommendations']['critical_requirements']))
                        
                    else:
                        st.error(f"❌ Teklif raporu oluşturma hatası: {result.get('message', 'Bilinmeyen hata')}")
                        
                except Exception as e:
                    st.error(f"❌ Hata: {e}")
        else:
            st.warning("⚠️ Lütfen bir Notice ID seçin.")
    
    # Mevcut teklif raporunu göster
    if nid and f"teklif_raporu_{nid}" in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Teklif Raporu Detayları")
        
        result = st.session_state[f"teklif_raporu_{nid}"]
        rapor = result['rapor']
        
        # Sekmeli görünüm
        tabs = st.tabs(["📋 SOW Analizi", "🏨 Otel Önerileri", "💰 Bütçe", "⚖️ Compliance", "💡 Öneriler"])
        
        with tabs[0]:  # SOW Analizi
            st.markdown("#### 📋 SOW Gereksinimleri")
            
            # Period of Performance
            if rapor['sow_analysis'].get('period_of_performance'):
                st.info(f"**Dönem:** {rapor['sow_analysis']['period_of_performance']}")
            
            # Room Requirements
            if rapor['sow_analysis'].get('room_requirements'):
                room_req = rapor['sow_analysis']['room_requirements']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Oda/Gece", room_req.get('total_rooms_per_night', 'N/A'))
                with col2:
                    st.metric("Gece Sayısı", room_req.get('nights', 'N/A'))
                with col3:
                    st.metric("Attrition", room_req.get('attrition_policy', 'N/A'))
            
            # Capacity Requirements
            if rapor['sow_analysis'].get('capacity_requirements'):
                cap_req = rapor['sow_analysis']['capacity_requirements']
                if cap_req.get('general_session'):
                    gs = cap_req['general_session']
                    st.write(f"**Genel Oturum:** {gs.get('capacity', 'N/A')} kişi, {gs.get('setup', 'N/A')} setup")
                
                if cap_req.get('breakout_rooms'):
                    br = cap_req['breakout_rooms']
                    st.write(f"**Breakout Odalar:** {br.get('count', 'N/A')} oda, her biri {br.get('capacity_each', 'N/A')} kişi")
            
            # A/V Requirements
            if rapor['sow_analysis'].get('av_requirements'):
                av_req = rapor['sow_analysis']['av_requirements']
                st.write(f"**A/V Gereksinimleri:**")
                st.write(f"- Projektör: {av_req.get('projector_lumens', 'N/A')} lumen")
                st.write(f"- Adaptörler: {', '.join(av_req.get('adapters', []))}")
                st.write(f"- Güç şeridi: {av_req.get('power_strips_min', 'N/A')} adet")
        
        with tabs[1]:  # Otel Önerileri
            st.markdown("#### 🏨 Otel Önerileri")
            
            hotels = rapor['hotel_recommendations']
            if hotels['total_found'] > 0:
                st.success(f"✅ {hotels['total_found']} otel önerisi bulundu")
                
                # Otel listesi
                for i, hotel in enumerate(hotels['top_recommendations'][:5], 1):
                    with st.expander(f"Otel {i}: {hotel.get('name', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Adres:** {hotel.get('address', 'N/A')}")
                            st.write(f"**Telefon:** {hotel.get('phone', 'N/A')}")
                        with col2:
                            st.write(f"**Mesafe:** {hotel.get('distance_km', 'N/A')} km")
                            st.write(f"**Skor:** {hotel.get('match_score', 'N/A')}")
            else:
                empty_state(
                    icon="🏨",
                    title="Otel önerisi bulunamadı",
                    description="Bu notice için henüz otel araştırması yapılmamış.",
                    action_text="Otel Araştır",
                    action_key="search_hotels"
                )
        
        with tabs[2]:  # Bütçe
            st.markdown("#### 💰 Bütçe Analizi")
            
            budget = rapor['budget_analysis']
            if budget.get('total_estimated_cost', 0) > 0:
                st.success(f"✅ Bütçe tahmini: ${budget['total_estimated_cost']:,.2f}")
                
                # Breakdown
                if budget.get('breakdown'):
                    st.markdown("**Maliyet Dağılımı:**")
                    breakdown_data = []
                    for category, amount in budget['breakdown'].items():
                        breakdown_data.append({"Kategori": category, "Miktar": f"${amount:,.2f}"})
                    
                    if breakdown_data:
                        st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)
                
                # Assumptions
                if budget.get('assumptions'):
                    with st.expander("Varsayımlar"):
                        st.json(budget['assumptions'])
            else:
                empty_state(
                    icon="💰",
                    title="Bütçe tahmini yok",
                    description="Bu notice için henüz bütçe tahmini yapılmamış.",
                    action_text="Bütçe Tahmini Yap",
                    action_key="estimate_budget"
                )
        
        with tabs[3]:  # Compliance
            st.markdown("#### ⚖️ Compliance Matrix")
            
            compliance = rapor['compliance_matrix']
            if compliance.get('overall_score', 0) > 0:
                st.success(f"✅ Compliance skoru: {compliance['overall_score']:.1f}%")
                
                # Requirements coverage
                if compliance.get('requirements_coverage'):
                    st.markdown("**Gereksinim Kapsamı:**")
                    coverage_data = []
                    for req, coverage in compliance['requirements_coverage'].items():
                        coverage_data.append({"Gereksinim": req, "Kapsam": f"{coverage:.1f}%"})
                    
                    if coverage_data:
                        st.dataframe(pd.DataFrame(coverage_data), use_container_width=True, hide_index=True)
                
                # Gaps
                if compliance.get('gaps'):
                    st.markdown("**Eksiklikler:**")
                    for gap in compliance['gaps']:
                        st.write(f"• {gap}")
            else:
                empty_state(
                    icon="⚖️",
                    title="Compliance analizi yok",
                    description="Bu notice için henüz compliance analizi yapılmamış.",
                    action_text="Compliance Analizi Yap",
                    action_key="analyze_compliance"
                )
        
        with tabs[4]:  # Öneriler
            st.markdown("#### 💡 Teklif Önerileri")
            
            recommendations = rapor['proposal_recommendations']
            
            # Kritik gereksinimler
            if recommendations.get('critical_requirements'):
                st.markdown("**🚨 Kritik Gereksinimler:**")
                for req in recommendations['critical_requirements']:
                    st.write(f"• {req}")
            
            # Fiyatlandırma stratejisi
            if recommendations.get('pricing_strategy'):
                st.markdown("**💰 Fiyatlandırma Stratejisi:**")
                for strategy in recommendations['pricing_strategy']:
                    st.write(f"• {strategy}")
            
            # Risk faktörleri
            if recommendations.get('risk_factors'):
                st.markdown("**⚠️ Risk Faktörleri:**")
                for risk in recommendations['risk_factors']:
                    st.write(f"• {risk}")
            
            # Rekabet avantajları
            if recommendations.get('competitive_advantages'):
                st.markdown("**🏆 Rekabet Avantajları:**")
                for advantage in recommendations['competitive_advantages']:
                    st.write(f"• {advantage}")
        
        # JSON indirme
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📄 JSON İndir",
                json.dumps(rapor, ensure_ascii=False, indent=2).encode("utf-8"),
                f"teklif_raporu_{nid}.json",
                mime="application/json"
            )
        with col2:
            st.info(f"📁 Dosya: {result['rapor_dosyasi']}")
    
    else:
        empty_state(
            icon="📋",
            title="Teklif raporu bulunamadı",
            description="Bu notice için henüz teklif raporu oluşturulmamış.",
            action_text="Teklif Raporu Oluştur",
            action_key="create_proposal_report"
        )

