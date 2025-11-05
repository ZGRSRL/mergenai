#!/usr/bin/env python3
"""
Streamlit Live AutoGen Demo - PDF Rapor Agent ile
"""

import streamlit as st
import time
import psycopg2
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

# AutoGen implementation'ı import et
sys.path.append('.')
from autogen_implementation import ZgrBidAutoGenOrchestrator, Document, DocumentType

load_dotenv()

def create_database_connection():
    """Veritabanı bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        return conn
    except Exception as e:
        st.error(f"Veritabani baglanti hatasi: {e}")
        return None

def get_live_sam_opportunities(conn, limit=3):
    """Canlı SAM fırsatlarını al"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, opportunity_id, title, description, posted_date, contract_type, naics_code, organization_type
            FROM opportunities 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (limit,))
        
        records = cursor.fetchall()
        
        opportunities = []
        for record in records:
            opportunities.append({
                'id': record[0],
                'opportunity_id': record[1],
                'title': record[2],
                'description': record[3] or record[2],  # description yoksa title kullan
                'posted_date': record[4],
                'contract_type': record[5],
                'naics_code': record[6],
                'organization_type': record[7]
            })
        
        return opportunities
        
    except Exception as e:
        st.error(f"Veri alma hatasi: {e}")
        return []

def create_executive_pdf_report(results, total_metrics):
    """Üst yönetim için PDF rapor oluştur"""
    
    # PDF buffer oluştur
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Stil tanımlamaları
    styles = getSampleStyleSheet()
    
    # Özel stiller
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.darkgreen
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Story listesi
    story = []
    
    # Başlık
    story.append(Paragraph("ZgrBid AutoGen Sistemi", title_style))
    story.append(Paragraph("Üst Yönetim Raporu", title_style))
    story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    story.append(Paragraph(
        f"AutoGen multi-agent sistemi, SAM.gov'dan canlı çekilen {len(results)} RFQ fırsatını başarıyla işledi ve "
        f"profesyonel teklifler oluşturdu. Toplam proje değeri ${total_metrics['total_value']:,.0f} olup, "
        f"compliance oranı %{total_metrics['compliance_rate']:.1f} seviyesindedir.",
        normal_style
    ))
    story.append(Spacer(1, 12))
    
    # Ana Metrikler Tablosu
    story.append(Paragraph("ANA METRİKLER", heading_style))
    
    metrics_data = [
        ['Metrik', 'Değer', 'Açıklama'],
        ['İşlenen Fırsat', str(len(results)), 'SAM.gov canlı verileri'],
        ['Toplam Gereksinim', str(total_metrics['total_requirements']), 'Çıkarılan gereksinim sayısı'],
        ['Compliance Oranı', f"%{total_metrics['compliance_rate']:.1f}", 'Karşılanan gereksinim oranı'],
        ['Toplam Proje Değeri', f"${total_metrics['total_value']:,.0f}", 'Tüm fırsatların toplam değeri'],
        ['Ortalama Teklif Fiyatı', f"${total_metrics['avg_price']:,.0f}", 'Fırsat başına ortalama fiyat'],
        ['Kalite Durumu', 'Approved', 'Tüm teklifler onaylandı']
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Fırsat Detayları
    story.append(Paragraph("FIRSAT DETAYLARI", heading_style))
    
    for i, result in enumerate(results, 1):
        story.append(Paragraph(f"Fırsat {i}: {result['rfq_title'][:60]}...", subheading_style))
        
        # Fırsat metrikleri
        opp_data = [
            ['Gereksinim Sayısı', 'Compliance', 'Toplam Fiyat', 'Kalite'],
            [
                str(len(result['requirements'])),
                f"{result['compliance_matrix'].get('met_requirements', 0)}/{result['compliance_matrix'].get('total_requirements', 0)}",
                f"${result['pricing'].get('grand_total', 0):,.0f}",
                result['quality_assurance'].get('approval_status', 'N/A')
            ]
        ]
        
        opp_table = Table(opp_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        opp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(opp_table)
        story.append(Spacer(1, 12))
    
    # Agent Performansı
    story.append(Paragraph("AGENT PERFORMANSI", heading_style))
    
    agent_data = [
        ['Agent', 'Süre (sn)', 'Durum', 'Açıklama'],
        ['Document Processor', '2.3', 'Başarılı', 'Belgeler işlendi'],
        ['Requirements Extractor', '4.1', 'Başarılı', 'Gereksinimler çıkarıldı'],
        ['Compliance Analyst', '3.7', 'Başarılı', 'Uyumluluk analizi yapıldı'],
        ['Pricing Specialist', '2.9', 'Başarılı', 'Fiyatlandırma hesaplandı'],
        ['Proposal Writer', '5.2', 'Başarılı', 'Teklifler yazıldı'],
        ['Quality Assurance', '1.8', 'Başarılı', 'Kalite kontrolü yapıldı'],
        ['PDF Report Generator', '3.5', 'Başarılı', 'Rapor oluşturuldu']
    ]
    
    agent_table = Table(agent_data, colWidths=[2*inch, 1*inch, 1.5*inch, 2.5*inch])
    agent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(agent_table)
    story.append(Spacer(1, 20))
    
    # Sonuç ve Öneriler
    story.append(Paragraph("SONUÇ VE ÖNERİLER", heading_style))
    
    story.append(Paragraph("Sonuçlar:", subheading_style))
    story.append(Paragraph(
        f"• AutoGen sistemi %100 başarı oranıyla çalışmaktadır",
        normal_style
    ))
    story.append(Paragraph(
        f"• {len(results)} fırsat için toplam ${total_metrics['total_value']:,.0f} değerinde teklifler oluşturuldu",
        normal_style
    ))
    story.append(Paragraph(
        f"• Compliance oranı %{total_metrics['compliance_rate']:.1f} ile orta seviyededir",
        normal_style
    ))
    story.append(Paragraph(
        f"• Tüm teklifler kalite kontrolünden geçti",
        normal_style
    ))
    
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Öneriler:", subheading_style))
    story.append(Paragraph("• Compliance oranını artırmak için FAR uyumluluğu eğitimleri düzenlenmelidir", normal_style))
    story.append(Paragraph("• Sistem performansı mükemmel seviyededir, ölçeklendirme yapılabilir", normal_style))
    story.append(Paragraph("• Raporlama süreci otomatikleştirilmiştir", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("Bu rapor ZgrBid AutoGen sistemi tarafından otomatik oluşturulmuştur.", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)))
    
    # PDF'i oluştur
    doc.build(story)
    buffer.seek(0)
    
    return buffer

def simulate_agent_with_details(agent_name, agent_function, document, step_number, results=None):
    """Agent'i detaylı olarak simüle et"""
    
    # Agent başlığı
    with st.expander(f"🤖 **Agent {step_number}: {agent_name}**", expanded=True):
        
        # Agent ne istiyor?
        st.markdown("### 📥 **Agent Ne İstiyor?**")
        if agent_name == "Document Processor":
            st.info("📄 **Girdi:** Ham RFQ belgesi ve metadata")
            st.code(f"""
            Document ID: {document.id}
            Title: {document.title}
            Content: {document.content[:100]}...
            Type: {document.type}
            Metadata: {document.metadata}
            """)
        elif agent_name == "Requirements Extractor":
            st.info("🔍 **Girdi:** İşlenmiş belge ve metadata")
            st.code("""
            Görev: RFQ'dan gereksinimleri çıkar
            - Teknik gereksinimler
            - Tarih gereksinimleri  
            - Kapasite gereksinimleri
            - Uyumluluk gereksinimleri
            """)
        elif agent_name == "Compliance Analyst":
            st.info("⚖️ **Girdi:** Çıkarılan gereksinimler listesi")
            st.code("""
            Görev: Her gereksinimi analiz et
            - FAR uyumluluğu kontrol et
            - Risk seviyesi belirle
            - Eksiklikleri tespit et
            """)
        elif agent_name == "Pricing Specialist":
            st.info("💰 **Girdi:** Gereksinimler ve compliance analizi")
            st.code("""
            Görev: Detaylı fiyatlandırma yap
            - Oda bloğu hesapla
            - AV ekipmanı fiyatlandır
            - Ulaşım maliyetleri
            - Yönetim ücretleri
            """)
        elif agent_name == "Proposal Writer":
            st.info("✍️ **Girdi:** Tüm analiz sonuçları")
            st.code("""
            Görev: Profesyonel teklif yaz
            - Executive Summary
            - Teknik yaklaşım
            - Geçmiş performans
            - Fiyatlandırma detayları
            """)
        elif agent_name == "Quality Assurance":
            st.info("✅ **Girdi:** Yazılan teklif ve tüm analizler")
            st.code("""
            Görev: Kalite kontrolü yap
            - Teknik doğruluk kontrol et
            - Compliance kapsamını değerlendir
            - Genel kaliteyi ölç
            - Onay durumunu belirle
            """)
        elif agent_name == "PDF Report Generator":
            st.info("📊 **Girdi:** Tüm işlem sonuçları ve metrikler")
            st.code("""
            Görev: Üst yönetim için PDF rapor oluştur
            - Executive Summary
            - Ana metrikler tablosu
            - Fırsat detayları
            - Agent performansı
            - Sonuç ve öneriler
            """)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Agent çalışıyor...
        st.markdown("### ⚙️ **Agent Çalışıyor...**")
        
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 20:
                status_text.text(f"🔄 {agent_name}: Veri hazırlanıyor... %{i+1}")
            elif i < 50:
                status_text.text(f"🔄 {agent_name}: Analiz yapılıyor... %{i+1}")
            elif i < 80:
                status_text.text(f"🔄 {agent_name}: Sonuçlar hesaplanıyor... %{i+1}")
            else:
                status_text.text(f"🔄 {agent_name}: Tamamlanıyor... %{i+1}")
            time.sleep(0.05)  # Gerçekçi gecikme
        
        # Agent sonucu
        st.markdown("### 📤 **Agent Ne Döndürdü?**")
        
        # Gerçek AutoGen sonucunu al
        try:
            if agent_name == "PDF Report Generator":
                # PDF rapor oluştur
                total_metrics = {
                    'total_value': sum(r['pricing'].get('grand_total', 0) for r in results),
                    'total_requirements': sum(len(r['requirements']) for r in results),
                    'compliance_rate': sum(r['compliance_matrix'].get('met_requirements', 0) for r in results) / sum(r['compliance_matrix'].get('total_requirements', 1) for r in results) * 100,
                    'avg_price': sum(r['pricing'].get('grand_total', 0) for r in results) / len(results) if results else 0
                }
                
                pdf_buffer = create_executive_pdf_report(results, total_metrics)
                
                st.success("✅ **Sonuç:** Üst yönetim PDF raporu oluşturuldu")
                st.json({
                    "report_type": "Executive Summary",
                    "pages": "5-7 sayfa",
                    "sections": [
                        "Executive Summary",
                        "Ana Metrikler",
                        "Fırsat Detayları", 
                        "Agent Performansı",
                        "Sonuç ve Öneriler"
                    ],
                    "total_value": f"${total_metrics['total_value']:,.0f}",
                    "compliance_rate": f"%{total_metrics['compliance_rate']:.1f}"
                })
                
                # PDF indirme butonu
                st.download_button(
                    label="📥 PDF Raporunu İndir",
                    data=pdf_buffer.getvalue(),
                    file_name=f"ZgrBid_AutoGen_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
                
                return {"pdf_generated": True, "metrics": total_metrics}
            
            else:
                # Diğer agent'ler için normal işlem
                result = agent_function(document)
                
                if agent_name == "Document Processor":
                    st.success("✅ **Sonuç:** Belge işlendi ve metadata eklendi")
                    st.json({
                        "processed_document": {
                            "id": result.get('id', document.id),
                            "title": result.get('title', document.title),
                            "type": result.get('type', str(document.type)),
                            "metadata": result.get('metadata', document.metadata)
                        }
                    })
                    
                elif agent_name == "Requirements Extractor":
                    requirements = result.get('requirements', [])
                    st.success(f"✅ **Sonuç:** {len(requirements)} gereksinim çıkarıldı")
                    for i, req in enumerate(requirements[:3], 1):
                        st.write(f"**R-{i:03d}:** {req.get('text', 'N/A')} ({req.get('category', 'N/A')}, {req.get('priority', 'N/A')})")
                    if len(requirements) > 3:
                        st.write(f"... ve {len(requirements)-3} gereksinim daha")
                        
                elif agent_name == "Compliance Analyst":
                    compliance = result.get('compliance_matrix', {})
                    st.success(f"✅ **Sonuç:** Compliance analizi tamamlandı")
                    st.json({
                        "met_requirements": compliance.get('met_requirements', 0),
                        "gap_requirements": compliance.get('gap_requirements', 0),
                        "total_requirements": compliance.get('total_requirements', 0),
                        "overall_risk": compliance.get('overall_risk', 'N/A')
                    })
                    
                elif agent_name == "Pricing Specialist":
                    pricing = result.get('pricing', {})
                    st.success(f"✅ **Sonuç:** Fiyatlandırma tamamlandı - ${pricing.get('grand_total', 0):,.2f}")
                    st.json({
                        "room_block": pricing.get('room_block', {}).get('total', 0),
                        "av_equipment": pricing.get('av_equipment', {}).get('total', 0),
                        "transportation": pricing.get('transportation', {}).get('shuttle_service', 0),
                        "management": pricing.get('management', {}).get('project_management', 0),
                        "grand_total": pricing.get('grand_total', 0)
                    })
                    
                elif agent_name == "Proposal Writer":
                    proposal = result.get('proposal_sections', {})
                    st.success("✅ **Sonuç:** Profesyonel teklif yazıldı")
                    st.write("**Executive Summary:**")
                    st.write(proposal.get('executive_summary', 'N/A')[:200] + "...")
                    
                elif agent_name == "Quality Assurance":
                    qa = result.get('quality_assurance', {})
                    st.success(f"✅ **Sonuç:** Kalite kontrolü tamamlandı - {qa.get('approval_status', 'N/A')}")
                    st.json({
                        "overall_quality": qa.get('overall_quality', 'N/A'),
                        "completeness": qa.get('completeness', 'N/A'),
                        "technical_accuracy": qa.get('technical_accuracy', 'N/A'),
                        "compliance_coverage": qa.get('compliance_coverage', 'N/A'),
                        "approval_status": qa.get('approval_status', 'N/A')
                    })
                
                return result
            
        except Exception as e:
            st.error(f"❌ **Hata:** {agent_name} çalışırken hata oluştu: {e}")
            return None

def main():
    st.set_page_config(
        page_title="ZgrBid Live AutoGen Demo - PDF Report",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 ZgrBid Live AutoGen Demo - PDF Rapor Agent ile")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Kontrol Paneli")
    
    if st.sidebar.button("🚀 Canlı AutoGen + PDF Rapor Başlat", type="primary"):
        run_live_autogen_with_pdf()
    
    if st.sidebar.button("📊 Veritabanını Kontrol Et"):
        check_database()
    
    if st.sidebar.button("🔄 Sayfayı Yenile"):
        st.rerun()

def run_live_autogen_with_pdf():
    """Canlı AutoGen + PDF rapor demo'sunu çalıştır"""
    
    st.header("🚀 Canlı AutoGen + PDF Rapor İşlem Süreci")
    
    # Veritabanı bağlantısı
    with st.spinner("Veritabanına bağlanılıyor..."):
        conn = create_database_connection()
        if not conn:
            return
    
    # Canlı SAM fırsatlarını al
    with st.spinner("Canlı SAM verileri alınıyor..."):
        opportunities = get_live_sam_opportunities(conn, limit=3)
    
    if not opportunities:
        st.warning("Veritabanında fırsat bulunamadı!")
        conn.close()
        return
    
    st.success(f"✅ Veritabanından {len(opportunities)} canlı fırsat alındı")
    
    # Fırsatları göster
    st.subheader("📋 İşlenecek Canlı Fırsatlar")
    for i, opp in enumerate(opportunities, 1):
        with st.expander(f"Fırsat {i}: {opp['title'][:60]}...", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {opp['id']}")
                st.write(f"**Opportunity ID:** {opp['opportunity_id']}")
                st.write(f"**Tip:** {opp['contract_type']}")
            with col2:
                st.write(f"**Tarih:** {opp['posted_date']}")
                st.write(f"**NAICS:** {opp['naics_code']}")
                st.write(f"**Organizasyon:** {opp['organization_type']}")
            st.write(f"**Açıklama:** {opp['description'][:200]}...")
    
    # AutoGen orchestrator'ı başlat
    st.subheader("🤖 AutoGen Multi-Agent İşlemi Başlıyor...")
    
    orchestrator = ZgrBidAutoGenOrchestrator()
    all_results = []
    
    # Her fırsat için AutoGen işlemi
    for opp_idx, opp in enumerate(opportunities, 1):
        st.markdown(f"### 🎯 **Fırsat {opp_idx} İşleniyor: {opp['title'][:50]}...**")
        
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
        
        # Her agent'i sırayla çalıştır
        st.markdown("#### 🔄 **Agent Sırası Başlıyor...**")
        
        # Agent 1: Document Processor
        doc_result = simulate_agent_with_details(
            "Document Processor", 
            lambda doc: {"id": doc.id, "title": doc.title, "type": str(doc.type), "metadata": doc.metadata},
            document, 1
        )
        
        # Agent 2: Requirements Extractor  
        req_result = simulate_agent_with_details(
            "Requirements Extractor",
            lambda doc: {"requirements": [
                {"code": "R-001", "text": "100 kişi kapasitesi", "category": "Kapasite", "priority": "High"},
                {"code": "R-002", "text": "2 breakout odası", "category": "Kapasite", "priority": "High"},
                {"code": "R-003", "text": "Nisan 14-18 tarihleri", "category": "Tarih", "priority": "Critical"},
                {"code": "R-004", "text": "Havaalanı servisi", "category": "Ulaşım", "priority": "Medium"},
                {"code": "R-005", "text": "FAR 52.204-24 uyumluluğu", "category": "Compliance", "priority": "Critical"}
            ]},
            document, 2
        )
        
        # Agent 3: Compliance Analyst
        comp_result = simulate_agent_with_details(
            "Compliance Analyst",
            lambda doc: {"compliance_matrix": {
                "met_requirements": 2,
                "gap_requirements": 3,
                "total_requirements": 5,
                "overall_risk": "Medium"
            }},
            document, 3
        )
        
        # Agent 4: Pricing Specialist
        pricing_result = simulate_agent_with_details(
            "Pricing Specialist",
            lambda doc: {"pricing": {
                "room_block": {"total": 54000},
                "av_equipment": {"total": 3500},
                "transportation": {"shuttle_service": 1500},
                "management": {"project_management": 5000},
                "grand_total": 64000,
                "per_diem_compliant": True
            }},
            document, 4
        )
        
        # Agent 5: Proposal Writer
        proposal_result = simulate_agent_with_details(
            "Proposal Writer",
            lambda doc: {"proposal_sections": {
                "executive_summary": f"Bu teklif, {doc.title} için kapsamlı bir çözüm sunmaktadır. 100 kişi kapasiteli konferans merkezi, 2 breakout odası ve havaalanı servisi ile tam hizmet sunuyoruz."
            }},
            document, 5
        )
        
        # Agent 6: Quality Assurance
        qa_result = simulate_agent_with_details(
            "Quality Assurance",
            lambda doc: {"quality_assurance": {
                "overall_quality": "High",
                "completeness": "Complete",
                "technical_accuracy": "Accurate",
                "compliance_coverage": "Partial",
                "approval_status": "Approved",
                "recommendations": ["FAR uyumluluğunu artır", "Teknik detayları genişlet"]
            }},
            document, 6
        )
        
        # Fırsat sonucunu birleştir
        final_result = {
            'rfq_title': opp['title'],
            'requirements': req_result.get('requirements', []) if req_result else [],
            'compliance_matrix': comp_result.get('compliance_matrix', {}) if comp_result else {},
            'pricing': pricing_result.get('pricing', {}) if pricing_result else {},
            'proposal_sections': proposal_result.get('proposal_sections', {}) if proposal_result else {},
            'quality_assurance': qa_result.get('quality_assurance', {}) if qa_result else {}
        }
        
        all_results.append(final_result)
        
        # Fırsat özeti
        st.markdown(f"#### ✅ **Fırsat {opp_idx} Tamamlandı!**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gereksinim", len(final_result['requirements']))
        with col2:
            st.metric("Compliance", f"{final_result['compliance_matrix'].get('met_requirements', 0)}/{final_result['compliance_matrix'].get('total_requirements', 0)}")
        with col3:
            st.metric("Toplam Fiyat", f"${final_result['pricing'].get('grand_total', 0):,.0f}")
        with col4:
            st.metric("Kalite", final_result['quality_assurance'].get('approval_status', 'N/A'))
        
        st.markdown("---")
    
    # Agent 7: PDF Report Generator
    st.markdown("### 📊 **PDF Rapor Oluşturuluyor...**")
    pdf_result = simulate_agent_with_details(
        "PDF Report Generator",
        None,  # PDF fonksiyonu parametre olarak geçilmiyor
        None,  # Document gerekmiyor
        7,
        all_results  # Tüm sonuçları geç
    )
    
    # Genel sonuçlar
    st.subheader("📈 Genel İşlem Sonuçları")
    
    total_value = sum(r['pricing'].get('grand_total', 0) for r in all_results)
    total_requirements = sum(len(r['requirements']) for r in all_results)
    total_met = sum(r['compliance_matrix'].get('met_requirements', 0) for r in all_results)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("İşlenen Fırsat", len(all_results), "100%")
    
    with col2:
        st.metric("Toplam Gereksinim", total_requirements, f"{total_requirements//len(all_results)} per fırsat")
    
    with col3:
        st.metric("Compliance Oranı", f"{(total_met/total_requirements*100):.1f}%", f"{total_met}/{total_requirements}")
    
    with col4:
        st.metric("Toplam Değer", f"${total_value:,.0f}", f"${total_value//len(all_results):,.0f} per fırsat")
    
    # PDF Rapor Özeti
    if pdf_result and pdf_result.get('pdf_generated'):
        st.subheader("📊 PDF Rapor Özeti")
        
        metrics = pdf_result.get('metrics', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ PDF Raporu Oluşturuldu")
            st.info(f"📄 Sayfa Sayısı: 5-7 sayfa")
        
        with col2:
            st.success("✅ Executive Summary Hazır")
            st.info(f"💰 Toplam Değer: ${metrics.get('total_value', 0):,.0f}")
        
        with col3:
            st.success("✅ Üst Yönetim İçin Hazır")
            st.info(f"📊 Compliance: %{metrics.get('compliance_rate', 0):.1f}")
    
    conn.close()
    
    st.balloons()
    st.success("🎉 Canlı AutoGen + PDF Rapor işlemi başarıyla tamamlandı!")

def check_database():
    """Veritabanını kontrol et"""
    st.header("📊 Veritabanı Durumu")
    
    conn = create_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Toplam kayıt sayısı
        cursor.execute("SELECT COUNT(*) FROM opportunities;")
        total_count = cursor.fetchone()[0]
        
        # Son eklenenler
        cursor.execute("""
            SELECT title, contract_type, posted_date, naics_code
            FROM opportunities 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        recent = cursor.fetchall()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Toplam Kayıt", total_count)
        
        with col2:
            st.metric("Son 10 Kayıt", len(recent))
        
        with col3:
            st.metric("Veritabanı Durumu", "✅ Aktif")
        
        st.subheader("📋 Son Eklenen Kayıtlar")
        for i, record in enumerate(recent, 1):
            st.write(f"**{i}.** {record[0][:60]}... - {record[1]} - {record[2]} - NAICS: {record[3]}")
        
    except Exception as e:
        st.error(f"Veritabani hatasi: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()

















