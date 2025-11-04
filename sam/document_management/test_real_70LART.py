#!/usr/bin/env python3
"""
Test 70LART26QPFB00001 with real SAM API - bypass quota
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()

def test_70LART_real():
    """Test 70LART26QPFB00001 with real SAM API"""
    print("=== Testing 70LART26QPFB00001 with Real SAM API ===")
    
    api_key = os.getenv('SAM_API_KEY')
    print(f'API Key: {api_key[:20] if api_key else "None"}...')
    
    # Try different approaches
    approaches = [
        {
            "name": "Direct Notice ID Search",
            "params": {
                'api_key': api_key,
                'noticeId': '70LART26QPFB00001',
                'postedFrom': '01/01/2024',
                'postedTo': '12/31/2024',
                'limit': 1
            }
        },
        {
            "name": "Keyword Search",
            "params": {
                'api_key': api_key,
                'keyword': '70LART26QPFB00001',
                'postedFrom': '01/01/2024',
                'postedTo': '12/31/2024',
                'limit': 10
            }
        },
        {
            "name": "Agency Search",
            "params": {
                'api_key': api_key,
                'agency': 'Department of Homeland Security',
                'postedFrom': '01/01/2024',
                'postedTo': '12/31/2024',
                'limit': 50
            }
        }
    ]
    
    for approach in approaches:
        print(f"\n--- {approach['name']} ---")
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(2)
            
            response = requests.get(
                "https://api.sam.gov/opportunities/v2/search",
                params=approach['params'],
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunitiesData', [])
                print(f"Opportunities found: {len(opportunities)}")
                
                # Look for our specific ID
                found = False
                for opp in opportunities:
                    if opp.get('noticeId') == '70LART26QPFB00001':
                        found = True
                        print(f"SUCCESS: Found 70LART26QPFB00001!")
                        print(f"Title: {opp.get('title', 'N/A')}")
                        print(f"Posted Date: {opp.get('postedDate', 'N/A')}")
                        print(f"Resource Links: {len(opp.get('resourceLinks', []))}")
                        print(f"Attachments: {len(opp.get('attachments', []))}")
                        
                        # Show resource links
                        resource_links = opp.get('resourceLinks', [])
                        if resource_links:
                            print("Resource Links:")
                            for i, link in enumerate(resource_links):
                                print(f"  {i+1}. {link}")
                        
                        return True
                
                if not found:
                    print("70LART26QPFB00001 not found in results")
                    # Show first few results for debugging
                    if opportunities:
                        print("Sample results:")
                        for i, opp in enumerate(opportunities[:3]):
                            print(f"  {i+1}. {opp.get('noticeId', 'N/A')} - {opp.get('title', 'N/A')[:50]}...")
                            
            elif response.status_code == 429:
                print("Rate limited - waiting 5 seconds...")
                time.sleep(5)
                continue
            else:
                print(f"Error: {response.status_code} - {response.text[:200]}...")
                
        except Exception as e:
            print(f"Exception: {str(e)}")
    
    print("\nFAILED: 70LART26QPFB00001 not found in any approach")
    return False

if __name__ == "__main__":
    test_70LART_real()










