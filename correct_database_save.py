#!/usr/bin/env python3
"""
Correct Database Save - Mevcut tablo yapısına uygun kaydetme
"""

import psycopg2
import os
from datetime import datetime
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

def save_opportunity_to_db(conn, opportunity):
    """Tek fırsatı veritabanına kaydet"""
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
        
        cursor.execute(insert_sql, (
            opportunity.get('opportunity_id', f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            opportunity.get('posted_date', datetime.now()),
            opportunity.get('naics_code', '721110'),
            opportunity.get('contract_type', ''),
            opportunity.get('organization_type', ''),
            opportunity.get('point_of_contact', '')
        ))
        
        opportunity_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Firsat kaydedildi - ID: {opportunity_id}")
        return opportunity_id
        
    except Exception as e:
        print(f"Kaydetme hatasi: {e}")
        return None

def demo_save_opportunities():
    """Demo fırsatları veritabanına kaydet"""
    
    print("=== CORRECT DATABASE SAVE TEST ===")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglanamadi!")
        return
    
    # Demo fırsatları
    demo_opportunities = [
        {
            'opportunity_id': 'DEMO-001',
            'title': 'Hotel Accommodation Services - Demo RFQ 1',
            'description': 'Demo hotel accommodation opportunity for testing purposes',
            'posted_date': datetime(2025, 10, 14),
            'naics_code': '721110',
            'contract_type': 'RFQ',
            'organization_type': 'Government',
            'point_of_contact': 'Demo Contact 1'
        },
        {
            'opportunity_id': 'DEMO-002',
            'title': 'Conference Center Services - Demo RFQ 2',
            'description': 'Demo conference center services opportunity',
            'posted_date': datetime(2025, 10, 13),
            'naics_code': '721110',
            'contract_type': 'Combined Synopsis/Solicitation',
            'organization_type': 'Government',
            'point_of_contact': 'Demo Contact 2'
        },
        {
            'opportunity_id': 'DEMO-003',
            'title': 'Lodging Services - Demo RFQ 3',
            'description': 'Demo lodging services opportunity',
            'posted_date': datetime(2025, 10, 12),
            'naics_code': '721110',
            'contract_type': 'Sources Sought',
            'organization_type': 'Government',
            'point_of_contact': 'Demo Contact 3'
        }
    ]
    
    print(f"Demo verileri hazir: {len(demo_opportunities)} firsat")
    
    saved_count = 0
    for i, opp in enumerate(demo_opportunities, 1):
        print(f"\n--- Demo Firsat {i} ---")
        print(f"Baslik: {opp['title']}")
        print(f"Tip: {opp['contract_type']}")
        print(f"Tarih: {opp['posted_date']}")
        
        # Veritabanına kaydet
        opportunity_id = save_opportunity_to_db(conn, opp)
        if opportunity_id:
            saved_count += 1
            print(f"Kaydedildi - ID: {opportunity_id}")
        else:
            print("Kaydedilemedi")
    
    print(f"\n=== OZET ===")
    print(f"Toplam firsat: {len(demo_opportunities)}")
    print(f"Kaydedilen: {saved_count}")
    print(f"Basarı orani: {(saved_count/len(demo_opportunities)*100):.1f}%")
    
    # Kaydedilen verileri göster
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, opportunity_id, title, contract_type, posted_date FROM opportunities ORDER BY created_at DESC LIMIT 5;")
        records = cursor.fetchall()
        
        print(f"\n=== VERITABANINDAKI SON 5 KAYIT ===")
        for record in records:
            print(f"ID: {record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
            
    except Exception as e:
        print(f"Kayit listeleme hatasi: {e}")
    
    conn.close()
    print("Veritabani baglantisi kapatildi")

if __name__ == "__main__":
    demo_save_opportunities()













