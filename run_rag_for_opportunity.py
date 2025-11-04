#!/usr/bin/env python3
"""
Bu script belirtilen SAM.gov fırsatı için RAG servisi çalıştırır
Fırsat: https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

NOTICE_ID = "086008536ec84226ad9de043dc738d06"
SAM_URL = "https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view"

def check_rag_api():
    """RAG API'nin çalışıp çalışmadığını kontrol et"""
    urls = [
        "http://localhost:8001/api/health",
        "http://rag_api:8000/api/health",
        "http://127.0.0.1:8001/api/health"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return url.replace("/api/health", "")
        except:
            continue
    
    return None

def main():
    print("=" * 70)
    print("SAM.GOV FIRSATI ICIN RAG SERVISI")
    print("=" * 70)
    print(f"\nFirsat ID: {NOTICE_ID}")
    print(f"URL: {SAM_URL}\n")
    
    # 1. RAG API kontrolü
    print("[1] RAG API kontrol ediliyor...")
    rag_url = check_rag_api()
    
    if not rag_url:
        print("\n[ERROR] RAG API calismiyor!")
        print("\nLutfen once servisi baslatin:")
        print("  docker-compose up -d rag_api")
        print("\nVeya servisin calistigindan emin olun:")
        print("  docker-compose ps rag_api")
        return 1
    
    print(f"[OK] RAG API erisilebilir: {rag_url}")
    
    # 2. Fırsat bilgilerini al (veritabanından veya varsayılan)
    print("\n[2] Firsat bilgileri hazirlaniyor...")
    agency = "Department of Defense"  # Varsayılan, gerçekte veritabanından alınabilir
    
    # 3. RAG servisi çağrısı
    print("\n[3] RAG servisi ile teklif olusturuluyor...")
    print("    Bu islem 30-300 saniye surebilir...\n")
    
    sys.path.insert(0, '.')
    from samai_integrator import call_rag_proposal_service
    
    # URL'yi güncelle
    import samai_integrator
    original_url = samai_integrator.RAG_API_URL
    samai_integrator.RAG_API_URL = rag_url
    
    try:
        query = (
            f"Bu SAM.gov fırsatı (Notice ID: {NOTICE_ID}) için kapsamlı bir teklif taslağı oluştur. "
            f"Geçmiş benzer fırsatlardan öğrenilen başarı faktörlerini, teknik gereksinimleri, "
            f"kritik başarısızlık noktalarını ve en iyi yaklaşımları dahil et."
        )
        
        print(f"Soru: {query[:100]}...")
        print(f"Notice ID: {NOTICE_ID}")
        print(f"Agency: {agency}\n")
        print("RAG servisi calisiyor, lutfen bekleyin...\n")
        
        start_time = time.time()
        result = call_rag_proposal_service(
            user_query=query,
            notice_id=NOTICE_ID,
            agency=agency
        )
        elapsed_time = time.time() - start_time
        
        # Sonuçları göster
        print("\n" + "=" * 70)
        print("SONUCLAR")
        print("=" * 70)
        print(f"\nIslem suresi: {elapsed_time:.1f} saniye\n")
        
        if result.get("status") == "success":
            print("[SUCCESS] Teklif basariyla olusturuldu!\n")
            
            proposal = result['result']['proposal_draft']
            print("-" * 70)
            print("TEKLIF TASLAGI:")
            print("-" * 70)
            print(proposal)
            print()
            
            # Kaynakları göster
            sources = result.get('sources', [])
            if sources:
                print("-" * 70)
                print(f"KAYNAKLAR ({len(sources)} adet):")
                print("-" * 70)
                for i, source in enumerate(sources[:5], 1):
                    print(f"\n{i}. Belge ID: {source.get('document_id')}")
                    print(f"   Benzerlik Skoru: {source.get('similarity', 0):.3f}")
                    preview = source.get('text_preview', '')[:200]
                    print(f"   Ozet: {preview}...")
                
                if len(sources) > 5:
                    print(f"\n... ve {len(sources) - 5} kaynak daha")
            
            # Metrikler
            metrics = result.get('result', {})
            print("\n" + "-" * 70)
            print("METRIKLER:")
            print("-" * 70)
            print(f"Kullanilan context: {metrics.get('context_used', 0)} belge")
            print(f"Target Agency: {metrics.get('target_agency', 'N/A')}")
            print(f"Notice ID: {metrics.get('notice_id', 'N/A')}")
            
            # Dosyaya kaydet
            output_file = f"proposal_{NOTICE_ID}_{int(time.time())}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"SAM.gov Fırsat Teklifi\n")
                f.write(f"{'=' * 70}\n")
                f.write(f"Notice ID: {NOTICE_ID}\n")
                f.write(f"URL: {SAM_URL}\n")
                f.write(f"Tarih: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'=' * 70}\n\n")
                f.write("TEKLİF TASLAĞI:\n")
                f.write(f"{'-' * 70}\n")
                f.write(proposal)
                f.write(f"\n\n{'-' * 70}\n")
                f.write(f"KAYNAKLAR ({len(sources)} adet):\n")
                for i, source in enumerate(sources, 1):
                    f.write(f"\n{i}. Belge ID: {source.get('document_id')}\n")
                    f.write(f"   Benzerlik: {source.get('similarity', 0):.3f}\n")
            
            print(f"\n[OK] Teklif dosyaya kaydedildi: {output_file}")
            
        else:
            print(f"[ERROR] Teklif olusturulamadi!")
            print(f"Status: {result.get('status')}")
            print(f"Mesaj: {result.get('message', 'Bilinmeyen hata')}")
            
            if "Connection" in str(result.get('message', '')):
                print("\nOneriler:")
                print("  1. RAG API servisinin calistigindan emin olun")
                print("  2. docker-compose up -d rag_api komutunu calistirin")
            return 1
        
        print("\n" + "=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        samai_integrator.RAG_API_URL = original_url

if __name__ == "__main__":
    sys.exit(main())

