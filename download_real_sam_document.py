#!/usr/bin/env python3
"""
Gerçek SAM.gov belgesini indirmek için script
"""

import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def download_real_sam_documents():
    """Gerçek SAM.gov belgelerini indir"""
    
    # Fırsat ID'si
    opportunity_id = "5289707bce504612a0b188ca01d9820c"
    
    # SAM.gov fırsat sayfası URL'si
    opportunity_url = f"https://sam.gov/workspace/contract/opp/{opportunity_id}/view"
    
    print(f"=== Gerçek SAM.gov Belge İndirici ===")
    print(f"Fırsat ID: {opportunity_id}")
    print(f"URL: {opportunity_url}")
    print()
    
    # Headers
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
        # Sayfa içeriğini al
        print("SAM.gov sayfası çekiliyor...")
        response = requests.get(opportunity_url, headers=headers, timeout=30)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Sayfa alınamadı: {response.status_code}")
            return
        
        # BeautifulSoup ile parse et
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sayfa başlığını kontrol et
        title = soup.find('title')
        if title:
            print(f"Sayfa Başlığı: {title.get_text()}")
        
        # Belge linklerini ara
        document_links = []
        
        # 1. Tüm 'a' tag'lerini ara ve PDF/doc linkleri bul
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt')):
                full_url = urljoin(opportunity_url, href)
                document_links.append({
                    'title': a_tag.get_text(strip=True) or 'Belge',
                    'url': full_url,
                    'type': 'pdf' if href.lower().endswith('.pdf') else 'doc'
                })
        
        # 2. JavaScript içindeki linkleri ara
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
        
        # 3. Data attributes
        data_elements = soup.find_all(attrs={'data-url': True})
        for element in data_elements:
            data_url = element.get('data-url')
            if data_url and any(data_url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']):
                full_url = urljoin(opportunity_url, data_url)
                document_links.append({
                    'title': 'Data URL Document',
                    'url': full_url,
                    'type': 'pdf' if data_url.lower().endswith('.pdf') else 'doc'
                })
        
        # 4. Genel linkler (belge olabilecek)
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and any(keyword in href.lower() for keyword in ['document', 'attachment', 'download', 'file', 'notice', 'solicitation']):
                full_url = urljoin(opportunity_url, href)
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
                        filename = f"real_sam_doc_{opportunity_id}_{i}{file_extension}"
                        
                        # Dosyayı kaydet
                        with open(filename, 'wb') as f:
                            for chunk in doc_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        file_size = os.path.getsize(filename)
                        print(f"[SUCCESS] Belge başarıyla kaydedildi: {filename}")
                        print(f"[INFO] Boyut: {file_size:,} bytes")
                        downloaded_count += 1
                        
                    elif doc_response.status_code == 401:
                        print(f"[ERROR] Unauthorized - API key gerekli")
                    elif doc_response.status_code == 403:
                        print(f"[ERROR] Forbidden - Erişim reddedildi")
                    elif doc_response.status_code == 404:
                        print(f"[ERROR] Not Found - Belge bulunamadı")
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
            print("[INFO] SAM.gov sayfası JavaScript ile yükleniyor olabilir.")
            print("[INFO] Selenium kullanarak dinamik içeriği çekmek gerekebilir.")
            
            # Sayfa içeriğinin bir kısmını göster
            print(f"\n=== Sayfa İçeriği Örneği ===")
            text_content = soup.get_text()
            print(f"Toplam metin uzunluğu: {len(text_content):,} karakter")
            print(f"İçerik: {text_content[:500]}...")
    
    except Exception as e:
        print(f"[ERROR] Genel hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    download_real_sam_documents()
