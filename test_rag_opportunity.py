#!/usr/bin/env python3
"""
SAM.gov Fırsatı için RAG Servisi Testi
Fırsat ID: 086008536ec84226ad9de043dc738d06
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Fırsat bilgileri
NOTICE_ID = "086008536ec84226ad9de043dc738d06"
SAM_URL = "https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view"

print("=" * 70)
print("SAM.GOV FIRSATI IÇIN RAG SERVISI TESTI")
print("=" * 70)
print(f"\nFirsat ID: {NOTICE_ID}")
print(f"SAM.gov URL: {SAM_URL}")
print("\n" + "=" * 70)

# 1. Fırsatı veritabanından kontrol et
print("\n[1/4] Veritabanindan firsat bilgileri kontrol ediliyor...")
try:
    import psycopg2
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database='ZGR_AI',
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'sarlio41'),
        port=os.getenv('DB_PORT', '5432')
    )
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                opportunity_id,
                title,
                organization_type,
                naics_code,
                posted_date,
                response_dead_line,
                place_of_performance
            FROM opportunities
            WHERE opportunity_id = %s
        """, (NOTICE_ID,))
        
        result = cursor.fetchone()
        
        if result:
            opp_id, title, org_type, naics, posted, deadline, pop = result
            print(f"  [OK] Firsat bulundu!")
            print(f"  Baslik: {title}")
            print(f"  Organizasyon: {org_type}")
            print(f"  NAICS: {naics}")
            print(f"  Posted: {posted}")
            print(f"  Deadline: {deadline}")
            agency = org_type or "Unknown"
        else:
            print(f"  [WARN] Firsat veritabaninda bulunamadi")
            print(f"  SAM.gov API'den cekilmesi gerekebilir")
            agency = "Unknown"
    
    conn.close()
    
except Exception as e:
    print(f"  [ERROR] Veritabanı hatası: {e}")
    agency = "Unknown"

# 2. RAG API URL kontrolü
print("\n[2/4] RAG API baglantisi kontrol ediliyor...")
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8001")
print(f"  RAG API URL: {RAG_API_URL}")

# Docker içinden mi, host makineden mi kontrol et
import requests
try:
    # Önce localhost'u dene (host makineden)
    test_url = "http://localhost:8001/api/health" if "localhost" in RAG_API_URL or "8001" in RAG_API_URL else f"{RAG_API_URL}/api/health"
    response = requests.get(test_url, timeout=5)
    if response.status_code == 200:
        print(f"  [OK] RAG API erisilebilir (localhost)")
        use_localhost = True
    else:
        print(f"  [WARN] RAG API yanıt verdi ama status: {response.status_code}")
        use_localhost = True
except:
    # Docker içinden dene
    try:
        test_url = "http://rag_api:8000/api/health"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            print(f"  [OK] RAG API erisilebilir (docker network)")
            use_localhost = False
            RAG_API_URL = "http://rag_api:8000"
        else:
            print(f"  [ERROR] RAG API erisilemiyor")
            print(f"  Docker Compose ile baslatmayi deneyin: docker-compose up -d rag_api")
            sys.exit(1)
    except:
        print(f"  [ERROR] RAG API erisilemiyor")
        print(f"  Docker Compose ile baslatmayi deneyin: docker-compose up -d rag_api")
        sys.exit(1)

# 3. RAG Servisi ile teklif oluştur
print("\n[3/4] RAG servisi ile teklif olusturuluyor...")
print("  Bu biraz zaman alabilir (30-300 saniye)...")

try:
    sys.path.insert(0, '.')
    from samai_integrator import call_rag_proposal_service
    
    # Eğer localhost kullanıyorsak, URL'yi güncelle
    if use_localhost:
        import samai_integrator
        original_url = samai_integrator.RAG_API_URL
        samai_integrator.RAG_API_URL = "http://localhost:8001"
    
    queries = [
        "Bu fırsat için ana teknik gereksinimler nelerdir ve geçmiş benzer fırsatlardan öğrenilen başarı faktörleri nelerdir?",
        "Bu fırsatta en kritik başarı faktörleri nelerdir?",
        "Benzer geçmiş fırsatlarda hangi yaklaşımlar başarılı oldu?"
    ]
    
    query = queries[0]  # İlk soruyu kullan
    
    print(f"\n  Soru: {query}")
    print(f"  Notice ID: {NOTICE_ID}")
    print(f"  Agency: {agency}")
    print("\n  RAG servisi calisiyor...")
    
    result = call_rag_proposal_service(
        user_query=query,
        notice_id=NOTICE_ID,
        agency=agency if agency != "Unknown" else None
    )
    
    if use_localhost:
        samai_integrator.RAG_API_URL = original_url
    
    # 4. Sonuçları göster
    print("\n[4/4] Sonuclar:")
    print("=" * 70)
    
    if result.get("status") == "success":
        print("\n[SUCCESS] Teklif basariyla olusturuldu!")
        print("\n" + "-" * 70)
        print("TEKLIF TASLAGI:")
        print("-" * 70)
        proposal = result['result']['proposal_draft']
        print(proposal)
        
        print("\n" + "-" * 70)
        print("KAYNAKLAR:")
        print("-" * 70)
        sources = result.get('sources', [])
        print(f"Toplam {len(sources)} kaynak kullanildi:\n")
        
        for i, source in enumerate(sources[:5], 1):  # İlk 5 kaynağı göster
            print(f"{i}. Belge ID: {source.get('document_id', 'N/A')}")
            print(f"   Benzerlik: {source.get('similarity', 0):.2f}")
            print(f"   Ozet: {source.get('text_preview', 'N/A')[:150]}...")
            print()
        
        if len(sources) > 5:
            print(f"... ve {len(sources) - 5} kaynak daha")
        
        print("\n" + "-" * 70)
        print("METRIKLER:")
        print("-" * 70)
        metrics = result.get('result', {})
        print(f"Kullanilan context sayisi: {metrics.get('context_used', 'N/A')}")
        print(f"Target Agency: {metrics.get('target_agency', 'N/A')}")
        print(f"Notice ID: {metrics.get('notice_id', 'N/A')}")
        
    elif result.get("status") == "warning":
        print("\n[WARNING] Teklif olusturuldu ama uyari var:")
        print(f"  Mesaj: {result.get('message')}")
        if result.get('result'):
            print("\nTeklif Taslagi:")
            print(result['result'].get('proposal_draft', 'N/A'))
    else:
        print(f"\n[ERROR] Teklif olusturulamadi!")
        print(f"  Status: {result.get('status')}")
        print(f"  Mesaj: {result.get('message', 'Bilinmeyen hata')}")
        print("\nOneriler:")
        print("  1. RAG API servisinin calistigindan emin olun:")
        print("     docker-compose up -d rag_api")
        print("  2. Veritabaninin erisilebilir oldugundan emin olun")
        print("  3. LLM servisinin calistigindan emin olun (Ollama/OpenAI)")
    
    print("\n" + "=" * 70)
    print("TEST TAMAMLANDI")
    print("=" * 70)
    
except ImportError as e:
    print(f"\n[ERROR] Modul import hatasi: {e}")
    print("  samai_integrator.py dosyasinin mevcut oldugundan emin olun")
except Exception as e:
    print(f"\n[ERROR] Beklenmeyen hata: {e}")
    import traceback
    traceback.print_exc()

