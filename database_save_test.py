#!/usr/bin/env python3
"""
Database Save Test - SAM.gov verilerini veritabanına kaydet
"""

import requests
import json
import os
import psycopg2
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

def create_opportunities_table(conn):
    """Opportunities tablosunu oluştur"""
    try:
        cursor = conn.cursor()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS opportunities (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500),
            agency VARCHAR(200),
            posted_date DATE,
            opportunity_type VARCHAR(100),
            naics_code VARCHAR(20),
            description TEXT,
            ui_link VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("Opportunities tablosu hazir")
        return True
        
    except Exception as e:
        print(f"Tablo olusturma hatasi: {e}")
        return False

def save_opportunity_to_db(conn, opportunity):
    """Tek fırsatı veritabanına kaydet"""
    try:
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO opportunities (title, agency, posted_date, opportunity_type, naics_code, description, ui_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        cursor.execute(insert_sql, (
            opportunity.get('title', ''),
            opportunity.get('agency', ''),
            opportunity.get('posted_date', ''),
            opportunity.get('type', ''),
            opportunity.get('naics_code', '721110'),
            opportunity.get('description', ''),
            opportunity.get('ui_link', '')
        ))
        
        opportunity_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Firsat kaydedildi - ID: {opportunity_id}")
        return opportunity_id
        
    except Exception as e:
        print(f"Kaydetme hatasi: {e}")
        return None

def fetch_and_save_sam_data():
    """SAM.gov'dan veri çek ve veritabanına kaydet"""
    
    print("=== DATABASE SAVE TEST ===")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglanamadi!")
        return
    
    # Tablo oluştur
    if not create_opportunities_table(conn):
        print("Tablo olusturulamadi!")
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
        "limit": 3,  # Sadece 3 sonuç
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "q": "hotel accommodation",
        "naics": "721110",
        "api_key": api_key
    }
    
    print(f"API Key: {api_key[:10]}...")
    print("SAM.gov'dan veri cekiliyor...")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            print(f"BASARILI! {len(opportunities)} firsat bulundu")
            
            saved_count = 0
            for i, opp in enumerate(opportunities, 1):
                print(f"\n--- Firsat {i} ---")
                print(f"Baslik: {opp.get('title', 'N/A')}")
                print(f"Ajans: {opp.get('department', 'N/A')}")
                print(f"Tarih: {opp.get('postedDate', 'N/A')}")
                print(f"Tip: {opp.get('type', 'N/A')}")
                
                # Veritabanına kaydet
                opportunity_data = {
                    'title': opp.get('title', ''),
                    'agency': opp.get('department', ''),
                    'posted_date': opp.get('postedDate', ''),
                    'type': opp.get('type', ''),
                    'naics_code': '721110',
                    'description': f"Hotel opportunity: {opp.get('title', '')}",
                    'ui_link': opp.get('uiLink', '')
                }
                
                opportunity_id = save_opportunity_to_db(conn, opportunity_data)
                if opportunity_id:
                    saved_count += 1
                    print(f"✅ Kaydedildi - ID: {opportunity_id}")
                else:
                    print("❌ Kaydedilemedi")
            
            print(f"\n=== OZET ===")
            print(f"Toplam firsat: {len(opportunities)}")
            print(f"Kaydedilen: {saved_count}")
            print(f"Basarı orani: {(saved_count/len(opportunities)*100):.1f}%")
            
        elif response.status_code == 429:
            print("RATE LIMIT HIT!")
            print("Yarin tekrar deneyin")
            
        else:
            print(f"HATA: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"HATA: {e}")
    
    finally:
        conn.close()
        print("Veritabani baglantisi kapatildi")

if __name__ == "__main__":
    fetch_and_save_sam_data()













