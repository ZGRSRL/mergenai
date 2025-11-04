#!/usr/bin/env python3
"""
SAM.gov Belge Scraper - Gerçek SAM.gov sayfalarından belgeleri indir
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin, urlparse
import sys
import os
sys.path.append('.')

from document_downloader import DocumentDownloader

class SAMGovScraper:
    """SAM.gov sayfalarından belgeleri çeken sınıf"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
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
        })
        self.downloader = DocumentDownloader()
    
    def scrape_opportunity_documents(self, opportunity_id):
        """Belirli bir fırsat için belgeleri çek"""
        
        sam_url = f"https://sam.gov/workspace/contract/opp/{opportunity_id}/view"
        
        print(f"[SAM_SCRAPER] SAM.gov sayfası çekiliyor: {sam_url}")
        
        try:
            # SAM.gov sayfasını çek
            response = self.session.get(sam_url, timeout=30)
            print(f"[SAM_SCRAPER] HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[SAM_SCRAPER] Sayfa yüklenemedi: HTTP {response.status_code}")
                return []
            
            # HTML'i parse et
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Belge linklerini ara
            document_links = self._find_document_links(soup, sam_url)
            
            print(f"[SAM_SCRAPER] {len(document_links)} belge linki bulundu")
            
            # Belgeleri indir
            downloaded_documents = []
            for i, link in enumerate(document_links[:5], 1):  # Maksimum 5 belge
                print(f"[SAM_SCRAPER] Belge {i}/{len(document_links)} indiriliyor: {link}")
                
                try:
                    doc_result = self.downloader.download_document(link, f"sam_{opportunity_id}_{i}")
                    if doc_result:
                        downloaded_documents.append(doc_result)
                        print(f"[SAM_SCRAPER] ✅ Belge indirildi: {doc_result['filename']}")
                    else:
                        print(f"[SAM_SCRAPER] ❌ Belge indirilemedi: {link}")
                except Exception as e:
                    print(f"[SAM_SCRAPER] ❌ İndirme hatası: {e}")
                
                # Rate limiting
                time.sleep(1)
            
            return downloaded_documents
            
        except Exception as e:
            print(f"[SAM_SCRAPER] Hata: {e}")
            return []
    
    def _find_document_links(self, soup, base_url):
        """HTML'den belge linklerini bul"""
        
        document_links = []
        
        # 1. Direkt PDF linkleri
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        for link in pdf_links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                document_links.append(full_url)
        
        # 2. Diğer belge linkleri
        doc_links = soup.find_all('a', href=re.compile(r'\.(doc|docx|xls|xlsx|txt)', re.I))
        for link in doc_links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                document_links.append(full_url)
        
        # 3. SAM.gov API linkleri
        api_links = soup.find_all('a', href=re.compile(r'api\.sam\.gov', re.I))
        for link in api_links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                document_links.append(full_url)
        
        # 4. Genel linkler (belge olabilecek)
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and self._looks_like_document(href):
                full_url = urljoin(base_url, href)
                document_links.append(full_url)
        
        # 5. JavaScript içindeki linkler
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                js_links = re.findall(r'https?://[^\s"\'<>]+\.(?:pdf|doc|docx|xls|xlsx|txt)', script.string, re.I)
                for js_link in js_links:
                    document_links.append(js_link)
        
        # 6. Data attributes
        data_links = soup.find_all(attrs={'data-url': True})
        for element in data_links:
            data_url = element.get('data-url')
            if data_url and self._looks_like_document(data_url):
                full_url = urljoin(base_url, data_url)
                document_links.append(full_url)
        
        # Duplicate'leri kaldır
        document_links = list(set(document_links))
        
        # Linkleri filtrele
        filtered_links = []
        for link in document_links:
            if self._is_valid_document_link(link):
                filtered_links.append(link)
        
        return filtered_links
    
    def _looks_like_document(self, url):
        """URL'nin belge gibi görünüp görünmediğini kontrol et"""
        
        doc_patterns = [
            r'\.pdf$',
            r'\.docx?$',
            r'\.xlsx?$',
            r'\.txt$',
            r'document',
            r'attachment',
            r'download',
            r'file',
            r'notice',
            r'solicitation'
        ]
        
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in doc_patterns)
    
    def _is_valid_document_link(self, url):
        """Belge linkinin geçerli olup olmadığını kontrol et"""
        
        # Geçersiz pattern'ler
        invalid_patterns = [
            r'javascript:',
            r'mailto:',
            r'tel:',
            r'#',
            r'\.css$',
            r'\.js$',
            r'\.png$',
            r'\.jpg$',
            r'\.gif$',
            r'\.ico$'
        ]
        
        url_lower = url.lower()
        return not any(re.search(pattern, url_lower) for pattern in invalid_patterns)
    
    def cleanup(self):
        """Temizlik"""
        self.downloader.cleanup()

def test_sam_gov_scraper():
    """SAM.gov scraper'ı test et"""
    
    scraper = SAMGovScraper()
    
    # Test fırsatları
    test_opportunities = [
        "5289707bce504612a0b188ca01d9820c",  # Lease of TFS Hangars
        "15d1e0267df94c9a815787c824591e87",  # BEAM,AIRCRAFT
        "ff69dee8ce534260975fb4a9c81ca972"   # Custodial services
    ]
    
    for opp_id in test_opportunities:
        print(f"\n=== Test Fırsatı: {opp_id} ===")
        documents = scraper.scrape_opportunity_documents(opp_id)
        
        if documents:
            print(f"[SUCCESS] {len(documents)} belge indirildi:")
            for i, doc in enumerate(documents, 1):
                print(f"  {i}. {doc['filename']} ({doc['size']:,} bytes)")
        else:
            print("[ERROR] Hiç belge indirilemedi")
    
    scraper.cleanup()

if __name__ == "__main__":
    test_sam_gov_scraper()
