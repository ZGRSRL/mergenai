#!/usr/bin/env python3
"""
SOW PDF Report Generator
Generates a comprehensive PDF report for SOW analysis and hotel suggestions
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

def get_sow_analysis(notice_id):
    """Get SOW analysis from database"""
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

def get_hotel_suggestions(notice_id):
    """Get hotel suggestions from database"""
    conn = psycopg2.connect(
        host='localhost',
        database='ZGR_AI',
        user='postgres',
        password='postgres',
        port='5432'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, address, phone, website, distance_km, match_score, lat, lon
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
            'lon': r[7]
        }
        for r in rows
    ]

def create_sow_pdf_report(notice_id, output_path):
    """Create comprehensive SOW PDF report"""
    
    # Get data
    sow_data = get_sow_analysis(notice_id)
    hotels = get_hotel_suggestions(notice_id)
    
    if not sow_data:
        print(f"No SOW analysis found for {notice_id}")
        return False
    
    # Create PDF
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
    
    story.append(Paragraph(f"SOW Analysis Report - {notice_id}", title_style))
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
    
    # SOW Analysis Section
    story.append(Paragraph("SOW Analysis Summary", styles['Heading2']))
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
    
    # Hotel Suggestions Section
    if hotels:
        story.append(PageBreak())
        story.append(Paragraph("Hotel Suggestions", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"Found {len(hotels)} hotel suggestions based on SOW requirements:", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Hotel Details Table
        hotel_details = [['Rank', 'Hotel Name', 'Distance (km)', 'Match Score', 'Phone', 'Address']]
        
        for i, hotel in enumerate(hotels, 1):
            hotel_details.append([
                str(i),
                hotel['name'] or 'N/A',
                f"{hotel['distance_km']:.2f}" if hotel['distance_km'] else 'N/A',
                f"{hotel['match_score']:.3f}" if hotel['match_score'] else 'N/A',
                hotel['phone'] or 'N/A',
                (hotel['address'] or 'N/A')[:50] + '...' if hotel['address'] and len(hotel['address']) > 50 else (hotel['address'] or 'N/A')
            ])
        
        hotel_table = Table(hotel_details, colWidths=[0.5*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1*inch, 2*inch])
        hotel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
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
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by ZGR SAM Document Management System", info_style))
    
    # Build PDF
    doc.build(story)
    return True

def main():
    notice_id = "70LART26QPFB00001"
    output_path = f"SOW_Report_{notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    print(f"Generating SOW PDF report for {notice_id}...")
    
    if create_sow_pdf_report(notice_id, output_path):
        print(f"SUCCESS: PDF report generated successfully: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
    else:
        print("ERROR: Failed to generate PDF report")

if __name__ == "__main__":
    main()
