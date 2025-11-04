#!/usr/bin/env python3
"""
SAM.gov API Client
Handles both Public API and System Account API with automatic fallback
"""

import os
import requests
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import time
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class SAMAPIClient:
    """SAM.gov API client with public/system account support"""
    
    def __init__(self, public_api_key: str = None, system_api_key: str = None, 
                 mode: str = "public", base_url: str = "https://api.sam.gov"):
        """
        Initialize SAM API client
        
        Args:
            public_api_key: Public API key for general access
            system_api_key: System account API key for FOUO/Sensitive content
            mode: "public", "system", or "auto" (auto-fallback)
            base_url: Base URL for SAM API
        """
        self.public_api_key = public_api_key or os.getenv('SAM_PUBLIC_API_KEY')
        self.system_api_key = system_api_key or os.getenv('SAM_SYSTEM_API_KEY')
        self.mode = mode
        self.base_url = base_url.rstrip('/')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests
        
        # Cache for downloaded documents
        self.download_cache = {}
        
        logger.info(f"SAM API Client initialized - Mode: {mode}")
    
    def _wait_for_rate_limit(self):
        """Ensure rate limiting compliance"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_api_key(self, force_system: bool = False) -> Optional[str]:
        """Get appropriate API key based on mode and requirements"""
        if force_system or self.mode == "system":
            return self.system_api_key
        elif self.mode == "public":
            return self.public_api_key
        elif self.mode == "auto":
            # Try public first, fallback to system if needed
            return self.public_api_key or self.system_api_key
        else:
            return self.public_api_key
    
    def _make_request(self, endpoint: str, params: Dict[str, Any], 
                     force_system: bool = False, timeout: int = 60) -> requests.Response:
        """Make API request with appropriate authentication"""
        self._wait_for_rate_limit()
        
        url = urljoin(self.base_url, endpoint)
        api_key = self._get_api_key(force_system)
        
        if api_key:
            params['api_key'] = api_key
        
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403] and not force_system and self.system_api_key:
                # Try with system account
                logger.info("Public API failed, trying system account...")
                return self._make_request(endpoint, params, force_system=True, timeout=timeout)
            else:
                raise
    
    def search_opportunities(self, notice_id: str = None, 
                           posted_from: str = None, posted_to: str = None,
                           limit: int = 100, **kwargs) -> Dict[str, Any]:
        """
        Search for opportunities using SAM API
        
        Args:
            notice_id: Specific notice ID to search for
            posted_from: Start date (MM/DD/YYYY format)
            posted_to: End date (MM/DD/YYYY format)
            limit: Maximum number of results
            **kwargs: Additional search parameters
        
        Returns:
            API response data
        """
        try:
            # Set default date range if not provided
            if not posted_from:
                posted_from = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
            if not posted_to:
                posted_to = datetime.now().strftime('%m/%d/%Y')
            
            params = {
                'postedFrom': posted_from,
                'postedTo': posted_to,
                'limit': limit,
                **kwargs
            }
            
            if notice_id:
                params['noticeid'] = notice_id
            
            logger.info(f"Searching opportunities: {params}")
            
            response = self._make_request('/opportunities/v2/search', params)
            data = response.json()
            
            logger.info(f"Found {len(data.get('opportunitiesData', []))} opportunities")
            return data
            
        except Exception as e:
            logger.error(f"Error searching opportunities: {e}")
            raise
    
    def get_opportunity_details(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific opportunity
        
        Args:
            notice_id: Notice ID to get details for
        
        Returns:
            Opportunity details or None if not found
        """
        try:
            data = self.search_opportunities(notice_id=notice_id, limit=1)
            opportunities = data.get('opportunitiesData', [])
            
            if opportunities:
                return opportunities[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting opportunity details for {notice_id}: {e}")
            return None
    
    def get_resource_links(self, notice_id: str) -> List[Dict[str, str]]:
        """
        Get resource links (attachments) for an opportunity
        
        Args:
            notice_id: Notice ID to get attachments for
        
        Returns:
            List of resource link dictionaries
        """
        try:
            opportunity = self.get_opportunity_details(notice_id)
            if not opportunity:
                return []
            
            resource_links = opportunity.get('resourceLinks', [])
            logger.info(f"Found {len(resource_links)} resource links for {notice_id}")
            
            return resource_links
            
        except Exception as e:
            logger.error(f"Error getting resource links for {notice_id}: {e}")
            return []
    
    def download_attachment(self, url: str, filename: str = None, 
                          download_dir: str = "downloads") -> Optional[str]:
        """
        Download an attachment from SAM.gov
        
        Args:
            url: Download URL
            filename: Local filename (auto-generated if None)
            download_dir: Directory to save file
        
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Check cache first
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.download_cache:
                cached_path = self.download_cache[url_hash]
                if os.path.exists(cached_path):
                    logger.info(f"Using cached file: {cached_path}")
                    return cached_path
            
            # Ensure download directory exists
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = f"attachment_{url_hash[:8]}.pdf"
            
            file_path = os.path.join(download_dir, filename)
            
            # Add API key to URL if needed
            download_url = self._prepare_download_url(url)
            
            logger.info(f"Downloading: {download_url}")
            
            # Download file
            response = requests.get(download_url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Cache the download
            self.download_cache[url_hash] = file_path
            
            logger.info(f"Downloaded: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading attachment from {url}: {e}")
            return None
    
    def _prepare_download_url(self, url: str) -> str:
        """Prepare download URL with API key if needed"""
        # Check if URL already has API key
        if 'api_key=' in url:
            return url
        
        # Add API key as query parameter
        api_key = self._get_api_key()
        if api_key:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}api_key={api_key}"
        
        return url
    
    def download_all_attachments(self, notice_id: str, 
                               download_dir: str = "downloads") -> List[str]:
        """
        Download all attachments for an opportunity
        
        Args:
            notice_id: Notice ID to download attachments for
            download_dir: Directory to save files
        
        Returns:
            List of downloaded file paths
        """
        try:
            resource_links = self.get_resource_links(notice_id)
            if not resource_links:
                logger.info(f"No attachments found for {notice_id}")
                return []
            
            downloaded_files = []
            
            for i, link in enumerate(resource_links, 1):
                url = link.get('url', '')
                if not url:
                    continue
                
                # Generate filename
                filename = link.get('filename', f"attachment_{i}.pdf")
                if not filename:
                    filename = f"attachment_{i}.pdf"
                
                # Download file
                file_path = self.download_attachment(url, filename, download_dir)
                if file_path:
                    downloaded_files.append(file_path)
                    logger.info(f"Downloaded attachment {i}/{len(resource_links)}: {file_path}")
                else:
                    logger.warning(f"Failed to download attachment {i}: {url}")
            
            logger.info(f"Downloaded {len(downloaded_files)} attachments for {notice_id}")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading attachments for {notice_id}: {e}")
            return []
    
    def get_opportunity_with_attachments(self, notice_id: str, 
                                       download_dir: str = "downloads") -> Dict[str, Any]:
        """
        Get opportunity details and download all attachments
        
        Args:
            notice_id: Notice ID to process
            download_dir: Directory to save attachments
        
        Returns:
            Dictionary with opportunity details and downloaded file paths
        """
        try:
            # Get opportunity details
            opportunity = self.get_opportunity_details(notice_id)
            if not opportunity:
                return {'error': 'Opportunity not found'}
            
            # Download attachments
            downloaded_files = self.download_all_attachments(notice_id, download_dir)
            
            return {
                'opportunity': opportunity,
                'downloaded_files': downloaded_files,
                'download_count': len(downloaded_files)
            }
            
        except Exception as e:
            logger.error(f"Error processing opportunity {notice_id}: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try a simple search
            data = self.search_opportunities(limit=1)
            return 'opportunitiesData' in data
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

def test_sam_api_client():
    """Test SAM API client functionality"""
    print("Testing SAM API Client...")
    print("=" * 50)
    
    # Initialize client
    client = SAMAPIClient(mode="auto")
    
    # Test connection
    print("[TEST] Testing API connection...")
    if client.test_connection():
        print("[SUCCESS] API connection working")
    else:
        print("[ERROR] API connection failed")
        return
    
    # Test specific opportunity
    notice_id = "70LART26QPFB00001"
    print(f"\n[TEST] Testing opportunity: {notice_id}")
    
    # Get opportunity details
    opportunity = client.get_opportunity_details(notice_id)
    if opportunity:
        print("[SUCCESS] Opportunity details retrieved")
        print(f"  - Title: {opportunity.get('title', 'N/A')}")
        print(f"  - Agency: {opportunity.get('department', 'N/A')}")
        print(f"  - Posted Date: {opportunity.get('postedDate', 'N/A')}")
    else:
        print("[WARNING] Opportunity not found")
    
    # Get resource links
    resource_links = client.get_resource_links(notice_id)
    print(f"\n[TEST] Resource links: {len(resource_links)} found")
    
    for i, link in enumerate(resource_links, 1):
        print(f"  {i}. {link.get('filename', 'Unknown')} - {link.get('url', 'No URL')}")
    
    # Test download (if links exist)
    if resource_links:
        print(f"\n[TEST] Testing download...")
        downloaded_files = client.download_all_attachments(notice_id, "test_downloads")
        print(f"[SUCCESS] Downloaded {len(downloaded_files)} files")
        
        for file_path in downloaded_files:
            print(f"  - {file_path}")
    else:
        print("[INFO] No attachments to download")
    
    print(f"\n[COMPLETE] SAM API Client test completed!")

if __name__ == "__main__":
    test_sam_api_client()
