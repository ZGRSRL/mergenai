#!/usr/bin/env python3
"""
Hotel Intelligence Bridge - ZgrProp RAG API Integration
ZgrSam için ZgrProp Hotel Intelligence (29,847 chunks, 7.2GB) köprüsü
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# RAG API URL - Docker içinde rag_api:8000, host makinede localhost:8001
# Environment variable'dan al, ama Docker içi adres (rag_api:8000) ise localhost'a çevir
env_url = os.getenv("RAG_API_URL", "http://localhost:8001")
if "rag_api:8000" in env_url or "rag_api" in env_url:
    # Host makineden çalışıyoruz, localhost kullan
    RAG_API_URL = "http://localhost:8001"
    logger.info(f"RAG_API_URL Docker içi adres tespit edildi, localhost'a çevriliyor: {RAG_API_URL}")
else:
    RAG_API_URL = env_url

RAG_API_TIMEOUT = int(os.getenv("RAG_API_TIMEOUT", "300"))


def check_zgrprop_connectivity() -> Dict[str, Any]:
    """
    ZgrProp RAG API bağlantısını kontrol eder.
    
    Returns:
        Bağlantı durumu dict'i
    """
    try:
        # Health endpoint /api/health veya root path'i dene
        health_urls = [
            f"{RAG_API_URL}/api/health",
            f"{RAG_API_URL}/health",
            f"{RAG_API_URL}/"
        ]
        
        response = None
        for url in health_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    break
            except:
                continue
        
        if not response or response.status_code != 200:
            raise requests.exceptions.ConnectionError("Health check failed")
        
        return {
            "status": "success",
            "connected": True,
            "url": RAG_API_URL,
            "response": response.json() if response.text else {}
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "connected": False,
            "message": f"ZgrProp RAG API'ye bağlanılamadı: {RAG_API_URL}"
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "message": f"Bağlantı kontrolü hatası: {str(e)}"
        }


def quick_hotel_analysis(
    notice_id: str,
    query: str,
    agency: Optional[str] = None,
    hybrid_alpha: float = 0.6,
    topk: int = 15
) -> Dict[str, Any]:
    """
    ZgrProp Hotel Intelligence kullanarak hızlı otel analizi yapar.
    
    Args:
        notice_id: SAM.gov fırsat ID'si
        query: Analiz edilecek soru/konu (örn: 'conference room military base requirements')
        agency: Ajans adı (opsiyonel)
        hybrid_alpha: Hibrit arama dengesi (0.0=keyword, 1.0=semantic)
        topk: Döndürülecek kayıt sayısı
    
    Returns:
        Analiz sonuçları ve kaynakları içeren dict
        
    Example:
        >>> result = quick_hotel_analysis(
        ...     '086008536ec84226ad9de043dc738d06',
        ...     'conference room military base requirements',
        ...     'Department of Defense'
        ... )
        >>> print(result['proposal_draft'][:200])
    """
    endpoint = f"{RAG_API_URL}/api/rag/generate_proposal"
    
    # Query'yi zenginleştir
    augmented_query = query
    if notice_id:
        augmented_query = f"Notice ID {notice_id}: {query}. Analyze hotel intelligence data for similar requirements."
    
    payload = {
        "query": augmented_query,
        "target_agency": agency,
        "notice_id": notice_id,
        "hybrid_alpha": hybrid_alpha,
        "topk": topk
    }
    
    try:
        logger.info(f"Hotel Intelligence analizi başlatılıyor: {query[:50]}...")
        
        response = requests.post(
            endpoint,
            json=payload,
            timeout=RAG_API_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("status") == "success":
            proposal = result.get("result", {}).get("proposal_draft", "")
            sources = result.get("sources", [])
            
            logger.info(f"Analiz tamamlandı: {len(proposal)} karakter, {len(sources)} kaynak")
            
            return {
                "status": "success",
                "proposal_draft": proposal,
                "sources": sources,
                "notice_id": notice_id,
                "query": query,
                "agency": agency,
                "source_count": len(sources),
                "response_length": len(proposal)
            }
        else:
            return {
                "status": "error",
                "message": result.get("message", "Bilinmeyen hata"),
                "result": result
            }
    
    except requests.exceptions.Timeout:
        error_msg = f"Zaman aşımı: {RAG_API_TIMEOUT}s içinde yanıt alınamadı"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except requests.exceptions.ConnectionError:
        error_msg = f"ZgrProp RAG API'ye bağlanılamadı: {RAG_API_URL}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP hatası: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    except Exception as e:
        error_msg = f"Hotel Intelligence analizi hatası: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}


def hybrid_search_hotel_intelligence(
    query: str,
    alpha: float = 0.6,
    topk: int = 10
) -> Dict[str, Any]:
    """
    Hotel Intelligence veritabanında hibrit arama yapar.
    
    Args:
        query: Arama sorgusu
        alpha: Hibrit ağırlık (0.0=keyword, 1.0=semantic)
        topk: Döndürülecek kayıt sayısı
    
    Returns:
        Arama sonuçları
    """
    endpoint = f"{RAG_API_URL}/api/rag/hybrid_search"
    
    params = {
        "query": query,
        "alpha": alpha,
        "topk": topk
    }
    
    try:
        response = requests.post(
            endpoint,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result
    
    except Exception as e:
        logger.error(f"Hibrit arama hatası: {e}")
        return {"status": "error", "message": str(e), "results": []}


def get_enhanced_sow_workflow(
    notice_id: str,
    query: str,
    agency: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gelişmiş SOW workflow'u ile birleşik analiz yapar.
    Hotel Intelligence + SOW analizi kombinasyonu.
    
    Args:
        notice_id: SAM.gov fırsat ID'si
        query: Analiz sorgusu
        agency: Ajans adı
    
    Returns:
        Birleşik analiz sonuçları ve güven skoru
    """
    # Hotel Intelligence analizi
    hotel_result = quick_hotel_analysis(
        notice_id=notice_id,
        query=query,
        agency=agency,
        topk=15
    )
    
    if hotel_result.get("status") != "success":
        return {
            "status": "error",
            "message": "Hotel Intelligence analizi başarısız",
            "hotel_result": hotel_result
        }
    
    # Güven skoru hesapla (kaynak sayısı ve uzunluk bazlı)
    source_count = hotel_result.get("source_count", 0)
    response_length = hotel_result.get("response_length", 0)
    
    # Basit güven skoru: kaynak sayısı ve içerik uzunluğu
    confidence = min(1.0, (source_count / 15.0) * 0.6 + min(1.0, response_length / 1000.0) * 0.4)
    
    return {
        "status": "success",
        "workflow_completed": True,
        "confidence": confidence,
        "hotel_intelligence": hotel_result,
        "source_count": source_count,
        "response_length": response_length
    }


if __name__ == "__main__":
    # Test için basit kullanım
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Hotel Intelligence Bridge Test")
    print("=" * 60)
    
    # Bağlantı kontrolü
    connectivity = check_zgrprop_connectivity()
    print(f"\n🔌 Bağlantı Durumu: {'✅ Bağlı' if connectivity.get('connected') else '❌ Bağlantı Yok'}")
    
    if connectivity.get("connected"):
        # Örnek analiz
        result = quick_hotel_analysis(
            notice_id="086008536ec84226ad9de043dc738d06",
            query="conference room military base requirements",
            agency="Department of Defense"
        )
        
        if result.get("status") == "success":
            print(f"\n✅ Analiz Başarılı!")
            print(f"📊 Kaynak Sayısı: {result.get('source_count')}")
            print(f"📝 Uzunluk: {result.get('response_length')} karakter")
            print(f"\n📄 Önizleme:\n{result.get('proposal_draft', '')[:200]}...")
        else:
            print(f"\n❌ Hata: {result.get('message')}")

