#!/usr/bin/env python3
"""
Opportunity Reprocessor - Handle reprocessing of specific opportunities
"""

import logging
from typing import Dict, Any, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class OpportunityReprocessor:
    """Handle reprocessing of opportunities with detailed status tracking"""
    
    def __init__(self):
        self.status_tracking = {}
    
    def reprocess_opportunity(self, notice_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Reprocess a specific opportunity end-to-end
        
        Args:
            notice_id: The opportunity notice ID
            force: Force reprocessing even if already processed
            
        Returns:
            Dict with reprocessing results and status
        """
        result = {
            "notice_id": notice_id,
            "status": "started",
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "attachments_processed": 0,
            "text_extracted": 0,
            "analysis_completed": False,
            "final_status": "unknown"
        }
        
        try:
            logger.info(f"Starting reprocess for opportunity: {notice_id}")
            
            # Step 1: Get opportunity data
            result["steps_completed"].append("get_opportunity_data")
            opp_data = self._get_opportunity_data(notice_id)
            if not opp_data:
                result["errors"].append("Opportunity data not found")
                result["final_status"] = "failed"
                return result
            
            # Step 2: Process attachments
            result["steps_completed"].append("process_attachments")
            attachment_results = self._process_attachments(notice_id, opp_data)
            result["attachments_processed"] = len(attachment_results)
            
            # Step 3: Extract text from attachments
            result["steps_completed"].append("extract_text")
            text_results = self._extract_text_from_attachments(attachment_results)
            result["text_extracted"] = len([r for r in text_results if r.get("success")])
            
            # Step 4: Run analysis
            result["steps_completed"].append("run_analysis")
            analysis_result = self._run_analysis(notice_id, text_results)
            result["analysis_completed"] = analysis_result.get("success", False)
            
            # Determine final status
            if result["errors"]:
                result["final_status"] = "failed"
            elif result["warnings"]:
                result["final_status"] = "completed_with_warnings"
            else:
                result["final_status"] = "completed"
            
            result["status"] = "completed"
            logger.info(f"Reprocess completed for {notice_id}: {result['final_status']}")
            
        except Exception as e:
            result["errors"].append(f"Reprocess error: {str(e)}")
            result["final_status"] = "failed"
            logger.error(f"Reprocess failed for {notice_id}: {e}")
        
        return result
    
    def _get_opportunity_data(self, notice_id: str) -> Dict[str, Any]:
        """Get opportunity data from database or mock"""
        try:
            from mock_sam_data import get_mock_opportunity_data
            return get_mock_opportunity_data(notice_id)
        except Exception as e:
            logger.error(f"Failed to get opportunity data for {notice_id}: {e}")
            return None
    
    def _process_attachments(self, notice_id: str, opp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process attachments for the opportunity"""
        results = []
        
        attachments = opp_data.get("attachments", [])
        if not attachments:
            logger.info(f"No attachments found for {notice_id}")
            return results
        
        from enhanced_attachment_downloader import EnhancedAttachmentDownloader
        downloader = EnhancedAttachmentDownloader()
        
        for i, att in enumerate(attachments):
            attachment_id = f"{notice_id}_att_{i+1}"
            url = att.get("url", "")
            filename = att.get("filename", f"attachment_{i+1}.pdf")
            
            if url:
                download_result = downloader.download_attachment(attachment_id, url, filename)
                results.append(download_result)
            else:
                results.append({
                    "attachment_id": attachment_id,
                    "status": "NO_URL",
                    "error_msg": "No URL provided",
                    "filename": filename
                })
        
        return results
    
    def _extract_text_from_attachments(self, attachment_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract text from successfully downloaded attachments"""
        text_results = []
        
        from enhanced_pdf_parser import EnhancedPDFParser
        parser = EnhancedPDFParser()
        
        for att_result in attachment_results:
            if att_result.get("status") == "DOWNLOADED" and att_result.get("download_path"):
                pdf_path = att_result["download_path"]
                text_result = parser.extract_text_enhanced(pdf_path)
                text_results.append(text_result)
            else:
                text_results.append({
                    "attachment_id": att_result.get("attachment_id", "unknown"),
                    "success": False,
                    "error": f"Attachment not downloaded: {att_result.get('status', 'unknown')}",
                    "text": ""
                })
        
        return text_results
    
    def _run_analysis(self, notice_id: str, text_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run analysis on the extracted text"""
        try:
            from enhanced_pdf_parser import EnhancedRAGProcessor
            from autogen_analysis_center import analyze_opportunity_comprehensive
            
            # Process text with RAG
            rag = EnhancedRAGProcessor()
            rag_result = rag.process_opportunity_text(notice_id, text_results)
            
            if not rag_result.get("analysis_ready"):
                return {
                    "success": False,
                    "error": "EMPTY_CORPUS",
                    "hint": "Attachment may be secure or OCR failed",
                    "rag_result": rag_result
                }
            
            # Run AutoGen analysis
            analysis_result = analyze_opportunity_comprehensive(notice_id)
            
            return {
                "success": analysis_result.get("success", False),
                "analysis_result": analysis_result,
                "rag_result": rag_result
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {notice_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_reprocess_status(self, notice_id: str) -> Dict[str, Any]:
        """Get current reprocessing status for an opportunity"""
        return self.status_tracking.get(notice_id, {
            "notice_id": notice_id,
            "status": "not_started",
            "last_updated": None
        })

def test_reprocessor():
    """Test the reprocessor functionality"""
    reprocessor = OpportunityReprocessor()
    
    print("Opportunity Reprocessor Test")
    print("=" * 40)
    
    # Test with our mock opportunity
    notice_id = "70LART26QPFB00001"
    
    print(f"Testing reprocess for: {notice_id}")
    result = reprocessor.reprocess_opportunity(notice_id)
    
    print(f"Status: {result['status']}")
    print(f"Steps Completed: {result['steps_completed']}")
    print(f"Attachments Processed: {result['attachments_processed']}")
    print(f"Text Extracted: {result['text_extracted']}")
    print(f"Analysis Completed: {result['analysis_completed']}")
    print(f"Final Status: {result['final_status']}")
    
    if result['errors']:
        print(f"Errors: {result['errors']}")
    
    if result['warnings']:
        print(f"Warnings: {result['warnings']}")

if __name__ == "__main__":
    test_reprocessor()
