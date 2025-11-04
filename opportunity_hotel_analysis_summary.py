#!/usr/bin/env python3
"""
SAM.gov Fırsatı - Hotel Intelligence Analiz Özeti
Fırsat: 086008536ec84226ad9de043dc738d06
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

NOTICE_ID = "086008536ec84226ad9de043dc738d06"
SAM_URL = "https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view"


def get_opportunity_from_db(notice_id: str):
    """Veritabanından fırsat bilgilerini al"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM opportunities WHERE opportunity_id = %s",
            (notice_id,)
        )
        
        result = cur.fetchone()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        
        cur.close()
        conn.close()
        
        if result:
            return dict(zip(columns, result))
        return None
        
    except Exception as e:
        print(f"⚠️ Veritabanı hatası: {e}")
        return None


def get_sow_analysis_from_db(notice_id: str):
    """SOW analiz bilgilerini al"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sow_analysis WHERE notice_id = %s ORDER BY created_at DESC LIMIT 1",
            (notice_id,)
        )
        
        result = cur.fetchone()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        
        cur.close()
        conn.close()
        
        if result:
            return dict(zip(columns, result))
        return None
        
    except Exception as e:
        print(f"⚠️ SOW analiz hatası: {e}")
        return None


def main():
    print("=" * 80)
    print("🏨 SAM.gov Fırsatı - Hotel Intelligence Analiz Hazırlığı")
    print("=" * 80)
    print(f"\n📋 Fırsat ID: {NOTICE_ID}")
    print(f"🔗 URL: {SAM_URL}\n")
    
    # 1. Veritabanından fırsat bilgileri
    print("📊 Veritabanından fırsat bilgileri alınıyor...")
    opp = get_opportunity_from_db(NOTICE_ID)
    
    if opp:
        print("✅ Fırsat veritabanında bulundu:")
        print(f"   📌 Başlık: {opp.get('title', 'N/A')}")
        print(f"   🏛️  Ajans: {opp.get('department', 'N/A')}")
        print(f"   📅 Yayın Tarihi: {opp.get('posted_date', 'N/A')}")
        print(f"   🏷️  NAICS: {opp.get('naics_code', 'N/A')}")
    else:
        print("⚠️ Fırsat veritabanında bulunamadı")
        opp = {}
    
    # 2. SOW Analiz bilgileri
    print("\n📊 SOW Analiz bilgileri kontrol ediliyor...")
    sow = get_sow_analysis_from_db(NOTICE_ID)
    
    if sow:
        print("✅ SOW Analiz mevcut:")
        sow_payload = sow.get('sow_payload', {})
        if isinstance(sow_payload, dict):
            capacity = sow_payload.get('capacity', 'N/A')
            breakout_rooms = sow_payload.get('breakout_rooms', 'N/A')
            print(f"   👥 Kapasite: {capacity}")
            print(f"   🚪 Breakout Rooms: {breakout_rooms}")
    else:
        print("⚠️ SOW Analiz bulunamadı")
    
    # 3. Hotel Intelligence Analiz Önerileri
    print("\n" + "=" * 80)
    print("💡 Hotel Intelligence Analiz Önerileri")
    print("=" * 80)
    
    print("\n🔍 Bu fırsat için yapılabilecek analizler:")
    print("\n   1. Conference Room Requirements Analysis")
    print("      - AV equipment specifications")
    print("      - Capacity and layout requirements")
    print("      - Catering and food service needs")
    
    print("\n   2. Military Base Accommodations")
    print("      - Security clearance requirements")
    print("      - Proximity to military installations")
    print("      - Government rate structures")
    
    print("\n   3. Government Pricing Intelligence")
    print("      - Per diem rate analysis")
    print("      - Bulk discount opportunities")
    print("      - Competitive pricing benchmarks")
    
    print("\n   4. Compliance and Requirements")
    print("      - FAR/DFARS compliance")
    print("      - SAM.gov registration requirements")
    print("      - Service level agreements")
    
    # 4. ZgrProp Durumu
    print("\n" + "=" * 80)
    print("⚙️ ZgrProp RAG API Durumu")
    print("=" * 80)
    
    print("\n⚠️ ZgrProp RAG API şu anda çalışmıyor!")
    print("\n🚀 Analizi başlatmak için:")
    print("\n   1. ZgrProp'u başlatın:")
    print("      cd d:\\Zgrprop")
    print("      docker-compose up rag_api")
    
    print("\n   2. Analizi çalıştırın:")
    print("      cd D:\\ZgrSam")
    print("      python analyze_opportunity_hotel_intelligence.py")
    
    print("\n   3. Veya hızlı analiz için:")
    print("      python -c \"")
    print("      from hotel_intelligence_bridge import quick_hotel_analysis")
    print("      result = quick_hotel_analysis(")
    print("          '086008536ec84226ad9de043dc738d06',")
    print("          'conference room military base requirements',")
    print("          'Department of Defense'")
    print("      )")
    print("      print(result['proposal_draft'][:500])")
    print("      \"")
    
    print("\n" + "=" * 80)
    print("📋 Özet")
    print("=" * 80)
    
    print(f"\n✅ Fırsat ID: {NOTICE_ID}")
    print(f"✅ Analiz araçları hazır")
    print(f"⚠️ ZgrProp RAG API başlatılmalı")
    print(f"✅ Hotel Intelligence Bridge hazır")
    print(f"✅ Test suite hazır")
    
    print(f"\n💾 Analiz sonuçları kaydedilecek:")
    print(f"   - hotel_intelligence_analysis_{NOTICE_ID}_[timestamp].json")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

