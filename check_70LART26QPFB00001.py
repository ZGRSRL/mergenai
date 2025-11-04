#!/usr/bin/env python3
"""
Check if opportunity 70LART26QPFB00001 exists in database
"""

import sys
import os
sys.path.append('./sam/document_management')

from database_manager import DatabaseUtils

def check_opportunity():
    """Check if opportunity exists in database"""
    opportunity_id = "70LART26QPFB00001"
    
    print(f"Checking opportunity: {opportunity_id}")
    print("=" * 50)
    
    # Check if opportunity exists
    opportunity = DatabaseUtils.get_opportunity_by_id(opportunity_id)
    
    if opportunity:
        print(f"[FOUND] Opportunity found in database!")
        print(f"[ID] Database ID: {opportunity.get('id')}")
        print(f"[TITLE] Title: {opportunity.get('title', 'N/A')}")
        print(f"[DESCRIPTION] Description: {opportunity.get('description', 'N/A')[:200]}...")
        print(f"[POSTED] Posted Date: {opportunity.get('posted_date')}")
        print(f"[NAICS] NAICS Code: {opportunity.get('naics_code')}")
        print(f"[CONTRACT] Contract Type: {opportunity.get('contract_type')}")
        print(f"[ORG] Organization: {opportunity.get('organization_type')}")
        
        # Check cached data
        cached_data = DatabaseUtils.get_cached_opportunity_data(opportunity_id)
        if cached_data:
            print(f"[CACHE] Cached data available")
        else:
            print(f"[CACHE] No cached data")
            
        # Check cache validity
        is_valid = DatabaseUtils.is_cache_valid(opportunity_id)
        print(f"[CACHE_VALID] Cache valid: {is_valid}")
        
    else:
        print(f"[NOT_FOUND] Opportunity not found in database")
        
        # Let's check what opportunities we do have
        print("\nChecking available opportunities...")
        try:
            from database_manager import execute_query
            result = execute_query("SELECT opportunity_id, title FROM opportunities LIMIT 10", fetch='all')
            if result:
                print(f"[AVAILABLE] Found {len(result)} opportunities in database:")
                for i, opp in enumerate(result, 1):
                    print(f"  {i}. {opp['opportunity_id']} - {opp['title'][:50]}...")
            else:
                print("[AVAILABLE] No opportunities found in database")
        except Exception as e:
            print(f"[ERROR] Error checking available opportunities: {e}")

if __name__ == "__main__":
    check_opportunity()
