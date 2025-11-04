#!/usr/bin/env python3
"""
Detaylı Fırsat Görüntüleyici - Streamlit Uygulaması
"""

import streamlit as st
import sys
import os
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection
from datetime import datetime, date
import pandas as pd

def get_opportunity_details(opportunity_id):
    """Belirli bir fırsatın detaylarını al"""
    conn = create_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, opportunity_id, title, description, posted_date, 
                   contract_type, naics_code, organization_type, created_at,
                   solicitation_number, set_aside, response_deadline,
                   estimated_value, place_of_performance
            FROM opportunities 
            WHERE id = %s;
        """, (opportunity_id,))
        
        record = cursor.fetchone()
        if record:
            return {
                'id': record[0],
                'opportunity_id': record[1],
                'title': record[2],
                'description': record[3],
                'posted_date': record[4],
                'contract_type': record[5],
                'naics_code': record[6],
                'organization_type': record[7],
                'created_at': record[8],
                'solicitation_number': record[9],
                'set_aside': record[10],
                'response_deadline': record[11],
                'estimated_value': record[12],
                'place_of_performance': record[13]
            }
        return None
    except Exception as e:
        st.error(f"Veri alma hatası: {e}")
        return None
    finally:
        conn.close()

def get_all_opportunities_summary():
    """Tüm fırsatların özetini al"""
    conn = create_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, opportunity_id, title, posted_date, contract_type, 
                   naics_code, organization_type, created_at
            FROM opportunities 
            ORDER BY created_at DESC;
        """)
        
        records = cursor.fetchall()
        opportunities = []
        for record in records:
            opportunities.append({
                'id': record[0],
                'opportunity_id': record[1],
                'title': record[2],
                'posted_date': record[3],
                'contract_type': record[4],
                'naics_code': record[5],
                'organization_type': record[6],
                'created_at': record[7]
            })
        return opportunities
    except Exception as e:
        st.error(f"Veri alma hatası: {e}")
        return []
    finally:
        conn.close()

def main():
    st.set_page_config(
        page_title="ZgrSam Fırsat Detayları",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("📋 ZgrSam Fırsat Detayları")
    st.markdown("---")
    
    # Fırsat listesi
    st.subheader("📊 Tüm Fırsatlar")
    
    opportunities = get_all_opportunities_summary()
    
    if not opportunities:
        st.warning("Veritabanında fırsat bulunamadı!")
        return
    
    # Fırsat seçimi
    opportunity_titles = [f"{opp['opportunity_id']} - {opp['title'][:50]}..." for opp in opportunities]
    selected_index = st.selectbox(
        "Fırsat Seçin:",
        range(len(opportunity_titles)),
        format_func=lambda x: opportunity_titles[x]
    )
    
    if selected_index is not None:
        selected_opportunity = opportunities[selected_index]
        
        # Detaylı bilgileri al
        details = get_opportunity_details(selected_opportunity['id'])
        
        if details:
            st.markdown("---")
            st.subheader("📄 Fırsat Detayları")
            
            # Ana bilgiler
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏷️ Temel Bilgiler")
                st.write(f"**Fırsat ID:** {details['opportunity_id']}")
                st.write(f"**Başlık:** {details['title']}")
                st.write(f"**Sözleşme Tipi:** {details['contract_type'] or 'N/A'}")
                st.write(f"**NAICS Kodu:** {details['naics_code'] or 'N/A'}")
                st.write(f"**Organizasyon Tipi:** {details['organization_type'] or 'N/A'}")
            
            with col2:
                st.markdown("### 📅 Tarih Bilgileri")
                st.write(f"**Yayın Tarihi:** {details['posted_date'] or 'N/A'}")
                st.write(f"**Sistem Kayıt Tarihi:** {details['created_at']}")
                st.write(f"**Yanıt Son Tarihi:** {details['response_deadline'] or 'N/A'}")
                st.write(f"**Tahmini Değer:** {details['estimated_value'] or 'N/A'}")
                st.write(f"**Set Aside:** {details['set_aside'] or 'N/A'}")
            
            # Açıklama
            st.markdown("### 📝 Açıklama")
            if details['description']:
                st.text_area(
                    "Fırsat Açıklaması:",
                    details['description'],
                    height=300,
                    disabled=True
                )
            else:
                st.info("Bu fırsat için açıklama bulunmuyor.")
            
            # Performans Yeri
            if details['place_of_performance']:
                st.markdown("### 📍 Performans Yeri")
                st.write(details['place_of_performance'])
            
            # Solicitation Number
            if details['solicitation_number']:
                st.markdown("### 🔢 Solicitation Number")
                st.write(details['solicitation_number'])
            
            # Ham veri görüntüleme
            with st.expander("🔍 Ham Veri (JSON)"):
                st.json(details)
        
        else:
            st.error("Fırsat detayları alınamadı!")
    
    # İstatistikler
    st.markdown("---")
    st.subheader("📈 İstatistikler")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Fırsat", len(opportunities))
    
    with col2:
        today_count = len([opp for opp in opportunities if opp['created_at'].date() == date.today()])
        st.metric("Bugün Eklenen", today_count)
    
    with col3:
        contract_types = {}
        for opp in opportunities:
            ct = opp['contract_type'] or 'Bilinmiyor'
            contract_types[ct] = contract_types.get(ct, 0) + 1
        most_common_type = max(contract_types.items(), key=lambda x: x[1])[0] if contract_types else 'N/A'
        st.metric("En Yaygın Tip", most_common_type)
    
    with col4:
        org_types = {}
        for opp in opportunities:
            ot = opp['organization_type'] or 'Bilinmiyor'
            org_types[ot] = org_types.get(ot, 0) + 1
        most_common_org = max(org_types.items(), key=lambda x: x[1])[0] if org_types else 'N/A'
        st.metric("En Yaygın Org", most_common_org)
    
    # Fırsat tablosu
    st.markdown("---")
    st.subheader("📊 Fırsat Tablosu")
    
    df = pd.DataFrame(opportunities)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d.%m.%Y %H:%M')
    df['posted_date'] = pd.to_datetime(df['posted_date']).dt.strftime('%d.%m.%Y') if df['posted_date'].notna().any() else 'N/A'
    
    st.dataframe(
        df[['opportunity_id', 'title', 'contract_type', 'posted_date', 'created_at']],
        use_container_width=True,
        height=400
    )

if __name__ == "__main__":
    main()
