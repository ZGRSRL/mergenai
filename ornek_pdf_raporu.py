#!/usr/bin/env python3
"""
PDF Rapor Örneği - Gerçek Verilerle
"""

import sys
import os
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities, create_executive_pdf_report

# Veritabanından gerçek fırsatları al
conn = create_database_connection()
if not conn:
    print("Veritabanı bağlantısı başarısız!")
    exit(1)

opportunities = get_live_sam_opportunities(conn, limit=3)
if not opportunities:
    print("Hiç fırsat bulunamadı!")
    conn.close()
    exit(1)

print(f"{len(opportunities)} gerçek fırsat alındı:")
for opp in opportunities:
    print(f"- {opp['title'][:50]}...")

# PDF için gerekli verileri hazırla (örnek analiz sonuçları)
results = []
for opp in opportunities:
    results.append({
        'rfq_title': opp['title'],
        'requirements': [{'text': 'Örnek gereksinim', 'category': 'General', 'priority': 'Medium'}],
        'compliance_matrix': {'met_requirements': 1, 'total_requirements': 2},
        'pricing': {'grand_total': 50000},
        'quality_assurance': {'approval_status': 'Approved'},
        'detected_location': 'washington_dc',
        'hotels': [{
            'name': 'Örnek Otel', 
            'location': 'washington_dc',
            'address': '123 Örnek Sokak, Washington DC',
            'rating': 4.5,
            'price_range': '$200-300',
            'capacity': 100,
            'distance': '2.5 km',
            'contract_friendly': True,
            'government_discount': True,
            'per_diem_compliant': True
        }]
    })

total_metrics = {
    'total_value': 150000,
    'total_requirements': 3,
    'compliance_rate': 50.0,
    'avg_price': 50000
}

hotel_data = [{
    'name': 'Örnek Otel', 
    'location': 'washington_dc',
    'address': '123 Örnek Sokak, Washington DC',
    'rating': 4.5,
    'price_range': '$200-300',
    'capacity': 100,
    'distance': '2.5 km',
    'contract_friendly': True,
    'government_discount': True,
    'per_diem_compliant': True
}]

# PDF oluştur
pdf_buffer = create_executive_pdf_report(results, total_metrics, hotel_data)

# PDF'yi kaydet
with open('ornek_pdf_raporu.pdf', 'wb') as f:
    f.write(pdf_buffer.getvalue())

print("PDF başarıyla oluşturuldu: ornek_pdf_raporu.pdf")

conn.close()
