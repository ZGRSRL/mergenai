#!/usr/bin/env python3
"""
Get real documents for 70LART26QPFB00001 from SAM API
"""

import os
import requests
import time
from dotenv import load_dotenv
from sam_api_client_safe import SamClientSafe

# Load environment variables
load_dotenv()

def get_real_documents():
    """Get real documents from SAM API"""
    print("Getting Real Documents for 70LART26QPFB00001")
    print("=" * 50)
    
    try:
        # Initialize safe SAM client
        client = SamClientSafe()
        print("[SUCCESS] SAM client initialized")
        
        # Try to get opportunity with archived status
        print(f"\n[SEARCH] Searching for archived opportunity...")
        
        # Search with archived status and proper date range
        search_params = {
            "noticeid": "70LART26QPFB00001",
            "postedFrom": "10/01/2024",
            "postedTo": "11/30/2024",
            "status": "archived",
            "limit": "1"
        }
        
        try:
            data = client.search(**search_params)
            opportunities = data.get("opportunitiesData", [])
            
            if opportunities:
                opp = opportunities[0]
                print("[SUCCESS] Found archived opportunity!")
                print(f"  - Title: {opp.get('title', 'N/A')}")
                print(f"  - Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"  - Status: {opp.get('status', 'N/A')}")
                
                # Get resource links
                resource_links = opp.get('resourceLinks', [])
                if resource_links:
                    print(f"\n[SUCCESS] Found {len(resource_links)} resource links!")
                    
                    # Create download directory
                    download_dir = "downloads_70LART_real"
                    os.makedirs(download_dir, exist_ok=True)
                    print(f"Download directory: {download_dir}")
                    
                    # Download each document
                    downloaded_files = []
                    for i, link in enumerate(resource_links, 1):
                        filename = link.get('filename', f'document_{i}.pdf')
                        url = link.get('url', '')
                        
                        if not url:
                            print(f"[WARNING] No URL for link {i}")
                            continue
                        
                        print(f"\n[DOWNLOAD {i}] {filename}")
                        print(f"  URL: {url}")
                        
                        try:
                            # Add API key to URL if needed
                            if 'api_key=' not in url:
                                separator = '&' if '?' in url else '?'
                                url = f"{url}{separator}api_key={client.key}"
                            
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
                        print(f"\n[SUCCESS] Downloaded {len(downloaded_files)} real documents!")
                        return True
                    else:
                        print(f"\n[ERROR] No documents were downloaded")
                        return False
                else:
                    print("[WARNING] No resource links found")
                    return False
            else:
                print("[WARNING] No archived opportunity found")
                return False
                
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Client initialization failed: {e}")
        return False

def search_recent_hotel_opportunities():
    """Search for recent hotel opportunities with documents"""
    print(f"\n[SEARCH] Looking for recent hotel opportunities with documents...")
    
    try:
        client = SamClientSafe()
        
        # Search recent hotel opportunities
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        search_params = {
            "naics": "721110",  # Hotels
            "postedFrom": start_date.strftime("%m/%d/%Y"),
            "postedTo": end_date.strftime("%m/%d/%Y"),
            "limit": "5"
        }
        
        print(f"Searching from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
        
        data = client.search(**search_params)
        opportunities = data.get("opportunitiesData", [])
        
        if opportunities:
            print(f"[SUCCESS] Found {len(opportunities)} hotel opportunities!")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"\n{i}. {opp.get('title', 'No Title')}")
                print(f"   Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"   Agency: {opp.get('department', 'N/A')}")
                print(f"   Posted: {opp.get('postedDate', 'N/A')}")
                
                # Check for resource links
                resource_links = opp.get('resourceLinks', [])
                if resource_links:
                    print(f"   Documents: {len(resource_links)} files")
                    for j, link in enumerate(resource_links[:2], 1):  # Show first 2
                        print(f"     {j}. {link.get('filename', 'Unknown')}")
                else:
                    print("   Documents: None")
        else:
            print("[WARNING] No hotel opportunities found")
            
    except Exception as e:
        print(f"[ERROR] Hotel search failed: {e}")

def main():
    """Main function"""
    print("SAM API Document Download Test")
    print("=" * 60)
    
    # Try to get real documents for 70LART26QPFB00001
    success = get_real_documents()
    
    if not success:
        print(f"\n[INFO] 70LART26QPFB00001 documents not available via API")
        print("This is expected since the opportunity is archived")
    
    # Search for recent hotel opportunities with documents
    search_recent_hotel_opportunities()
    
    print(f"\n[COMPLETE] Document search completed!")

if __name__ == "__main__":
    main()









