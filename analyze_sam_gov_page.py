#!/usr/bin/env python3
"""
SAM.gov sayfasını analiz et
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def analyze_sam_gov_page():
    """SAM.gov sayfasını analiz et"""
    
    opportunity_id = "5289707bce504612a0b188ca01d9820c"
    sam_url = f"https://sam.gov/workspace/contract/opp/{opportunity_id}/view"
    
    print(f"=== SAM.gov Sayfa Analizi ===")
    print(f"URL: {sam_url}")
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(sam_url, headers=headers, timeout=30)
        print(f"HTTP Status: {response.status_code}")
        print(f"Content Length: {len(response.content):,} bytes")
        print()
        
        if response.status_code != 200:
            print(f"[ERROR] Sayfa yüklenemedi: HTTP {response.status_code}")
            return
        
        # HTML'i parse et
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sayfa başlığı
        title = soup.find('title')
        if title:
            print(f"Sayfa Başlığı: {title.get_text()}")
        
        # Tüm linkleri bul
        all_links = soup.find_all('a', href=True)
        print(f"\nToplam Link Sayısı: {len(all_links)}")
        
        # PDF linkleri
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        print(f"PDF Linkleri: {len(pdf_links)}")
        for link in pdf_links[:5]:
            print(f"  - {link.get('href')}")
        
        # Diğer belge linkleri
        doc_links = soup.find_all('a', href=re.compile(r'\.(doc|docx|xls|xlsx|txt)', re.I))
        print(f"Diğer Belge Linkleri: {len(doc_links)}")
        for link in doc_links[:5]:
            print(f"  - {link.get('href')}")
        
        # SAM.gov API linkleri
        api_links = soup.find_all('a', href=re.compile(r'api\.sam\.gov', re.I))
        print(f"SAM.gov API Linkleri: {len(api_links)}")
        for link in api_links[:5]:
            print(f"  - {link.get('href')}")
        
        # JavaScript içindeki linkler
        scripts = soup.find_all('script')
        js_links = []
        for script in scripts:
            if script.string:
                found_links = re.findall(r'https?://[^\s"\'<>]+\.(?:pdf|doc|docx|xls|xlsx|txt)', script.string, re.I)
                js_links.extend(found_links)
        
        print(f"JavaScript'teki Belge Linkleri: {len(js_links)}")
        for link in js_links[:5]:
            print(f"  - {link}")
        
        # Data attributes
        data_elements = soup.find_all(attrs={'data-url': True})
        print(f"Data URL'li Elementler: {len(data_elements)}")
        for element in data_elements[:5]:
            print(f"  - {element.get('data-url')}")
        
        # Sayfa içeriğini analiz et
        text_content = soup.get_text()
        print(f"\nSayfa Metin Uzunluğu: {len(text_content):,} karakter")
        
        # Belge referanslarını ara
        doc_refs = re.findall(r'[^\s]*\.(?:pdf|doc|docx|xls|xlsx|txt)', text_content, re.I)
        print(f"Metindeki Belge Referansları: {len(doc_refs)}")
        for ref in doc_refs[:10]:
            print(f"  - {ref}")
        
        # URL'leri ara
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text_content)
        print(f"Metindeki URL'ler: {len(urls)}")
        for url in urls[:10]:
            print(f"  - {url}")
        
        # Sayfa kaynağının bir kısmını göster
        print(f"\n=== Sayfa Kaynağı Örneği ===")
        print(response.text[:1000] + "...")
        
    except Exception as e:
        print(f"[ERROR] Analiz hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_sam_gov_page()
