import os
import sys
from pathlib import Path
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_simple_analysis_report():
    """Basit doküman analizi raporu oluştur"""
    print("=" * 80)
    print("BASIT DOKUMAN ANALIZI RAPORU OLUSTURULUYOR")
    print("=" * 80)
    
    # PDF dosya adı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"FLETC_Artesia_Lodging_Analysis_Report_{timestamp}.pdf"
    
    try:
        # PDF oluştur
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Başlık
        story.append(Paragraph("FLETC ARTESIA OFF-CENTER LODGING SERVICES", styles['Heading1']))
        story.append(Paragraph("Kapsamli Dokuman Analizi ve Teklif Raporu", styles['Heading2']))
        story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", styles['Heading2']))
        story.append(Paragraph(
            "Bu rapor, FLETC Artesia Off-Center Lodging Services ihalesi için yuklenen 9 dokumanin "
            "kapsamli analizini icermektedir. Analiz, federal konaklama hizmetleri ihalesinin "
            "gereksinimlerini, kisitlamalarini ve basarili teklif verme stratejilerini detaylandirmaktadir.",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Dokuman Analizi
        story.append(Paragraph("DOKUMAN ANALIZI", styles['Heading2']))
        
        documents = [
            "70LART26QPFB00001.pdf - Ana Firsat Dokumani",
            "FLETC+Artesia+Off-Center+Lodging+Services+SOW.pdf - Is Tanimi",
            "Attachment+3+_+Hotel+and+Motel+Fire+Safety+Act+of+1990.pdf - Yangin Guvenligi Yasasi",
            "Attachment+1_Wage+Determination.pdf - Ucret Belirleme Tablolari",
            "Attachment+2_OF347+(fillable).pdf - Teklif Formu",
            "Attachment+4+_+Fire+Administration+Authorization+Act+of+1992.pdf - Yangin Yonetimi Yasasi",
            "Attachment+5_+Summary+Sheet.pdf - Ozet Bilgiler",
            "Attachment+6+_+Sample+Invoice.pdf (2 adet) - Faturalama Ornekleri"
        ]
        
        for i, doc_name in enumerate(documents, 1):
            story.append(Paragraph(f"{i}. {doc_name}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Kritik Gereksinimler
        story.append(Paragraph("KRITIK GEREKSINIMLER", styles['Heading2']))
        
        requirements = [
            "YANGIN GUVENLIGI (EN KRITIK): Hotel and Motel Fire Safety Act of 1990 tam uyumluluk",
            "DAVIS-BACON ACT UCRET GEREKSINIMLERI: Federal minimum ucret standartlarina uyum",
            "FEDERAL SOZLESME DENEYIMI: Federal sozlesme yonetimi deneyimi",
            "PERFORMANS KRITERLERI: Musteri memnuniyeti olcumu ve raporlama"
        ]
        
        for req in requirements:
            story.append(Paragraph(f"• {req}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Teklif Stratejisi
        story.append(Paragraph("TEKLIF STRATEJISI", styles['Heading2']))
        
        strategy = [
            "KISA VADELI (1-2 Ay): Yangin guvenligi sertifikalari alin",
            "ORTA VADELI (3-6 Ay): Teknik teklif hazirlayin",
            "UZUN VADELI (6+ Ay): Federal denetim hazirligi yapin"
        ]
        
        for item in strategy:
            story.append(Paragraph(f"• {item}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Sonuc
        story.append(Paragraph("SONUC VE ONERILER", styles['Heading2']))
        story.append(Paragraph(
            "Bu analiz, FLETC Artesia Off-Center Lodging Services ihalesinin karmasik gereksinimlerini "
            "ve basarili teklif verme icin gerekli hazirliklari ortaya koymaktadir. Yangin guvenligi "
            "sertifikalari en kritik gereksinim olup, bu olmadan teklif verilemez.",
            styles['Normal']
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
        pdf_filename = create_simple_analysis_report()
        
        if pdf_filename:
            print("Rapor basariyla olusturuldu!")
            print(f"PDF dosyasi: {pdf_filename}")
        else:
            print("Rapor olusturulamadi!")
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()










