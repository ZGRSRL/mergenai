#!/usr/bin/env python3
"""
Download documents for new opportunity 31c170b76f4d477ca23b83ba6074a6f3
"""

import os
import time
import requests
from dotenv import load_dotenv
from sam_api_client_safe import SamClientSafe
from pathlib import Path

# Load environment variables
load_dotenv()

def download_new_opportunity_documents():
    """Download documents for the new opportunity"""
    print("Downloading Documents for 31c170b76f4d477ca23b83ba6074a6f3")
    print("=" * 60)
    
    notice_id = "31c170b76f4d477ca23b83ba6074a6f3"
    
    # Get API key
    api_key = os.getenv('SAM_API_KEY')
    if not api_key:
        print("[ERROR] No SAM API key found!")
        return False
    
    try:
        # Get opportunity details
        client = SamClientSafe()
        opportunity = client.get_opportunity(notice_id)
        
        if not opportunity:
            print("[ERROR] Opportunity not found!")
            return False
        
        print(f"[SUCCESS] Found opportunity: {opportunity.get('title', 'N/A')}")
        
        # Get resource links
        resource_links = opportunity.get('resourceLinks', [])
        if not resource_links:
            print("[ERROR] No resource links found!")
            return False
        
        print(f"[INFO] Found {len(resource_links)} resource links")
        
        # Create download directory
        download_dir = Path("downloads") / notice_id
        download_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Download directory: {download_dir}")
        
        # Download each document
        downloaded_files = []
        for i, url in enumerate(resource_links, 1):
            print(f"\n[DOWNLOAD {i}] {url}")
            
            try:
                # Add API key to URL if needed
                if 'api_key=' not in url:
                    separator = '&' if '?' in url else '?'
                    url_with_key = f"{url}{separator}api_key={api_key}"
                else:
                    url_with_key = url
                
                # Download file
                print(f"  Downloading from: {url_with_key}")
                response = requests.get(url_with_key, stream=True, timeout=120)
                response.raise_for_status()
                
                # Generate filename
                filename = f"document_{i}.pdf"
                
                # Try to get filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    import re
                    match = re.search(r'filename="?([^"]+)"?', content_disposition)
                    if match:
                        filename = match.group(1)
                
                # Save file
                file_path = download_dir / filename
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = os.path.getsize(file_path)
                print(f"  [SUCCESS] Downloaded: {file_path} ({file_size} bytes)")
                
                # Validate PDF
                with open(file_path, 'rb') as f:
                    header = f.read(5)
                    if header == b'%PDF-':
                        print(f"  [SUCCESS] Valid PDF file")
                    else:
                        print(f"  [WARNING] Not a valid PDF file")
                
                downloaded_files.append(file_path)
                
                # Wait between downloads
                if i < len(resource_links):
                    print("  Waiting 2 seconds...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"  [ERROR] Download failed: {e}")
                continue
        
        if downloaded_files:
            print(f"\n[SUCCESS] Downloaded {len(downloaded_files)} files successfully!")
            print(f"Files saved to: {download_dir.absolute()}")
            
            # List downloaded files
            for file_path in downloaded_files:
                file_size = os.path.getsize(file_path)
                print(f"  - {file_path.name} ({file_size} bytes)")
            
            return True
        else:
            print(f"\n[ERROR] No files were downloaded")
            return False
            
    except Exception as e:
        print(f"[ERROR] Download process failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = download_new_opportunity_documents()
    
    if success:
        print(f"\n[SUCCESS] Document download completed!")
    else:
        print(f"\n[ERROR] Document download failed!")

if __name__ == "__main__":
    main()









