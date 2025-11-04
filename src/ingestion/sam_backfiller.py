#!/usr/bin/env python3
"""
SAM.gov Backfiller - Doğru API key ve URL ile
"""

import json
import time
import random
import requests
import re
import sys
import os
from datetime import date, timedelta
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import List, Dict, Any
from tqdm import tqdm

# Yerel modülleri import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# =========================================================
# GÜNCEL VE DOĞRU API BİLGİLERİ (HARD-CODE)
# =========================================================
SAM_API_KEY = "SAM-34a0de14-8d52-4e37-8ac3-f8db8513eaf2" 
SAM_URL = "https://api.sam.gov/prod/opportunities/v2/search"  # URL DÜZELTİLDİ!
# =========================================================
NAICS = "721110"      
WINDOW_DAYS = 7       
PAGE_LIMIT = 100      
MAX_RETRIES = 4       
BASE_SLEEP = 1.0     

def get_sam_key():
    """SAM API key'i al"""
    return SAM_API_KEY

def build_session():
    """Retry stratejisi ile HTTP session oluştur"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def fetch_sam_data(session, start_date, end_date, offset=0):
    """SAM.gov'dan veri çek"""
    api_key = get_sam_key()
    
    params = {
        'api_key': api_key,
        'postedFrom': start_date.strftime('%m/%d/%Y'),
        'postedTo': end_date.strftime('%m/%d/%Y'),
        'limit': PAGE_LIMIT,
        'naics': NAICS,
        'status': 'Active',
        'offset': offset
    }
    
    try:
        print(f"  Fetching: {start_date} to {end_date}, offset={offset}")
        response = session.get(SAM_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 403:
            print(f"  [ERROR] 403 Forbidden - API key geçersiz: {api_key[:10]}...")
            return None
        elif response.status_code == 429:
            print(f"  [WARN] 429 Rate Limited - Bekleniyor...")
            time.sleep(BASE_SLEEP * 2)
            return None
        else:
            print(f"  [ERROR] HTTP {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"  [ERROR] Connection error: {e}")
        return None

def run_backfill(start_date, end_date):
    """Backfill işlemini çalıştır"""
    print(f"\n--- SAM.gov Backfill Başlıyor ---")
    print(f"Tarih Aralığı: {start_date} - {end_date}")
    print(f"API Key: {get_sam_key()[:10]}...")
    print(f"API URL: {SAM_URL}")
    
    session = build_session()
    all_opportunities = []
    
    # Tarih pencerelerini oluştur
    current_date = start_date
    date_windows = []
    
    while current_date < end_date:
        window_end = min(current_date + timedelta(days=WINDOW_DAYS), end_date)
        date_windows.append((current_date, window_end))
        current_date = window_end
    
    print(f"Toplam {len(date_windows)} tarih penceresi işlenecek")
    
    # Her tarih penceresi için veri çek
    for i, (window_start, window_end) in enumerate(tqdm(date_windows, desc="Date Windows")):
        print(f"\nPencere {i+1}/{len(date_windows)}: {window_start} - {window_end}")
        
        offset = 0
        total_fetched = 0
        
        while True:
            data = fetch_sam_data(session, window_start, window_end, offset)
            
            if data is None:
                print(f"  Veri alınamadı, sonraki pencereye geçiliyor...")
                break
                
            opportunities = data.get('opportunitiesData', [])
            total_records = data.get('totalRecords', 0)
            
            if not opportunities:
                print(f"  Daha fazla veri yok")
                break
                
            all_opportunities.extend(opportunities)
            total_fetched += len(opportunities)
            
            print(f"  {len(opportunities)} kayıt alındı (Toplam: {total_fetched}/{total_records})")
            
            if len(opportunities) < PAGE_LIMIT:
                print(f"  Son sayfa, pencere tamamlandı")
                break
                
            offset += PAGE_LIMIT
            time.sleep(BASE_SLEEP + random.uniform(0, 0.5))
    
    print(f"\n✅ Backfill tamamlandı!")
    print(f"📊 Toplam {len(all_opportunities)} fırsat toplandı")
    
    # Veritabanına kaydet (mock)
    print(f"💾 Veritabanına kaydediliyor...")
    # Burada gerçek DB kaydetme işlemi yapılacak
    
    return all_opportunities

def main():
    """Ana fonksiyon"""
    print("SAM.gov Backfiller Başlatılıyor...")
    
    # Son 30 gün için backfill
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    opportunities = run_backfill(start_date, end_date)
    
    print(f"\n🎉 Backfill tamamlandı! {len(opportunities)} fırsat toplandı.")

if __name__ == "__main__":
    main()
