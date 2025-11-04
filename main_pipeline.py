#!/usr/bin/env python3
"""
Main Pipeline - SAM.gov veri işleme pipeline'ı
"""

import datetime
from datetime import timedelta
import sys
import os

# Yerel modülleri import et
sys.path.append('.')

def run_full_pipeline(start_date, end_date, step="all"):
    """Ana pipeline'ı çalıştır"""
    print(f"\n--- Pipeline Başlatılıyor ---")
    print(f"Tarih Aralığı: {start_date} - {end_date}")
    print(f"Adım: {step}")
    
    try:
        if step in ["all", "backfill"]:
            print("\n[ADIM 2] SAM.gov Backfill Başlatılıyor...")
            from src.ingestion.sam_backfiller import run_backfill
            opportunities = run_backfill(start_date, end_date)
            print(f"✅ Backfill tamamlandı! {len(opportunities)} fırsat toplandı.")
        
        if step in ["all", "download"]:
            print("\n[ADIM 3] Ek İndirme Başlatılıyor...")
            # Mock download - gerçek implementasyon için attachment downloader kullan
            print("   - Mock download tamamlandı")
        
        if step in ["all", "process"]:
            print("\n[ADIM 4] CBR İşleme ve Vektörleme Başlatılıyor...")
            # Mock process - gerçek implementasyon için SOW workflow kullan
            print("   - Mock process tamamlandı")
        
        print("\n✅ Pipeline başarıyla tamamlandı!")
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test için
    END = datetime.date.today()
    START = END - timedelta(days=7)  # Son 7 gün
    
    print("Pipeline test başlatılıyor...")
    run_full_pipeline(START, END, step="backfill")
