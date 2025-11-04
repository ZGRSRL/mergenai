#!/usr/bin/env python3
"""
Fırsat ID'lerinin doğruluğunu kontrol et ve fırsat linklerini ekle
"""

import sys
import os
sys.path.append('.')

from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities
import re
import requests
from datetime import datetime

def check_opportunity_ids():
    """Fırsat ID'lerini kontrol et ve linklerini ekle"""
    
    # Veritabanından fırsatları al
    conn = create_database_connection()
    if not conn:
        print("Veritabanı bağlantısı başarısız!")
        return
    
    opportunities = get_live_sam_opportunities(conn, limit=10)
    if not opportunities:
        print("Hiç fırsat bulunamadı!")
        conn.close()
        return
    
    print(f"=== {len(opportunities)} Fırsat ID Kontrolü ===\n")
    
    valid_count = 0
    invalid_count = 0
    
    for i, opp in enumerate(opportunities, 1):
        print(f"--- Fırsat {i}: {opp['title'][:60]}... ---")
        print(f"Database ID: {opp['id']}")
        print(f"Opportunity ID: {opp['opportunity_id']}")
        
        # SAM.gov linkini oluştur
        sam_link = f"https://sam.gov/workspace/contract/opp/{opp['opportunity_id']}/view"
        print(f"SAM.gov Link: {sam_link}")
        
        # ID formatını kontrol et
        opp_id = opp['opportunity_id']
        is_valid_format = False
        
        # UUID format kontrolü (32 karakter hex)
        if len(opp_id) == 32 and all(c in '0123456789abcdef' for c in opp_id.lower()):
            is_valid_format = True
            print(f"[OK] ID formatı geçerli (UUID)")
        # Demo ID kontrolü
        elif opp_id.startswith('DEMO-'):
            is_valid_format = True
            print(f"[OK] Demo ID formatı geçerli")
        else:
            print(f"[WARNING] ID formatı şüpheli: {opp_id}")
        
        # SAM.gov linkini test et
        try:
            print("SAM.gov linki test ediliyor...")
            response = requests.get(sam_link, timeout=10)
            
            if response.status_code == 200:
                print(f"[OK] SAM.gov linki erişilebilir (HTTP 200)")
                valid_count += 1
                
                # Sayfa içeriğini kontrol et
                if 'opportunity' in response.text.lower() or 'contract' in response.text.lower():
                    print(f"[OK] Sayfa içeriği fırsat ile ilgili görünüyor")
                else:
                    print(f"[WARNING] Sayfa içeriği fırsat ile ilgili görünmüyor")
                    
            elif response.status_code == 404:
                print(f"[ERROR] SAM.gov linki bulunamadı (HTTP 404)")
                invalid_count += 1
            elif response.status_code == 403:
                print(f"[ERROR] SAM.gov linki erişim reddedildi (HTTP 403)")
                invalid_count += 1
            else:
                print(f"[WARNING] SAM.gov linki HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] SAM.gov linki test hatası: {e}")
            invalid_count += 1
        
        # Description'da ID referanslarını kontrol et
        description = opp.get('description', '') or ''
        if description:
            print(f"Description uzunluğu: {len(description)} karakter")
            
            # ID referanslarını ara
            id_refs = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', description, re.I)
            if id_refs:
                print(f"Description'da UUID referansları: {id_refs}")
            
            # 32 karakter hex ID'leri ara
            hex_ids = re.findall(r'[a-f0-9]{32}', description, re.I)
            if hex_ids:
                print(f"Description'da hex ID'ler: {hex_ids}")
                
                # Bu ID'lerin opportunity_id ile eşleşip eşleşmediğini kontrol et
                for hex_id in hex_ids:
                    if hex_id.lower() == opp_id.lower():
                        print(f"[OK] Description'daki ID opportunity_id ile eşleşiyor")
                    else:
                        print(f"[WARNING] Description'daki ID farklı: {hex_id}")
        
        print()
    
    # Özet
    print("=== ÖZET ===")
    print(f"Toplam fırsat: {len(opportunities)}")
    print(f"Geçerli linkler: {valid_count}")
    print(f"Geçersiz linkler: {invalid_count}")
    print(f"Başarı oranı: {(valid_count/len(opportunities)*100):.1f}%")
    
    conn.close()

def add_opportunity_links():
    """Fırsatlara SAM.gov linklerini ekle"""
    
    conn = create_database_connection()
    if not conn:
        print("Veritabanı bağlantısı başarısız!")
        return
    
    try:
        cursor = conn.cursor()
        
        # opportunities tablosuna sam_link sütunu ekle (eğer yoksa)
        try:
            cursor.execute("ALTER TABLE opportunities ADD COLUMN sam_link VARCHAR(500)")
            print("[INFO] sam_link sütunu eklendi")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("[INFO] sam_link sütunu zaten mevcut")
            else:
                print(f"[WARNING] sam_link sütunu eklenemedi: {e}")
        
        # Tüm fırsatları güncelle
        opportunities = get_live_sam_opportunities(conn, limit=1000)
        
        updated_count = 0
        for opp in opportunities:
            sam_link = f"https://sam.gov/workspace/contract/opp/{opp['opportunity_id']}/view"
            
            update_query = """
            UPDATE opportunities 
            SET sam_link = %s 
            WHERE id = %s
            """
            cursor.execute(update_query, (sam_link, opp['id']))
            updated_count += 1
        
        conn.commit()
        print(f"[SUCCESS] {updated_count} fırsata SAM.gov linki eklendi!")
        
    except Exception as e:
        print(f"[ERROR] Link ekleme hatası: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=== Fırsat ID Kontrolü ve Link Ekleme ===")
    print()
    
    # Önce ID'leri kontrol et
    check_opportunity_ids()
    print("\n" + "="*50 + "\n")
    
    # Sonra linkleri ekle
    add_opportunity_links()
