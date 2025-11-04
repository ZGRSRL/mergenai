#!/usr/bin/env python3
"""
Enhanced Attachment Downloader with detailed logging and error handling
"""

import requests
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class EnhancedAttachmentDownloader:
    """Enhanced attachment downloader with detailed error reporting"""
    
    def __init__(self, download_dir: str = "attachments"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def download_attachment(self, attachment_id: str, url: str, filename: str) -> Dict[str, Any]:
        """
        Download attachment with detailed error reporting
        
        Returns:
            Dict with status, error details, and metadata
        """
        result = {
            "attachment_id": attachment_id,
            "url": url,
            "filename": filename,
            "status": "unknown",
            "error_msg": None,
            "metadata": {},
            "is_secure": False,
            "download_path": None
        }
        
        try:
            logger.info(f"Downloading attachment {attachment_id}: {url}")
            
            # Make request with detailed headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=60, 
                allow_redirects=True,
                stream=True
            )
            
            # Capture metadata
            metadata = {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "content_length": response.headers.get("content-length", ""),
                "server": response.headers.get("server", ""),
                "final_url": response.url,
                "redirect_count": len(response.history)
            }
            
            result["metadata"] = metadata
            logger.info(f"Response metadata for {attachment_id}: {metadata}")
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                
                if "pdf" in content_type or "application/octet-stream" in content_type:
                    # Save file
                    file_path = self.download_dir / f"{attachment_id}_{filename}"
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    result["status"] = "DOWNLOADED"
                    result["download_path"] = str(file_path)
                    result["file_size"] = file_path.stat().st_size
                    
                    logger.info(f"Successfully downloaded {attachment_id} to {file_path}")
                    
                else:
                    result["status"] = "UNSUPPORTED_TYPE"
                    result["error_msg"] = f"Unsupported content type: {content_type}"
                    logger.warning(f"Unsupported content type for {attachment_id}: {content_type}")
                    
            elif response.status_code in (401, 403):
                result["status"] = "NEEDS_SYSTEM_ACCOUNT"
                result["is_secure"] = True
                result["error_msg"] = f"Authentication required: {metadata}"
                logger.warning(f"Secure attachment {attachment_id}: {metadata}")
                
            elif response.status_code == 404:
                result["status"] = "NOT_FOUND"
                result["error_msg"] = f"Attachment not found: {metadata}"
                logger.warning(f"Attachment not found {attachment_id}: {metadata}")
                
            elif response.status_code >= 500:
                result["status"] = "SERVER_ERROR"
                result["error_msg"] = f"Server error: {metadata}"
                logger.error(f"Server error for {attachment_id}: {metadata}")
                
            else:
                result["status"] = "FAILED"
                result["error_msg"] = f"Unexpected status: {metadata}"
                logger.error(f"Unexpected status for {attachment_id}: {metadata}")
                
        except requests.exceptions.Timeout:
            result["status"] = "TIMEOUT"
            result["error_msg"] = "Request timeout after 60 seconds"
            logger.error(f"Timeout downloading {attachment_id}")
            
        except requests.exceptions.ConnectionError as e:
            result["status"] = "CONNECTION_ERROR"
            result["error_msg"] = f"Connection error: {str(e)}"
            logger.error(f"Connection error for {attachment_id}: {e}")
            
        except Exception as e:
            result["status"] = "UNKNOWN_ERROR"
            result["error_msg"] = f"Unknown error: {str(e)}"
            logger.error(f"Unknown error downloading {attachment_id}: {e}")
        
        return result
    
    def test_attachment_urls(self, urls: list) -> Dict[str, Any]:
        """Test multiple attachment URLs and return summary"""
        results = []
        
        for i, url in enumerate(urls):
            attachment_id = f"test_{i+1}"
            filename = f"test_{i+1}.pdf"
            
            result = self.download_attachment(attachment_id, url, filename)
            results.append(result)
        
        # Summary
        summary = {
            "total": len(results),
            "downloaded": len([r for r in results if r["status"] == "DOWNLOADED"]),
            "needs_auth": len([r for r in results if r["status"] == "NEEDS_SYSTEM_ACCOUNT"]),
            "not_found": len([r for r in results if r["status"] == "NOT_FOUND"]),
            "server_error": len([r for r in results if r["status"] == "SERVER_ERROR"]),
            "failed": len([r for r in results if r["status"] in ["FAILED", "UNKNOWN_ERROR", "TIMEOUT", "CONNECTION_ERROR"]]),
            "results": results
        }
        
        return summary

def test_mock_attachments():
    """Test the mock attachment URLs"""
    downloader = EnhancedAttachmentDownloader()
    
    # Mock URLs from our data
    mock_urls = [
        "https://sam.gov/api/prod/attachments/12345",
        "https://sam.gov/api/prod/attachments/12346"
    ]
    
    print("Testing mock attachment URLs...")
    print("=" * 50)
    
    summary = downloader.test_attachment_urls(mock_urls)
    
    print(f"Total URLs tested: {summary['total']}")
    print(f"Downloaded: {summary['downloaded']}")
    print(f"Needs Authentication: {summary['needs_auth']}")
    print(f"Not Found: {summary['not_found']}")
    print(f"Server Error: {summary['server_error']}")
    print(f"Failed: {summary['failed']}")
    print()
    
    for result in summary['results']:
        print(f"Attachment {result['attachment_id']}:")
        print(f"  Status: {result['status']}")
        print(f"  Error: {result['error_msg']}")
        print(f"  Content-Type: {result['metadata'].get('content_type', 'N/A')}")
        print(f"  Status Code: {result['metadata'].get('status_code', 'N/A')}")
        print()

if __name__ == "__main__":
    test_mock_attachments()
