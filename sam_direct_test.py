#!/usr/bin/env python3
"""
SAM.gov Direct Test - API olmadan
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

def test_sam_direct():
    """SAM.gov API'yi doğrudan test et"""
    
    print("=== SAM.gov API Direct Test ===")
    print("Hotel verilerini 3 ay icin cekiyor...")
    
    # API key'i al
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        print("HATA: SAM_API_KEY .env dosyasinda bulunamadi!")
        return
    
    print(f"API Key: {api_key[:10]}...")
    
    # API endpoint
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    
    # 3 ay öncesinden bugüne kadar
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Hotel kategorisi için parametreler
    params = {
        "limit": 5,
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "q": "hotel accommodation lodging",
        "naics": "721110",
        "api_key": api_key
    }
    
    print(f"Tarih: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    print(f"Kategori: Hotel (NAICS: 721110)")
    
    try:
        print("\nAPI'ye baglaniyor...")
        response = requests.get(base_url, params=params, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            print(f"Basarili! {len(opportunities)} firsat bulundu")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"\n--- Firsat {i} ---")
                print(f"Baslik: {opp.get('title', 'N/A')}")
                print(f"Ajans: {opp.get('department', 'N/A')}")
                print(f"Tarih: {opp.get('postedDate', 'N/A')}")
                print(f"Tip: {opp.get('type', 'N/A')}")
                print(f"Link: {opp.get('uiLink', 'N/A')}")
                
        elif response.status_code == 401:
            print("HATA: API key gerekli!")
            print("SAM.gov'da API key alin ve .env dosyasina ekleyin")
            
        else:
            print(f"HATA: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"BAGLANTI HATASI: {e}")
    except Exception as e:
        print(f"GENEL HATA: {e}")

if __name__ == "__main__":
    test_sam_direct()
