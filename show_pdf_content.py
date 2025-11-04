import os
from pathlib import Path
import PyPDF2
import sys

def show_pdf_content(pdf_filename):
    """PDF içeriğini terminalde göster"""
    try:
        if not os.path.exists(pdf_filename):
            print(f"PDF dosyasi bulunamadi: {pdf_filename}")
            return
        
        print("=" * 80)
        print(f"PDF ICERIGI: {pdf_filename}")
        print("=" * 80)
        
        with open(pdf_filename, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Toplam sayfa sayisi: {num_pages}")
            print("=" * 80)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                print(f"\n--- SAYFA {page_num + 1} ---")
                print(text)
                print("-" * 40)
        
    except Exception as e:
        print(f"PDF okuma hatasi: {str(e)}")
        print("PyPDF2 kutuphanesi gerekli. Yuklemek icin: pip install PyPDF2")

def main():
    """Ana fonksiyon"""
    # En son oluşturulan PDF dosyasını bul
    pdf_files = list(Path(".").glob("FLETC_Artesia_Detailed_Attachment_Analysis_*.pdf"))
    
    if not pdf_files:
        print("PDF dosyasi bulunamadi!")
        return
    
    # En yeni dosyayı al
    latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
    print(f"En yeni PDF dosyasi: {latest_pdf}")
    
    # PDF içeriğini göster
    show_pdf_content(str(latest_pdf))

if __name__ == "__main__":
    main()
