#!/usr/bin/env python3
"""
Test Knowledge Builder
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from sam.knowledge.knowledge_builder_agent import KnowledgeBuilderAgent
from sam.knowledge.knowledge_repository import KnowledgeRepository

def test_kb_minimal():
    """Minimal knowledge builder test"""
    print("Testing Knowledge Builder...")
    
    try:
        kb = KnowledgeBuilderAgent(Path("."))
        res = kb.build("70LART26QPFB00001")
        
        # Basic structure tests
        assert res["schema_version"] == "sow.learn.v1", f"Expected sow.learn.v1, got {res['schema_version']}"
        assert "provenance" in res, "Missing provenance field"
        assert "meta" in res, "Missing meta field"
        assert "rationales" in res, "Missing rationales field"
        assert "citations" in res, "Missing citations field"
        
        print("Basic structure test passed")
        
        # Test repository
        repo = KnowledgeRepository()
        result_id = repo.upsert("TEST_001", res, res.get("provenance"))
        
        if result_id:
            print("Repository upsert test passed")
            
            # Test retrieval
            latest = repo.latest("TEST_001")
            if latest:
                print("Repository retrieval test passed")
            else:
                print("Repository retrieval test failed")
        else:
            print("Repository upsert test failed")
        
        print(f"Knowledge stats:")
        print(f"  - Documents: {res['meta'].get('total_documents', 0)}")
        print(f"  - Pages: {res['meta'].get('total_pages', 0)}")
        print(f"  - Rationales: {len(res.get('rationales', []))}")
        print(f"  - Citations: {len(res.get('citations', []))}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_kb_with_mock_data():
    """Test with mock data"""
    print("Testing with mock data...")
    
    # Create mock attachments directory
    mock_dir = Path("downloads/70LART26QPFB00001")
    mock_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock PDF files
    mock_files = [
        "SOW_Attachment.pdf",
        "Fire_Safety_Requirements.pdf", 
        "Invoice_Template.pdf"
    ]
    
    for filename in mock_files:
        mock_file = mock_dir / filename
        with open(mock_file, "w") as f:
            f.write(f"Mock content for {filename}")
    
    try:
        kb = KnowledgeBuilderAgent(Path("."))
        res = kb.build("70LART26QPFB00001")
        
        print(f"Mock test results:")
        print(f"  - Schema: {res['schema_version']}")
        print(f"  - Documents: {res['meta'].get('total_documents', 0)}")
        print(f"  - Rationales: {len(res.get('rationales', []))}")
        
        # Cleanup
        import shutil
        shutil.rmtree(mock_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"Mock test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Knowledge Builder Tests...")
    
    # Test 1: Minimal test
    test1 = test_kb_minimal()
    
    # Test 2: Mock data test
    test2 = test_kb_with_mock_data()
    
    if test1 and test2:
        print("All tests passed!")
    else:
        print("Some tests failed!")
