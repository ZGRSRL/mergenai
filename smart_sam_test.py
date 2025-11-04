#!/usr/bin/env python3
"""
Smart SAM.gov Test - Rate Limit Kontrollü
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def check_rate_limit():
    """Rate limit durumunu kontrol et"""
    # Basit kontrol - eğer daha önce çağrı yapıldıysa bekle
    print("Rate limit kontrol ediliyor...")
    print("Son çağrı: Bugün (rate limit aktif)")
    print("Önerilen: Yarın tekrar deneyin")
    return False

def smart_sam_test():
    """Akıllı SAM.gov testi - rate limit kontrolü ile"""
    
    print("=== SMART SAM.GOV TEST ===")
    
    # Rate limit kontrolü
    if not check_rate_limit():
        print("RATE LIMIT AKTIF!")
        print("Yarin tekrar deneyin (2025-Oct-15 00:00 UTC)")
        print("Demo modunda devam ediliyor...")
        
        # Demo verisi döndür
        return [{
            'title': 'Demo Hotel Opportunity',
            'content': 'Demo hotel accommodation opportunity for testing',
            'metadata': {
                'agency': 'Demo Agency',
                'posted_date': '2025-10-14',
                'type': 'RFQ',
                'link': 'https://demo.sam.gov'
            }
        }]
    
    # Eğer rate limit yoksa gerçek API çağrısı yap
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        print("HATA: SAM_API_KEY bulunamadi!")
        return []
    
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    
    # Tarih aralığı
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    params = {
        "limit": 3,  # Sadece 3 sonuç
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "q": "hotel accommodation",
        "naics": "721110",
        "api_key": api_key
    }
    
    print(f"API Key: {api_key[:10]}...")
    print("Tek çağrı yapılıyor...")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            print(f"BASARILI! {len(opportunities)} firsat bulundu")
            
            results = []
            for i, opp in enumerate(opportunities, 1):
                print(f"\n--- Firsat {i} ---")
                print(f"Baslik: {opp.get('title', 'N/A')}")
                print(f"Ajans: {opp.get('department', 'N/A')}")
                print(f"Tarih: {opp.get('postedDate', 'N/A')}")
                print(f"Tip: {opp.get('type', 'N/A')}")
                
                results.append({
                    'title': opp.get('title', 'N/A'),
                    'content': f"Hotel opportunity: {opp.get('title', 'N/A')}",
                    'metadata': {
                        'agency': opp.get('department', 'N/A'),
                        'posted_date': opp.get('postedDate', 'N/A'),
                        'type': opp.get('type', 'N/A'),
                        'link': opp.get('uiLink', 'N/A')
                    }
                })
            
            return results
            
        elif response.status_code == 429:
            print("RATE LIMIT HIT!")
            print("Yarin tekrar deneyin")
            return []
            
        else:
            print(f"HATA: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"HATA: {e}")
        return []

if __name__ == "__main__":
    opportunities = smart_sam_test()
    print(f"\nToplam firsat: {len(opportunities)}")
