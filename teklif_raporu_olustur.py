#!/usr/bin/env python3
"""
Teklif Raporu Oluşturucu
SOW analizi + Otel önerileri + Bütçe + Compliance = Detaylı teklif raporu
"""

import json
import os
from datetime import datetime
from pathlib import Path
from sam.knowledge.knowledge_repository import KnowledgeRepository
from sow_analysis_manager import SOWAnalysisManager
from sam.hotels.hotel_repository import list_hotel_suggestions
from budget_estimator import BudgetEstimatorAgent
from compliance_matrix_agent import ComplianceMatrixAgent

def teklif_raporu_olustur(notice_id: str) -> dict:
    """Detaylı teklif raporu oluştur"""
    print(f"Teklif raporu oluşturuluyor: {notice_id}")
    
    try:
        # 1. SOW Analizi
        print("1. SOW analizi yapılıyor...")
        sow_manager = SOWAnalysisManager()
        sow_analysis = sow_manager.get_analysis(notice_id)
        
        if not sow_analysis or 'sow_payload' not in sow_analysis:
            return {"status": "error", "message": "SOW analizi bulunamadı"}
        
        sow_payload = sow_analysis['sow_payload']
        
        # 2. Knowledge Facts
        print("2. Knowledge facts yükleniyor...")
        knowledge_repo = KnowledgeRepository()
        knowledge = knowledge_repo.latest(notice_id)
        
        # 3. Otel Önerileri
        print("3. Otel önerileri yükleniyor...")
        hotels = list_hotel_suggestions(notice_id, limit=10)
        
        # 4. Bütçe Tahmini
        print("4. Bütçe tahmini yapılıyor...")
        budget_agent = BudgetEstimatorAgent()
        budget = budget_agent.estimate_budget(sow_payload)  # SOW'dan bütçe tahmini
        
        # 5. Compliance Matrix
        print("5. Compliance matrix oluşturuluyor...")
        compliance_agent = ComplianceMatrixAgent()
        compliance = compliance_agent.analyze_compliance(sow_payload, "")  # Proposal yok, SOW vs SOW
        
        # 6. Teklif Raporu Oluştur
        print("6. Teklif raporu derleniyor...")
        
        rapor = {
            "notice_id": notice_id,
            "generated_at": datetime.now().isoformat(),
            "sow_analysis": {
                "period_of_performance": sow_payload.get('period_of_performance', {}),
                "room_requirements": sow_payload.get('room_block', {}),
                "capacity_requirements": sow_payload.get('function_space', {}),
                "av_requirements": sow_payload.get('av', {}),
                "location": sow_payload.get('location', {}),
                "assumptions": sow_payload.get('assumptions', [])
            },
            "knowledge_facts": {
                "compliance_requirements": knowledge['payload'].get('compliance', {}) if knowledge else {},
                "rationales": knowledge['payload'].get('rationales', []) if knowledge else [],
                "citations": knowledge['payload'].get('citations', []) if knowledge else []
            },
            "hotel_recommendations": {
                "total_found": len(hotels),
                "top_recommendations": hotels[:5],
                "selection_criteria": "Distance, match score, contact information availability"
            },
            "budget_analysis": {
                "total_estimated_cost": budget.get('total_estimated_cost', 0),
                "breakdown": budget.get('breakdown', {}),
                "assumptions": budget.get('assumptions', {})
            },
            "compliance_matrix": {
                "overall_score": compliance.get('overall_score', 0),
                "requirements_coverage": compliance.get('requirements_coverage', {}),
                "gaps": compliance.get('gaps', [])
            },
            "proposal_recommendations": {
                "critical_requirements": _extract_critical_requirements(sow_payload, knowledge),
                "pricing_strategy": _generate_pricing_strategy(budget, sow_payload),
                "risk_factors": _identify_risk_factors(sow_payload, knowledge),
                "competitive_advantages": _suggest_competitive_advantages(hotels, budget)
            }
        }
        
        # 7. Raporu kaydet
        rapor_dosyasi = f"Teklif_Raporu_{notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(rapor, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Teklif raporu oluşturuldu: {rapor_dosyasi}")
        return {
            "status": "success",
            "rapor_dosyasi": rapor_dosyasi,
            "rapor": rapor
        }
        
    except Exception as e:
        print(f"ERROR: Teklif raporu oluşturma hatası: {e}")
        return {"status": "error", "message": str(e)}

def _extract_critical_requirements(sow_payload, knowledge):
    """Kritik gereksinimleri çıkar"""
    critical = []
    
    # Room requirements
    if sow_payload.get('room_block', {}).get('total_rooms_per_night'):
        rooms = sow_payload['room_block']['total_rooms_per_night']
        critical.append(f"Minimum {rooms} oda/gece - Bu kritik gereksinim, daha az oda ile teklif verilemez")
    
    # Capacity requirements
    if sow_payload.get('function_space', {}).get('general_session', {}).get('capacity'):
        capacity = sow_payload['function_space']['general_session']['capacity']
        critical.append(f"Genel oturum kapasitesi {capacity} kişi - Venue bu kapasiteyi karşılamalı")
    
    # A/V requirements
    if sow_payload.get('av', {}).get('projector_lumens'):
        lumens = sow_payload['av']['projector_lumens']
        critical.append(f"Projektör minimum {lumens} lumen - Aydınlık ortamlar için kritik")
    
    # Knowledge'dan gelen kritik gereksinimler
    if knowledge and knowledge['payload'].get('compliance'):
        compliance = knowledge['payload']['compliance']
        if compliance.get('fire_safety_act_1990'):
            critical.append("Fire Safety Act 1990 uyumluluğu - Sprinkler ve duman dedektörü zorunlu")
        if compliance.get('sca_applicable'):
            critical.append("Service Contract Act uygulanabilir - Minimum ücret gereksinimleri")
    
    return critical

def _generate_pricing_strategy(budget, sow_payload):
    """Fiyatlandırma stratejisi öner"""
    strategy = []
    
    total_cost = budget.get('total_estimated_cost', 0)
    
    # Temel fiyatlandırma
    strategy.append(f"Temel teklif fiyatı: ${total_cost:,.2f}")
    
    # Rekabetçi fiyatlandırma
    competitive_price = total_cost * 0.95  # %5 indirim
    strategy.append(f"Rekabetçi fiyat (önerilen): ${competitive_price:,.2f} (%5 indirim)")
    
    # Premium fiyatlandırma
    premium_price = total_cost * 1.1  # %10 prim
    strategy.append(f"Premium fiyat (kalite vurgusu): ${premium_price:,.2f} (%10 prim)")
    
    # Fiyatlandırma faktörleri
    strategy.append("Fiyatlandırma faktörleri:")
    strategy.append("- Oda kalitesi ve konumu")
    strategy.append("- A/V ekipman kalitesi")
    strategy.append("- Catering kalitesi")
    strategy.append("- Ek hizmetler (transfer, 24/7 destek)")
    
    return strategy

def _identify_risk_factors(sow_payload, knowledge):
    """Risk faktörlerini belirle"""
    risks = []
    
    # Zaman riski
    if sow_payload.get('period_of_performance'):
        period = sow_payload['period_of_performance']
        if isinstance(period, dict) and period.get('start'):
            risks.append("Zaman riski: Kısa süreli proje, hızlı başlangıç gerekebilir")
    
    # Kapasite riski
    if sow_payload.get('function_space', {}).get('general_session', {}).get('capacity'):
        capacity = sow_payload['function_space']['general_session']['capacity']
        if capacity > 100:
            risks.append(f"Kapasite riski: {capacity} kişilik büyük grup, uygun venue bulma zorluğu")
    
    # Compliance riski
    if knowledge and knowledge['payload'].get('compliance'):
        compliance = knowledge['payload']['compliance']
        if compliance.get('fire_safety_act_1990'):
            risks.append("Compliance riski: Fire safety gereksinimleri, venue uyumluluğu kontrol edilmeli")
    
    # Lokasyon riski
    if sow_payload.get('location', {}).get('city'):
        city = sow_payload['location']['city']
        risks.append(f"Lokasyon riski: {city} şehrinde uygun venue ve otel bulma zorluğu")
    
    return risks

def _suggest_competitive_advantages(hotels, budget):
    """Rekabet avantajları öner"""
    advantages = []
    
    # Otel kalitesi
    if hotels:
        top_hotel = hotels[0]
        advantages.append(f"Premium otel seçimi: {top_hotel.get('name', 'N/A')} (Skor: {top_hotel.get('match_score', 0):.2f})")
    
    # Bütçe avantajı
    total_cost = budget.get('total_estimated_cost', 0)
    if total_cost > 0:
        advantages.append(f"Rekabetçi fiyatlandırma: ${total_cost:,.2f} - Piyasa ortalamasının altında")
    
    # Hizmet avantajları
    advantages.append("24/7 destek hizmeti")
    advantages.append("Esnek iptal politikası")
    advantages.append("Ücretsiz transfer hizmeti")
    advantages.append("Profesyonel A/V ekipman")
    
    return advantages

if __name__ == "__main__":
    # Test için 70LART26QPFB00001
    result = teklif_raporu_olustur("70LART26QPFB00001")
    
    if result["status"] == "success":
        print(f"\nSUCCESS: Teklif raporu başarıyla oluşturuldu!")
        print(f"File: {result['rapor_dosyasi']}")
        
        # Özet bilgileri göster
        rapor = result['rapor']
        print(f"\nRapor Özeti:")
        print(f"  - Notice ID: {rapor['notice_id']}")
        print(f"  - Otel önerisi: {rapor['hotel_recommendations']['total_found']} adet")
        print(f"  - Toplam maliyet: ${rapor['budget_analysis']['total_estimated_cost']:,.2f}")
        print(f"  - Compliance skoru: {rapor['compliance_matrix']['overall_score']:.1f}%")
        print(f"  - Kritik gereksinim: {len(rapor['proposal_recommendations']['critical_requirements'])} adet")
    else:
        print(f"ERROR: {result['message']}")
