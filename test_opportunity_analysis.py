#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test opportunity analysis workflow - Step by step"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('.')

notice_id = "a81c7ad026c74b7799b0e28e735aeeb7"

print("=" * 60)
print(f"ADIM ADIM ILAN ANALIZI")
print(f"Notice ID: {notice_id}")
print("=" * 60)

try:
    from analyze_opportunity_workflow import OpportunityAnalysisWorkflow
    
    workflow = OpportunityAnalysisWorkflow(
        download_dir="./downloads",
        use_llm=True
    )
    
    # ADIM 1: Metadata Cekme
    print("\n[ADIM 1] Metadata cekiliyor...")
    metadata = workflow.fetch_metadata(notice_id)
    
    if metadata:
        print(f"SUCCESS - Metadata bulundu:")
        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Agency: {metadata.get('agency', 'N/A')}")
        print(f"   Posted Date: {metadata.get('posted_date', 'N/A')}")
        print(f"   NAICS: {metadata.get('naics_code', 'N/A')}")
        print(f"   Description: {metadata.get('description', 'N/A')[:100]}...")
        print(f"   Attachments: {len(metadata.get('attachments', []))} adet")
    else:
        print("ERROR - Metadata cekilemedi")
        sys.exit(1)
    
    # ADIM 2: Dokuman Indirme ve Cikarma
    print("\n[ADIM 2] Dokumanlar indiriliyor ve metin cikariliyor...")
    downloaded_files = workflow.download_and_extract_docs(notice_id, metadata)
    
    if downloaded_files:
        print(f"SUCCESS - {len(downloaded_files)} dosya indirildi:")
        for i, file_path in enumerate(downloaded_files, 1):
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   {i}. {os.path.basename(file_path)} ({size:,} bytes)")
            else:
                print(f"   {i}. {file_path} (DOSYA BULUNAMADI!)")
    else:
        print("WARNING - Hic dosya indirilemedi veya metin cikarilamadi")
    
    # ADIM 3: Gereksinim Cikarimi
    print("\n[ADIM 3] Gereksinimler cikariliyor (LLM ile)...")
    requirements = workflow.extract_requirements(notice_id, metadata, downloaded_files)
    
    if requirements:
        print(f"SUCCESS - Gereksinimler cikarildi:")
        print(f"   Room Requirements: {len(requirements.get('room_requirements', []))} adet")
        print(f"   Conference Requirements: {len(requirements.get('conference_requirements', []))} adet")
        print(f"   AV Requirements: {len(requirements.get('av_requirements', []))} adet")
        print(f"   Catering Requirements: {len(requirements.get('catering_requirements', []))} adet")
        print(f"   Compliance Requirements: {len(requirements.get('compliance_requirements', []))} adet")
    else:
        print("ERROR - Gereksinimler cikarilamadi")
    
    # ADIM 4: SOW Analizi
    print("\n[ADIM 4] SOW analizi yapiliyor...")
    sow_analysis = workflow.analyze_sow(notice_id, metadata, requirements, downloaded_files)
    
    if sow_analysis:
        print(f"SUCCESS - SOW analizi tamamlandi")
        sow_payload = sow_analysis.get('sow_payload', {})
        print(f"   Period of Performance: {sow_payload.get('period_of_performance', 'N/A')}")
        print(f"   Room Block: {sow_payload.get('room_block', {}).get('total_rooms_per_night', 'N/A')} rooms")
    else:
        print("ERROR - SOW analizi yapilamadi")
    
    # ADIM 5: Veritabanina Kaydetme
    print("\n[ADIM 5] Sonuclar veritabanina kaydediliyor...")
    result = workflow.run(notice_id)
    
    if result.success:
        print(f"SUCCESS - Analiz tamamlandi!")
        print(f"   Analysis ID: {result.analysis_id}")
        print(f"   Metadata: {'OK' if result.metadata else 'FAIL'}")
        print(f"   Downloaded Files: {len(result.downloaded_files or [])}")
        print(f"   Requirements: {'OK' if result.extracted_requirements else 'FAIL'}")
        print(f"   SOW Analysis: {'OK' if result.sow_analysis else 'FAIL'}")
        
        if result.errors:
            print(f"\nWARNINGS:")
            for error in result.errors:
                print(f"   - {error}")
    else:
        print(f"ERROR - Analiz basarisiz!")
        if result.errors:
            for error in result.errors:
                print(f"   - {error}")
    
except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()

