#!/usr/bin/env python3
"""
Test attachment download
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_download():
    """Test if we can download attachments"""
    print("=== Attachment Download Test ===")
    
    # Test URLs from real opportunity
    urls = [
        'https://sam.gov/api/prod/opps/v3/opportunities/resources/files/0a26abbce72748819d55f345d2c972a2/download',
        'https://sam.gov/api/prod/opps/v3/opportunities/resources/files/45b74b073f7d4a33a126731b0c626d79/download'
    ]
    
    api_key = os.getenv('SAM_API_KEY')
    print(f'API Key: {api_key[:20] if api_key else "None"}...')
    
    for i, url in enumerate(urls):
        try:
            print(f"\nTesting URL {i+1}:")
            print(f"URL: {url}")
            
            response = requests.get(url, params={'api_key': api_key}, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
                print("SUCCESS: Download successful!")
            else:
                print(f"Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_download()
