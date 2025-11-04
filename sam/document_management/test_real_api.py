#!/usr/bin/env python3
"""
Test real SAM API call
"""

import requests
import os
from datetime import datetime, timedelta

def test_real_sam_api():
    """Test real SAM API call"""
    print("=== Real SAM API Test ===")
    
    # API key
    api_key = "SAM-0020b32f-de95-4052-9c89-0442d20fcf65"
    
    # Search parameters - try very short range
    posted_from = (datetime.now() - timedelta(days=7)).strftime('%m/%d/%Y')
    posted_to = datetime.now().strftime('%m/%d/%Y')
    
    # Try specific opportunity ID
    params = {
        'api_key': api_key,
        'noticeId': 'ffa04fa070794f8a87095f49af364831',
        'postedFrom': posted_from,
        'postedTo': posted_to,
        'limit': 1
    }
    
    print(f"Posted From: {posted_from}")
    print(f"Posted To: {posted_to}")
    print(f"Notice ID: 70LART26QPFB00001")
    
    try:
        response = requests.get(
            "https://api.sam.gov/opportunities/v2/search",
            params=params,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            print(f"Opportunities found: {len(opportunities)}")
            
            if opportunities:
                opp = opportunities[0]
                print(f"Title: {opp.get('title', 'N/A')}")
                print(f"Resource Links: {opp.get('resourceLinks', [])}")
                print(f"Attachments: {opp.get('attachments', [])}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_real_sam_api()
