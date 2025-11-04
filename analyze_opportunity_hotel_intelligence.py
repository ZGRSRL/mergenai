#!/usr/bin/env python3
"""
SAM.gov Fırsatı için Hotel Intelligence Analizi
Fırsat: 086008536ec84226ad9de043dc738d06
"""

import sys
import json
from datetime import datetime
from hotel_intelligence_bridge import (
    check_zgrprop_connectivity,
    quick_hotel_analysis,
    get_enhanced_sow_workflow
)
from sam_api_client import SAMAPIClient

NOTICE_ID = "086008536ec84226ad9de043dc738d06"
SAM_URL = "https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view"


def get_opportunity_info(notice_id: str) -> dict:
    """Fırsat bilgilerini al"""
    try:
        client = SAMAPIClient()
        details = client.get_opportunity_details(notice_id)
        
        if details:
            return {
                "title": details.get("title", "N/A"),
                "agency": details.get("department", {}).get("name", "N/A") if isinstance(details.get("department"), dict) else details.get("department", "N/A"),
                "description": details.get("description", ""),
                "posted_date": details.get("postedDate", "N/A"),
                "response_deadline": details.get("responseDeadline", "N/A"),
                "naics_code": details.get("naicsCodes", [{}])[0].get("code", "N/A") if details.get("naicsCodes") else "N/A",
                "point_of_contact": details.get("pointOfContact", {}).get("name", "N/A") if isinstance(details.get("pointOfContact"), dict) else "N/A"
            }
        return None
    except Exception as e:
        print(f"⚠️ Fırsat bilgileri alınamadı: {e}")
        return None


def analyze_opportunity():
    """Fırsat için Hotel Intelligence analizi yap"""
    
    print("=" * 80)
    print("🏨 SAM.gov Fırsatı - Hotel Intelligence Analizi")
    print("=" * 80)
    print(f"\n📋 Fırsat ID: {NOTICE_ID}")
    print(f"🔗 URL: {SAM_URL}\n")
    
    # 1. Fırsat bilgilerini al
    print("📊 Fırsat bilgileri alınıyor...")
    opp_info = get_opportunity_info(NOTICE_ID)
    
    if opp_info:
        print(f"\n✅ Fırsat Bulundu:")
        print(f"   📌 Başlık: {opp_info['title']}")
        print(f"   🏛️  Ajans: {opp_info['agency']}")
        print(f"   📅 Yayın Tarihi: {opp_info['posted_date']}")
        print(f"   ⏰ Yanıt Son Tarihi: {opp_info['response_deadline']}")
        print(f"   🏷️  NAICS: {opp_info['naics_code']}")
    else:
        print("⚠️ Fırsat bilgileri alınamadı, genel analiz yapılacak")
        opp_info = {"agency": "Department of Defense"}  # Default
    
    # 2. ZgrProp bağlantısını kontrol et
    print("\n🔌 ZgrProp RAG API bağlantısı kontrol ediliyor...")
    connectivity = check_zgrprop_connectivity()
    
    if not connectivity.get("connected"):
        print(f"❌ HATA: ZgrProp RAG API'ye bağlanılamadı!")
        print(f"   URL: {connectivity.get('message', 'Unknown error')}")
        print("\n💡 Çözüm:")
        print("   1. ZgrProp'u başlatın: cd d:\\Zgrprop && docker-compose up rag_api")
        print("   2. API'nin http://localhost:8001 adresinde çalıştığından emin olun")
        return
    
    print("✅ ZgrProp RAG API'ye bağlanıldı")
    
    # 3. Hotel Intelligence analizi
    print("\n🔍 Hotel Intelligence analizi başlatılıyor...")
    print("   📝 Analiz konuları:")
    print("      - Conference room requirements")
    print("      - Military base accommodations")
    print("      - Hotel services compliance")
    print("      - Government pricing intelligence")
    
    analysis_queries = [
        "conference room military base requirements and specifications",
        "hotel accommodations for government contracts compliance",
        "military base hotel services pricing and per diem rates",
        "conference facility AV equipment capacity catering requirements"
    ]
    
    results = []
    
    for i, query in enumerate(analysis_queries, 1):
        print(f"\n   📌 Analiz {i}/{len(analysis_queries)}: {query[:50]}...")
        
        result = quick_hotel_analysis(
            notice_id=NOTICE_ID,
            query=query,
            agency=opp_info.get("agency", "Department of Defense"),
            topk=15
        )
        
        if result.get("status") == "success":
            results.append({
                "query": query,
                "proposal": result.get("proposal_draft", ""),
                "sources": result.get("source_count", 0),
                "length": result.get("response_length", 0)
            })
            print(f"      ✅ Başarılı: {result.get('source_count')} kaynak, {result.get('response_length')} karakter")
        else:
            print(f"      ❌ Hata: {result.get('message', 'Unknown error')}")
    
    # 4. Enhanced SOW Workflow analizi
    print("\n🔄 Enhanced SOW Workflow analizi...")
    workflow_result = get_enhanced_sow_workflow(
        notice_id=NOTICE_ID,
        query="comprehensive hotel and conference room requirements for military base contract",
        agency=opp_info.get("agency", "Department of Defense")
    )
    
    if workflow_result.get("status") == "success":
        print(f"   ✅ Workflow tamamlandı")
        print(f"   📊 Güven skoru: {workflow_result.get('confidence', 0):.2%}")
        print(f"   📚 Kaynak sayısı: {workflow_result.get('source_count', 0)}")
    
    # 5. Sonuçları özetle
    print("\n" + "=" * 80)
    print("📊 ANALİZ SONUÇLARI ÖZETİ")
    print("=" * 80)
    
    if results:
        total_sources = sum(r["sources"] for r in results)
        total_length = sum(r["length"] for r in results)
        
        print(f"\n✅ Toplam Analiz: {len(results)}")
        print(f"📚 Toplam Kaynak: {total_sources}")
        print(f"📝 Toplam İçerik: {total_length:,} karakter")
        
        print("\n📋 Detaylı Sonuçlar:")
        for i, r in enumerate(results, 1):
            print(f"\n   {i}. {r['query'][:60]}...")
            print(f"      Kaynak: {r['sources']}, Uzunluk: {r['length']:,} karakter")
            print(f"      Önizleme: {r['proposal'][:150]}...")
    
    if workflow_result.get("status") == "success":
        print(f"\n🎯 Enhanced Workflow Güven Skoru: {workflow_result.get('confidence', 0):.2%}")
    
    # 6. JSON olarak kaydet
    output_file = f"hotel_intelligence_analysis_{NOTICE_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_data = {
        "notice_id": NOTICE_ID,
        "url": SAM_URL,
        "opportunity_info": opp_info,
        "analysis_timestamp": datetime.now().isoformat(),
        "analysis_results": results,
        "workflow_result": workflow_result,
        "summary": {
            "total_analyses": len(results),
            "total_sources": sum(r["sources"] for r in results) if results else 0,
            "total_length": sum(r["length"] for r in results) if results else 0,
            "confidence": workflow_result.get("confidence", 0) if workflow_result.get("status") == "success" else 0
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Sonuçlar kaydedildi: {output_file}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        analyze_opportunity()
    except KeyboardInterrupt:
        print("\n\n⚠️ Analiz kullanıcı tarafından durduruldu")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

