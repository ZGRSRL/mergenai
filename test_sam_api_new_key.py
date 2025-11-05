#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test SAM API with new key"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('.')

from sam_api_client import SAMAPIClient
from datetime import datetime

notice_id = "a81c7ad026c74b7799b0e28e735aeeb7"

api_key = os.getenv('SAM_API_KEY') or os.getenv('SAM_PUBLIC_API_KEY')

print("=" * 60)
print("SAM API TEST - Yeni API Key")
print("=" * 60)

if not api_key:
    print("ERROR: SAM_API_KEY bulunamadi")
    sys.exit(1)

print(f"API Key: {api_key[:15]}...")
print(f"API Key Length: {len(api_key)}")
print()

try:
    # Test 1: API Client Olusturma
    print("[TEST 1] SAM API Client olusturuluyor...")
    sam_client = SAMAPIClient(public_api_key=api_key, mode="public")
    print("SUCCESS - Client olusturuldu")
    print()
    
    # Test 2: Basit Arama (Connection Test)
    print("[TEST 2] Basit arama testi (connection)...")
    today = datetime.now()
    posted_from = (today.replace(day=1)).strftime('%m/%d/%Y')  # Ayin ilk gunu
    posted_to = today.strftime('%m/%d/%Y')
    
    try:
        result = sam_client.search_opportunities(
            posted_from=posted_from,
            posted_to=posted_to,
            limit=5
        )
        opportunities = result.get('opportunitiesData', [])
        print(f"SUCCESS - {len(opportunities)} ilan bulundu")
        if opportunities:
            print(f"   Ornek: {opportunities[0].get('title', 'N/A')[:50]}...")
    except Exception as e:
        print(f"ERROR - Arama basarisiz: {e}")
        print(f"   Error Type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:200]}")
    print()
    
    # Test 3: Specific Notice ID Arama
    print(f"[TEST 3] Specific Notice ID arama: {notice_id}")
    try:
        opportunity = sam_client.get_opportunity_details(notice_id)
        if opportunity:
            print(f"SUCCESS - Ilan bulundu:")
            print(f"   Title: {opportunity.get('title', 'N/A')}")
            print(f"   Agency: {opportunity.get('department', 'N/A')}")
            print(f"   Posted Date: {opportunity.get('postedDate', 'N/A')}")
            print(f"   NAICS: {opportunity.get('naicsCode', 'N/A')}")
            print(f"   Solicitation: {opportunity.get('solicitationNumber', 'N/A')}")
            
            # Resource links
            resource_links = opportunity.get('resourceLinks', [])
            print(f"   Resource Links: {len(resource_links)} adet")
            if resource_links:
                for i, link in enumerate(resource_links[:3], 1):
                    print(f"      {i}. {link.get('filename', 'N/A')}")
        else:
            print("ERROR - Ilan bulunamadi")
    except Exception as e:
        print(f"ERROR - Notice ID arama basarisiz: {e}")
        print(f"   Error Type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:200]}")
    print()
    
    # Test 4: Resource Links Test
    print(f"[TEST 4] Resource Links testi...")
    try:
        resource_links = sam_client.get_resource_links(notice_id)
        if resource_links:
            print(f"SUCCESS - {len(resource_links)} resource link bulundu")
            for i, link in enumerate(resource_links[:3], 1):
                print(f"   {i}. {link.get('filename', 'N/A')} - {link.get('url', 'N/A')[:50]}...")
        else:
            print("WARNING - Resource links bulunamadi")
    except Exception as e:
        print(f"ERROR - Resource links basarisiz: {e}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()

