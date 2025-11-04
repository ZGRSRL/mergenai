#!/usr/bin/env python3
"""
Gerçek verilerle AutoGen analizini tetikle
"""

import sys
import os
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities
from autogen_implementation import ZgrSamAutoGenOrchestrator, Document, DocumentType
from datetime import datetime

def trigger_autogen_analysis():
    """Gerçek verilerle AutoGen analizini başlat"""
    
    print("=== ZgrSam AutoGen Analizi Başlatılıyor ===")
    print(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print()
    
    # Veritabanı bağlantısı
    conn = create_database_connection()
    if not conn:
        print("[ERROR] Veritabani baglantisi basarisiz!")
        return
    
    # Canlı fırsatları al
    opportunities = get_live_sam_opportunities(conn, limit=3)
    if not opportunities:
        print("[ERROR] Hic firsat bulunamadi!")
        conn.close()
        return
    
    print(f"[OK] {len(opportunities)} gercek firsat alindi:")
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp['title'][:60]}...")
    print()
    
    # AutoGen orchestrator'ı başlat
    print("[ROBOT] AutoGen Multi-Agent Islemi Basliyor...")
    print()
    
    orchestrator = ZgrSamAutoGenOrchestrator()
    all_results = []
    
    # Her fırsat için AutoGen işlemi
    for opp_idx, opp in enumerate(opportunities, 1):
        print(f"[TARGET] Firsat {opp_idx} Isleniyor: {opp['title'][:50]}...")
        print("-" * 60)
        
        # Document oluştur
        document = Document(
            id=opp['id'],
            type=DocumentType.RFQ,
            title=opp['title'],
            content=opp['description'],
            metadata={
                'opportunity_id': opp['opportunity_id'],
                'posted_date': str(opp['posted_date']),
                'naics_code': opp['naics_code'],
                'contract_type': opp['contract_type'],
                'organization_type': opp['organization_type']
            }
        )
        
        print(f"[DOC] Document olusturuldu: {document.title[:40]}...")
        
        # Agent 1: Document Processor
        print("[AGENT1] Document Processor calisiyor...")
        doc_result = orchestrator.document_processor.process_document(document)
        print(f"[OK] Document islendi: {doc_result.get('id', 'N/A')}")
        
        # Agent 2: Requirements Extractor
        print("[AGENT2] Requirements Extractor calisiyor...")
        req_result = orchestrator.requirements_extractor.extract_requirements(document)
        requirements = req_result if isinstance(req_result, list) else req_result.get('requirements', [])
        print(f"[OK] {len(requirements)} gereksinim cikarildi")
        for i, req in enumerate(requirements[:3], 1):
            if isinstance(req, dict):
                print(f"   R-{i:03d}: {req.get('text', 'N/A')[:50]}...")
            else:
                print(f"   R-{i:03d}: {str(req)[:50]}...")
        if len(requirements) > 3:
            print(f"   ... ve {len(requirements)-3} gereksinim daha")
        
        # Agent 3: Compliance Analyst
        print("[AGENT3] Compliance Analyst calisiyor...")
        facility_data = {"capacity": 100, "breakout_rooms": 2, "location": "washington_dc"}
        comp_result = orchestrator.compliance_analyst.analyze_compliance(document, facility_data)
        compliance = comp_result if isinstance(comp_result, dict) else comp_result.get('compliance_matrix', {})
        print(f"[OK] Compliance analizi tamamlandi")
        print(f"   Karsilanan: {compliance.get('met_requirements', 0)}")
        print(f"   Toplam: {compliance.get('total_requirements', 0)}")
        print(f"   Risk: {compliance.get('overall_risk', 'N/A')}")
        
        # Agent 4: Pricing Specialist
        print("[AGENT4] Pricing Specialist calisiyor...")
        pricing_result = orchestrator.pricing_specialist.calculate_pricing(document)
        pricing = pricing_result if isinstance(pricing_result, dict) else pricing_result.get('pricing', {})
        print(f"[OK] Fiyatlandirma tamamlandi")
        print(f"   Toplam Fiyat: ${pricing.get('grand_total', 0):,.2f}")
        print(f"   Oda Blogu: ${pricing.get('room_block', {}).get('total', 0):,.2f}")
        print(f"   AV Ekipmani: ${pricing.get('av_equipment', {}).get('total', 0):,.2f}")
        
        # Agent 5: Proposal Writer
        print("[AGENT5] Proposal Writer calisiyor...")
        proposal_result = orchestrator.proposal_writer.write_proposal(document)
        proposal = proposal_result if isinstance(proposal_result, dict) else proposal_result.get('proposal_sections', {})
        print(f"[OK] Teklif yazildi")
        print(f"   Executive Summary: {proposal.get('executive_summary', 'N/A')[:100]}...")
        
        # Agent 6: Quality Assurance
        print("[AGENT6] Quality Assurance calisiyor...")
        qa_result = orchestrator.quality_assurance.review_quality(document)
        qa = qa_result if isinstance(qa_result, dict) else qa_result.get('quality_assurance', {})
        print(f"[OK] Kalite kontrolu tamamlandi")
        print(f"   Durum: {qa.get('approval_status', 'N/A')}")
        print(f"   Kalite: {qa.get('overall_quality', 'N/A')}")
        print(f"   Tamamlanma: {qa.get('completeness', 'N/A')}")
        
        # Fırsat sonucunu birleştir
        final_result = {
            'rfq_title': opp['title'],
            'requirements': requirements,
            'compliance_matrix': compliance,
            'pricing': pricing,
            'proposal_sections': proposal,
            'quality_assurance': qa,
            'detected_location': 'washington_dc',  # Varsayılan
            'hotels': []  # Şimdilik boş
        }
        
        all_results.append(final_result)
        
        print(f"[OK] Firsat {opp_idx} tamamlandi!")
        print("=" * 60)
        print()
    
    # Genel sonuçlar
    print("[RESULTS] GENEL ISLEM SONUCLARI")
    print("=" * 60)
    
    total_value = sum(r['pricing'].get('grand_total', 0) for r in all_results)
    total_requirements = sum(len(r['requirements']) for r in all_results)
    total_met = sum(r['compliance_matrix'].get('met_requirements', 0) for r in all_results)
    total_total = sum(r['compliance_matrix'].get('total_requirements', 0) for r in all_results)
    
    print(f"Islenen Firsat: {len(all_results)}")
    print(f"Toplam Gereksinim: {total_requirements}")
    print(f"Compliance Orani: {(total_met/total_total*100):.1f}%" if total_total > 0 else "Compliance Orani: 0%")
    print(f"Toplam Deger: ${total_value:,.2f}")
    print(f"Ortalama Fiyat: ${total_value/len(all_results):,.2f}")
    
    print()
    print("[SUCCESS] AutoGen analizi basariyla tamamlandi!")
    
    conn.close()
    return all_results

if __name__ == "__main__":
    results = trigger_autogen_analysis()
