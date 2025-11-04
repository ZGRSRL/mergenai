#!/usr/bin/env python3
"""
Attachments Learn Page - Streamlit UI
"""

import streamlit as st
import json
import pandas as pd
from ui_components import page_header, sticky_action_bar, status_badge, empty_state, metric_card
from sam.knowledge.knowledge_repository import KnowledgeRepository
from sow_autogen_workflow import learn_from_attachments

def attachments_learn_page():
    """📚 Attachments → Learn sayfası"""
    
    # Page header
    page_header("📚 Attachments → Learn", "Eklerden öğren, teklife hazır bilgi üret")
    
    # Sticky action bar
    sticky_action_bar(
        ("🔄 Yeniden Öğren", "btn_relearn", "primary"),
        ("📊 Özet Görünüm", "btn_summary", "secondary"),
        ("💾 JSON İndir", "btn_download", "secondary"),
        ("🗑️ Temizle", "btn_clear", "secondary")
    )
    
    # Notice ID girişi
    st.markdown("### 📋 Notice ID Seçimi")
    
    # Mock notice listesi
    choices = ["70LART26QPFB00001", "140D0424P0066", "31c170b76f4d", "DEMO-001", "TEST-002"]
    nid = st.selectbox("Notice ID", choices, key="learn_notice_id")
    
    # Öğrenme butonu
    if st.button("🧠 Learn from Attachments", use_container_width=True):
        if nid:
            with st.spinner("Attachments'tan bilgi öğreniliyor..."):
                try:
                    result = learn_from_attachments(nid)
                    
                    if result.get("status") == "success":
                        st.success("✅ Başarıyla öğrenildi!")
                        
                        # Sonuçları göster
                        facts = result.get("facts", {})
                        
                        # Ana metrikler
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Doküman Sayısı", facts.get("meta", {}).get("total_documents", 0))
                        with col2:
                            st.metric("Toplam Sayfa", facts.get("meta", {}).get("total_pages", 0))
                        with col3:
                            st.metric("Gerekçe Sayısı", len(facts.get("rationales", [])))
                        with col4:
                            st.metric("Kaynak Sayısı", len(facts.get("citations", [])))
                        
                        # Knowledge ID'yi session state'e kaydet
                        st.session_state[f"knowledge_{nid}"] = result
                        
                    else:
                        st.error(f"❌ Öğrenme hatası: {result.get('message', 'Bilinmeyen hata')}")
                        
                except Exception as e:
                    st.error(f"❌ Hata: {e}")
        else:
            st.warning("⚠️ Lütfen bir Notice ID seçin.")
    
    # Mevcut knowledge facts'i göster
    if nid:
        st.markdown("---")
        st.markdown("### 📊 Mevcut Knowledge Facts")
        
        try:
            repo = KnowledgeRepository()
            knowledge = repo.latest(nid)
            
            if knowledge:
                st.success(f"✅ Knowledge facts bulundu (ID: {knowledge['id'][:8]}...)")
                
                # Özet bilgiler
                payload = knowledge['payload']
                
                # Requirements
                if payload.get("requirements"):
                    st.markdown("#### 📋 Requirements")
                    req_data = []
                    for key, value in payload["requirements"].items():
                        req_data.append({"Kategori": key, "Değer": str(value)})
                    if req_data:
                        st.dataframe(pd.DataFrame(req_data), use_container_width=True, hide_index=True)
                
                # Compliance
                if payload.get("compliance"):
                    st.markdown("#### ⚖️ Compliance")
                    comp_data = []
                    for key, value in payload["compliance"].items():
                        comp_data.append({"Kategori": key, "Gerekli": "✅" if value else "❌"})
                    if comp_data:
                        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
                
                # Rationales
                if payload.get("rationales"):
                    st.markdown("#### 💡 Gerekçeler")
                    for i, rationale in enumerate(payload["rationales"], 1):
                        st.write(f"{i}. {rationale}")
                
                # Citations
                if payload.get("citations"):
                    st.markdown("#### 📚 Kaynaklar")
                    for citation in payload["citations"]:
                        st.write(f"**{citation.get('file', 'N/A')}** - Sayfa: {citation.get('pages', 'N/A')}")
                
                # JSON indirme
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📄 JSON İndir",
                        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                        f"knowledge_{nid}.json",
                        mime="application/json"
                    )
                with col2:
                    if st.button("🗑️ Knowledge'ı Sil", type="secondary"):
                        if repo.delete_for_notice(nid):
                            st.success("Knowledge facts silindi")
                            st.rerun()
                        else:
                            st.error("Silme işlemi başarısız")
                
            else:
                empty_state(
                    icon="📚",
                    title="Knowledge facts bulunamadı",
                    description="Bu notice için henüz knowledge facts oluşturulmamış.",
                    action_text="Learn from Attachments",
                    action_key="learn_now"
                )
                
        except Exception as e:
            st.error(f"Knowledge yükleme hatası: {e}")
    
    # Önceki knowledge facts'ler
    if nid:
        st.markdown("---")
        st.markdown("### 📚 Önceki Knowledge Facts")
        
        try:
            repo = KnowledgeRepository()
            all_knowledge = repo.list_for_notice(nid, limit=5)
            
            if all_knowledge:
                for i, k in enumerate(all_knowledge):
                    with st.expander(f"Knowledge {i+1} - {k['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                        st.json(k['payload'])
            else:
                st.info("Önceki knowledge facts bulunamadı.")
                
        except Exception as e:
            st.error(f"Liste yükleme hatası: {e}")
    
    # Test butonu (geliştirme için)
    if st.button("🧪 Test Knowledge Builder", type="secondary"):
        st.markdown("### 🧪 Test Sonuçları")
        
        # Mock test data
        test_facts = {
            "schema_version": "sow.learn.v1",
            "meta": {
                "notice_id": nid,
                "total_documents": 3,
                "total_pages": 15
            },
            "requirements": {
                "projector_lumens_min": 5000,
                "rooms_per_night": 80,
                "capacity": 120
            },
            "compliance": {
                "fire_safety_act_1990": True,
                "sca_applicable": True
            },
            "rationales": [
                "Projector minimum brightness found as 5000 lumens in SOW attachment",
                "Fire safety compliance required per Hotel and Motel Fire Safety Act of 1990"
            ],
            "citations": [
                {"file": "SOW_Attachment.pdf", "pages": [2, 3]},
                {"file": "Fire_Safety_Requirements.pdf", "pages": [1]}
            ]
        }
        
        st.json(test_facts)
        st.success("Test data oluşturuldu!")

