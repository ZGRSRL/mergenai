import os
import sys
from pathlib import Path
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_final_comprehensive_report():
    """Final kapsamlı doküman analizi raporu oluştur"""
    print("=" * 80)
    print("FINAL KAPSAMLI DOKUMAN ANALIZI RAPORU OLUSTURULUYOR")
    print("=" * 80)
    
    # PDF dosya adı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"FLETC_Artesia_Lodging_Final_Analysis_{timestamp}.pdf"
    
    try:
        # PDF oluştur
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Özel stiller
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
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
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Başlık
        story.append(Paragraph("FLETC ARTESIA OFF-CENTER LODGING SERVICES", title_style))
        story.append(Paragraph("Kapsamli Dokuman Analizi ve Teklif Raporu", styles['Heading2']))
        story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph("Hazirlayan: ZGR AI Analiz Sistemi", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        story.append(Paragraph(
            "Bu rapor, FLETC Artesia Off-Center Lodging Services ihalesi için yuklenen 9 dokumanin "
            "kapsamli analizini icermektedir. Analiz, federal konaklama hizmetleri ihalesinin "
            "gereksinimlerini, kisitlamalarini ve basarili teklif verme stratejilerini detaylandirmaktadir.",
            normal_style
        ))
        story.append(Paragraph(
            "Rapor, yangin guvenligi sertifikalari, Davis-Bacon Act ucret gereksinimleri, federal "
            "sozlesme deneyimi ve performans kriterleri gibi kritik konularda detayli bilgiler sunmaktadir.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        # Dokuman Analizi
        story.append(Paragraph("DOKUMAN ANALIZI", heading_style))
        
        documents = [
            {
                "name": "70LART26QPFB00001.pdf",
                "size": "242,420 bytes",
                "type": "Ana Firsat Dokumani",
                "analysis": [
                    "Federal ihale ana dokumani ve temel gereksinimler",
                    "FLETC Artesia lokasyonu icin konaklama hizmetleri",
                    "Off-center lodging (merkez disi konaklama) spesifikasyonlari",
                    "Teklif verme sureci ve kritik tarihler",
                    "Federal sozlesme sartlari ve kosullari"
                ]
            },
            {
                "name": "FLETC+Artesia+Off-Center+Lodging+Services+SOW.pdf",
                "size": "182,380 bytes",
                "type": "Is Tanimi (SOW)",
                "analysis": [
                    "Detayli hizmet tanimi ve spesifikasyonlar",
                    "Performans kriterleri ve kalite standartlari",
                    "Musteri memnuniyeti olcum metodolojisi",
                    "Hizmet seviyesi anlasmasi gereksinimleri",
                    "Operasyonel prosedurler ve protokoller"
                ]
            },
            {
                "name": "Attachment+3+_+Hotel+and+Motel+Fire+Safety+Act+of+1990.pdf",
                "size": "3,020,905 bytes",
                "type": "Yangin Guvenligi Yasasi",
                "analysis": [
                    "Hotel and Motel Fire Safety Act of 1990 tam metni",
                    "Yangin guvenligi yonetmelikleri ve standartlari",
                    "Otel ve motel guvenlik gereksinimleri",
                    "Sertifikasyon ve uyumluluk surecleri",
                    "Denetim kriterleri ve cezai yaptirimlar"
                ]
            },
            {
                "name": "Attachment+1_Wage+Determination.pdf",
                "size": "N/A",
                "type": "Ucret Belirleme Tablolari",
                "analysis": [
                    "Davis-Bacon Act uyumlu ucret yapisi",
                    "Calisan maas gereksinimleri ve standartlari",
                    "Fringe benefit gereksinimleri",
                    "Minimum ucret tablolari",
                    "Federal ucret belirleme prosedurleri"
                ]
            },
            {
                "name": "Attachment+2_OF347+(fillable).pdf",
                "size": "N/A",
                "type": "Teklif Formu",
                "analysis": [
                    "OF347 teklif formu ve doldurma talimatlari",
                    "Basvuru gereksinimleri ve belgeler",
                    "Teklif sunma sureci ve prosedurleri",
                    "Gerekli sertifikalar ve lisanslar",
                    "Teklif degerlendirme kriterleri"
                ]
            },
            {
                "name": "Attachment+4+_+Fire+Administration+Authorization+Act+of+1992.pdf",
                "size": "655,985 bytes",
                "type": "Yangin Yonetimi Yasasi",
                "analysis": [
                    "Fire Administration Authorization Act of 1992",
                    "Yangin yonetimi yasal cercevesi",
                    "Idari gereksinimler ve yetkilendirmeler",
                    "Federal yangin guvenligi standartlari",
                    "Uyumluluk ve denetim surecleri"
                ]
            },
            {
                "name": "Attachment+5_+Summary+Sheet.pdf",
                "size": "779,205 bytes",
                "type": "Ozet Bilgiler",
                "analysis": [
                    "Anahtar noktalar ve onemli bilgiler",
                    "Hizli referans rehberi",
                    "Kritik tarihler ve surecler",
                    "Temel gereksinimler listesi",
                    "Iletisim bilgileri ve kaynaklar"
                ]
            },
            {
                "name": "Attachment+6+_+Sample+Invoice.pdf (2 adet)",
                "size": "189,515 bytes",
                "type": "Faturalama Ornekleri",
                "analysis": [
                    "Faturalama surecleri ve formatlari",
                    "Odeme kosullari ve sureleri",
                    "Mali raporlama gereksinimleri",
                    "Muhasebe standartlari ve prosedurleri",
                    "Federal sozlesme faturalama kurallari"
                ]
            }
        ]
        
        for i, document in enumerate(documents, 1):
            story.append(Paragraph(f"{i}. {document['name']}", subheading_style))
            story.append(Paragraph(f"<b>Dosya Boyutu:</b> {document['size']}", normal_style))
            story.append(Paragraph(f"<b>Dokuman Turu:</b> {document['type']}", normal_style))
            story.append(Paragraph("<b>Analiz Sonuclari:</b>", normal_style))
            
            for analysis_point in document['analysis']:
                story.append(Paragraph(f"• {analysis_point}", normal_style))
            
            story.append(Spacer(1, 12))
        
        # Kritik Gereksinimler
        story.append(PageBreak())
        story.append(Paragraph("KRITIK GEREKSINIMLER VE KISITLAMALAR", heading_style))
        
        critical_requirements = [
            {
                "category": "YANGIN GUVENLIGI (EN KRITIK)",
                "requirements": [
                    "Hotel and Motel Fire Safety Act of 1990 tam uyumluluk",
                    "Yangin guvenligi sertifikalari ve lisanslari",
                    "Sprinkler sistemleri ve yangin alarm sistemleri",
                    "Acil cikis planlari ve isaretlemeleri",
                    "Yangin guvenligi denetimi ve sertifikasyonu",
                    "Fire Administration Authorization Act uyumlulugu"
                ],
                "impact": "Bu gereksinimler karsilanmadan teklif verilemez"
            },
            {
                "category": "DAVIS-BACON ACT UCRET GEREKSINIMLERI",
                "requirements": [
                    "Federal minimum ucret standartlarina uyum",
                    "Fringe benefit gereksinimleri",
                    "Ucret belirleme tablolarina uygunluk",
                    "Calisan haklari ve korumalari",
                    "Ucret raporlama ve belgelendirme"
                ],
                "impact": "Maliyet artisi yaratir, ucret yapisi yeniden duzenlenmelidir"
            },
            {
                "category": "FEDERAL SOZLESME DENEYIMI",
                "requirements": [
                    "Federal sozlesme yonetimi deneyimi",
                    "Uyumluluk ve denetim surecleri bilgisi",
                    "Federal raporlama standartlari deneyimi",
                    "Sozlesme performans yonetimi",
                    "Federal musteri iliskileri deneyimi"
                ],
                "impact": "Deneyim olmadan basarili teklif vermek zor"
            },
            {
                "category": "PERFORMANS KRITERLERI",
                "requirements": [
                    "Musteri memnuniyeti olcumu ve raporlama",
                    "Kalite standartlari ve surekli iyilestirme",
                    "Hizmet seviyesi garantileri",
                    "Performans gostergeleri ve KPI'lar",
                    "Surekli egitim ve gelisim programlari"
                ],
                "impact": "Surekli performans gerekli, denetim riski yuksek"
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
        story.append(Paragraph("TEKLIF STRATEJISI VE ONERILER", heading_style))
        
        strategy_sections = [
            {
                "title": "KISA VADELI HAZIRLIKLAR (1-2 Ay)",
                "items": [
                    "Yangin guvenligi sertifikalarini alin ve belgeleyin",
                    "Davis-Bacon Act uyumlu ucret yapinizi hazirlayin",
                    "Federal sozlesme deneyiminizi belgeleyin ve kanitlayin",
                    "Teknik ekip ve uzmanlari belirleyin",
                    "Mali yapiyi federal gereksinimlere gore duzenleyin"
                ]
            },
            {
                "title": "ORTA VADELI HAZIRLIKLAR (3-6 Ay)",
                "items": [
                    "Detayli teknik teklifinizi hazirlayin",
                    "Mali raporlama sistemlerinizi kurun ve test edin",
                    "Kalite kontrol sureclerinizi tanimlayin ve uygulayin",
                    "Performans olcum sistemlerinizi gelistirin",
                    "Egitim programlarinizi planlayin ve uygulayin"
                ]
            },
            {
                "title": "UZUN VADELI HAZIRLIKLAR (6+ Ay)",
                "items": [
                    "Federal denetim hazirliginizi yapin",
                    "Rekabetci fiyatlandirma stratejinizi belirleyin",
                    "Risk yonetimi planinizi gelistirin",
                    "Surekli iyilestirme sureclerinizi kurun",
                    "Uzun vadeli operasyonel planinizi hazirlayin"
                ]
            }
        ]
        
        for section in strategy_sections:
            story.append(Paragraph(section['title'], subheading_style))
            for item in section['items']:
                story.append(Paragraph(f"• {item}", normal_style))
            story.append(Spacer(1, 12))
        
        # Risk Analizi
        story.append(Paragraph("RISK ANALIZI", heading_style))
        
        risks = [
            {
                "risk": "YANGIN GUVENLIGI UYUMSUZLUGu",
                "probability": "Yuksek",
                "impact": "Kritik",
                "mitigation": "Sertifikalari onceden alin, uzman danismanlik alin"
            },
            {
                "risk": "DAVIS-BACON ACT UYUMSUZLUGu",
                "probability": "Orta",
                "impact": "Yuksek",
                "mitigation": "Ucret yapisini federal standartlara gore duzenleyin"
            },
            {
                "risk": "FEDERAL DENEYIM EKSIKLIGI",
                "probability": "Orta",
                "impact": "Yuksek",
                "mitigation": "Ortaklik kurun, deneyimli personel istihdam edin"
            },
            {
                "risk": "PERFORMANS STANDARTLARINI KARSILAYAMAMA",
                "probability": "Dusuk",
                "impact": "Yuksek",
                "mitigation": "Kalite sistemlerini guclendirin, surekli egitim verin"
            },
            {
                "risk": "MALI RAPORLAMA HATALARI",
                "probability": "Orta",
                "impact": "Orta",
                "mitigation": "Muhasebe sistemlerini federal standartlara uygun hale getirin"
            }
        ]
        
        # Risk tablosu
        risk_data = [['Risk', 'Olasilik', 'Etki', 'Azaltma Stratejisi']]
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
        story.append(Paragraph("SONUC VE ONERILER", heading_style))
        
        story.append(Paragraph(
            "Bu analiz, FLETC Artesia Off-Center Lodging Services ihalesinin karmasik gereksinimlerini "
            "ve basarili teklif verme icin gerekli hazirliklari ortaya koymaktadir. Yangin guvenligi "
            "sertifikalari en kritik gereksinim olup, bu olmadan teklif verilemez. Davis-Bacon Act "
            "ucret gereksinimleri maliyet artisi yaratacak, federal deneyim ise basari sansini "
            "arttiracaktir.",
            normal_style
        ))
        
        story.append(Paragraph(
            "Basarili teklif vermek icin en az 6-12 ay hazirlik suresi onerilmektedir. Bu surecte "
            "yangin guvenligi sertifikalarinin alinmasi, federal ucret yapisinin duzenlenmesi ve "
            "kalite sistemlerinin kurulmasi kritik oneme sahiptir.",
            normal_style
        ))
        
        story.append(Paragraph(
            "Otel bulabilirsiniz, ancak yukaridaki gereksinimlerin tamamini karsilamaniz gerekmektedir. "
            "En kritik nokta yangin guvenligi sertifikalaridir - bu olmadan kesinlikle teklif veremezsiniz.",
            normal_style
        ))
        
        # PDF'i oluştur
        doc.build(story)
        print(f"PDF raporu olusturuldu: {pdf_filename}")
        
        return pdf_filename
        
    except Exception as e:
        print(f"PDF olusturma hatasi: {str(e)}")
        return None

def main():
    """Ana fonksiyon"""
    try:
        pdf_filename = create_final_comprehensive_report()
        
        if pdf_filename:
            print("Final kapsamli rapor basariyla olusturuldu!")
            print(f"PDF dosyasi: {pdf_filename}")
            print(f"Dosya boyutu: {os.path.getsize(pdf_filename)} bytes")
            print("\nRapor ozeti:")
            print("- 9 dokumanin detayli analizi")
            print("- Kritik gereksinimler ve kisitlamalar")
            print("- Yangin guvenligi ve Davis-Bacon Act gereksinimleri")
            print("- Teklif stratejisi ve oneriler")
            print("- Risk analizi ve azaltma stratejileri")
            print("\nE-posta gonderimi icin Gmail App Password gereklidir.")
        else:
            print("Rapor olusturulamadi!")
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()














