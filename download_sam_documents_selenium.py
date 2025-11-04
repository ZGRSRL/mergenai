#!/usr/bin/env python3
"""
Selenium ile SAM.gov belgelerini indir
"""

import os
import time
import requests
from urllib.parse import urljoin
import re

def download_sam_documents_selenium():
    """Selenium ile SAM.gov belgelerini indir"""
    
    opportunity_id = "5289707bce504612a0b188ca01d9820c"
    sam_url = f"https://sam.gov/workspace/contract/opp/{opportunity_id}/view"
    
    print(f"=== Selenium ile SAM.gov Belge İndirici ===")
    print(f"Fırsat ID: {opportunity_id}")
    print(f"URL: {sam_url}")
    print()
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup
        
        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        print("Chrome driver başlatılıyor...")
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print("SAM.gov sayfası yükleniyor...")
            driver.get(sam_url)
            
            # Sayfa yüklenmesini bekle
            wait = WebDriverWait(driver, 20)
            time.sleep(5)  # Ekstra bekleme
            
            print(f"Sayfa başlığı: {driver.title}")
            print(f"URL: {driver.current_url}")
            
            # Sayfa kaynağını al
            page_source = driver.page_source
            print(f"Sayfa kaynağı uzunluğu: {len(page_source):,} karakter")
            
            # BeautifulSoup ile parse et
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Belge linklerini ara
            document_links = []
            
            # 1. PDF linkleri
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            for link in pdf_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(sam_url, href)
                    document_links.append({
                        'title': link.get_text(strip=True) or 'PDF Document',
                        'url': full_url,
                        'type': 'pdf'
                    })
            
            # 2. Diğer belge linkleri
            doc_links = soup.find_all('a', href=re.compile(r'\.(doc|docx|xls|xlsx|txt)', re.I))
            for link in doc_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(sam_url, href)
                    document_links.append({
                        'title': link.get_text(strip=True) or 'Document',
                        'url': full_url,
                        'type': 'doc'
                    })
            
            # 3. JavaScript içindeki linkler
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # PDF linkleri
                    pdf_links = re.findall(r'https?://[^\s"\'<>]+\.pdf', script.string, re.I)
                    for link in pdf_links:
                        document_links.append({
                            'title': 'JavaScript PDF',
                            'url': link,
                            'type': 'pdf'
                        })
                    
                    # Diğer belge linkleri
                    doc_links = re.findall(r'https?://[^\s"\'<>]+\.(?:doc|docx|xls|xlsx|txt)', script.string, re.I)
                    for link in doc_links:
                        document_links.append({
                            'title': 'JavaScript Document',
                            'url': link,
                            'type': 'doc'
                        })
            
            # 4. Data attributes
            data_elements = soup.find_all(attrs={'data-url': True})
            for element in data_elements:
                data_url = element.get('data-url')
                if data_url and any(data_url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']):
                    full_url = urljoin(sam_url, data_url)
                    document_links.append({
                        'title': 'Data URL Document',
                        'url': full_url,
                        'type': 'pdf' if data_url.lower().endswith('.pdf') else 'doc'
                    })
            
            # 5. Genel linkler
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href and any(keyword in href.lower() for keyword in ['document', 'attachment', 'download', 'file', 'notice', 'solicitation']):
                    full_url = urljoin(sam_url, href)
                    document_links.append({
                        'title': link.get_text(strip=True) or 'Document Link',
                        'url': full_url,
                        'type': 'unknown'
                    })
            
            # Benzersiz linkleri al
            unique_links = []
            seen_urls = set()
            for link in document_links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            print(f"\nBulunan belge sayısı: {len(unique_links)}")
            for i, link in enumerate(unique_links, 1):
                print(f"{i}. {link['title']} - {link['url']}")
            
            # Belgeleri indir
            if unique_links:
                print(f"\n=== Belgeler İndiriliyor ===")
                downloaded_count = 0
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                for i, doc in enumerate(unique_links[:5], 1):  # Maksimum 5 belge
                    print(f"\n--- Belge {i}: {doc['title']} ---")
                    print(f"URL: {doc['url']}")
                    
                    try:
                        # Belgeyi indir
                        doc_response = requests.get(doc['url'], headers=headers, stream=True, timeout=30)
                        print(f"HTTP Status: {doc_response.status_code}")
                        
                        if doc_response.status_code == 200:
                            # Dosya adını oluştur
                            file_extension = '.pdf' if doc['type'] == 'pdf' else '.doc'
                            filename = f"selenium_sam_doc_{opportunity_id}_{i}{file_extension}"
                            
                            # Dosyayı kaydet
                            with open(filename, 'wb') as f:
                                for chunk in doc_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            file_size = os.path.getsize(filename)
                            print(f"[SUCCESS] Belge başarıyla kaydedildi: {filename}")
                            print(f"[INFO] Boyut: {file_size:,} bytes")
                            downloaded_count += 1
                            
                        else:
                            print(f"[ERROR] Belge indirilemedi: HTTP {doc_response.status_code}")
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"[ERROR] İndirme hatası: {e}")
                
                print(f"\n=== Özet ===")
                print(f"Toplam bulunan belge: {len(unique_links)}")
                print(f"Başarıyla indirilen: {downloaded_count}")
                
            else:
                print("\n[WARNING] Hiç belge bulunamadı.")
                print("[INFO] Sayfa içeriği analiz ediliyor...")
                
                # Sayfa içeriğini analiz et
                text_content = soup.get_text()
                print(f"Toplam metin uzunluğu: {len(text_content):,} karakter")
                
                # Belge referanslarını ara
                doc_refs = re.findall(r'[^\s]*\.(?:pdf|doc|docx|xls|xlsx|txt)', text_content, re.I)
                if doc_refs:
                    print(f"Metindeki belge referansları: {len(doc_refs)}")
                    for ref in doc_refs[:10]:
                        print(f"  - {ref}")
                
                # URL'leri ara
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text_content)
                if urls:
                    print(f"Metindeki URL'ler: {len(urls)}")
                    for url in urls[:10]:
                        print(f"  - {url}")
            
        finally:
            driver.quit()
            
    except ImportError:
        print("[ERROR] Selenium yüklü değil.")
        print("[INFO] Yüklemek için: pip install selenium")
        print("[INFO] Chrome driver gerekli: https://chromedriver.chromium.org/")
    except Exception as e:
        print(f"[ERROR] Selenium hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    download_sam_documents_selenium()
