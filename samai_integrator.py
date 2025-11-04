#!/usr/bin/env python3
"""
SAMAI Projesi - RAG Servisi Entegrasyonu
SAM.gov fırsatları için RAG servisini kullanarak teklif oluşturma
ZgrProp Hotel Intelligence (7GB data) entegrasyonu ile
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Docker Compose'da Servis Adı (rag_api) ve Port (8000) kullanılır.
# Harici bir sunucuda bu adresi, sunucunun IP'si ile değiştirmeniz gerekir.
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag_api:8000")
RAG_API_TIMEOUT = int(os.getenv("RAG_API_TIMEOUT", "300"))


def call_rag_proposal_service(
    user_query: str,
    notice_id: Optional[str] = None,
    agency: Optional[str] = None,
    hybrid_alpha: float = 0.6,
    topk: int = 15
) -> dict:
    """
    RAG API servisine POST isteği göndererek Teklif Taslağı oluşturur.
    
    Args:
        user_query: LLM'e sorulacak soru (örn: 'Bu fırsat için ana teknik gereksinimler').
        notice_id: Analiz edilecek SAM.gov Fırsatının ID'si.
        agency: Fırsatın sahibi olan Ajans.
        hybrid_alpha: Hibrit arama dengesi (0.0=keyword, 1.0=semantic, varsayılan: 0.6).
        topk: Döndürülecek en üst kayıt sayısı (varsayılan: 15).
        
    Returns:
        LLM'den gelen cevap ve kaynakları içeren JSON yanıtı.
        
    Example:
        >>> result = call_rag_proposal_service(
        ...     user_query="military base için otel hizmetlerinde en kritik başarısızlık noktaları nelerdir?",
        ...     notice_id="086008536ec84226ad9de043dc738d06",
        ...     agency="Department of Defense"
        ... )
        >>> if result.get("status") == "success":
        ...     print(result["result"]["proposal_draft"])
    """
    
    endpoint = f"{RAG_API_URL}/api/rag/generate_proposal"
    
    # Not: rag_api_service.py'de Notice ID almayan bir model oluşturduk.
    # Burada Notice ID'yi query içine ekleyerek bağlamı zenginleştirebiliriz.
    augmented_query = user_query
    if notice_id:
        augmented_query = f"Notice ID {notice_id} için kullanıcı sorusu: {user_query}. Bu ilana benzer geçmiş fırsatlara göre teklif taslağı oluştur."
    
    payload = {
        "query": augmented_query,
        "target_agency": agency,
        "notice_id": notice_id,
        "hybrid_alpha": hybrid_alpha,  # Dengeli arama
        "topk": topk
    }
    
    try:
        logger.info(f"RAG API'ye istek gönderiliyor: {endpoint}")
        logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            endpoint,
            json=payload,
            timeout=RAG_API_TIMEOUT  # LLM muhakemesi için uzun timeout
        )
        response.raise_for_status()  # HTTP hatalarını yakalar (4xx, 5xx)
        
        result = response.json()
        logger.info(f"RAG API'den başarılı yanıt alındı. Status: {result.get('status')}")
        
        return result
    
    except requests.exceptions.Timeout:
        error_msg = f"RAG API servisine bağlanırken zaman aşımı (timeout) oluştu. {RAG_API_TIMEOUT}s içinde yanıt alınamadı."
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except requests.exceptions.ConnectionError:
        error_msg = f"RAG API servisine bağlanılamadı. Docker konteyneri kontrol edin. URL: {RAG_API_URL}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"RAG API servisi HTTP hatası döndü: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"RAG API Servisine Bağlanılamadı veya Hata Döndü: {e}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}


def call_rag_hybrid_search(
    query: str,
    alpha: float = 0.6,
    topk: int = 10
) -> dict:
    """
    RAG API servisini kullanarak hibrit arama yapar.
    
    Args:
        query: Arama sorgusu
        alpha: Hibrit ağırlık (0.0=keyword, 1.0=semantic)
        topk: Döndürülecek kayıt sayısı
    
    Returns:
        Hibrit arama sonuçları
    """
    endpoint = f"{RAG_API_URL}/api/rag/hybrid_search"
    
    params = {
        "query": query,
        "alpha": alpha,
        "topk": topk
    }
    
    try:
        logger.info(f"RAG hibrit arama isteği gönderiliyor: {endpoint}")
        
        response = requests.post(
            endpoint,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Hibrit arama başarılı. {result.get('total', 0)} sonuç bulundu.")
        
        return result
    
    except Exception as e:
        logger.error(f"Hibrit arama hatası: {e}")
        return {"status": "error", "message": str(e), "results": []}


# --- Kullanım Örneği ---
if __name__ == '__main__':
    # Logging ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Canlı ilanınızdan alınan varsayımsal veriler
    ilan_id = "086008536ec84226ad9de043dc738d06"
    ilan_ajans = "Department of Defense"
    
    print("=" * 60)
    print("SAMAI RAG Servisi Entegrasyon Testi")
    print("=" * 60)
    
    result = call_rag_proposal_service(
        user_query="military base için otel hizmetlerinde en kritik başarısızlık noktaları nelerdir?",
        notice_id=ilan_id,
        agency=ilan_ajans
    )
    
    if result.get("status") == "success":
        print("\n✅ Teklif Taslağı Başarıyla Alındı!")
        print("\n" + "=" * 60)
        print("TEKLİF TASLAĞI:")
        print("=" * 60)
        print(result['result']['proposal_draft'])
        
        print("\n" + "=" * 60)
        print(f"KAYNAKLAR ({len(result.get('sources', []))} adet):")
        print("=" * 60)
        for i, source in enumerate(result.get('sources', [])[:5], 1):
            print(f"\n{i}. Belge ID: {source['document_id']}")
            print(f"   Benzerlik: {source['similarity']:.2f}")
            print(f"   Önizleme: {source['text_preview'][:100]}...")
    else:
        print("❌ Hata:", result.get("message"))
        print(f"Status: {result.get('status')}")

