#!/usr/bin/env python3
"""
Real SAM.gov to Database - Gerçek verileri rate limit olmadan kaydet
"""

import requests
import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def create_database_connection():
    """Veritabanı bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        return conn
    except Exception as e:
        print(f"Veritabani baglanti hatasi: {e}")
        return None

def save_real_opportunity_to_db(conn, opportunity):
    """Gerçek fırsatı veritabanına kaydet"""
    try:
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO opportunities (
            opportunity_id, title, description, posted_date, 
            naics_code, contract_type, organization_type, point_of_contact
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        # Tarih formatını düzelt
        posted_date = None
        if opportunity.get('postedDate'):
            try:
                posted_date = datetime.strptime(opportunity['postedDate'], '%Y-%m-%d')
            except:
                posted_date = datetime.now()
        
        cursor.execute(insert_sql, (
            opportunity.get('opportunityId', f"SAM-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            posted_date,
            opportunity.get('naicsCode', '721110'),
            opportunity.get('type', ''),
            opportunity.get('organizationType', 'Government'),
            opportunity.get('pointOfContact', '')
        ))
        
        opportunity_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Gerçek fırsat kaydedildi - ID: {opportunity_id}")
        return opportunity_id
        
    except Exception as e:
        print(f"Kaydetme hatasi: {e}")
        return None

def fetch_and_save_real_sam_data():
    """Gerçek SAM.gov verilerini çek ve kaydet"""
    
    print("=== REAL SAM.GOV TO DATABASE ===")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglanamadi!")
        return
    
    # SAM.gov API çağrısı
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        print("API key bulunamadi!")
        return
    
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    
    # Tarih aralığı
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    params = {
        "limit": 5,  # 5 sonuç
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "q": "hotel accommodation",
        "naics": "721110",
        "api_key": api_key
    }
    
    print(f"API Key: {api_key[:10]}...")
    print("SAM.gov'dan gerçek veri cekiliyor...")
    print(f"Tarih: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            print(f"BASARILI! {len(opportunities)} gerçek fırsat bulundu")
            
            saved_count = 0
            for i, opp in enumerate(opportunities, 1):
                print(f"\n--- Gerçek Fırsat {i} ---")
                print(f"Başlık: {opp.get('title', 'N/A')}")
                print(f"Ajans: {opp.get('department', 'N/A')}")
                print(f"Tarih: {opp.get('postedDate', 'N/A')}")
                print(f"Tip: {opp.get('type', 'N/A')}")
                print(f"Link: {opp.get('uiLink', 'N/A')}")
                
                # Veritabanına kaydet
                opportunity_data = {
                    'opportunityId': opp.get('opportunityId', ''),
                    'title': opp.get('title', ''),
                    'description': opp.get('description', ''),
                    'postedDate': opp.get('postedDate', ''),
                    'naicsCode': '721110',
                    'type': opp.get('type', ''),
                    'organizationType': 'Government',
                    'pointOfContact': opp.get('pointOfContact', '')
                }
                
                opportunity_id = save_real_opportunity_to_db(conn, opportunity_data)
                if opportunity_id:
                    saved_count += 1
                    print(f"Kaydedildi - ID: {opportunity_id}")
                else:
                    print("Kaydedilemedi")
            
            print(f"\n=== OZET ===")
            print(f"Toplam fırsat: {len(opportunities)}")
            print(f"Kaydedilen: {saved_count}")
            print(f"Başarı oranı: {(saved_count/len(opportunities)*100):.1f}%")
            
        elif response.status_code == 429:
            print("RATE LIMIT HIT!")
            print("Yarın tekrar deneyin")
            
        else:
            print(f"HATA: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"HATA: {e}")
    
    finally:
        conn.close()
        print("Veritabani baglantisi kapatildi")

if __name__ == "__main__":
    fetch_and_save_real_sam_data()













