#!/usr/bin/env python3
"""
Test AutoGen analysis functionality
"""

from autogen_analysis_center import analyze_opportunity_comprehensive
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_autogen_analysis():
    """Test AutoGen analysis functionality"""
    print("=== AutoGen Analysis Test ===")
    
    try:
        print("=== Starting Analysis ===")
        result = analyze_opportunity_comprehensive('70LART26QPFB00001')
        
        print(f"SUCCESS: Analysis completed")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"Status: {result.get('status', 'N/A')}")
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"Error: {result.get('error', 'N/A')}")
            print(f"Confidence: {result.get('confidence_score', 'N/A')}")
            print(f"Risk Level: {result.get('risk_level', 'N/A')}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    test_autogen_analysis()
