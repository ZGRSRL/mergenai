#!/usr/bin/env python3
"""
Search SAM opportunities to find available ones
"""

import os
from dotenv import load_dotenv
from sam_api_client import SAMAPIClient
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def search_opportunities():
    """Search for available opportunities"""
    print("Searching SAM Opportunities")
    print("=" * 40)
    
    # Get API key
    api_key = os.getenv('SAM_API_KEY')
    if not api_key:
        print("[ERROR] No SAM API key found!")
        return
    
    print(f"Using API key: {api_key[:10]}...")
    
    try:
        # Initialize client
        client = SAMAPIClient(public_api_key=api_key, mode="public")
        
        # Test connection
        if not client.test_connection():
            print("[ERROR] API connection failed")
            return
        
        print("[SUCCESS] API connection working!")
        
        # Search for recent opportunities
        print("\n[SEARCH] Looking for recent opportunities...")
        
        # Search last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        search_params = {
            'posted_from': start_date.strftime('%m/%d/%Y'),
            'posted_to': end_date.strftime('%m/%d/%Y'),
            'limit': 10
        }
        
        print(f"Searching from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
        
        # Search opportunities
        result = client.search_opportunities(**search_params)
        opportunities = result.get('opportunitiesData', [])
        
        if not opportunities:
            print("[WARNING] No opportunities found in the last 30 days")
            
            # Try broader search
            print("\n[SEARCH] Trying broader search (last 90 days)...")
            start_date = end_date - timedelta(days=90)
            search_params['posted_from'] = start_date.strftime('%m/%d/%Y')
            
            result = client.search_opportunities(**search_params)
            opportunities = result.get('opportunitiesData', [])
        
        if opportunities:
            print(f"[SUCCESS] Found {len(opportunities)} opportunities!")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"\n{i}. {opp.get('title', 'No Title')}")
                print(f"   Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"   Agency: {opp.get('department', 'N/A')}")
                print(f"   Posted: {opp.get('postedDate', 'N/A')}")
                print(f"   Type: {opp.get('typeOfSetAside', 'N/A')}")
                
                # Check for resource links
                resource_links = opp.get('resourceLinks', [])
                if resource_links:
                    print(f"   Attachments: {len(resource_links)} files")
                    for j, link in enumerate(resource_links[:3], 1):  # Show first 3
                        print(f"     {j}. {link.get('filename', 'Unknown')}")
                else:
                    print("   Attachments: None")
        else:
            print("[WARNING] No opportunities found")
            
            # Try searching for specific keywords
            print("\n[SEARCH] Trying keyword search...")
            keyword_searches = [
                'lodging',
                'hotel',
                'conference',
                'training',
                'FLETC'
            ]
            
            for keyword in keyword_searches:
                print(f"Searching for '{keyword}'...")
                search_params = {
                    'q': keyword,
                    'limit': 5
                }
                
                try:
                    result = client.search_opportunities(**search_params)
                    opps = result.get('opportunitiesData', [])
                    if opps:
                        print(f"  Found {len(opps)} opportunities for '{keyword}'")
                        for opp in opps[:2]:  # Show first 2
                            print(f"    - {opp.get('title', 'No Title')} ({opp.get('noticeId', 'N/A')})")
                    else:
                        print(f"  No opportunities found for '{keyword}'")
                except Exception as e:
                    print(f"  Error searching for '{keyword}': {e}")
        
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    search_opportunities()

if __name__ == "__main__":
    main()









