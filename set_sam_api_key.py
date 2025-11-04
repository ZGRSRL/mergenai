#!/usr/bin/env python3
"""
Set SAM API Key environment variable
"""

import os
import sys

def set_sam_api_key():
    """Set SAM API key environment variable"""
    print("SAM API Key Setup")
    print("=" * 30)
    
    # Check current variables
    current_public = os.getenv('SAM_PUBLIC_API_KEY')
    current_sam = os.getenv('SAM_API_KEY')
    
    print(f"Current SAM_PUBLIC_API_KEY: {current_public}")
    print(f"Current SAM_API_KEY: {current_sam}")
    
    # Get API key from user
    print("\nEnter your SAM API key:")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return False
    
    # Set environment variable
    os.environ['SAM_API_KEY'] = api_key
    os.environ['SAM_PUBLIC_API_KEY'] = api_key  # Also set the public one
    
    print(f"\n[SUCCESS] API key set!")
    print(f"  SAM_API_KEY: {api_key[:10]}...")
    print(f"  SAM_PUBLIC_API_KEY: {api_key[:10]}...")
    
    return True

def test_api_key():
    """Test the API key"""
    api_key = os.getenv('SAM_API_KEY')
    if not api_key:
        print("No API key found")
        return False
    
    print(f"\nTesting API key: {api_key[:10]}...")
    
    try:
        from sam_api_client import SAMAPIClient
        client = SAMAPIClient(public_api_key=api_key, mode="public")
        
        if client.test_connection():
            print("[SUCCESS] API key is working!")
            return True
        else:
            print("[ERROR] API key test failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error testing API key: {e}")
        return False

def main():
    """Main function"""
    if set_sam_api_key():
        print("\nTesting API key...")
        if test_api_key():
            print("\n[SUCCESS] Your SAM API is ready!")
            print("\nYou can now run:")
            print("  python sam_api_client.py")
            print("  python sow_sam_integrated_workflow.py")
        else:
            print("\n[ERROR] API key test failed")
    else:
        print("\n[ERROR] Failed to set API key")

if __name__ == "__main__":
    main()
