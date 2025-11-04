#!/usr/bin/env python3
"""
Fırsatlardaki URL'leri kontrol et
"""

import sys
import os
sys.path.append('.')

from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities
import re

def check_opportunity_urls():
    """Fırsatlardaki URL'leri kontrol et"""
    
    # Veritabanından fırsatları al
    conn = create_database_connection()
    if not conn:
        print("Veritabanı bağlantısı başarısız!")
        return
    
    opportunities = get_live_sam_opportunities(conn, limit=5)
    if not opportunities:
        print("Hiç fırsat bulunamadı!")
        conn.close()
        return
    
    print(f"=== {len(opportunities)} Fırsat Kontrol Ediliyor ===\n")
    
    for i, opp in enumerate(opportunities, 1):
        print(f"--- Fırsat {i}: {opp['title'][:60]}... ---")
        print(f"ID: {opp['id']}")
        print(f"Opportunity ID: {opp['opportunity_id']}")
        
        # Description'da URL ara
        description = opp.get('description', '') or ''
        print(f"Description uzunluğu: {len(description)} karakter")
        
        # URL pattern'leri
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            r'api\.sam\.gov[^\s<>"{}|\\^`\[\]]*',
            r'sam\.gov[^\s<>"{}|\\^`\[\]]*',
            r'[^\s<>"{}|\\^`\[\]]*\.pdf[^\s<>"{}|\\^`\[\]]*',
            r'[^\s<>"{}|\\^`\[\]]*\.docx?[^\s<>"{}|\\^`\[\]]*',
            r'[^\s<>"{}|\\^`\[\]]*\.xlsx?[^\s<>"{}|\\^`\[\]]*',
        ]
        
        found_urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            found_urls.extend(matches)
        
        # Duplicate'leri kaldır
        found_urls = list(set(found_urls))
        
        if found_urls:
            print(f"[OK] {len(found_urls)} URL bulundu:")
            for j, url in enumerate(found_urls[:5], 1):  # İlk 5 URL'yi göster
                print(f"  {j}. {url}")
            if len(found_urls) > 5:
                print(f"  ... ve {len(found_urls) - 5} tane daha")
        else:
            print("[ERROR] Hiç URL bulunamadı")
            
            # Description'ın bir kısmını göster
            if description:
                print("Description örneği:")
                print(description[:200] + "..." if len(description) > 200 else description)
        
        print()
    
    conn.close()

if __name__ == "__main__":
    check_opportunity_urls()
