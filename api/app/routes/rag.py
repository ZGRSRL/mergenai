"""
RAG (Retrieval-Augmented Generation) API endpoints
Teklif oluşturma ve hibrit arama için RAG servisi
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from ..db import get_db
from ..services.llm.rag import search_documents, retrieve_context
from ..services.llm.router import generate_text
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ProposalRequest(BaseModel):
    """Teklif oluşturma isteği"""
    query: str
    target_agency: Optional[str] = None
    notice_id: Optional[str] = None
    hybrid_alpha: float = 0.6  # 0.0 (keyword) - 1.0 (semantic)
    topk: int = 15


class ProposalResponse(BaseModel):
    """Teklif oluşturma yanıtı"""
    status: str
    result: Optional[dict] = None
    message: Optional[str] = None
    sources: Optional[list] = None


@router.post("/generate_proposal", response_model=ProposalResponse)
async def generate_proposal(
    request: ProposalRequest,
    db: Session = Depends(get_db)
):
    """
    RAG kullanarak teklif taslağı oluştur
    
    Args:
        query: LLM'e sorulacak soru veya talimat
        target_agency: Hedef ajans (opsiyonel)
        notice_id: SAM.gov fırsat ID'si (opsiyonel)
        hybrid_alpha: Hibrit arama dengesi (0.0=keyword, 1.0=semantic)
        topk: Döndürülecek en üst kayıt sayısı
    
    Returns:
        LLM cevabı ve kaynakları içeren teklif taslağı
    """
    try:
        logger.info(f"Teklif oluşturma isteği: query={request.query[:50]}..., notice_id={request.notice_id}")
        
        # 1. RAG ile ilgili belgeleri bul
        logger.info("RAG arama başlatılıyor...")
        
        # Query'yi zenginleştir (notice_id varsa)
        augmented_query = request.query
        if request.notice_id:
            augmented_query = f"Notice ID {request.notice_id} için kullanıcı sorusu: {request.query}. Bu ilana benzer geçmiş fırsatlara göre teklif taslağı oluştur."
        
        # RAG ile ilgili context'i çek
        rag_results = search_documents(
            db=db,
            query=augmented_query,
            document_type=None,
            limit=request.topk
        )
        
        if not rag_results:
            logger.warning("RAG arama sonucu bulunamadı")
            return ProposalResponse(
                status="warning",
                message="İlgili belgeler bulunamadı. Genel teklif oluşturuluyor.",
                result={"proposal_draft": "Belgeler bulunamadığı için genel bir teklif oluşturulamadı."},
                sources=[]
            )
        
        # 2. Context'i birleştir
        context_parts = []
        for result in rag_results:
            context_parts.append(
                f"[Belge {result['document_id']}] (Benzerlik: {result['similarity']:.2f})\n"
                f"{result['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)
        
        # 3. LLM prompt'unu oluştur
        agency_info = f" için {request.target_agency}" if request.target_agency else ""
        notice_info = f" (Notice ID: {request.notice_id})" if request.notice_id else ""
        
        prompt = f"""Aşağıdaki geçmiş fırsatlar ve tekliflerden yararlanarak, {request.query}{agency_info}{notice_info} için kapsamlı bir teklif taslağı oluştur.

Geçmiş Fırsatlar ve Teklifler:
{context}

Görev:
1. Yukarıdaki geçmiş fırsatlardan öğrenilen bilgileri kullanarak
2. {request.query} için detaylı bir teklif taslağı hazırla
3. Geçmiş başarılı tekliflerdeki yaklaşımları adapte et
4. Kritik başarı faktörlerini ve riskleri belirt
5. Teknik yaklaşım, geçmiş performans ve fiyatlandırma bölümlerini içer

Teklif Taslağı:"""
        
        # 4. LLM ile teklif oluştur
        logger.info("LLM ile teklif oluşturuluyor...")
        proposal_draft = await generate_text(prompt)
        
        # 5. Kaynakları hazırla
        sources = [
            {
                "document_id": r["document_id"],
                "chunk_id": r["chunk_id"],
                "similarity": r["similarity"],
                "text_preview": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"]
            }
            for r in rag_results[:10]  # İlk 10 kaynağı göster
        ]
        
        logger.info(f"Teklif başarıyla oluşturuldu. Kaynak sayısı: {len(sources)}")
        
        return ProposalResponse(
            status="success",
            result={
                "proposal_draft": proposal_draft,
                "query": request.query,
                "target_agency": request.target_agency,
                "notice_id": request.notice_id,
                "context_used": len(rag_results)
            },
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Teklif oluşturma hatası: {e}", exc_info=True)
        return ProposalResponse(
            status="error",
            message=f"Teklif oluşturulurken hata oluştu: {str(e)}",
            result=None,
            sources=None
        )


@router.post("/hybrid_search")
async def hybrid_search(
    query: str,
    alpha: float = 0.6,
    topk: int = 10,
    db: Session = Depends(get_db)
):
    """
    Hibrit arama (keyword + semantic)
    
    Args:
        query: Arama sorgusu
        alpha: Hibrit ağırlık (0.0=keyword, 1.0=semantic)
        topk: Döndürülecek kayıt sayısı
    
    Returns:
        Hibrit arama sonuçları
    """
    try:
        # Şimdilik sadece semantic search (RAG)
        # Keyword search için full-text search eklenebilir
        results = search_documents(db, query, None, topk)
        
        return {
            "query": query,
            "alpha": alpha,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Hibrit arama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

