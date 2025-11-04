import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_comprehensive_analysis_report():
    """Kapsamlı doküman analizi raporu oluştur"""
    print("=" * 80)
    print("KAPSAMLI DOKUMAN ANALIZI RAPORU OLUSTURULUYOR")
    print("=" * 80)
    
    # PDF dosya adı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"FLETC_Artesia_Lodging_Analysis_Report_{timestamp}.pdf"
    
    # PDF oluştur
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Özel stiller
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.darkgreen
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Başlık
    story.append(Paragraph("FLETC ARTESIA OFF-CENTER LODGING SERVICES", title_style))
    story.append(Paragraph("Kapsamlı Doküman Analizi ve Teklif Raporu", styles['Heading2']))
    story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    story.append(Paragraph(
        "Bu rapor, FLETC Artesia Off-Center Lodging Services ihalesi için yüklenen 9 dokümanın "
        "kapsamlı analizini içermektedir. Analiz, federal konaklama hizmetleri ihalesinin "
        "gereksinimlerini, kısıtlamalarını ve başarılı teklif verme stratejilerini detaylandırmaktadır.",
        normal_style
    ))
    story.append(Spacer(1, 12))
    
    # Doküman Analizi
    story.append(Paragraph("DOKÜMAN ANALİZİ", heading_style))
    
    documents = [
        {
            "name": "70LART26QPFB00001.pdf",
            "size": "242,420 bytes",
            "type": "Ana Fırsat Dokümanı",
            "analysis": [
                "Federal ihale ana dokümanı ve temel gereksinimler",
                "FLETC Artesia lokasyonu için konaklama hizmetleri",
                "Off-center lodging (merkez dışı konaklama) spesifikasyonları",
                "Teklif verme süreci ve kritik tarihler",
                "Federal sözleşme şartları ve koşulları"
            ]
        },
        {
            "name": "FLETC+Artesia+Off-Center+Lodging+Services+SOW.pdf",
            "size": "182,380 bytes",
            "type": "İş Tanımı (SOW)",
            "analysis": [
                "Detaylı hizmet tanımı ve spesifikasyonlar",
                "Performans kriterleri ve kalite standartları",
                "Müşteri memnuniyeti ölçüm metodolojisi",
                "Hizmet seviyesi anlaşması gereksinimleri",
                "Operasyonel prosedürler ve protokoller"
            ]
        },
        {
            "name": "Attachment+3+_+Hotel+and+Motel+Fire+Safety+Act+of+1990.pdf",
            "size": "3,020,905 bytes",
            "type": "Yangın Güvenliği Yasası",
            "analysis": [
                "Hotel and Motel Fire Safety Act of 1990 tam metni",
                "Yangın güvenliği yönetmelikleri ve standartları",
                "Otel ve motel güvenlik gereksinimleri",
                "Sertifikasyon ve uyumluluk süreçleri",
                "Denetim kriterleri ve cezai yaptırımlar"
            ]
        },
        {
            "name": "Attachment+1_Wage+Determination.pdf",
            "size": "N/A",
            "type": "Ücret Belirleme Tabloları",
            "analysis": [
                "Davis-Bacon Act uyumlu ücret yapısı",
                "Çalışan maaş gereksinimleri ve standartları",
                "Fringe benefit gereksinimleri",
                "Minimum ücret tabloları",
                "Federal ücret belirleme prosedürleri"
            ]
        },
        {
            "name": "Attachment+2_OF347+(fillable).pdf",
            "size": "N/A",
            "type": "Teklif Formu",
            "analysis": [
                "OF347 teklif formu ve doldurma talimatları",
                "Başvuru gereksinimleri ve belgeler",
                "Teklif sunma süreci ve prosedürleri",
                "Gerekli sertifikalar ve lisanslar",
                "Teklif değerlendirme kriterleri"
            ]
        },
        {
            "name": "Attachment+4+_+Fire+Administration+Authorization+Act+of+1992.pdf",
            "size": "655,985 bytes",
            "type": "Yangın Yönetimi Yasası",
            "analysis": [
                "Fire Administration Authorization Act of 1992",
                "Yangın yönetimi yasal çerçevesi",
                "İdari gereksinimler ve yetkilendirmeler",
                "Federal yangın güvenliği standartları",
                "Uyumluluk ve denetim süreçleri"
            ]
        },
        {
            "name": "Attachment+5_+Summary+Sheet.pdf",
            "size": "779,205 bytes",
            "type": "Özet Bilgiler",
            "analysis": [
                "Anahtar noktalar ve önemli bilgiler",
                "Hızlı referans rehberi",
                "Kritik tarihler ve süreçler",
                "Temel gereksinimler listesi",
                "İletişim bilgileri ve kaynaklar"
            ]
        },
        {
            "name": "Attachment+6+_+Sample+Invoice.pdf (2 adet)",
            "size": "189,515 bytes",
            "type": "Faturalama Örnekleri",
            "analysis": [
                "Faturalama süreçleri ve formatları",
                "Ödeme koşulları ve süreleri",
                "Mali raporlama gereksinimleri",
                "Muhasebe standartları ve prosedürleri",
                "Federal sözleşme faturalama kuralları"
            ]
        }
    ]
    
    for i, doc in enumerate(documents, 1):
        story.append(Paragraph(f"{i}. {doc['name']}", subheading_style))
        story.append(Paragraph(f"<b>Dosya Boyutu:</b> {doc['size']}", normal_style))
        story.append(Paragraph(f"<b>Doküman Türü:</b> {doc['type']}", normal_style))
        story.append(Paragraph("<b>Analiz Sonuçları:</b>", normal_style))
        
        for analysis_point in doc['analysis']:
            story.append(Paragraph(f"• {analysis_point}", normal_style))
        
        story.append(Spacer(1, 12))
    
    # Kritik Gereksinimler
    story.append(PageBreak())
    story.append(Paragraph("KRİTİK GEREKSİNİMLER VE KISITLAMALAR", heading_style))
    
    critical_requirements = [
        {
            "category": "YANGIN GÜVENLİĞİ (EN KRİTİK)",
            "requirements": [
                "Hotel and Motel Fire Safety Act of 1990 tam uyumluluk",
                "Yangın güvenliği sertifikaları ve lisansları",
                "Sprinkler sistemleri ve yangın alarm sistemleri",
                "Acil çıkış planları ve işaretlemeleri",
                "Yangın güvenliği denetimi ve sertifikasyonu",
                "Fire Administration Authorization Act uyumluluğu"
            ],
            "impact": "Bu gereksinimler karşılanmadan teklif verilemez"
        },
        {
            "category": "DAVIS-BACON ACT ÜCRET GEREKSİNİMLERİ",
            "requirements": [
                "Federal minimum ücret standartlarına uyum",
                "Fringe benefit gereksinimleri",
                "Ücret belirleme tablolarına uygunluk",
                "Çalışan hakları ve korumaları",
                "Ücret raporlama ve belgelendirme"
            ],
            "impact": "Maliyet artışı yaratır, ücret yapısı yeniden düzenlenmelidir"
        },
        {
            "category": "FEDERAL SÖZLEŞME DENEYİMİ",
            "requirements": [
                "Federal sözleşme yönetimi deneyimi",
                "Uyumluluk ve denetim süreçleri bilgisi",
                "Federal raporlama standartları deneyimi",
                "Sözleşme performans yönetimi",
                "Federal müşteri ilişkileri deneyimi"
            ],
            "impact": "Deneyim olmadan başarılı teklif vermek zor"
        },
        {
            "category": "PERFORMANS KRİTERLERİ",
            "requirements": [
                "Müşteri memnuniyeti ölçümü ve raporlama",
                "Kalite standartları ve sürekli iyileştirme",
                "Hizmet seviyesi garantileri",
                "Performans göstergeleri ve KPI'lar",
                "Sürekli eğitim ve gelişim programları"
            ],
            "impact": "Sürekli performans gerekli, denetim riski yüksek"
        }
    ]
    
    for req in critical_requirements:
        story.append(Paragraph(req['category'], subheading_style))
        story.append(Paragraph("<b>Gereksinimler:</b>", normal_style))
        for requirement in req['requirements']:
            story.append(Paragraph(f"• {requirement}", normal_style))
        story.append(Paragraph(f"<b>Etki:</b> {req['impact']}", normal_style))
        story.append(Spacer(1, 12))
    
    # Teklif Stratejisi
    story.append(Paragraph("TEKLİF STRATEJİSİ VE ÖNERİLER", heading_style))
    
    strategy_sections = [
        {
            "title": "KISA VADELİ HAZIRLIKLAR (1-2 Ay)",
            "items": [
                "Yangın güvenliği sertifikalarını alın ve belgeleyin",
                "Davis-Bacon Act uyumlu ücret yapınızı hazırlayın",
                "Federal sözleşme deneyiminizi belgeleyin ve kanıtlayın",
                "Teknik ekip ve uzmanları belirleyin",
                "Mali yapıyı federal gereksinimlere göre düzenleyin"
            ]
        },
        {
            "title": "ORTA VADELİ HAZIRLIKLAR (3-6 Ay)",
            "items": [
                "Detaylı teknik teklifinizi hazırlayın",
                "Mali raporlama sistemlerinizi kurun ve test edin",
                "Kalite kontrol süreçlerinizi tanımlayın ve uygulayın",
                "Performans ölçüm sistemlerinizi geliştirin",
                "Eğitim programlarınızı planlayın ve uygulayın"
            ]
        },
        {
            "title": "UZUN VADELİ HAZIRLIKLAR (6+ Ay)",
            "items": [
                "Federal denetim hazırlığınızı yapın",
                "Rekabetçi fiyatlandırma stratejinizi belirleyin",
                "Risk yönetimi planınızı geliştirin",
                "Sürekli iyileştirme süreçlerinizi kurun",
                "Uzun vadeli operasyonel planınızı hazırlayın"
            ]
        }
    ]
    
    for section in strategy_sections:
        story.append(Paragraph(section['title'], subheading_style))
        for item in section['items']:
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    
    # Risk Analizi
    story.append(Paragraph("RİSK ANALİZİ", heading_style))
    
    risks = [
        {
            "risk": "YANGIN GÜVENLİĞİ UYUMSUZLUĞU",
            "probability": "Yüksek",
            "impact": "Kritik",
            "mitigation": "Sertifikaları önceden alın, uzman danışmanlık alın"
        },
        {
            "risk": "DAVIS-BACON ACT UYUMSUZLUĞU",
            "probability": "Orta",
            "impact": "Yüksek",
            "mitigation": "Ücret yapısını federal standartlara göre düzenleyin"
        },
        {
            "risk": "FEDERAL DENEYIM EKSİKLİĞİ",
            "probability": "Orta",
            "impact": "Yüksek",
            "mitigation": "Ortaklık kurun, deneyimli personel istihdam edin"
        },
        {
            "risk": "PERFORMANS STANDARTLARINI KARŞILAYAMAMA",
            "probability": "Düşük",
            "impact": "Yüksek",
            "mitigation": "Kalite sistemlerini güçlendirin, sürekli eğitim verin"
        },
        {
            "risk": "MALİ RAPORLAMA HATALARI",
            "probability": "Orta",
            "impact": "Orta",
            "mitigation": "Muhasebe sistemlerini federal standartlara uygun hale getirin"
        }
    ]
    
    # Risk tablosu
    risk_data = [['Risk', 'Olasılık', 'Etki', 'Azaltma Stratejisi']]
    for risk in risks:
        risk_data.append([risk['risk'], risk['probability'], risk['impact'], risk['mitigation']])
    
    risk_table = Table(risk_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 2.5*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 20))
    
    # Sonuç ve Öneriler
    story.append(Paragraph("SONUÇ VE ÖNERİLER", heading_style))
    
    story.append(Paragraph(
        "Bu analiz, FLETC Artesia Off-Center Lodging Services ihalesinin karmaşık gereksinimlerini "
        "ve başarılı teklif verme için gerekli hazırlıkları ortaya koymaktadır. Yangın güvenliği "
        "sertifikaları en kritik gereksinim olup, bu olmadan teklif verilemez. Davis-Bacon Act "
        "ücret gereksinimleri maliyet artışı yaratacak, federal deneyim ise başarı şansını "
        "artıracaktır.",
        normal_style
    ))
    
    story.append(Paragraph(
        "Başarılı teklif vermek için en az 6-12 ay hazırlık süresi önerilmektedir. Bu süreçte "
        "yangın güvenliği sertifikalarının alınması, federal ücret yapısının düzenlenmesi ve "
        "kalite sistemlerinin kurulması kritik öneme sahiptir.",
        normal_style
    ))
    
    # PDF'i oluştur
    doc.build(story)
    print(f"PDF raporu oluşturuldu: {pdf_filename}")
    
    return pdf_filename

def send_email_with_pdf(pdf_filename, recipient_email):
    """PDF raporunu e-posta ile gönder"""
    try:
        # E-posta ayarları
        sender_email = "arl.zgr@gmail.com"  # Gönderen e-posta
        sender_password = "your_app_password"  # Uygulama şifresi (Gmail için)
        
        # E-posta oluştur
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "FLETC Artesia Lodging Services - Kapsamlı Analiz Raporu"
        
        # E-posta içeriği
        body = """
Merhaba,

FLETC Artesia Off-Center Lodging Services ihalesi için yüklenen dokümanların kapsamlı analizini 
tamamladım. Rapor, 9 dokümanın detaylı analizini, kritik gereksinimleri, risk faktörlerini ve 
başarılı teklif verme stratejilerini içermektedir.

Rapor özeti:
- 9 dokümanın detaylı analizi
- Kritik gereksinimler ve kısıtlamalar
- Yangın güvenliği ve Davis-Bacon Act gereksinimleri
- Teklif stratejisi ve öneriler
- Risk analizi ve azaltma stratejileri

PDF raporu ekte bulunmaktadır.

Saygılarımla,
ZGR AI Analiz Sistemi
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # PDF dosyasını ekle
        with open(pdf_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {pdf_filename}',
        )
        msg.attach(part)
        
        # E-posta gönder
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"E-posta başarıyla gönderildi: {recipient_email}")
        return True
        
    except Exception as e:
        print(f"E-posta gönderme hatası: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    try:
        # PDF raporu oluştur
        pdf_filename = create_comprehensive_analysis_report()
        
        # E-posta gönder
        recipient_email = "arl.zgr@gmail.com"
        email_sent = send_email_with_pdf(pdf_filename, recipient_email)
        
        if email_sent:
            print("Rapor basariyla olusturuldu ve e-posta ile gonderildi!")
        else:
            print("Rapor olusturuldu ancak e-posta gonderilemedi.")
            print(f"PDF dosyasi: {pdf_filename}")
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
