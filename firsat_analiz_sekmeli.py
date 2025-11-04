#!/usr/bin/env python3
"""
Fırsat Analizi - Sekmeli Görünüm
"""

import streamlit as st
import pandas as pd
import json
from ui_components import page_header, sticky_action_bar, opportunity_card, status_badge, empty_state, status_strip
from sow_analysis_manager import SOWAnalysisManager
from agent_log_manager import AgentLogManager

def firsat_analiz_sekmeli_page():
    """Fırsat Arama ve Analiz - sekmeli görünüm"""
    
    # Page header
    page_header("📊 Fırsat Analizi", "Notice ID ile fırsat ara ve AutoGen analizini tetikle")
    
    # Sticky action bar
    sticky_action_bar(
        ("📄 SOW PDF", "btn_sow_pdf", "secondary"),
        ("📦 Kapsamlı Rapor", "btn_comp_pdf", "secondary"),
        ("🔁 Analizi Çalıştır", "btn_rerun", "primary"),
        ("💾 DB'ye Kaydet", "btn_save_db", "secondary")
    )
    
    # Notice ID girişi
    notice_id = st.text_input(
        "Notice ID Girin",
        placeholder="70LART26QPFB00001",
        help="Örneğin: 70LART26QPFB00001"
    )
    
    if notice_id:
        # Fırsat verilerini yükle
        try:
            from mock_sam_data import get_mock_opportunity_data
            opp = get_mock_opportunity_data(notice_id)
            
            if opp:
                st.success(f"Fırsat bulundu: {opp.get('title', 'N/A')}")
                
                # Sekmeli görünüm
                tabs = st.tabs(["📋 Özet", "📎 Ekler", "🤖 AutoGen", "📄 SOW", "📊 Loglar"])
                
                with tabs[0]:  # Özet
                    opportunity_card(
                        notice_id=opp.get('opportunityId', notice_id),
                        title=opp.get('title', 'Başlık yok'),
                        naics=opp.get('naicsCode', 'N/A'),
                        date=opp.get('postedDate', 'N/A')[:10] if opp.get('postedDate') else 'N/A',
                        poc=opp.get('pointOfContact', {}).get('name', 'N/A'),
                        summary=opp.get('description', 'Açıklama yok')[:200] + '...' if opp.get('description') else 'Açıklama yok'
                    )
                    
                    # Durum şeridi
                    status_strip("OK", "CONNECTED", "IDLE")
                    
                    # Ek bilgiler
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Deadline", opp.get('responseDeadLine', 'N/A')[:10] if opp.get('responseDeadLine') else 'N/A')
                    with col2:
                        st.metric("Type", opp.get('type', 'N/A'))
                    with col3:
                        st.metric("Status", opp.get('status', 'N/A'))
                
                with tabs[1]:  # Ekler
                    attachments = opp.get('attachments', [])
                    if attachments:
                        st.markdown("### 📎 Ekler")
                        for i, att in enumerate(attachments):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"**{att.get('filename', 'Ek dosyası')}**")
                                st.caption(att.get('url', 'URL mevcut değil'))
                            with col2:
                                status_badge("✅ İndirildi", "ok")
                            with col3:
                                if st.button("İndir", key=f"download_{i}"):
                                    st.info("İndirme başlatıldı")
                    else:
                        empty_state(
                            icon="📎",
                            title="Ek bulunamadı",
                            description="Bu fırsat için ek dosya bulunamadı veya henüz yüklenmedi.",
                            action_text="Ekleri Kontrol Et",
                            action_key="check_attachments"
                        )
                
                with tabs[2]:  # AutoGen
                    # AutoGen sonucunu yükle
                    result = st.session_state.get('analysis_results', {}).get(notice_id, {})
                    
                    if not result:
                        # Mock analiz sonucu
                        result = {
                            "status": "success",
                            "confidence_score": 0.85,
                            "recommendations": [
                                "SOW analizi tamamlandı",
                                "Otel önerileri hazırlandı",
                                "Bütçe tahmini oluşturuldu"
                            ],
                            "analysis_summary": "Bu fırsat için kapsamlı analiz tamamlandı."
                        }
                        st.session_state['analysis_results'] = st.session_state.get('analysis_results', {})
                        st.session_state['analysis_results'][notice_id] = result
                    
                    if result:
                        status_badge(result.get("status", "unknown").title(), 
                                   "ok" if result.get("status") == "success" else "warn")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Confidence", f"{result.get('confidence_score', 0):.2f}")
                        with col2:
                            st.metric("Recommendations", len(result.get('recommendations', [])))
                        
                        st.markdown("#### Öneriler")
                        for rec in result.get("recommendations", []):
                            st.write(f"• {rec}")
                        
                        with st.expander("Detaylı Analiz"):
                            st.json(result)
                    else:
                        empty_state(
                            icon="🤖",
                            title="AutoGen sonucu yok",
                            description="Bu fırsat için AutoGen analizi henüz çalıştırılmadı.",
                            action_text="Analizi Çalıştır",
                            action_key="run_analysis"
                        )
                
                with tabs[3]:  # SOW
                    mgr = SOWAnalysisManager()
                    sow = mgr.get_analysis(notice_id)
                    
                    if sow and 'sow_payload' in sow:
                        st.markdown("### 📄 SOW Analizi")
                        
                        # Ana alanlar kutucukları
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            period = sow['sow_payload'].get('period_of_performance', {})
                            if isinstance(period, dict):
                                period_text = f"{period.get('start', 'N/A')} - {period.get('end', 'N/A')}"
                            else:
                                period_text = str(period)
                            st.metric("Dönem", period_text)
                        
                        with col2:
                            capacity = sow['sow_payload'].get('function_space', {}).get('general_session', {}).get('capacity', 'N/A')
                            st.metric("Genel Oturum", capacity)
                        
                        with col3:
                            rooms = sow['sow_payload'].get('room_block', {}).get('total_rooms_per_night', 'N/A')
                            st.metric("Oda/Gece", rooms)
                        
                        # SOW JSON
                        with st.expander("SOW JSON"):
                            st.code(json.dumps(sow['sow_payload'], ensure_ascii=False, indent=2), language="json")
                    else:
                        empty_state(
                            icon="📄",
                            title="SOW bulunamadı",
                            description="Bu fırsat için SOW analizi bulunamadı. 'Ekleri indir + Analiz' ardından tekrar deneyin.",
                            action_text="SOW Analizi Çalıştır",
                            action_key="run_sow_analysis"
                        )
                
                with tabs[4]:  # Loglar
                    # Mock log verisi
                    logs = [
                        {"timestamp": "2025-01-18 14:32:15", "agent": "SOWParserAgent", "action": "parse_sow", "status": "success", "duration_ms": 1200},
                        {"timestamp": "2025-01-18 14:31:45", "agent": "HotelFinderAgent", "action": "find_hotels", "status": "success", "duration_ms": 800},
                        {"timestamp": "2025-01-18 14:31:20", "agent": "DocumentProcessor", "action": "extract_text", "status": "success", "duration_ms": 500},
                    ]
                    
                    if logs:
                        st.markdown("### 📊 Agent Logları")
                        df = pd.DataFrame(logs)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        empty_state(
                            icon="📊",
                            title="Log kaydı yok",
                            description="Bu fırsat için henüz log kaydı bulunamadı.",
                            action_text="Logları Kontrol Et",
                            action_key="check_logs"
                        )
            else:
                st.error(f"Fırsat bulunamadı: {notice_id}")
        except Exception as e:
            st.error(f"Veri yükleme hatası: {e}")
    else:
        st.info("Lütfen bir Notice ID girin.")

