#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test SAM API with updated header format"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.append('.')

from sam_api_client import SAMAPIClient

def test_opportunity(notice_id: str):
    """Test opportunity fetch with new API key format"""
    # Try new API key first, then fallback to environment
    api_key = "SAM-34a0de14-8d52-4e37-8ac3-f8db8513eaf2"
    if not api_key:
        api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')
    
    if not api_key:
        print("ERROR: SAM_API_KEY not found in environment")
        return
    
    print(f"API Key: {api_key[:20]}...")
    print(f"Testing Notice ID: {notice_id}")
    print("=" * 60)
    
    # Wait a bit to avoid rate limit
    print("Waiting 60 seconds for rate limit to reset...")
    time.sleep(60)
    
    client = SAMAPIClient(public_api_key=api_key, mode='public')
    
    print("Fetching opportunity details...")
    opp = client.get_opportunity_details(notice_id)
    
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    
    if opp:
        print("SUCCESS - Opportunity found!")
        print(f"Title: {opp.get('title', 'N/A')}")
        print(f"Agency: {opp.get('department', 'N/A')}")
        print(f"Posted Date: {opp.get('postedDate', 'N/A')}")
        print(f"NAICS: {opp.get('naicsCode', 'N/A')}")
        print(f"Resource Links: {len(opp.get('resourceLinks', []))}")
        
        resource_links = opp.get('resourceLinks', [])
        if resource_links:
            print("\nResource Links:")
            for i, link in enumerate(resource_links[:5], 1):
                if isinstance(link, dict):
                    print(f"  {i}. {link.get('filename', 'N/A')}: {link.get('url', 'N/A')[:60]}...")
                else:
                    print(f"  {i}. {link[:60]}...")
    else:
        print("FAILED - Opportunity not found or API error")
    
    print("=" * 60)

if __name__ == "__main__":
    notice_id = "a81c7ad026c74b7799b0e28e735aeeb7"
    test_opportunity(notice_id)

