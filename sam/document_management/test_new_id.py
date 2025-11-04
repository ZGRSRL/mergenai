#!/usr/bin/env python3
"""
Test with new opportunity ID
"""

from sam_document_access_v2 import SAMDocumentAccessManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_new_opportunity():
    """Test with new opportunity ID"""
    print("=== Real SAM API Test with New ID ===")
    
    try:
        sam_manager = SAMDocumentAccessManager()
        opp = sam_manager.get_opportunity_details('ffa04fa070794f8a87095f49af364831')
        
        if opp:
            print(f"SUCCESS: Title: {opp.get('title', 'N/A')}")
            print(f"SUCCESS: Attachments: {len(opp.get('attachments', []))}")
            
            attachments = opp.get('attachments', [])
            if attachments:
                print("=== Attachment Details ===")
                for i, att in enumerate(attachments):
                    print(f"  {i+1}. {att.get('filename', 'N/A')} - {att.get('url', 'N/A')}")
            else:
                print("No attachments found")
        else:
            print("ERROR: No opportunity found")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    test_new_opportunity()
