#!/usr/bin/env python3
"""
Download documents for 70LART26QPFB00001 from cached data
"""

import os
import json
import requests
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Load environment variables
load_dotenv()

def download_70LART_documents():
    """Download documents for 70LART26QPFB00001"""
    print("Downloading 70LART26QPFB00001 Documents")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv('SAM_API_KEY')
    if not api_key:
        print("[ERROR] No SAM API key found!")
        return False
    
    print(f"API Key: {api_key[:10]}...")
    
    # Database connection
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'sam',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'sarlio41'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        print("[SUCCESS] Connected to SAM database")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get opportunity data
            cursor.execute("""
                SELECT 
                    opportunity_id,
                    title,
                    cached_data
                FROM opportunities 
                WHERE opportunity_id = %s
            """, ("70LART26QPFB00001",))
            
            opportunity = cursor.fetchone()
            
            if not opportunity:
                print("[ERROR] Opportunity not found in database")
                return False
            
            print(f"[INFO] Opportunity: {opportunity['title']}")
            
            # Parse cached data
            cached_data = opportunity.get('cached_data')
            if isinstance(cached_data, str):
                cached_data = json.loads(cached_data)
            
            # Get attachments
            attachments = cached_data.get('attachments', [])
            if not attachments:
                print("[WARNING] No attachments found in cached data")
                return False
            
            print(f"[INFO] Found {len(attachments)} attachments")
            
            # Create download directory
            download_dir = "downloads_70LART"
            Path(download_dir).mkdir(exist_ok=True)
            print(f"[INFO] Download directory: {download_dir}")
            
            # Download each attachment
            downloaded_files = []
            for i, attachment in enumerate(attachments, 1):
                filename = attachment.get('filename', f'document_{i}.pdf')
                url = attachment.get('url', '')
                
                if not url:
                    print(f"[WARNING] No URL for attachment {i}")
                    continue
                
                print(f"\n[DOWNLOAD {i}] {filename}")
                print(f"  URL: {url}")
                
                try:
                    # Add API key to URL if needed
                    if 'api_key=' not in url:
                        separator = '&' if '?' in url else '?'
                        url = f"{url}{separator}api_key={api_key}"
                    
                    # Download file
                    response = requests.get(url, stream=True, timeout=120)
                    response.raise_for_status()
                    
                    # Save file
                    file_path = os.path.join(download_dir, filename)
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(file_path)
                    print(f"  [SUCCESS] Downloaded: {file_path} ({file_size} bytes)")
                    downloaded_files.append(file_path)
                    
                except Exception as e:
                    print(f"  [ERROR] Download failed: {e}")
            
            if downloaded_files:
                print(f"\n[SUCCESS] Downloaded {len(downloaded_files)} files!")
                print(f"Download directory: {os.path.abspath(download_dir)}")
                
                # List downloaded files
                for file_path in downloaded_files:
                    file_size = os.path.getsize(file_path)
                    print(f"  - {os.path.basename(file_path)} ({file_size} bytes)")
                
                return True
            else:
                print(f"\n[ERROR] No files were downloaded")
                return False
                
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

def test_downloaded_documents():
    """Test if downloaded documents are readable"""
    print(f"\n[TEST] Testing downloaded documents...")
    
    download_dir = "downloads_70LART"
    if not os.path.exists(download_dir):
        print("[WARNING] Download directory not found")
        return
    
    files = list(Path(download_dir).glob("*.pdf"))
    if not files:
        print("[WARNING] No PDF files found in download directory")
        return
    
    print(f"[INFO] Found {len(files)} PDF files")
    
    for file_path in files:
        file_size = os.path.getsize(file_path)
        print(f"  - {file_path.name}: {file_size} bytes")
        
        # Try to read first few bytes to check if it's a valid PDF
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    print(f"    [SUCCESS] Valid PDF file")
                else:
                    print(f"    [WARNING] Not a valid PDF file")
        except Exception as e:
            print(f"    [ERROR] Could not read file: {e}")

def main():
    """Main function"""
    success = download_70LART_documents()
    
    if success:
        test_downloaded_documents()
        print(f"\n[SUCCESS] Document download completed!")
    else:
        print(f"\n[ERROR] Document download failed!")

if __name__ == "__main__":
    main()













