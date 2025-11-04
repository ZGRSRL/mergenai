#!/usr/bin/env python3
"""
Comprehensive Report Generator
Tüm agentları içeren kapsamlı özet rapor oluşturur
"""

import sys
sys.path.append('.')

import psycopg2
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Import our agents
from compliance_matrix_agent import ComplianceMatrixAgent
from budget_estimator import BudgetEstimatorAgent

class ComprehensiveReportGenerator:
    """Kapsamlı rapor oluşturucu - tüm agentları içerir"""
    
    def __init__(self):
        self.compliance_agent = ComplianceMatrixAgent()
        self.budget_agent = BudgetEstimatorAgent()
    
    def generate_comprehensive_report(self, notice_id: str, proposal_text: str = None) -> str:
        """Kapsamlı rapor oluşturur"""
        
        # Veritabanından verileri al
        sow_data = self._get_sow_analysis(notice_id)
        hotels = self._get_hotel_suggestions(notice_id)
        agent_logs = self._get_agent_logs(notice_id)
        
        if not sow_data:
            return None
        
        # Compliance analysis (eğer proposal text varsa)
        compliance_data = None
        if proposal_text:
            compliance_data = self.compliance_agent.analyze_compliance(sow_data['sow_payload'], proposal_text)
        
        # Budget estimation
        budget_data = self.budget_agent.estimate_budget(sow_data['sow_payload'])
        
        # PDF oluştur
        output_path = f"Comprehensive_Report_{notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self._create_comprehensive_pdf(
            notice_id, sow_data, hotels, compliance_data, budget_data, agent_logs, output_path
        )
        
        return output_path
    
    def _get_sow_analysis(self, notice_id: str):
        """SOW analizini veritabanından al"""
        conn = psycopg2.connect(
            host='localhost',
            database='ZGR_AI',
            user='postgres',
            password='postgres',
            port='5432'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sow_payload, template_version, created_at 
            FROM sow_analysis 
            WHERE notice_id=%s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (notice_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'sow_payload': row[0],
                'template_version': row[1],
                'created_at': row[2]
            }
        return None
    
    def _get_hotel_suggestions(self, notice_id: str):
        """Otel önerilerini veritabanından al"""
        conn = psycopg2.connect(
            host='localhost',
            database='ZGR_AI',
            user='postgres',
            password='postgres',
            port='5432'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, address, phone, website, distance_km, match_score, lat, lon, selected
            FROM hotel_suggestions 
            WHERE notice_id=%s 
            ORDER BY match_score DESC, distance_km ASC
        """, (notice_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': r[0],
                'address': r[1],
                'phone': r[2],
                'website': r[3],
                'distance_km': r[4],
                'match_score': r[5],
                'lat': r[6],
                'lon': r[7],
                'selected': r[8]
            }
            for r in rows
        ]
    
    def _get_agent_logs(self, notice_id: str):
        """Agent loglarını al"""
        try:
            # Log dosyasından oku
            log_file = f"logs/agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    return [log for log in logs if log.get('notice_id') == notice_id]
        except:
            pass
        return []
    
    def _create_comprehensive_pdf(self, notice_id: str, sow_data: dict, hotels: list, 
                                compliance_data: dict, budget_data: dict, agent_logs: list, output_path: str):
        """Kapsamlı PDF oluşturur"""
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
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
        
        story.append(Paragraph(f"Comprehensive Analysis Report - {notice_id}", title_style))
        story.append(Spacer(1, 20))
        
        # Report Info
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"Template Version: {sow_data['template_version']}", info_style))
        story.append(Paragraph(f"Analysis Date: {sow_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        summary_text = f"""
        This comprehensive analysis report covers all aspects of opportunity {notice_id}, 
        including SOW requirements, hotel suggestions, budget estimation, and compliance analysis.
        The analysis identified {len(hotels)} hotel options with an estimated budget of 
        ${budget_data['total']:,.2f}. Agent processing completed successfully with 
        {len(agent_logs)} logged actions.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 1. SOW Analysis Section
        story.append(Paragraph("1. SOW Analysis Summary", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        sow_payload = sow_data['sow_payload']
        
        # SOW Details Table
        period = sow_payload.get('period_of_performance', 'N/A')
        if isinstance(period, dict):
            period_str = f"{period.get('start', 'N/A')} - {period.get('end', 'N/A')}"
        else:
            period_str = str(period)
        
        function_space = sow_payload.get('function_space', {})
        general_session = function_space.get('general_session', {}) if isinstance(function_space, dict) else {}
        breakout_rooms = function_space.get('breakout_rooms', {}) if isinstance(function_space, dict) else {}
        room_block = sow_payload.get('room_block', {})
        av = sow_payload.get('av', {})
        
        sow_details = [
            ['Field', 'Value'],
            ['Period of Performance', period_str],
            ['Setup Deadline', str(sow_payload.get('setup_deadline', 'N/A'))],
            ['General Session Capacity', str(general_session.get('capacity', 'N/A') if isinstance(general_session, dict) else 'N/A')],
            ['Breakout Rooms Count', str(breakout_rooms.get('count', 'N/A') if isinstance(breakout_rooms, dict) else 'N/A')],
            ['Total Rooms per Night', str(room_block.get('total_rooms_per_night', 'N/A') if isinstance(room_block, dict) else 'N/A')],
            ['Total Nights', str(room_block.get('total_nights', 'N/A') if isinstance(room_block, dict) else 'N/A')],
            ['Projector Lumens', str(av.get('projector_lumens', 'N/A') if isinstance(av, dict) else 'N/A')],
            ['Tax Exemption', str(sow_payload.get('tax_exemption', 'N/A'))]
        ]
        
        sow_table = Table(sow_details, colWidths=[2*inch, 4*inch])
        sow_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(sow_table)
        story.append(Spacer(1, 20))
        
        # 2. Budget Estimation Section
        story.append(PageBreak())
        story.append(Paragraph("2. Budget Estimation", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        budget_details = [
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
        
        budget_table = Table(budget_details, colWidths=[1.5*inch, 1.2*inch, 3*inch])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, -2), (-1, -1), colors.darkgreen),
            ('TEXTCOLOR', (0, -2), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold')
        ]))
        
        story.append(budget_table)
        story.append(Spacer(1, 20))
        
        # 3. Hotel Suggestions Section
        story.append(Paragraph("3. Hotel Suggestions", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        if hotels:
            story.append(Paragraph(f"Found {len(hotels)} hotel suggestions based on SOW requirements:", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Hotel Details Table
            hotel_details = [['Rank', 'Hotel Name', 'Distance (km)', 'Match Score', 'Selected', 'Phone', 'Address']]
            
            for i, hotel in enumerate(hotels, 1):
                hotel_details.append([
                    str(i),
                    hotel['name'] or 'N/A',
                    f"{hotel['distance_km']:.2f}" if hotel['distance_km'] else 'N/A',
                    f"{hotel['match_score']:.3f}" if hotel['match_score'] else 'N/A',
                    'Yes' if hotel.get('selected') else 'No',
                    hotel['phone'] or 'N/A',
                    (hotel['address'] or 'N/A')[:40] + '...' if hotel['address'] and len(hotel['address']) > 40 else (hotel['address'] or 'N/A')
                ])
            
            hotel_table = Table(hotel_details, colWidths=[0.5*inch, 1.2*inch, 0.7*inch, 0.7*inch, 0.6*inch, 1*inch, 1.8*inch])
            hotel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            story.append(hotel_table)
            story.append(Spacer(1, 20))
            
            # Top 3 Hotels Details
            story.append(Paragraph("Top 3 Hotel Recommendations", styles['Heading3']))
            story.append(Spacer(1, 10))
            
            for i, hotel in enumerate(hotels[:3], 1):
                story.append(Paragraph(f"<b>{i}. {hotel['name']}</b>", styles['Heading4']))
                story.append(Paragraph(f"Distance: {hotel['distance_km']:.2f} km", styles['Normal']))
                story.append(Paragraph(f"Match Score: {hotel['match_score']:.3f}", styles['Normal']))
                story.append(Paragraph(f"Phone: {hotel['phone'] or 'N/A'}", styles['Normal']))
                story.append(Paragraph(f"Website: {hotel['website'] or 'N/A'}", styles['Normal']))
                story.append(Paragraph(f"Address: {hotel['address'] or 'N/A'}", styles['Normal']))
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No hotel suggestions found.", styles['Normal']))
        
        # 4. Compliance Analysis Section (if available)
        if compliance_data:
            story.append(PageBreak())
            story.append(Paragraph("4. Compliance Analysis", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"Compliance Score: {compliance_data['compliance_score']:.1f}%", styles['Heading3']))
            story.append(Paragraph(f"Total Requirements: {len(compliance_data['compliance_matrix'])}", styles['Normal']))
            story.append(Paragraph(f"Gaps Identified: {len(compliance_data['gaps'])}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Compliance Matrix Table
            matrix_data = [['Requirement', 'Category', 'Covered', 'Confidence']]
            for item in compliance_data['compliance_matrix']:
                matrix_data.append([
                    item['requirement'],
                    item['category'],
                    'Yes' if item['is_covered'] else 'No',
                    f"{item['confidence']:.2f}"
                ])
            
            matrix_table = Table(matrix_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 0.8*inch])
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            story.append(matrix_table)
            story.append(Spacer(1, 20))
        
        # 5. Agent Processing Log Section
        story.append(PageBreak())
        story.append(Paragraph("5. Agent Processing Log", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        if agent_logs:
            story.append(Paragraph(f"Processing completed with {len(agent_logs)} agent actions:", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Agent Logs Table
            log_data = [['Agent', 'Action', 'Status', 'Duration (ms)', 'Timestamp']]
            for log in agent_logs[-10:]:  # Son 10 log
                log_data.append([
                    log.get('agent_name', 'N/A'),
                    log.get('action', 'N/A'),
                    log.get('status', 'N/A'),
                    str(log.get('duration_ms', 'N/A')),
                    log.get('timestamp', 'N/A')[:19] if log.get('timestamp') else 'N/A'
                ])
            
            log_table = Table(log_data, colWidths=[1.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1.5*inch])
            log_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            story.append(log_table)
        else:
            story.append(Paragraph("No agent processing logs available.", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by ZGR SAM Document Management System - Comprehensive Analysis", info_style))
        
        # Build PDF
        doc.build(story)
        return True

# Test function
def test_comprehensive_report():
    """Test comprehensive report generation"""
    generator = ComprehensiveReportGenerator()
    
    # Test with 70LART26QPFB00001
    notice_id = "70LART26QPFB00001"
    
    # Sample proposal text for compliance analysis
    proposal_text = """
    Our proposal includes accommodation for 80 rooms per night with 4 breakout rooms.
    The general session can accommodate 120 participants. We provide high-quality
    audio-visual equipment including projectors with 5000 lumens. All services
    comply with tax exemption requirements.
    """
    
    output_path = generator.generate_comprehensive_report(notice_id, proposal_text)
    
    if output_path:
        print(f"Comprehensive report generated: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
    else:
        print("Failed to generate comprehensive report")

if __name__ == "__main__":
    test_comprehensive_report()

