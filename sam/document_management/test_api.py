#!/usr/bin/env python3
"""
Test SAM API functionality
"""

from sam_document_access_v2 import SAMDocumentAccessManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sam_api():
    """Test SAM API functionality"""
    print("=== SAM API Test ===")
    
    try:
        # Create manager
        sam_manager = SAMDocumentAccessManager()
        print("SUCCESS: Manager created")
        
        # Test opportunity fetch
        print("=== Fetching Opportunity ===")
        opp = sam_manager.get_opportunity_details('70LART26QPFB00001')
        
        if opp:
            print(f"SUCCESS: Result: {opp is not None}")
            print(f"SUCCESS: Title: {opp.get('title', 'N/A')}")
            print(f"SUCCESS: Attachments: {len(opp.get('attachments', []))}")
            
            # Test attachments
            attachments = opp.get('attachments', [])
            if attachments:
                print("=== Attachment Details ===")
                for i, att in enumerate(attachments):
                    print(f"  {i+1}. {att.get('filename', 'N/A')} - {att.get('url', 'N/A')}")
        else:
            print("ERROR: No opportunity found")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    test_sam_api()
