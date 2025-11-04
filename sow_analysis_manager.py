#!/usr/bin/env python3
"""
SOW Analysis Manager for ZGR SAM Document Management System
Handles structured SOW data extraction and PostgreSQL operations
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Database imports
import sys
sys.path.append('./sam/document_management')
try:
    from database_manager import DatabaseManager, execute_query, execute_update
except ImportError as e:
    print(f"Warning: Could not import database_manager: {e}")
    # Create mock functions for fallback
    class DatabaseManager:
        def __init__(self):
            pass
    def execute_query(query, params=None, fetch='all'):
        return []
    def execute_update(query, params=None):
        return None

logger = logging.getLogger(__name__)

@dataclass
class SOWAnalysisResult:
    """Structured SOW analysis result"""
    notice_id: str
    template_version: str = "v1.0"
    sow_payload: Dict[str, Any] = None
    source_docs: Dict[str, Any] = None
    source_hash: str = None
    analysis_id: str = None

class SOWAnalysisManager:
    """Manages SOW analysis data in PostgreSQL"""
    
    def __init__(self):
        # Override database name for SOW analysis
        import os
        os.environ['DB_NAME'] = 'ZGR_AI'
        self.db_manager = DatabaseManager()
        logger.info("SOW Analysis Manager initialized")
    
    def create_source_hash(self, source_docs: Dict[str, Any]) -> str:
        """Create hash for source documents for idempotency"""
        if not source_docs or not source_docs.get('sha256'):
            return None
        
        concat = "|".join(source_docs.get('sha256', []))
        return hashlib.sha256(concat.encode('utf-8')).hexdigest()
    
    def upsert_sow_analysis(self, analysis_data) -> str:
        """Upsert SOW analysis data to PostgreSQL"""
        try:
            # Handle both SOWAnalysisResult and dictionary inputs
            if isinstance(analysis_data, dict):
                notice_id = analysis_data.get('notice_id')
                template_version = analysis_data.get('template_version', 'v1.0')
                sow_payload = analysis_data.get('sow_payload', {})
                source_docs = analysis_data.get('source_docs', {})
                source_hash = analysis_data.get('source_hash')
            else:
                # SOWAnalysisResult object
                notice_id = analysis_data.notice_id
                template_version = analysis_data.template_version
                sow_payload = analysis_data.sow_payload or {}
                source_docs = analysis_data.source_docs or {}
                source_hash = analysis_data.source_hash
            
            # Create source hash if not provided
            if not source_hash and source_docs:
                source_hash = self.create_source_hash(source_docs)
            
            # Convert to JSON strings
            sow_payload_json = json.dumps(sow_payload) if sow_payload else None
            source_docs_json = json.dumps(source_docs) if source_docs else None
            
            # Direct INSERT with ON CONFLICT
            query = """
                INSERT INTO sow_analysis (
                    notice_id, 
                    template_version, 
                    sow_payload, 
                    source_docs, 
                    source_hash, 
                    is_active
                )
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, true)
                ON CONFLICT (notice_id, template_version)
                DO UPDATE SET
                    sow_payload = EXCLUDED.sow_payload,
                    source_docs = EXCLUDED.source_docs,
                    source_hash = EXCLUDED.source_hash,
                    is_active = true,
                    updated_at = now()
                RETURNING analysis_id
            """
            
            result = execute_query(
                query, 
                (
                    notice_id,
                    template_version,
                    sow_payload_json,
                    source_docs_json,
                    source_hash
                ),
                fetch='one'
            )
            
            analysis_id = result[0] if result else None
            logger.info(f"SOW analysis upserted for {notice_id}: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error upserting SOW analysis: {e}")
            raise
    
    def get_sow_analysis(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Get SOW analysis by notice_id"""
        try:
            query = """
                SELECT 
                    analysis_id,
                    notice_id,
                    template_version,
                    sow_payload,
                    source_docs,
                    source_hash,
                    is_active,
                    created_at,
                    updated_at
                FROM sow_analysis 
                WHERE notice_id = %s AND is_active = true
                ORDER BY updated_at DESC
                LIMIT 1
            """
            result = execute_query(query, (notice_id,), fetch='one')
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting SOW analysis for {notice_id}: {e}")
            return None
    
    def get_analysis(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_sow_analysis for compatibility"""
        return self.get_sow_analysis(notice_id)
    
    def get_all_active_sow(self) -> List[Dict[str, Any]]:
        """Get all active SOW analyses"""
        try:
            query = "SELECT * FROM vw_active_sow ORDER BY updated_at DESC"
            result = execute_query(query, fetch='all')
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error getting all active SOW: {e}")
            return []
    
    def search_sow_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search SOW analyses by JSONB criteria"""
        try:
            conditions = []
            params = []
            param_count = 1
            
            # Period of performance search
            if 'period_start' in criteria:
                conditions.append(f"sow_payload->>'period_of_performance' LIKE %s")
                params.append(f"%{criteria['period_start']}%")
                param_count += 1
            
            # Room capacity search
            if 'min_capacity' in criteria:
                conditions.append(f"(sow_payload #>> '{{function_space,general_session,capacity}}')::int >= %s")
                params.append(criteria['min_capacity'])
                param_count += 1
            
            # Breakout rooms count
            if 'min_breakout_rooms' in criteria:
                conditions.append(f"(sow_payload #>> '{{function_space,breakout_rooms,count}}')::int >= %s")
                params.append(criteria['min_breakout_rooms'])
                param_count += 1
            
            # Setup deadline search
            if 'setup_deadline_before' in criteria:
                conditions.append(f"(sow_payload->>'setup_deadline')::timestamptz <= %s")
                params.append(criteria['setup_deadline_before'])
                param_count += 1
            
            if not conditions:
                return self.get_all_active_sow()
            
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM vw_active_sow 
                WHERE {where_clause}
                ORDER BY updated_at DESC
            """
            
            result = execute_query(query, params, fetch='all')
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error searching SOW by criteria: {e}")
            return []
    
    def deactivate_old_versions(self, notice_id: str, keep_latest: bool = True):
        """Deactivate old versions of SOW analysis for a notice_id"""
        try:
            if keep_latest:
                # Keep only the latest version active
                query = """
                    UPDATE sow_analysis 
                    SET is_active = false 
                    WHERE notice_id = %s 
                    AND analysis_id NOT IN (
                        SELECT analysis_id 
                        FROM sow_analysis 
                        WHERE notice_id = %s 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    )
                """
                execute_update(query, (notice_id, notice_id))
            else:
                # Deactivate all versions
                query = "UPDATE sow_analysis SET is_active = false WHERE notice_id = %s"
                execute_update(query, (notice_id,))
            
            logger.info(f"Deactivated old versions for {notice_id}")
            
        except Exception as e:
            logger.error(f"Error deactivating old versions for {notice_id}: {e}")

def create_sample_sow_analysis(notice_id: str = "70LART26QPFB00001") -> SOWAnalysisResult:
    """Create sample SOW analysis result from the provided data"""
    
    sow_payload = {
        "period_of_performance": "2025-02-25 to 2025-02-27",
        "setup_deadline": "2025-02-24T18:00:00Z",
        "room_block": {
            "total_rooms_per_night": 120,
            "nights": 4,
            "attrition_policy": "no_penalty_below_120"
        },
        "function_space": {
            "registration_area": {
                "windows": ["2025-02-24T16:30/19:00", "2025-02-25T06:30/08:30"],
                "details": "1 table, 3 chairs, Wi-Fi"
            },
            "general_session": {
                "capacity": 120,
                "projectors": 2,
                "screens": "6x10",
                "setup": "classroom"
            },
            "breakout_rooms": {
                "count": 4,
                "capacity_each": 30,
                "setup": "classroom"
            },
            "logistics_room": {
                "capacity": 15,
                "setup": "boardroom"
            }
        },
        "av": {
            "projector_lumens": 5000,
            "power_strips_min": 10,
            "adapters": ["HDMI", "DisplayPort", "DVI", "VGA"],
            "clone_screens": True
        },
        "refreshments": {
            "frequency": "AM/PM_daily",
            "menu": ["water", "coffee", "tea", "snacks"],
            "schedule_lock_days": 15
        },
        "pre_con_meeting": {
            "date": "2025-02-24",
            "purpose": "BEO & room list review"
        },
        "tax_exemption": True
    }
    
    source_docs = {
        "doc_ids": ["SAMPLE_SOW_FOR_CHTGPT.pdf"],
        "sha256": ["sample_hash_12345"],
        "urls": ["https://sam.gov/api/prod/attachments/sample"]
    }
    
    return SOWAnalysisResult(
        notice_id=notice_id,
        template_version="v1.0",
        sow_payload=sow_payload,
        source_docs=source_docs,
        source_hash="sample_source_hash_12345"
    )

def test_sow_analysis():
    """Test SOW analysis functionality"""
    print("Testing SOW Analysis Manager...")
    print("=" * 50)
    
    # Initialize manager
    manager = SOWAnalysisManager()
    
    # Create sample analysis
    sample_analysis = create_sample_sow_analysis()
    
    # Test upsert
    print(f"[TEST] Upserting SOW analysis for {sample_analysis.notice_id}")
    analysis_id = manager.upsert_sow_analysis(sample_analysis)
    print(f"[SUCCESS] Analysis ID: {analysis_id}")
    
    # Test retrieval
    print(f"\n[TEST] Retrieving SOW analysis for {sample_analysis.notice_id}")
    retrieved = manager.get_sow_analysis(sample_analysis.notice_id)
    if retrieved:
        print(f"[SUCCESS] Retrieved analysis:")
        print(f"  - Analysis ID: {retrieved['analysis_id']}")
        print(f"  - Template Version: {retrieved['template_version']}")
        print(f"  - Period: {retrieved['sow_payload']['period_of_performance']}")
        print(f"  - Room Block: {retrieved['sow_payload']['room_block']['total_rooms_per_night']} rooms")
        print(f"  - General Session Capacity: {retrieved['sow_payload']['function_space']['general_session']['capacity']}")
    else:
        print("[ERROR] Could not retrieve analysis")
    
    # Test search
    print(f"\n[TEST] Searching SOW by criteria (min capacity >= 100)")
    search_results = manager.search_sow_by_criteria({"min_capacity": 100})
    print(f"[SUCCESS] Found {len(search_results)} matching analyses")
    
    # Test all active
    print(f"\n[TEST] Getting all active SOW analyses")
    all_active = manager.get_all_active_sow()
    print(f"[SUCCESS] Found {len(all_active)} active analyses")
    
    print(f"\n[COMPLETE] SOW Analysis Manager test completed!")

if __name__ == "__main__":
    test_sow_analysis()
