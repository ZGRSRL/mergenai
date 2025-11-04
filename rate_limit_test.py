#!/usr/bin/env python3
"""
SAM.gov Rate Limit Test
"""

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_rate_limits():
    """SAM.gov API rate limit'lerini test et"""
    
    print("=== SAM.gov RATE LIMIT TEST ===")
    
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        print("HATA: SAM_API_KEY bulunamadi!")
        return
    
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    
    # Test parametreleri
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    params = {
        "limit": 1,  # Sadece 1 sonuç
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "q": "test",
        "api_key": api_key
    }
    
    print(f"API Key: {api_key[:10]}...")
    print("Rate limit testi basliyor...")
    
    # 5 ardışık çağrı yap
    for i in range(5):
        print(f"\n--- Cagri {i+1}/5 ---")
        
        try:
            start_time = time.time()
            response = requests.get(base_url, params=params, timeout=30)
            end_time = time.time()
            
            print(f"HTTP Status: {response.status_code}")
            print(f"Response Time: {end_time - start_time:.2f} saniye")
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunitiesData', [])
                print(f"Sonuc: {len(opportunities)} firsat")
                
            elif response.status_code == 429:
                print("RATE LIMIT HIT! Too many requests")
                print(f"Response: {response.text[:200]}")
                break
                
            elif response.status_code == 401:
                print("UNAUTHORIZED! API key problemi")
                break
                
            else:
                print(f"HATA: {response.status_code}")
                print(f"Response: {response.text[:200]}")
            
            # 1 saniye bekle
            if i < 4:  # Son çağrı değilse
                print("1 saniye bekleniyor...")
                time.sleep(1)
                
        except requests.exceptions.RequestException as e:
            print(f"BAGLANTI HATASI: {e}")
            break
        except Exception as e:
            print(f"GENEL HATA: {e}")
            break
    
    print("\n=== RATE LIMIT TEST TAMAMLANDI ===")

if __name__ == "__main__":
    test_rate_limits()
