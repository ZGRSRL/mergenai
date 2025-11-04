#!/usr/bin/env python3
"""
Compliance Matrix Agent
SOW maddelerini teklif dokümanındaki karşılıklarıyla eşleştirir, gap listesi üretir
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import sys
import os
sys.path.append('.')

logger = logging.getLogger(__name__)

class ComplianceMatrixAgent:
    """SOW-Teklif uyumluluk analizi"""
    
    def __init__(self):
        self.logger = logging.getLogger("ComplianceMatrixAgent")
    
    def analyze_compliance(self, sow_payload: Dict, proposal_text: str) -> Dict[str, Any]:
        """SOW ve teklif arasında uyumluluk analizi yapar"""
        
        # SOW gereksinimlerini çıkar
        sow_requirements = self._extract_sow_requirements(sow_payload)
        
        # Teklif metnini analiz et
        proposal_analysis = self._analyze_proposal_text(proposal_text)
        
        # Uyumluluk matrisi oluştur
        compliance_matrix = self._create_compliance_matrix(sow_requirements, proposal_analysis)
        
        # Gap listesi oluştur
        gaps = self._identify_gaps(compliance_matrix)
        
        return {
            "sow_requirements": sow_requirements,
            "proposal_analysis": proposal_analysis,
            "compliance_matrix": compliance_matrix,
            "gaps": gaps,
            "compliance_score": self._calculate_compliance_score(compliance_matrix),
            "analysis_date": datetime.now().isoformat()
        }
    
    def _extract_sow_requirements(self, sow_payload: Dict) -> List[Dict[str, Any]]:
        """SOW'dan gereksinimleri çıkarır"""
        requirements = []
        
        # Temel gereksinimler
        if sow_payload.get('function_space'):
            fs = sow_payload['function_space']
            if fs.get('general_session', {}).get('capacity'):
                requirements.append({
                    "category": "Capacity",
                    "requirement": f"General session capacity: {fs['general_session']['capacity']}",
                    "type": "mandatory",
                    "priority": "high"
                })
            
            if fs.get('breakout_rooms', {}).get('count'):
                requirements.append({
                    "category": "Rooms",
                    "requirement": f"Breakout rooms: {fs['breakout_rooms']['count']}",
                    "type": "mandatory",
                    "priority": "high"
                })
        
        if sow_payload.get('room_block'):
            rb = sow_payload['room_block']
            if rb.get('total_rooms_per_night'):
                requirements.append({
                    "category": "Accommodation",
                    "requirement": f"Rooms per night: {rb['total_rooms_per_night']}",
                    "type": "mandatory",
                    "priority": "high"
                })
        
        if sow_payload.get('av', {}).get('projector_lumens'):
            requirements.append({
                "category": "AV Equipment",
                "requirement": f"Projector lumens: {sow_payload['av']['projector_lumens']}",
                "type": "technical",
                "priority": "medium"
            })
        
        if sow_payload.get('tax_exemption'):
            requirements.append({
                "category": "Legal",
                "requirement": "Tax exemption compliance",
                "type": "legal",
                "priority": "high"
            })
        
        return requirements
    
    def _analyze_proposal_text(self, proposal_text: str) -> Dict[str, Any]:
        """Teklif metnini analiz eder"""
        # Basit anahtar kelime analizi (gerçek uygulamada NLP kullanılabilir)
        keywords = {
            "capacity": ["capacity", "seating", "attendees", "participants"],
            "rooms": ["room", "breakout", "meeting", "conference"],
            "accommodation": ["hotel", "lodging", "accommodation", "rooms"],
            "av": ["projector", "audio", "visual", "equipment", "lumens"],
            "legal": ["tax", "exemption", "compliance", "certification"]
        }
        
        found_keywords = {}
        for category, words in keywords.items():
            found_keywords[category] = []
            for word in words:
                if word.lower() in proposal_text.lower():
                    found_keywords[category].append(word)
        
        return {
            "text_length": len(proposal_text),
            "found_keywords": found_keywords,
            "coverage_score": sum(len(v) for v in found_keywords.values()) / sum(len(v) for v in keywords.values())
        }
    
    def _create_compliance_matrix(self, requirements: List[Dict], proposal_analysis: Dict) -> List[Dict[str, Any]]:
        """Uyumluluk matrisi oluşturur"""
        matrix = []
        
        for req in requirements:
            category = req['category'].lower()
            found_keywords = proposal_analysis['found_keywords'].get(category, [])
            
            # Basit eşleşme kontrolü
            is_covered = len(found_keywords) > 0
            
            matrix.append({
                "requirement": req['requirement'],
                "category": req['category'],
                "type": req['type'],
                "priority": req['priority'],
                "is_covered": is_covered,
                "evidence": found_keywords,
                "confidence": len(found_keywords) / 3.0  # 0-1 arası güven skoru
            })
        
        return matrix
    
    def _identify_gaps(self, compliance_matrix: List[Dict]) -> List[Dict[str, Any]]:
        """Gap listesi oluşturur"""
        gaps = []
        
        for item in compliance_matrix:
            if not item['is_covered']:
                gaps.append({
                    "requirement": item['requirement'],
                    "category": item['category'],
                    "priority": item['priority'],
                    "gap_type": "missing",
                    "recommendation": f"Add section covering {item['requirement']}"
                })
            elif item['confidence'] < 0.5:
                gaps.append({
                    "requirement": item['requirement'],
                    "category": item['category'],
                    "priority": item['priority'],
                    "gap_type": "insufficient",
                    "recommendation": f"Strengthen coverage of {item['requirement']}"
                })
        
        return gaps
    
    def _calculate_compliance_score(self, compliance_matrix: List[Dict]) -> float:
        """Uyumluluk skoru hesaplar"""
        if not compliance_matrix:
            return 0.0
        
        total_weight = 0
        weighted_score = 0
        
        for item in compliance_matrix:
            weight = 3 if item['priority'] == 'high' else 2 if item['priority'] == 'medium' else 1
            total_weight += weight
            
            if item['is_covered']:
                weighted_score += weight * item['confidence']
        
        return (weighted_score / total_weight) * 100 if total_weight > 0 else 0.0

def generate_compliance_pdf(compliance_data: Dict, notice_id: str, output_path: str):
    """Compliance matrix'i PDF'e dönüştürür"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    story.append(Paragraph(f"Compliance Matrix Report - {notice_id}", title_style))
    story.append(Spacer(1, 20))
    
    # Summary
    story.append(Paragraph("Summary", styles['Heading2']))
    story.append(Paragraph(f"Compliance Score: {compliance_data['compliance_score']:.1f}%", styles['Normal']))
    story.append(Paragraph(f"Total Requirements: {len(compliance_data['compliance_matrix'])}", styles['Normal']))
    story.append(Paragraph(f"Gaps Identified: {len(compliance_data['gaps'])}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Compliance Matrix Table
    story.append(Paragraph("Compliance Matrix", styles['Heading2']))
    
    matrix_data = [['Requirement', 'Category', 'Covered', 'Confidence', 'Evidence']]
    for item in compliance_data['compliance_matrix']:
        matrix_data.append([
            item['requirement'],
            item['category'],
            'Yes' if item['is_covered'] else 'No',
            f"{item['confidence']:.2f}",
            ', '.join(item['evidence'])
        ])
    
    matrix_table = Table(matrix_data, colWidths=[2*inch, 1*inch, 0.8*inch, 0.8*inch, 2*inch])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ]))
    
    story.append(matrix_table)
    story.append(Spacer(1, 20))
    
    # Gaps Section
    if compliance_data['gaps']:
        story.append(Paragraph("Identified Gaps", styles['Heading2']))
        
        gaps_data = [['Requirement', 'Priority', 'Gap Type', 'Recommendation']]
        for gap in compliance_data['gaps']:
            gaps_data.append([
                gap['requirement'],
                gap['priority'],
                gap['gap_type'],
                gap['recommendation']
            ])
        
        gaps_table = Table(gaps_data, colWidths=[2*inch, 1*inch, 1*inch, 2*inch])
        gaps_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        
        story.append(gaps_table)
    
    doc.build(story)
    return True

# Test function
def test_compliance_analysis():
    """Test compliance analysis"""
    agent = ComplianceMatrixAgent()
    
    # Sample SOW payload
    sow_payload = {
        "function_space": {
            "general_session": {"capacity": 120},
            "breakout_rooms": {"count": 4}
        },
        "room_block": {
            "total_rooms_per_night": 80
        },
        "av": {
            "projector_lumens": 5000
        },
        "tax_exemption": True
    }
    
    # Sample proposal text
    proposal_text = """
    Our proposal includes accommodation for 80 rooms per night with 4 breakout rooms.
    The general session can accommodate 120 participants. We provide high-quality
    audio-visual equipment including projectors with 5000 lumens. All services
    comply with tax exemption requirements.
    """
    
    result = agent.analyze_compliance(sow_payload, proposal_text)
    
    print(f"Compliance Score: {result['compliance_score']:.1f}%")
    print(f"Gaps: {len(result['gaps'])}")
    
    # Generate PDF
    output_path = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generate_compliance_pdf(result, "TEST001", output_path)
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    test_compliance_analysis()

