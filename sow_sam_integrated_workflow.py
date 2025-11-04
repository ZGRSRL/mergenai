#!/usr/bin/env python3
"""
SOW SAM Integrated Workflow
Enhanced SOW processing with SAM.gov API integration
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Local imports
from sam_api_client import SAMAPIClient
from sow_autogen_workflow import SOWWorkflowPipeline, DocumentInfo
from sow_analysis_manager import SOWAnalysisManager, SOWAnalysisResult

logger = logging.getLogger(__name__)

class SOWSAMIntegratedWorkflow:
    """Enhanced SOW workflow with SAM.gov API integration"""
    
    def __init__(self, sam_public_key: str = None, sam_system_key: str = None):
        """
        Initialize integrated workflow
        
        Args:
            sam_public_key: SAM.gov public API key
            sam_system_key: SAM.gov system account API key
        """
        # Initialize SAM API client
        self.sam_client = SAMAPIClient(
            public_api_key=sam_public_key,
            system_api_key=sam_system_key,
            mode="auto"  # Auto-fallback strategy
        )
        
        # Initialize SOW workflow
        self.sow_workflow = SOWWorkflowPipeline()
        self.sow_manager = SOWAnalysisManager()
        
        logger.info("SOW SAM Integrated Workflow initialized")
    
    def process_opportunity_from_sam(self, notice_id: str, 
                                   download_dir: str = "sam_downloads",
                                   process_attachments: bool = True) -> Dict[str, Any]:
        """
        Process opportunity directly from SAM.gov
        
        Args:
            notice_id: SAM.gov notice ID
            download_dir: Directory to save downloaded files
            process_attachments: Whether to process downloaded attachments
        
        Returns:
            Processing result with analysis data
        """
        try:
            logger.info(f"Processing opportunity from SAM: {notice_id}")
            
            # Step 1: Get opportunity details and download attachments
            sam_result = self.sam_client.get_opportunity_with_attachments(
                notice_id, download_dir
            )
            
            if 'error' in sam_result:
                return {
                    'success': False,
                    'notice_id': notice_id,
                    'error': sam_result['error'],
                    'timestamp': datetime.now().isoformat()
                }
            
            opportunity = sam_result['opportunity']
            downloaded_files = sam_result['downloaded_files']
            
            logger.info(f"Downloaded {len(downloaded_files)} attachments")
            
            # Step 2: Process downloaded attachments if requested
            analysis_result = None
            if process_attachments and downloaded_files:
                analysis_result = self._process_downloaded_attachments(
                    notice_id, downloaded_files, opportunity
                )
            
            # Step 3: Store opportunity metadata
            self._store_opportunity_metadata(notice_id, opportunity, downloaded_files)
            
            return {
                'success': True,
                'notice_id': notice_id,
                'opportunity': opportunity,
                'downloaded_files': downloaded_files,
                'analysis_result': analysis_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing opportunity {notice_id}: {e}")
            return {
                'success': False,
                'notice_id': notice_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_downloaded_attachments(self, notice_id: str, 
                                      downloaded_files: List[str],
                                      opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process downloaded attachments through SOW workflow"""
        try:
            logger.info(f"Processing {len(downloaded_files)} attachments for {notice_id}")
            
            # Filter for SOW-related documents
            sow_documents = self._filter_sow_documents(downloaded_files)
            
            if not sow_documents:
                logger.warning(f"No SOW documents found in {len(downloaded_files)} attachments")
                return None
            
            # Process through SOW workflow
            analysis_id = self.sow_workflow.process_sow_documents(
                notice_id, sow_documents
            )
            
            # Get analysis result
            analysis_data = self.sow_manager.get_sow_analysis(notice_id)
            
            return {
                'analysis_id': analysis_id,
                'analysis_data': analysis_data,
                'processed_documents': sow_documents
            }
            
        except Exception as e:
            logger.error(f"Error processing attachments for {notice_id}: {e}")
            return None
    
    def _filter_sow_documents(self, file_paths: List[str]) -> List[str]:
        """Filter documents that are likely SOW-related"""
        sow_keywords = [
            'sow', 'statement of work', 'work statement',
            'requirements', 'specification', 'scope',
            'lodging', 'accommodation', 'conference',
            'meeting', 'event', 'training'
        ]
        
        sow_documents = []
        
        for file_path in file_paths:
            filename = os.path.basename(file_path).lower()
            
            # Check if filename contains SOW-related keywords
            if any(keyword in filename for keyword in sow_keywords):
                sow_documents.append(file_path)
                logger.info(f"Identified SOW document: {filename}")
            else:
                logger.debug(f"Skipping non-SOW document: {filename}")
        
        return sow_documents
    
    def _store_opportunity_metadata(self, notice_id: str, 
                                  opportunity: Dict[str, Any],
                                  downloaded_files: List[str]):
        """Store opportunity metadata in database"""
        try:
            # Create metadata structure
            metadata = {
                'sam_opportunity': opportunity,
                'downloaded_files': [
                    {
                        'filename': os.path.basename(f),
                        'path': f,
                        'size': os.path.getsize(f) if os.path.exists(f) else 0
                    }
                    for f in downloaded_files
                ],
                'download_timestamp': datetime.now().isoformat()
            }
            
            # Store in SOW analysis with metadata
            sow_payload = {
                'sam_metadata': metadata,
                'notice_id': notice_id,
                'title': opportunity.get('title', ''),
                'agency': opportunity.get('department', ''),
                'posted_date': opportunity.get('postedDate', ''),
                'description': opportunity.get('description', ''),
                'naics_code': opportunity.get('naicsCode', ''),
                'contract_type': opportunity.get('typeOfSetAside', ''),
                'organization_type': opportunity.get('organizationType', '')
            }
            
            # Create analysis result
            analysis_result = SOWAnalysisResult(
                notice_id=notice_id,
                template_version="v1.0",
                sow_payload=sow_payload,
                source_docs={
                    'doc_ids': [os.path.basename(f) for f in downloaded_files],
                    'sha256': [self._calculate_file_hash(f) for f in downloaded_files],
                    'urls': []  # SAM URLs are not stored for security
                },
                source_hash=self._calculate_source_hash(downloaded_files)
            )
            
            # Store in database
            analysis_id = self.sow_manager.upsert_sow_analysis(analysis_result)
            logger.info(f"Stored opportunity metadata: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error storing opportunity metadata: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        import hashlib
        
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "unknown"
    
    def _calculate_source_hash(self, file_paths: List[str]) -> str:
        """Calculate combined hash of all source files"""
        import hashlib
        
        hashes = [self._calculate_file_hash(f) for f in file_paths]
        combined = "|".join(hashes)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def search_and_process_opportunities(self, search_params: Dict[str, Any],
                                       download_dir: str = "sam_downloads",
                                       max_opportunities: int = 10) -> List[Dict[str, Any]]:
        """
        Search for opportunities and process them
        
        Args:
            search_params: Search parameters for SAM API
            download_dir: Directory to save downloaded files
            max_opportunities: Maximum number of opportunities to process
        
        Returns:
            List of processing results
        """
        try:
            logger.info(f"Searching opportunities with params: {search_params}")
            
            # Search opportunities
            search_result = self.sam_client.search_opportunities(**search_params)
            opportunities = search_result.get('opportunitiesData', [])
            
            if not opportunities:
                logger.info("No opportunities found")
                return []
            
            # Limit results
            opportunities = opportunities[:max_opportunities]
            logger.info(f"Processing {len(opportunities)} opportunities")
            
            results = []
            
            for opportunity in opportunities:
                notice_id = opportunity.get('noticeId')
                if not notice_id:
                    continue
                
                logger.info(f"Processing opportunity: {notice_id}")
                
                # Process opportunity
                result = self.process_opportunity_from_sam(
                    notice_id, download_dir, process_attachments=True
                )
                
                results.append(result)
                
                # Add delay between requests to respect rate limits
                import time
                time.sleep(1)
            
            logger.info(f"Completed processing {len(results)} opportunities")
            return results
            
        except Exception as e:
            logger.error(f"Error in search and process: {e}")
            return []
    
    def get_opportunity_status(self, notice_id: str) -> Dict[str, Any]:
        """Get current status of an opportunity"""
        try:
            # Check if we have analysis data
            analysis_data = self.sow_manager.get_sow_analysis(notice_id)
            
            # Get fresh data from SAM
            sam_opportunity = self.sam_client.get_opportunity_details(notice_id)
            
            return {
                'notice_id': notice_id,
                'has_analysis': analysis_data is not None,
                'analysis_id': analysis_data.get('analysis_id') if analysis_data else None,
                'sam_available': sam_opportunity is not None,
                'last_updated': analysis_data.get('updated_at') if analysis_data else None,
                'sam_title': sam_opportunity.get('title') if sam_opportunity else None
            }
            
        except Exception as e:
            logger.error(f"Error getting opportunity status: {e}")
            return {'error': str(e)}

def test_sam_integrated_workflow():
    """Test SAM integrated workflow"""
    print("Testing SOW SAM Integrated Workflow...")
    print("=" * 60)
    
    # Initialize workflow
    workflow = SOWSAMIntegratedWorkflow()
    
    # Test specific opportunity
    notice_id = "70LART26QPFB00001"
    print(f"[TEST] Processing opportunity: {notice_id}")
    
    # Process opportunity
    result = workflow.process_opportunity_from_sam(
        notice_id, 
        download_dir="test_sam_downloads",
        process_attachments=True
    )
    
    if result['success']:
        print("[SUCCESS] Opportunity processed successfully")
        print(f"  - Downloaded files: {len(result['downloaded_files'])}")
        print(f"  - Analysis result: {'Yes' if result['analysis_result'] else 'No'}")
        
        # Show downloaded files
        for i, file_path in enumerate(result['downloaded_files'], 1):
            print(f"    {i}. {os.path.basename(file_path)}")
    else:
        print(f"[ERROR] Processing failed: {result['error']}")
    
    # Test opportunity status
    print(f"\n[TEST] Checking opportunity status...")
    status = workflow.get_opportunity_status(notice_id)
    print(f"  - Has Analysis: {status.get('has_analysis', False)}")
    print(f"  - SAM Available: {status.get('sam_available', False)}")
    print(f"  - Analysis ID: {status.get('analysis_id', 'N/A')}")
    
    print(f"\n[COMPLETE] SAM Integrated Workflow test completed!")

if __name__ == "__main__":
    test_sam_integrated_workflow()
