#!/usr/bin/env python3
"""
Kritik İlan Analizi Workflow'u
SAM.gov ilanını tam otomatik analiz edip RAG sistemine hazır hale getirir

Adımlar:
1. SAM.gov'dan metadata çekme
2. Dokümanları indirme ve metin çıkarma
3. Gereksinimleri çıkarma (LLM/Agent)
4. SOW analizi yapma
5. Veritabanına kaydetme
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Add current directory to path
sys.path.append('.')
sys.path.append('./sam/document_management')

# Import dependencies
try:
    from sam_api_client import SAMAPIClient
    from sow_analysis_manager import SOWAnalysisManager, SOWAnalysisResult
    # download_sam_docs fallback için (API primary, bu fallback)
    try:
        from download_sam_docs import fetch_resource_links, download_attachment
    except ImportError:
        fetch_resource_links = None
        download_attachment = None
        logging.warning("download_sam_docs optional - sam_api_client kullanilacak")
except ImportError as e:
    logging.warning(f"Import error (some modules may be optional): {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AnalysisWorkflowResult:
    """Workflow sonuç veri yapısı"""
    notice_id: str
    success: bool
    metadata: Dict[str, Any] = None
    downloaded_files: List[str] = None
    extracted_requirements: Dict[str, Any] = None
    sow_analysis: Dict[str, Any] = None
    analysis_id: str = None
    errors: List[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.errors is None:
            self.errors = []


class OpportunityAnalysisWorkflow:
    """
    Tam otomatik ilan analizi workflow'u
    
    Bu workflow şunları yapar:
    1. SAM.gov'dan ilan metadata'sını çeker
    2. Ek dokümanları indirir ve metin çıkarır
    3. LLM/Agent ile gereksinimleri çıkarır
    4. SOW analizi yapar
    5. ZGR_AI veritabanına kaydeder
    """
    
    def __init__(self, download_dir: str = None, use_llm: bool = True):
        """
        Initialize workflow
        
        Args:
            download_dir: Dokümanların indirileceği dizin
            use_llm: LLM ile gereksinim çıkarımı yapılsın mı?
        """
        # Initialize SAM API client
        self.sam_client = SAMAPIClient(
            public_api_key=os.getenv('SAM_PUBLIC_API_KEY'),
            system_api_key=os.getenv('SAM_SYSTEM_API_KEY'),
            mode="auto"
        )
        
        # Initialize SOW analysis manager
        self.sow_manager = SOWAnalysisManager()
        
        # Download directory
        self.download_dir = Path(download_dir or os.getenv('DOWNLOAD_PATH', './downloads'))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_llm = use_llm
        logger.info(f"Opportunity Analysis Workflow initialized")
        logger.info(f"Download directory: {self.download_dir.absolute()}")
    
    def run(self, notice_id: str) -> AnalysisWorkflowResult:
        """
        Tam workflow'u çalıştır
        
        Args:
            notice_id: SAM.gov notice ID
            
        Returns:
            AnalysisWorkflowResult with all analysis data
        """
        result = AnalysisWorkflowResult(notice_id=notice_id, success=False)
        logger.info(f"=" * 80)
        logger.info(f"ILAN ANALIZI BASLIYOR: {notice_id}")
        logger.info(f"=" * 80)
        
        try:
            # ADIM 1: Metadata Çekme
            logger.info(f"\n[ADIM 1] Metadata cekiliyor...")
            metadata = self.fetch_metadata(notice_id)
            if not metadata:
                result.errors.append("Metadata cekilemedi")
                return result
            result.metadata = metadata
            logger.info(f"[OK] Metadata cekildi: {metadata.get('title', 'N/A')}")
            
            # ADIM 2: Doküman İndirme ve Metin Çıkarma
            logger.info(f"\n[ADIM 2] Dokumanlar indiriliyor...")
            downloaded_files = self.download_and_extract_docs(notice_id, metadata)
            if not downloaded_files:
                logger.warning("Dokuman indirilemedi, devam ediliyor...")
            result.downloaded_files = downloaded_files
            logger.info(f"[OK] {len(downloaded_files)} dosya indirildi")
            
            # ADIM 3: Gereksinim Çıkarımı
            logger.info(f"\n[ADIM 3] Gereksinimler cikariliyor...")
            requirements = self.extract_requirements(notice_id, metadata, downloaded_files)
            result.extracted_requirements = requirements
            logger.info(f"[OK] Gereksinimler cikarildi")
            
            # ADIM 4: SOW Analizi
            logger.info(f"\n[ADIM 4] SOW analizi yapiliyor...")
            sow_analysis = self.analyze_sow(notice_id, metadata, requirements, downloaded_files)
            result.sow_analysis = sow_analysis
            logger.info(f"[OK] SOW analizi tamamlandi")
            
            # ADIM 5: Veritabanına Kaydetme
            logger.info(f"\n[ADIM 5] Veritabanina kaydediliyor...")
            analysis_id = self.save_analysis(notice_id, metadata, requirements, sow_analysis, downloaded_files)
            result.analysis_id = analysis_id
            result.success = True
            logger.info(f"[OK] Analiz kaydedildi: {analysis_id}")
            
            logger.info(f"\n" + "=" * 80)
            logger.info(f"ILAN ANALIZI BASARILI!")
            logger.info(f"=" * 80)
            
        except Exception as e:
            logger.error(f"Workflow hatasi: {e}", exc_info=True)
            result.errors.append(str(e))
            result.success = False
        
        return result
    
    def fetch_metadata(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """
        ADIM 1: SAM.gov'dan ilan metadata'sını çek
        
        Args:
            notice_id: Notice ID
            
        Returns:
            Metadata dictionary
        """
        try:
            # SAM API'den ilan detaylarını çek
            opportunity = self.sam_client.get_opportunity_details(notice_id)
            
            if not opportunity:
                logger.warning("SAM API'den veri alinamadi")
                # Minimum fallback - sadece notice_id ile devam et
                return {
                    'notice_id': notice_id,
                    'title': f'Opportunity {notice_id}',
                    'url': f"https://sam.gov/workspace/contract/opp/{notice_id}/view"
                }
            
            # Metadata yapılandır
            metadata = {
                'notice_id': notice_id,
                'title': opportunity.get('title', ''),
                'agency': opportunity.get('department', ''),
                'organization_type': opportunity.get('organizationType', ''),
                'naics_code': opportunity.get('naicsCode', ''),
                'posted_date': opportunity.get('postedDate', ''),
                'response_deadline': opportunity.get('responseDeadline', ''),
                'description': opportunity.get('description', ''),
                'contract_type': opportunity.get('typeOfSetAside', ''),
                'attachments': opportunity.get('attachments', []),
                'point_of_contact': opportunity.get('pointOfContact', {}),
                'url': f"https://sam.gov/workspace/contract/opp/{notice_id}/view"
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata cekme hatasi: {e}")
            return None
    
    
    def download_and_extract_docs(self, notice_id: str, metadata: Dict[str, Any]) -> List[str]:
        """
        ADIM 2: Ek dokümanları indir ve metin çıkar
        
        Args:
            notice_id: Notice ID
            metadata: İlan metadata'sı
            
        Returns:
            İndirilen dosya yolları listesi
        """
        downloaded_files = []
        
        try:
            # Notice ID klasörü oluştur
            opp_dir = self.download_dir / notice_id
            opp_dir.mkdir(parents=True, exist_ok=True)
            
            # API tabanlı indirme - sam_api_client kullan
            logger.info(f"API tabanli dokuman indirme basliyor...")
            
            # Method 1: sam_api_client.get_resource_links + download_all_attachments
            try:
                resource_links = self.sam_client.get_resource_links(notice_id)
                
                if resource_links:
                    logger.info(f"Resource links API'den bulundu: {len(resource_links)} link")
                    # sam_api_client ile indirme
                    downloaded_files = self.sam_client.download_all_attachments(
                        notice_id, 
                        str(opp_dir)
                    )
                    if downloaded_files:
                        logger.info(f"[OK] {len(downloaded_files)} dosya indirildi (API)")
                        return [str(f) for f in downloaded_files]
                
            except Exception as e:
                logger.warning(f"sam_api_client indirme hatasi: {e}, fetch_resource_links deneniyor...")
            
            # Method 2: download_sam_docs.fetch_resource_links (fallback)
            if fetch_resource_links and download_attachment:
                try:
                    logger.info(f"fetch_resource_links ile deneme (fallback)...")
                    resource_links = fetch_resource_links(notice_id)
                    
                    if not resource_links:
                        logger.warning("Resource links bulunamadi (fetch_resource_links)")
                        return downloaded_files
                    
                    logger.info(f"Resource links bulundu: {len(resource_links)} link")
                    
                    # Her resource link için doküman indir
                    last_call = [0.0]
                    for i, link_data in enumerate(resource_links[:20], 1):  # İlk 20 doküman
                        try:
                            url = link_data.get('url') or link_data.get('link')
                            if not url:
                                continue
                            
                            filename = link_data.get('filename') or link_data.get('title') or f"document_{i}.pdf"
                            base_name = Path(filename).stem
                            
                            logger.info(f"[{i}/{len(resource_links)}] Indiriliyor: {filename}")
                            file_path = download_attachment(url, opp_dir, base_name, last_call)
                            
                            if file_path and file_path.exists():
                                downloaded_files.append(str(file_path))
                                logger.info(f"[OK] {filename} indirildi -> {file_path}")
                            
                        except Exception as e:
                            logger.warning(f"Dosya indirme hatasi {i}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"fetch_resource_links hatasi: {e}")
            else:
                logger.info("fetch_resource_links/download_attachment modulleri yok, sadece API kullanildi")
            
            # İndirilen dosyalardan metin çıkar (opsiyonel)
            if downloaded_files:
                logger.info(f"Metin cikarma basliyor...")
                # comprehensive_document_analysis kullanılabilir
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Dokuman indirme hatasi: {e}")
            return downloaded_files
    
    def extract_requirements(self, notice_id: str, metadata: Dict[str, Any], 
                            downloaded_files: List[str]) -> Dict[str, Any]:
        """
        ADIM 3: Dokümanlardan gereksinimleri çıkar (LLM/Agent kullanarak)
        
        Args:
            notice_id: Notice ID
            metadata: İlan metadata'sı
            downloaded_files: İndirilen dosya yolları
            
        Returns:
            Yapılandırılmış gereksinimler dictionary
        """
        requirements = {
            'room_requirements': {},
            'conference_requirements': {},
            'av_requirements': {},
            'catering_requirements': {},
            'compliance_requirements': {},
            'pricing_requirements': {},
            'general_requirements': []
        }
        
        try:
            if not self.use_llm:
                logger.info("LLM kullanilmadan temel gereksinimler cikariliyor...")
                return self._extract_requirements_basic(metadata, downloaded_files)
            
            # LLM ile gereksinim çıkarımı
            logger.info("LLM ile gereksinimler cikariliyor...")
            
            # Doküman metinlerini birleştir
            all_text = []
            all_text.append(f"Title: {metadata.get('title', '')}")
            all_text.append(f"Description: {metadata.get('description', '')}")
            
            # İndirilen dosyalardan metin çıkar
            for file_path in downloaded_files[:5]:  # İlk 5 dosya
                try:
                    from unstructured.partition.auto import partition
                    elements = partition(str(file_path))
                    text = "\n".join([str(elem) for elem in elements if hasattr(elem, 'text')])
                    all_text.append(f"\n--- {Path(file_path).name} ---\n{text[:5000]}")  # İlk 5000 karakter
                except Exception as e:
                    logger.warning(f"Metin cikarma hatasi {file_path}: {e}")
            
            combined_text = "\n\n".join(all_text)
            
            # LLM prompt hazırla
            prompt = f"""Aşağıdaki SAM.gov ilan dokümanını analiz et ve gereksinimleri çıkar.

NOTICE ID: {notice_id}
TITLE: {metadata.get('title', '')}
AGENCY: {metadata.get('agency', '')}

DOKUMAN ICERIGI:
{combined_text[:10000]}

Görev: Aşağıdaki kategorilerde gereksinimleri çıkar:
1. Room Requirements (oda sayısı, tip, tarihler)
2. Conference Requirements (kapasite, setup, tarihler)
3. AV Requirements (projektör, ekran, ses sistemi)
4. Catering Requirements (yemek, içecek, coffee break)
5. Compliance Requirements (FAR clauses, güvenlik, sertifikasyonlar)
6. Pricing Requirements (ödeme yöntemi, fiyatlandırma yapısı)

JSON formatında yanıt ver:
{{
  "room_requirements": {{}},
  "conference_requirements": {{}},
  "av_requirements": {{}},
  "catering_requirements": {{}},
  "compliance_requirements": {{}},
  "pricing_requirements": {{}},
  "general_requirements": []
}}"""

            # LLM çağrısı (Ollama veya OpenAI)
            requirements_json = self._call_llm(prompt)
            
            if requirements_json:
                try:
                    requirements = json.loads(requirements_json)
                except json.JSONDecodeError:
                    logger.warning("LLM yanıtı JSON parse edilemedi, temel çıkarım kullanılıyor")
                    requirements = self._extract_requirements_basic(metadata, downloaded_files)
            else:
                logger.warning("LLM yanıtı alınamadı, temel çıkarım kullanılıyor")
                requirements = self._extract_requirements_basic(metadata, downloaded_files)
            
        except Exception as e:
            logger.error(f"Gereksinim cikarma hatasi: {e}")
            requirements = self._extract_requirements_basic(metadata, downloaded_files)
        
        return requirements
    
    def _extract_requirements_basic(self, metadata: Dict, downloaded_files: List[str]) -> Dict[str, Any]:
        """Temel gereksinim çıkarımı (LLM olmadan)"""
        requirements = {
            'room_requirements': {},
            'conference_requirements': {},
            'av_requirements': {},
            'catering_requirements': {},
            'compliance_requirements': {},
            'pricing_requirements': {},
            'general_requirements': []
        }
        
        # Metadata'dan temel bilgiler
        title = metadata.get('title', '').lower()
        description = metadata.get('description', '').lower()
        
        # Basit keyword matching
        if 'room' in title or 'lodging' in title or 'accommodation' in title:
            requirements['room_requirements']['required'] = True
        
        if 'conference' in title or 'meeting' in title or 'training' in title:
            requirements['conference_requirements']['required'] = True
        
        requirements['general_requirements'].append({
            'source': 'metadata',
            'text': metadata.get('description', '')
        })
        
        return requirements
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """LLM çağrısı yap (Ollama veya OpenAI)"""
        try:
            use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
            
            if use_ollama:
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model = os.getenv("OLLAMA_MODEL", "llama3.2")
                
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    return response.json().get('response', '')
            else:
                # OpenAI fallback
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM cagrisi hatasi: {e}")
            return None
        
        return None
    
    def analyze_sow(self, notice_id: str, metadata: Dict[str, Any], 
                   requirements: Dict[str, Any], downloaded_files: List[str]) -> Dict[str, Any]:
        """
        ADIM 4: SOW analizi yap
        
        Args:
            notice_id: Notice ID
            metadata: İlan metadata'sı
            requirements: Çıkarılan gereksinimler
            downloaded_files: İndirilen dosyalar
            
        Returns:
            Yapılandırılmış SOW analizi
        """
        sow_data = {
            'period_of_performance': {},
            'room_block': {},
            'function_space': {},
            'av': {},
            'refreshments': {},
            'location': {},
            'pre_con_meeting': {},
            'tax_exemption': True,
            'assumptions': []
        }
        
        try:
            # Requirements'dan SOW yapısını doldur
            if requirements.get('room_requirements'):
                sow_data['room_block'] = requirements['room_requirements']
            
            if requirements.get('conference_requirements'):
                sow_data['function_space'] = {
                    'general_session': requirements['conference_requirements']
                }
            
            if requirements.get('av_requirements'):
                sow_data['av'] = requirements['av_requirements']
            
            if requirements.get('catering_requirements'):
                sow_data['refreshments'] = requirements['catering_requirements']
            
            # Metadata'dan location bilgisi
            description = metadata.get('description', '')
            # Basit location extraction (geliştirilebilir)
            sow_data['location'] = {
                'description': description
            }
            
            # Assumptions ekle
            sow_data['assumptions'].append({
                'source': 'workflow',
                'text': 'Requirements extracted from SAM.gov documents and metadata'
            })
            
        except Exception as e:
            logger.error(f"SOW analizi hatasi: {e}")
        
        return sow_data
    
    def save_analysis(self, notice_id: str, metadata: Dict[str, Any],
                     requirements: Dict[str, Any], sow_analysis: Dict[str, Any],
                     downloaded_files: List[str]) -> Optional[str]:
        """
        ADIM 5: Analiz sonuçlarını veritabanına kaydet
        
        Args:
            notice_id: Notice ID
            metadata: İlan metadata'sı
            requirements: Çıkarılan gereksinimler
            sow_analysis: SOW analizi
            downloaded_files: İndirilen dosyalar
            
        Returns:
            Analysis ID
        """
        try:
            # Source docs hash hesapla
            source_docs = {
                'doc_ids': [Path(f).name for f in downloaded_files],
                'sha256': [self._calculate_file_hash(f) for f in downloaded_files],
                'urls': []
            }
            
            source_hash = self._calculate_source_hash(source_docs)
            
            # SOW payload oluştur
            sow_payload = {
                'metadata': metadata,
                'requirements': requirements,
                'sow_data': sow_analysis,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # SOWAnalysisResult oluştur
            analysis_result = SOWAnalysisResult(
                notice_id=notice_id,
                template_version="v1.0",
                sow_payload=sow_payload,
                source_docs=source_docs,
                source_hash=source_hash
            )
            
            # Veritabanına kaydet
            analysis_id = self.sow_manager.upsert_sow_analysis(analysis_result)
            
            logger.info(f"Analiz kaydedildi: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Veritabani kayit hatasi: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Dosya SHA256 hash hesapla"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "unknown"
    
    def _calculate_source_hash(self, source_docs: Dict[str, Any]) -> str:
        """Source documents combined hash"""
        hashes = source_docs.get('sha256', [])
        concat = "|".join(hashes)
        return hashlib.sha256(concat.encode()).hexdigest()


def main():
    """Test için main fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(description="İlan Analizi Workflow'u")
    parser.add_argument("notice_id", help="SAM.gov Notice ID")
    parser.add_argument("--download-dir", help="Download dizini", default=None)
    parser.add_argument("--no-llm", action="store_true", help="LLM kullanma")
    
    args = parser.parse_args()
    
    # Workflow oluştur
    workflow = OpportunityAnalysisWorkflow(
        download_dir=args.download_dir,
        use_llm=not args.no_llm
    )
    
    # Workflow çalıştır
    result = workflow.run(args.notice_id)
    
    # Sonuçları göster
    print("\n" + "=" * 80)
    print("WORKFLOW SONUÇLARI")
    print("=" * 80)
    print(f"Notice ID: {result.notice_id}")
    print(f"Success: {result.success}")
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Metadata: {'OK' if result.metadata else 'NOK'}")
    print(f"Downloaded Files: {len(result.downloaded_files or [])}")
    print(f"Requirements: {'OK' if result.extracted_requirements else 'NOK'}")
    print(f"SOW Analysis: {'OK' if result.sow_analysis else 'NOK'}")
    
    if result.errors:
        print(f"\nHatalar:")
        for error in result.errors:
            print(f"  - {error}")
    
    # Sonuçları JSON'a kaydet
    output_file = f"analysis_{result.notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2)
    print(f"\nSonuçlar kaydedildi: {output_file}")


if __name__ == "__main__":
    main()

