#!/usr/bin/env python3
"""
Basit AutoGen Demo - Gerçek Verilerle
"""

import sys
import os
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities
from datetime import datetime

def simple_autogen_demo():
    """Basit AutoGen demo'su - gerçek verilerle"""
    
    print("=== ZgrSam Basit AutoGen Demo ===")
    print(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print()
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("[ERROR] Veritabani baglantisi basarisiz!")
        return
    
    # Canlı fırsatları al
    opportunities = get_live_sam_opportunities(conn, limit=3)
    if not opportunities:
        print("[ERROR] Hic firsat bulunamadi!")
        conn.close()
        return
    
    print(f"[OK] {len(opportunities)} gercek firsat alindi:")
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp['title'][:60]}...")
    print()
    
    # Her fırsat için basit analiz
    for opp_idx, opp in enumerate(opportunities, 1):
        print(f"[TARGET] Firsat {opp_idx}: {opp['title'][:50]}...")
        print("-" * 60)
        
        # Temel bilgiler
        print(f"[INFO] Firsat ID: {opp['opportunity_id']}")
        print(f"[INFO] Sözlesme Tipi: {opp['contract_type'] or 'N/A'}")
        print(f"[INFO] NAICS Kodu: {opp['naics_code'] or 'N/A'}")
        print(f"[INFO] Organizasyon: {opp['organization_type'] or 'N/A'}")
        print(f"[INFO] Yayin Tarihi: {opp['posted_date']}")
        
        # Açıklama analizi
        description = opp['description'] or opp['title']
        print(f"[INFO] Aciklama Uzunlugu: {len(description)} karakter")
        
        # Basit gereksinim analizi
        print("[ANALYSIS] Gereksinim analizi yapiliyor...")
        
        # Anahtar kelime analizi
        keywords = ['conference', 'meeting', 'hotel', 'venue', 'capacity', 'room', 'event', 'seminar', 'training']
        found_keywords = [kw for kw in keywords if kw.lower() in description.lower()]
        print(f"[ANALYSIS] Bulunan anahtar kelimeler: {', '.join(found_keywords) if found_keywords else 'Yok'}")
        
        # Kapasite analizi
        import re
        capacity_matches = re.findall(r'(\d+)\s*(?:person|people|attendee|capacity|guest)', description.lower())
        if capacity_matches:
            print(f"[ANALYSIS] Tespit edilen kapasite: {max(capacity_matches)} kişi")
        else:
            print("[ANALYSIS] Kapasite bilgisi bulunamadı")
        
        # Tarih analizi
        date_matches = re.findall(r'(?:april|may|june|july|august|september|october|november|december|january|february|march)\s+\d{1,2}', description.lower())
        if date_matches:
            print(f"[ANALYSIS] Tespit edilen tarihler: {', '.join(date_matches[:3])}")
        else:
            print("[ANALYSIS] Tarih bilgisi bulunamadı")
        
        # Konum analizi
        location_keywords = ['washington', 'dc', 'virginia', 'maryland', 'california', 'texas', 'florida', 'new york']
        found_locations = [loc for loc in location_keywords if loc.lower() in description.lower()]
        if found_locations:
            print(f"[ANALYSIS] Tespit edilen konumlar: {', '.join(found_locations)}")
        else:
            print("[ANALYSIS] Konum bilgisi bulunamadı")
        
        # Basit fiyatlandırma simülasyonu
        print("[PRICING] Fiyatlandirma simülasyonu...")
        base_price = 50000
        capacity_factor = 1.0
        if capacity_matches:
            capacity = int(max(capacity_matches))
            if capacity > 100:
                capacity_factor = capacity / 100
        location_factor = 1.2 if 'washington' in description.lower() or 'dc' in description.lower() else 1.0
        
        estimated_price = base_price * capacity_factor * location_factor
        print(f"[PRICING] Tahmini fiyat: ${estimated_price:,.2f}")
        print(f"[PRICING] Kapasite faktörü: {capacity_factor:.2f}")
        print(f"[PRICING] Konum faktörü: {location_factor:.2f}")
        
        # Compliance simülasyonu
        print("[COMPLIANCE] Uyumluluk analizi...")
        compliance_score = 0
        total_checks = 5
        
        # FAR uyumluluğu kontrolü
        if 'far' in description.lower() or 'federal' in description.lower():
            compliance_score += 1
            print("[COMPLIANCE] FAR uyumlulugu: OK")
        else:
            print("[COMPLIANCE] FAR uyumlulugu: NO")
        
        # Kapasite belirtilmiş mi?
        if capacity_matches:
            compliance_score += 1
            print("[COMPLIANCE] Kapasite belirtilmis: OK")
        else:
            print("[COMPLIANCE] Kapasite belirtilmis: NO")
        
        # Tarih belirtilmiş mi?
        if date_matches:
            compliance_score += 1
            print("[COMPLIANCE] Tarih belirtilmis: OK")
        else:
            print("[COMPLIANCE] Tarih belirtilmis: NO")
        
        # Konum belirtilmiş mi?
        if found_locations:
            compliance_score += 1
            print("[COMPLIANCE] Konum belirtilmis: OK")
        else:
            print("[COMPLIANCE] Konum belirtilmis: NO")
        
        # Teknik gereksinimler var mı?
        tech_keywords = ['av', 'audio', 'visual', 'equipment', 'setup', 'technical']
        if any(tech in description.lower() for tech in tech_keywords):
            compliance_score += 1
            print("[COMPLIANCE] Teknik gereksinimler: OK")
        else:
            print("[COMPLIANCE] Teknik gereksinimler: NO")
        
        compliance_rate = (compliance_score / total_checks) * 100
        print(f"[COMPLIANCE] Uyumluluk orani: {compliance_rate:.1f}% ({compliance_score}/{total_checks})")
        
        # Kalite değerlendirmesi
        print("[QUALITY] Kalite degerlendirmesi...")
        quality_score = 0
        if len(description) > 500:
            quality_score += 1
        if capacity_matches:
            quality_score += 1
        if date_matches:
            quality_score += 1
        if found_locations:
            quality_score += 1
        if compliance_rate >= 60:
            quality_score += 1
        
        quality_status = "Yuksek" if quality_score >= 4 else "Orta" if quality_score >= 2 else "Dusuk"
        print(f"[QUALITY] Kalite durumu: {quality_status} ({quality_score}/5)")
        
        print(f"[OK] Firsat {opp_idx} analizi tamamlandi!")
        print("=" * 60)
        print()
    
    # Genel sonuçlar
    print("[RESULTS] GENEL ANALIZ SONUCLARI")
    print("=" * 60)
    
    total_opportunities = len(opportunities)
    avg_compliance = 0
    total_estimated_value = 0
    
    for opp in opportunities:
        # Her fırsat için basit hesaplamalar
        description = opp['description'] or opp['title']
        
        # Compliance hesaplama
        compliance_score = 0
        if 'far' in description.lower() or 'federal' in description.lower():
            compliance_score += 1
        if re.search(r'(\d+)\s*(?:person|people|attendee|capacity|guest)', description.lower()):
            compliance_score += 1
        if re.search(r'(?:april|may|june|july|august|september|october|november|december|january|february|march)\s+\d{1,2}', description.lower()):
            compliance_score += 1
        if any(loc in description.lower() for loc in ['washington', 'dc', 'virginia', 'maryland']):
            compliance_score += 1
        if any(tech in description.lower() for tech in ['av', 'audio', 'visual', 'equipment']):
            compliance_score += 1
        
        compliance_rate = (compliance_score / 5) * 100
        avg_compliance += compliance_rate
        
        # Fiyat hesaplama
        capacity_matches = re.findall(r'(\d+)\s*(?:person|people|attendee|capacity|guest)', description.lower())
        capacity_factor = 1.0
        if capacity_matches:
            capacity = int(max(capacity_matches))
            capacity_factor = capacity / 100
        
        location_factor = 1.2 if 'washington' in description.lower() or 'dc' in description.lower() else 1.0
        estimated_price = 50000 * capacity_factor * location_factor
        total_estimated_value += estimated_price
    
    avg_compliance = avg_compliance / total_opportunities
    avg_price = total_estimated_value / total_opportunities
    
    print(f"Islenen Firsat: {total_opportunities}")
    print(f"Ortalama Compliance: {avg_compliance:.1f}%")
    print(f"Toplam Tahmini Deger: ${total_estimated_value:,.2f}")
    print(f"Ortalama Fiyat: ${avg_price:,.2f}")
    
    # En yaygın organizasyon tipi
    org_types = {}
    for opp in opportunities:
        org_type = opp['organization_type'] or 'Bilinmiyor'
        org_types[org_type] = org_types.get(org_type, 0) + 1
    
    most_common_org = max(org_types.items(), key=lambda x: x[1])[0] if org_types else 'N/A'
    print(f"En Yaygin Organizasyon: {most_common_org}")
    
    print()
    print("[SUCCESS] Basit AutoGen analizi basariyla tamamlandi!")
    
    conn.close()
    return opportunities

if __name__ == "__main__":
    results = simple_autogen_demo()
