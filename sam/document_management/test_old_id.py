#!/usr/bin/env python3
"""
Test old opportunity ID with real SAM API
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def test_old_id():
    """Test old opportunity ID with real SAM API"""
    print("=== Testing Old ID: 70LART26QPFB00001 ===")
    
    api_key = os.getenv('SAM_API_KEY')
    print(f'API Key: {api_key[:20] if api_key else "None"}...')
    
    # Try different date ranges
    date_ranges = [
        (7, "Last 7 days"),
        (30, "Last 30 days"),
        (90, "Last 90 days"),
        (365, "Last 365 days")
    ]
    
    for days, description in date_ranges:
        print(f"\n--- Testing {description} ---")
        
        posted_from = (datetime.now() - timedelta(days=days)).strftime('%m/%d/%Y')
        posted_to = datetime.now().strftime('%m/%d/%Y')
        
        params = {
            'api_key': api_key,
            'noticeId': '70LART26QPFB00001',
            'postedFrom': posted_from,
            'postedTo': posted_to,
            'limit': 1
        }
        
        try:
            response = requests.get(
                "https://api.sam.gov/opportunities/v2/search",
                params=params,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunitiesData', [])
                print(f"Opportunities found: {len(opportunities)}")
                
                if opportunities:
                    opp = opportunities[0]
                    print(f"SUCCESS: Found opportunity!")
                    print(f"Title: {opp.get('title', 'N/A')}")
                    print(f"Notice ID: {opp.get('noticeId', 'N/A')}")
                    print(f"Posted Date: {opp.get('postedDate', 'N/A')}")
                    print(f"Resource Links: {len(opp.get('resourceLinks', []))}")
                    print(f"Attachments: {len(opp.get('attachments', []))}")
                    
                    # Show resource links
                    resource_links = opp.get('resourceLinks', [])
                    if resource_links:
                        print("Resource Links:")
                        for i, link in enumerate(resource_links[:3]):  # Show first 3
                            print(f"  {i+1}. {link}")
                    
                    return True
                else:
                    print("No opportunities found in this date range")
            else:
                print(f"Error: {response.status_code} - {response.text[:200]}...")
                
        except Exception as e:
            print(f"Exception: {str(e)}")
    
    print("\n❌ Old ID not found in any date range")
    return False

if __name__ == "__main__":
    test_old_id()
