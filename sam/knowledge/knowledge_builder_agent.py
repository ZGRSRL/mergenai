#!/usr/bin/env python3
"""
KnowledgeBuilderAgent - Ana akıl
Eklerden öğren, teklife hazır bilgi üret
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from pathlib import Path
from .document_parsers import (
    load_attachments, parse_fire_safety, parse_wage_determination, 
    parse_invoice_template, parse_of347, parse_summary_sow_like,
    parse_accessibility, parse_insurance
)
from sow_analysis_manager import SOWAnalysisManager
from datetime import datetime

SCHEMA_VERSION = "sow.learn.v1"

class KnowledgeBuilderAgent:
    """Eklerden bilgi çıkarıp yapılandırılmış JSON üreten agent"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def build(self, notice_id: str) -> Dict[str, Any]:
        """Notice için knowledge facts oluştur"""
        print(f"Building knowledge for {notice_id}")
        
        # Attachments klasöründen dokümanları yükle
        att_dir = self.base_dir / "downloads" / notice_id
        docs = load_attachments(att_dir)
        
        if not docs:
            print(f"No attachments found for {notice_id}")
            return self._empty_knowledge(notice_id)
        
        print(f"Found {len(docs)} documents")
        
        # Bilgi toplama
        facts = {}
        rationales = []
        citations = []
        assumptions = []
        
        # Her dokümanı analiz et
        for doc in docs:
            print(f"Processing: {doc.filename}")
            doc_facts, doc_rationales, doc_citations = self._analyze_document(doc)
            
            # Facts'i birleştir
            facts = self._merge_facts(facts, doc_facts)
            rationales.extend(doc_rationales)
            citations.extend(doc_citations)
        
        # SOW'dan mevcut bilgileri al
        sow_data = self._get_sow_data(notice_id)
        if sow_data:
            facts = self._merge_sow_data(facts, sow_data)
        
        # Assumptions oluştur
        assumptions = self._generate_assumptions(facts)
        
        # Metrics hesapla
        metrics = self._calculate_metrics(facts, sow_data)
        
        # Final knowledge structure
        knowledge = {
            "schema_version": SCHEMA_VERSION,
            "meta": {
                "notice_id": notice_id,
                "generated_at": datetime.now().isoformat(),
                "total_documents": len(docs),
                "total_pages": sum(len(doc.pages) for doc in docs)
            },
            "requirements": facts.get("requirements", {}),
            "compliance": facts.get("compliance", {}),
            "finance": facts.get("finance", {}),
            "forms": facts.get("forms", {}),
            "insurance": facts.get("insurance", {}),
            "metrics": metrics,
            "assumptions": assumptions,
            "rationales": rationales,
            "citations": citations,
            "provenance": [{"file": doc.filename, "sha256": doc.sha256, "pages": len(doc.pages)} for doc in docs]
        }
        
        print(f"Knowledge built successfully: {len(rationales)} rationales, {len(citations)} citations")
        return knowledge
    
    def _analyze_document(self, doc) -> tuple:
        """Tek dokümanı analiz et"""
        filename_lower = doc.filename.lower()
        facts = {}
        rationales = []
        citations = []
        
        # Dosya adına göre parser seç
        if any(k in filename_lower for k in ["fire", "safety", "nfpa"]):
            result = parse_fire_safety(doc)
            facts["compliance"] = {"fire_safety_act_1990": result["compliance_required"]}
            if result.get("rationale"):
                rationales.append(result["rationale"])
            citations.extend(result.get("citations", []))
        
        elif any(k in filename_lower for k in ["wage", "determination", "sca"]):
            result = parse_wage_determination(doc)
            facts["compliance"] = {"sca_applicable": result["sca_applicable"]}
            if result.get("rationale"):
                rationales.append(result["rationale"])
        
        elif any(k in filename_lower for k in ["invoice", "template", "billing"]):
            result = parse_invoice_template(doc)
            facts["finance"] = {
                "tax_exempt": result["tax_exempt"],
                "invoice_fields": result["invoice_fields"]
            }
            if result.get("rationale"):
                rationales.append(result["rationale"])
        
        elif any(k in filename_lower for k in ["of347", "order", "supplies"]):
            result = parse_of347(doc)
            facts["forms"] = {"of347_required": result["of347_required"]}
            if result.get("rationale"):
                rationales.append(result["rationale"])
        
        elif any(k in filename_lower for k in ["accessibility", "ada", "disability"]):
            result = parse_accessibility(doc)
            facts["compliance"] = {"ada_compliance_required": result["ada_compliance_required"]}
            if result.get("rationale"):
                rationales.append(result["rationale"])
        
        elif any(k in filename_lower for k in ["insurance", "liability", "coverage"]):
            result = parse_insurance(doc)
            facts["insurance"] = {
                "general_liability_required": result["general_liability_required"],
                "workers_comp_required": result["workers_comp_required"],
                "auto_insurance_required": result["auto_insurance_required"],
                "coverage_amount": result["coverage_amount"]
            }
            if result.get("rationale"):
                rationales.append(result["rationale"])
        
        else:
            # SOW benzeri genel doküman
            result = parse_summary_sow_like(doc)
            if result:
                facts["requirements"] = result
                # Rationale oluştur
                if result.get("projector_lumens_min"):
                    rationales.append(f"Projector minimum brightness found as {result['projector_lumens_min']} lumens in {doc.filename}")
                if result.get("rooms_per_night"):
                    rationales.append(f"Room requirement found as {result['rooms_per_night']} rooms per night in {doc.filename}")
                if result.get("capacity"):
                    rationales.append(f"Capacity requirement found as {result['capacity']} participants in {doc.filename}")
        
        return facts, rationales, citations
    
    def _merge_facts(self, existing: Dict, new: Dict) -> Dict:
        """Facts'leri güvenli şekilde birleştir"""
        result = existing.copy()
        
        for key, value in new.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key].update(value)
            else:
                result[key] = value
        
        return result
    
    def _get_sow_data(self, notice_id: str) -> Dict[str, Any]:
        """SOW'dan mevcut bilgileri al"""
        try:
            mgr = SOWAnalysisManager()
            analysis = mgr.get_analysis(notice_id)
            if analysis and 'sow_payload' in analysis:
                return analysis['sow_payload']
        except Exception as e:
            print(f"SOW data retrieval error: {e}")
        return {}
    
    def _merge_sow_data(self, facts: Dict, sow_data: Dict) -> Dict:
        """SOW verilerini facts ile birleştir"""
        # Room block bilgisi
        if 'room_block' in sow_data:
            facts.setdefault("requirements", {}).update({
                "rooms_per_night": sow_data['room_block'].get('total_rooms_per_night'),
                "total_nights": sow_data['room_block'].get('total_nights')
            })
        
        # Function space bilgisi
        if 'function_space' in sow_data:
            general_session = sow_data['function_space'].get('general_session', {})
            if 'capacity' in general_session:
                facts.setdefault("requirements", {}).update({
                    "capacity": general_session['capacity']
                })
        
        # A/V bilgisi
        if 'av' in sow_data:
            facts.setdefault("requirements", {}).update({
                "av_requirements": sow_data['av']
            })
        
        return facts
    
    def _generate_assumptions(self, facts: Dict) -> List[str]:
        """Facts'e dayalı varsayımlar oluştur"""
        assumptions = []
        
        # A/V varsayımları
        if "av" in facts.get("requirements", {}):
            av_req = facts["requirements"]["av"]
            if "projector_lumens_min" in av_req:
                lumens = av_req["projector_lumens_min"]
                assumptions.append(f"If venue ambient light is high, {lumens} lumens remains minimum; higher may be preferable.")
        
        # Room varsayımları
        if "rooms_per_night" in facts.get("requirements", {}):
            rooms = facts["requirements"]["rooms_per_night"]
            assumptions.append(f"Room block of {rooms} rooms assumes standard double occupancy; single occupancy may require more rooms.")
        
        # Compliance varsayımları
        if facts.get("compliance", {}).get("fire_safety_act_1990"):
            assumptions.append("Fire safety compliance assumes venue has sprinkler systems and smoke detectors as required by law.")
        
        # Finance varsayımları
        if facts.get("finance", {}).get("tax_exempt"):
            assumptions.append("Tax exemption applies to all pricing; ensure proper documentation for tax-exempt status.")
        
        return assumptions
    
    def _calculate_metrics(self, facts: Dict, sow_data: Dict) -> Dict[str, Any]:
        """Metrics hesapla"""
        metrics = {}
        
        # Room metrics
        if "rooms_per_night" in facts.get("requirements", {}):
            metrics["room_block"] = {
                "total_rooms_per_night": facts["requirements"]["rooms_per_night"],
                "total_nights": facts["requirements"].get("total_nights", 1)
            }
        
        # Capacity metrics
        if "capacity" in facts.get("requirements", {}):
            metrics["capacity"] = facts["requirements"]["capacity"]
        
        # Duration metrics
        if "duration_days" in facts.get("requirements", {}):
            metrics["duration_days"] = facts["requirements"]["duration_days"]
        
        return metrics
    
    def _empty_knowledge(self, notice_id: str) -> Dict[str, Any]:
        """Boş knowledge structure"""
        return {
            "schema_version": SCHEMA_VERSION,
            "meta": {
                "notice_id": notice_id,
                "generated_at": datetime.now().isoformat(),
                "total_documents": 0,
                "total_pages": 0
            },
            "requirements": {},
            "compliance": {},
            "finance": {},
            "forms": {},
            "insurance": {},
            "metrics": {},
            "assumptions": [],
            "rationales": [],
            "citations": [],
            "provenance": []
        }

