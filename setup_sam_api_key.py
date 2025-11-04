#!/usr/bin/env python3
"""
SAM API Key Setup Helper
"""

import os
import sys

def setup_api_key():
    """Setup SAM API key"""
    print("SAM API Key Setup")
    print("=" * 40)
    
    # Check current key
    current_key = os.getenv('SAM_PUBLIC_API_KEY')
    if current_key and current_key != 'test_key_placeholder':
        print(f"Current API key: {current_key[:10]}...")
        print("This looks like a real API key!")
        return current_key
    
    print("No valid API key found.")
    print("\nTo get your SAM API key:")
    print("1. Go to https://sam.gov")
    print("2. Login to your account")
    print("3. Go to Account Details")
    print("4. Find 'API Key' section")
    print("5. Create a new API key")
    print("6. Copy the key")
    
    print("\nThen set it as environment variable:")
    print("PowerShell: $env:SAM_PUBLIC_API_KEY='your_key_here'")
    print("Command Prompt: set SAM_PUBLIC_API_KEY=your_key_here")
    
    return None

def test_api_key(api_key):
    """Test API key"""
    if not api_key:
        print("No API key to test")
        return False
    
    print(f"\nTesting API key: {api_key[:10]}...")
    
    try:
        from sam_api_client import SAMAPIClient
        client = SAMAPIClient(public_api_key=api_key, mode="public")
        
        # Test connection
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
    # Setup API key
    api_key = setup_api_key()
    
    if api_key:
        # Test the key
        if test_api_key(api_key):
            print("\n[SUCCESS] Your SAM API is ready to use!")
            print("\nYou can now run:")
            print("  python sam_api_client.py")
            print("  python sow_sam_integrated_workflow.py")
        else:
            print("\n[WARNING] API key test failed. Please check your key.")
    else:
        print("\n[INFO] Please get your API key from SAM.gov first.")

if __name__ == "__main__":
    main()
