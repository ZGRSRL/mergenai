#!/usr/bin/env python3
"""
AutoGen Trigger - Veritabanındaki SAM verilerini AutoGen ile işle
"""

import psycopg2
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# AutoGen implementation'ı import et
sys.path.append('.')
from autogen_implementation import ZgrBidAutoGenOrchestrator, Document, DocumentType

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

def get_sam_opportunities_from_db(conn, limit=3):
    """Veritabanından SAM fırsatlarını al"""
    try:
        cursor = conn.cursor()
        
        # Son eklenen SAM fırsatlarını al
        cursor.execute("""
            SELECT id, opportunity_id, title, description, posted_date, contract_type, naics_code
            FROM opportunities 
            WHERE naics_code = '721110' 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (limit,))
        
        records = cursor.fetchall()
        
        opportunities = []
        for record in records:
            opportunities.append({
                'id': record[0],
                'opportunity_id': record[1],
                'title': record[2],
                'description': record[3],
                'posted_date': record[4],
                'contract_type': record[5],
                'naics_code': record[6]
            })
        
        return opportunities
        
    except Exception as e:
        print(f"Veri alma hatasi: {e}")
        return []

def process_with_autogen(opportunities):
    """AutoGen ile fırsatları işle"""
    
    print("=== AUTOGEN TRIGGER ===")
    print(f"AutoGen ile {len(opportunities)} fırsat işlenecek...")
    
    # AutoGen orchestrator'ı başlat
    orchestrator = ZgrBidAutoGenOrchestrator()
    
    results = []
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n--- Fırsat {i} İşleniyor ---")
        print(f"ID: {opp['id']}")
        print(f"Başlık: {opp['title']}")
        print(f"Tip: {opp['contract_type']}")
        print(f"Tarih: {opp['posted_date']}")
        
        # Document oluştur
        document = Document(
            id=opp['id'],
            type=DocumentType.RFQ,
            title=opp['title'],
            content=opp['description'] or f"Hotel opportunity: {opp['title']}",
            metadata={
                'opportunity_id': opp['opportunity_id'],
                'contract_type': opp['contract_type'],
                'posted_date': str(opp['posted_date']),
                'naics_code': opp['naics_code']
            }
        )
        
        # AutoGen ile işle
        print("AutoGen işleme başlıyor...")
        result = orchestrator.process_rfq(document)
        results.append(result)
        
        # Sonuçları göster
        print(f"Islem tamamlandi!")
        print(f"Gereksinimler: {len(result['requirements'])}")
        print(f"Compliance: {result['compliance_matrix']['met_requirements']}/{result['compliance_matrix']['total_requirements']} karsilandi")
        print(f"Risk Seviyesi: {result['compliance_matrix']['overall_risk']}")
        print(f"Toplam Maliyet: ${result['pricing']['grand_total']:,.2f}")
        print(f"Kalite Durumu: {result['quality_assurance']['approval_status']}")
    
    return results

def show_autogen_results(results):
    """AutoGen sonuçlarını göster"""
    
    print("\n" + "=" * 60)
    print("AUTOGEN SONUÇLARI")
    print("=" * 60)
    
    total_value = 0
    total_requirements = 0
    total_met = 0
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Firsat {i}: {result['rfq_title']} ---")
        
        # Gereksinimler
        print(f"\nGereksinimler ({len(result['requirements'])}):")
        for req in result['requirements']:
            print(f"  - {req['code']}: {req['text']} ({req['category']}, {req['priority']})")
        
        # Compliance
        compliance = result['compliance_matrix']
        print(f"\nCompliance Matrix:")
        print(f"  - Karsilanan: {compliance['met_requirements']}")
        print(f"  - Eksik: {compliance['gap_requirements']}")
        print(f"  - Risk: {compliance['overall_risk']}")
        
        # Pricing
        pricing = result['pricing']
        print(f"\nFiyatlandirma:")
        print(f"  - Oda Blogu: ${pricing['room_block']['total']:,.2f}")
        print(f"  - AV Ekipman: ${pricing['av_equipment']['total']:,.2f}")
        print(f"  - Ulasim: ${pricing['transportation']['shuttle_service']:,.2f}")
        print(f"  - Yonetim: ${pricing['management']['project_management']:,.2f}")
        print(f"  - TOPLAM: ${pricing['grand_total']:,.2f}")
        
        # Executive Summary
        print(f"\nExecutive Summary:")
        print(result['proposal_sections']['executive_summary'][:200] + "...")
        
        # Istatistikler
        total_value += pricing['grand_total']
        total_requirements += compliance['total_requirements']
        total_met += compliance['met_requirements']
    
    print(f"\n=== GENEL OZET ===")
    print(f"Islenen Firsat: {len(results)}")
    print(f"Toplam Deger: ${total_value:,.2f}")
    print(f"Toplam Gereksinim: {total_requirements}")
    print(f"Karsilanan: {total_met}")
    print(f"Compliance Orani: {(total_met/total_requirements*100):.1f}%")
    print(f"Ortalama Fiyat: ${total_value/len(results):,.2f}")

def main():
    """Ana fonksiyon"""
    
    print("=== AUTOGEN TRIGGER BASLATIYOR ===")
    print("Veritabanindaki SAM verilerini AutoGen ile isliyor...")
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglanamadi!")
        return
    
    # SAM fırsatlarını al
    opportunities = get_sam_opportunities_from_db(conn, limit=3)
    
    if not opportunities:
        print("Veritabaninda SAM firsati bulunamadi!")
        conn.close()
        return
    
    print(f"Veritabanindan {len(opportunities)} firsat alindi")
    
    # AutoGen ile isle
    results = process_with_autogen(opportunities)
    
    # Sonuclari goster
    show_autogen_results(results)
    
    conn.close()
    print("\n=== AUTOGEN TRIGGER TAMAMLANDI ===")

if __name__ == "__main__":
    main()
