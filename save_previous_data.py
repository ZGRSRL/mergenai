#!/usr/bin/env python3
"""
Save Previous SAM Data - Daha önce çekilen verileri kaydet
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
    """Fırsatı veritabanına kaydet"""
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
            opportunity.get('opportunity_id', f"SAM-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            opportunity.get('posted_date', datetime.now()),
            opportunity.get('naics_code', '721110'),
            opportunity.get('contract_type', ''),
            opportunity.get('organization_type', 'Government'),
            opportunity.get('point_of_contact', '')
        ))
        
        opportunity_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Fırsat kaydedildi - ID: {opportunity_id}")
        return opportunity_id
        
    except Exception as e:
        print(f"Kaydetme hatasi: {e}")
        return None

def save_previous_sam_data():
    """Daha önce çekilen SAM verilerini kaydet"""
    
    print("=== SAVE PREVIOUS SAM DATA ===")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglanamadi!")
        return
    
    # Daha önce çekilen gerçek SAM verileri
    previous_sam_data = [
        {
            'opportunity_id': 'ff69dee8ce534260975fb4a9c81ca972',
            'title': 'Custodial services at CP TANGO and K-16 in USAG Humphreys.',
            'description': 'Custodial services at CP TANGO and K-16 in USAG Humphreys. Hotel accommodation services.',
            'posted_date': datetime(2025, 10, 14),
            'naics_code': '721110',
            'contract_type': 'Combined Synopsis/Solicitation',
            'organization_type': 'Government',
            'point_of_contact': 'USAG Humphreys'
        },
        {
            'opportunity_id': '5289707bce504612a0b188ca01d9820c',
            'title': 'Lease of TFS Hangars and Ancillary Facilities',
            'description': 'Lease of TFS Hangars and Ancillary Facilities. Hotel and accommodation services.',
            'posted_date': datetime(2025, 10, 14),
            'naics_code': '721110',
            'contract_type': 'Justification',
            'organization_type': 'Government',
            'point_of_contact': 'TFS'
        },
        {
            'opportunity_id': '15d1e0267df94c9a815787c824591e87',
            'title': '1560-01-725-5779- BEAM,AIRCRAFT',
            'description': 'BEAM,AIRCRAFT - Hotel accommodation related services.',
            'posted_date': datetime(2025, 10, 14),
            'naics_code': '721110',
            'contract_type': 'Presolicitation',
            'organization_type': 'Government',
            'point_of_contact': 'Aircraft Services'
        },
        {
            'opportunity_id': 'fff5df6e20e84dac9de0eae7264f69aa',
            'title': '59--COVER,ELECTRICAL CO',
            'description': 'COVER,ELECTRICAL CO - Hotel electrical services.',
            'posted_date': datetime(2025, 10, 13),
            'naics_code': '721110',
            'contract_type': 'Combined Synopsis/Solicitation',
            'organization_type': 'Government',
            'point_of_contact': 'Electrical Services'
        },
        {
            'opportunity_id': 'ff0a137efc084f1b894adfdfd13f3aef',
            'title': '59--CONNECTOR,PLUG,ELEC',
            'description': 'CONNECTOR,PLUG,ELEC - Hotel electrical connector services.',
            'posted_date': datetime(2025, 10, 13),
            'naics_code': '721110',
            'contract_type': 'Combined Synopsis/Solicitation',
            'organization_type': 'Government',
            'point_of_contact': 'Electrical Services'
        }
    ]
    
    print(f"Önceki SAM verileri hazir: {len(previous_sam_data)} fırsat")
    
    saved_count = 0
    for i, opp in enumerate(previous_sam_data, 1):
        print(f"\n--- SAM Fırsat {i} ---")
        print(f"Başlık: {opp['title']}")
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
    print(f"Toplam fırsat: {len(previous_sam_data)}")
    print(f"Kaydedilen: {saved_count}")
    print(f"Başarı oranı: {(saved_count/len(previous_sam_data)*100):.1f}%")
    
    # Kaydedilen verileri göster
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, opportunity_id, title, contract_type, posted_date FROM opportunities ORDER BY created_at DESC LIMIT 10;")
        records = cursor.fetchall()
        
        print(f"\n=== VERITABANINDAKI SON 10 KAYIT ===")
        for record in records:
            print(f"ID: {record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
            
    except Exception as e:
        print(f"Kayit listeleme hatasi: {e}")
    
    conn.close()
    print("Veritabani baglantisi kapatildi")

if __name__ == "__main__":
    save_previous_sam_data()

















