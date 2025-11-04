import os
from pathlib import Path
import PyPDF2
import sys

def show_detailed_pdf_content():
    """Detaylı PDF içeriğini terminalde göster"""
    try:
        pdf_filename = "FLETC_Artesia_Detailed_Attachment_Analysis_20251018_012150.pdf"
        
        if not os.path.exists(pdf_filename):
            print(f"PDF dosyasi bulunamadi: {pdf_filename}")
            return
        
        print("=" * 100)
        print(f"DETAYLI PDF ICERIGI: {pdf_filename}")
        print("=" * 100)
        
        with open(pdf_filename, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Toplam sayfa sayisi: {num_pages}")
            print("=" * 100)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                print(f"\n{'='*50} SAYFA {page_num + 1} {'='*50}")
                print(text)
                print(f"{'='*100}")
        
    except Exception as e:
        print(f"PDF okuma hatasi: {str(e)}")
        print("PyPDF2 kutuphanesi gerekli. Yuklemek icin: pip install PyPDF2")

if __name__ == "__main__":
    show_detailed_pdf_content()










