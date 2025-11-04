#!/usr/bin/env python3
"""
AutoProposal Engine
SOW → Otel shortlist → Bütçe → Uyum → Teklif PDF (tek komut/tek buton)
"""

import sys
sys.path.append('.')

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import our agents
from sow_analysis_manager import SOWAnalysisManager
from sam.hotels.hotel_finder_agent import run_hotel_finder_from_sow
from sam.hotels.hotel_repository import save_hotel_suggestions, list_hotel_suggestions
from budget_estimator import BudgetEstimatorAgent
from compliance_matrix_agent import ComplianceMatrixAgent
from comprehensive_report_generator import ComprehensiveReportGenerator
from agent_log_manager import log_agent_action

logger = logging.getLogger(__name__)

class AutoProposalEngine:
    """AutoProposal Mode - Müşteriye hazır çıktı üretici"""
    
    def __init__(self):
        self.sow_manager = SOWAnalysisManager()
        self.budget_agent = BudgetEstimatorAgent()
        self.compliance_agent = ComplianceMatrixAgent()
        self.report_generator = ComprehensiveReportGenerator()
        
        # Snapshot klasörü oluştur
        self.snapshots_dir = Path("snapshots")
        self.snapshots_dir.mkdir(exist_ok=True)
    
    def generate_autoproposal(self, notice_id: str, proposal_text: str = None, 
                            selected_hotels: List[str] = None) -> Dict[str, Any]:
        """AutoProposal zincirini çalıştırır"""
        
        start_time = datetime.now()
        logger.info(f"Starting AutoProposal for {notice_id}")
        
        try:
            # 1. SOW Analizi
            logger.info("Step 1: SOW Analysis")
            sow_data = self.sow_manager.get_analysis(notice_id)
            if not sow_data:
                raise ValueError(f"No SOW analysis found for {notice_id}")
            
            sow_payload = sow_data['sow_payload']
            
            # 2. Otel Arama
            logger.info("Step 2: Hotel Search")
            hotels = run_hotel_finder_from_sow(sow_payload, notice_id)
            
            # Otelleri veritabanına kaydet
            save_hotel_suggestions(notice_id, hotels)
            
            # Seçili otelleri belirle
            if selected_hotels:
                # Belirtilen otelleri seç
                for hotel in hotels:
                    if hotel['name'] in selected_hotels:
                        hotel['selected'] = True
            else:
                # Top-3 otomatik seç
                for i, hotel in enumerate(hotels[:3]):
                    hotel['selected'] = True
            
            # 3. Bütçe Tahmini
            logger.info("Step 3: Budget Estimation")
            budget_data = self.budget_agent.estimate_budget(sow_payload)
            
            # 4. Compliance Analizi
            logger.info("Step 4: Compliance Analysis")
            compliance_data = None
            if proposal_text:
                compliance_data = self.compliance_agent.analyze_compliance(sow_payload, proposal_text)
            
            # 5. Snapshot Oluştur
            logger.info("Step 5: Creating Snapshot")
            snapshot_path = self._create_snapshot(notice_id, sow_payload, hotels, budget_data, compliance_data)
            
            # 6. AutoProposal PDF Oluştur
            logger.info("Step 6: Generating AutoProposal PDF")
            pdf_path = self._generate_autoproposal_pdf(notice_id, sow_payload, hotels, budget_data, compliance_data)
            
            # 7. Agent Log
            processing_time = (datetime.now() - start_time).total_seconds()
            log_agent_action(
                agent_name="AutoProposalEngine",
                notice_id=notice_id,
                action="generate_autoproposal",
                input_data={"notice_id": notice_id, "hotels_count": len(hotels)},
                output_data={"pdf_path": pdf_path, "snapshot_path": snapshot_path},
                processing_time=processing_time,
                status="success",
                schema_version="autoproposal.v1.0"
            )
            
            return {
                "status": "success",
                "notice_id": notice_id,
                "pdf_path": pdf_path,
                "snapshot_path": snapshot_path,
                "hotels_count": len(hotels),
                "selected_hotels": [h['name'] for h in hotels if h.get('selected')],
                "budget_total": budget_data['total'],
                "compliance_score": compliance_data['compliance_score'] if compliance_data else None,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"AutoProposal failed for {notice_id}: {e}")
            
            # Error log
            log_agent_action(
                agent_name="AutoProposalEngine",
                notice_id=notice_id,
                action="generate_autoproposal",
                input_data={"notice_id": notice_id},
                output_data={"error": str(e)},
                processing_time=(datetime.now() - start_time).total_seconds(),
                status="error",
                error_message=str(e),
                error_type="autoproposal_error"
            )
            
            return {
                "status": "error",
                "notice_id": notice_id,
                "error": str(e)
            }
    
    def _create_snapshot(self, notice_id: str, sow_payload: Dict, hotels: List[Dict], 
                        budget_data: Dict, compliance_data: Dict) -> str:
        """Snapshot oluşturur"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = self.snapshots_dir / notice_id / timestamp
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # SOW snapshot
        with open(snapshot_dir / "sow.json", 'w', encoding='utf-8') as f:
            json.dump(sow_payload, f, indent=2, ensure_ascii=False)
        
        # Hotels snapshot
        with open(snapshot_dir / "hotels.json", 'w', encoding='utf-8') as f:
            json.dump(hotels, f, indent=2, ensure_ascii=False)
        
        # Budget snapshot
        with open(snapshot_dir / "budget.json", 'w', encoding='utf-8') as f:
            json.dump(budget_data, f, indent=2, ensure_ascii=False)
        
        # Compliance snapshot
        if compliance_data:
            with open(snapshot_dir / "compliance.json", 'w', encoding='utf-8') as f:
                json.dump(compliance_data, f, indent=2, ensure_ascii=False)
        
        # Metadata
        metadata = {
            "notice_id": notice_id,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": ["sow.json", "hotels.json", "budget.json"]
        }
        if compliance_data:
            metadata["files"].append("compliance.json")
        
        with open(snapshot_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return str(snapshot_dir)
    
    def _generate_autoproposal_pdf(self, notice_id: str, sow_payload: Dict, hotels: List[Dict], 
                                  budget_data: Dict, compliance_data: Dict) -> str:
        """AutoProposal PDF oluşturur"""
        
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # PDF dosya adı
        pdf_filename = f"Proposal_{notice_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_path = pdf_filename
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story.append(Paragraph(f"AutoProposal - {notice_id}", title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        selected_hotels = [h for h in hotels if h.get('selected')]
        summary_text = f"""
        This AutoProposal provides a comprehensive solution for opportunity {notice_id}, 
        including {len(selected_hotels)} selected hotel options with an estimated budget of 
        ${budget_data['total']:,.2f}. The proposal includes SOW compliance analysis and 
        detailed cost breakdown for immediate client presentation.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Selected Hotels Section
        story.append(Paragraph("Selected Hotel Recommendations", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        if selected_hotels:
            hotel_data = [['Hotel Name', 'Distance (km)', 'Match Score', 'Phone', 'Address']]
            for hotel in selected_hotels:
                hotel_data.append([
                    hotel['name'] or 'N/A',
                    f"{hotel['distance_km']:.2f}" if hotel['distance_km'] else 'N/A',
                    f"{hotel['match_score']:.3f}" if hotel['match_score'] else 'N/A',
                    hotel['phone'] or 'N/A',
                    (hotel['address'] or 'N/A')[:50] + '...' if hotel['address'] and len(hotel['address']) > 50 else (hotel['address'] or 'N/A')
                ])
            
            hotel_table = Table(hotel_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.2*inch, 2*inch])
            hotel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(hotel_table)
        else:
            story.append(Paragraph("No hotels selected for this proposal.", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Budget Section
        story.append(Paragraph("Budget Breakdown", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        budget_data_table = [
            ['Category', 'Amount (USD)', 'Description'],
            ['Accommodation', f"{budget_data['accommodation']:,.2f}", 
             f"{budget_data['parameters']['rooms_per_night']} rooms × {budget_data['parameters']['total_nights']} nights"],
            ['AV Equipment', f"{budget_data['av_equipment']:,.2f}", 
             f"{budget_data['parameters']['duration_days']} days"],
            ['Catering', f"{budget_data['catering']:,.2f}", 
             f"{budget_data['parameters']['capacity']} people × {budget_data['parameters']['duration_days']} days"],
            ['Meeting Rooms', f"{budget_data['meeting_rooms']:,.2f}", 
             f"{budget_data['parameters']['breakout_rooms']} rooms × {budget_data['parameters']['duration_days']} days"],
            ['Setup Fee', f"{budget_data['setup']:,.2f}", 'One-time setup'],
            ['Subtotal', f"{budget_data['subtotal']:,.2f}", ''],
            ['Tax', f"{budget_data['tax']:,.2f}", f"{budget_data['pricing_rates']['tax_rate']*100:.1f}%"],
            ['TOTAL', f"{budget_data['total']:,.2f}", '']
        ]
        
        budget_table = Table(budget_data_table, colWidths=[1.5*inch, 1.2*inch, 3*inch])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, -2), (-1, -1), colors.darkblue),
            ('TEXTCOLOR', (0, -2), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold')
        ]))
        
        story.append(budget_table)
        story.append(Spacer(1, 20))
        
        # Compliance Section (if available)
        if compliance_data:
            story.append(Paragraph("Compliance Summary", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"Compliance Score: {compliance_data['compliance_score']:.1f}%", styles['Heading3']))
            story.append(Paragraph(f"Total Requirements: {len(compliance_data['compliance_matrix'])}", styles['Normal']))
            story.append(Paragraph(f"Gaps Identified: {len(compliance_data['gaps'])}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Generated by ZGR SAM AutoProposal Engine - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        
        # Build PDF
        doc.build(story)
        
        # Snapshot klasörüne kopyala
        snapshot_dir = self.snapshots_dir / notice_id / datetime.now().strftime("%Y%m%d_%H%M%S")
        if snapshot_dir.exists():
            import shutil
            shutil.copy2(pdf_path, snapshot_dir / pdf_filename)
        
        return pdf_path

# CLI Interface
def run_autoproposal_cli(notice_id: str, proposal_text: str = None, selected_hotels: List[str] = None):
    """CLI interface for AutoProposal"""
    
    engine = AutoProposalEngine()
    result = engine.generate_autoproposal(notice_id, proposal_text, selected_hotels)
    
    if result['status'] == 'success':
        print(f"SUCCESS: AutoProposal generated successfully!")
        print(f"PDF: {result['pdf_path']}")
        print(f"Snapshot: {result['snapshot_path']}")
        print(f"Hotels: {result['hotels_count']} found, {len(result['selected_hotels'])} selected")
        print(f"Budget: ${result['budget_total']:,.2f}")
        if result['compliance_score']:
            print(f"Compliance: {result['compliance_score']:.1f}%")
        print(f"Processing time: {result['processing_time']:.2f}s")
    else:
        print(f"ERROR: AutoProposal failed: {result['error']}")

# Test function
def test_autoproposal():
    """Test AutoProposal engine"""
    notice_id = "70LART26QPFB00001"
    
    # Sample proposal text
    proposal_text = """
    Our proposal includes accommodation for 80 rooms per night with 4 breakout rooms.
    The general session can accommodate 120 participants. We provide high-quality
    audio-visual equipment including projectors with 5000 lumens. All services
    comply with tax exemption requirements.
    """
    
    run_autoproposal_cli(notice_id, proposal_text)

if __name__ == "__main__":
    test_autoproposal()
