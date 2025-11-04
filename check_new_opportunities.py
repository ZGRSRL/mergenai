#!/usr/bin/env python3
"""
Bugün için yeni fırsatları kontrol et
"""

import sys
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection
from datetime import datetime, date

def check_new_opportunities():
    """Bugün için yeni fırsatları kontrol et"""
    
    conn = create_database_connection()
    if not conn:
        print("[ERROR] Veritabani baglantisi basarisiz!")
        return
    
    print("=== BUGUN ICIN YENI FIRSATLAR ===")
    print(f"Kontrol Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print()
    
    cursor = conn.cursor()
    today = date.today()
    
    # Bugün eklenen fırsatları kontrol et
    cursor.execute('''
        SELECT id, opportunity_id, title, posted_date, contract_type, naics_code
        FROM opportunities 
        WHERE DATE(created_at) = %s
        ORDER BY created_at DESC;
    ''', (today,))
    
    today_opportunities = cursor.fetchall()
    
    if today_opportunities:
        print(f"[OK] Bugun {len(today_opportunities)} yeni firsat bulundu:")
        print()
        for i, opp in enumerate(today_opportunities, 1):
            print(f"{i}. {opp[2][:60]}...")
            print(f"   ID: {opp[1]} | Tip: {opp[4]} | NAICS: {opp[5]}")
            print(f"   Tarih: {opp[3]}")
            print()
    else:
        print("[NO] Bugun icin yeni firsat bulunamadi.")
        print()
        
        # Son 3 günün fırsatlarını göster
        cursor.execute('''
            SELECT id, opportunity_id, title, posted_date, contract_type, naics_code
            FROM opportunities 
            WHERE DATE(created_at) >= %s
            ORDER BY created_at DESC
            LIMIT 10;
        ''', (date.today().replace(day=date.today().day-3),))
        
        recent_opportunities = cursor.fetchall()
        
        if recent_opportunities:
            print(f"[INFO] Son 3 gunun firsatlari ({len(recent_opportunities)} adet):")
            for i, opp in enumerate(recent_opportunities, 1):
                print(f"{i}. {opp[2][:50]}... - {opp[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_new_opportunities()
