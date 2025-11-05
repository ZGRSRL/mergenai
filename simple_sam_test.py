#!/usr/bin/env python3
"""
Simple SAM API test with minimal requests
"""

import os
import time
from dotenv import load_dotenv
from sam_api_client import SAMAPIClient

# Load environment variables
load_dotenv()

def simple_test():
    """Simple SAM API test"""
    print("Simple SAM API Test")
    print("=" * 30)
    
    # Get API key
    api_key = os.getenv('SAM_API_KEY')
    print(f"API Key: {api_key[:10]}...")
    
    if not api_key:
        print("[ERROR] No API key found!")
        return False
    
    try:
        # Initialize client with longer rate limiting
        client = SAMAPIClient(public_api_key=api_key, mode="public")
        
        # Override rate limiting for this test
        client.min_request_interval = 5.0  # 5 seconds between requests
        
        print("\n[TEST] Testing API connection...")
        print("Waiting 10 seconds before first request...")
        time.sleep(10)  # Wait before first request
        
        # Test connection
        if client.test_connection():
            print("[SUCCESS] API connection working!")
        else:
            print("[ERROR] API connection failed")
            return False
        
        print("\n[TEST] Testing simple search...")
        print("Waiting 5 seconds before search...")
        time.sleep(5)
        
        # Try a very simple search
        try:
            # Search for any opportunity with minimal parameters
            result = client.search_opportunities(
                posted_from="01/01/2024",
                posted_to="12/31/2024", 
                limit=1
            )
            
            opportunities = result.get('opportunitiesData', [])
            if opportunities:
                opp = opportunities[0]
                print("[SUCCESS] Found opportunity!")
                print(f"  - Title: {opp.get('title', 'N/A')}")
                print(f"  - Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"  - Agency: {opp.get('department', 'N/A')}")
                return True
            else:
                print("[WARNING] No opportunities found")
                return True
                
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return False
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

def main():
    """Main function"""
    print("Waiting 30 seconds before starting test...")
    print("(This helps avoid rate limiting)")
    time.sleep(30)
    
    success = simple_test()
    
    if success:
        print("\n[SUCCESS] SAM API is working!")
    else:
        print("\n[ERROR] SAM API test failed")

if __name__ == "__main__":
    main()













