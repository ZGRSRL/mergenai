#!/usr/bin/env python3
"""
Duplicate Guard - Idempotent processing for notice_id + source_hash
"""

import hashlib
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class ProcessingRecord:
    """Processing record for duplicate detection"""
    notice_id: str
    source_hash: str
    processing_time: datetime
    status: str  # processing, completed, failed
    analysis_id: Optional[str] = None
    error_message: Optional[str] = None

class DuplicateGuard:
    """Duplicate guard for idempotent processing"""
    
    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours
        self.logger = logging.getLogger("DuplicateGuard")
        self.processing_records: Dict[str, ProcessingRecord] = {}
        self.active_processing: Set[str] = set()
    
    def _generate_key(self, notice_id: str, source_hash: str) -> str:
        """Generate unique key for notice + source combination"""
        return f"{notice_id}:{source_hash}"
    
    def _is_record_expired(self, record: ProcessingRecord) -> bool:
        """Check if processing record is expired"""
        age = datetime.now() - record.processing_time
        return age > timedelta(hours=self.max_age_hours)
    
    def _cleanup_expired_records(self) -> None:
        """Clean up expired processing records"""
        expired_keys = []
        
        for key, record in self.processing_records.items():
            if self._is_record_expired(record):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.processing_records[key]
            self.logger.info(f"Cleaned up expired record: {key}")
    
    def should_process(self, notice_id: str, source_hash: str) -> Dict[str, Any]:
        """Check if notice should be processed (idempotent check)"""
        self._cleanup_expired_records()
        
        key = self._generate_key(notice_id, source_hash)
        
        # Check if currently processing
        if key in self.active_processing:
            return {
                "should_process": False,
                "reason": "currently_processing",
                "message": f"Notice {notice_id} is currently being processed"
            }
        
        # Check if already processed successfully
        if key in self.processing_records:
            record = self.processing_records[key]
            
            if record.status == "completed":
                return {
                    "should_process": False,
                    "reason": "already_completed",
                    "message": f"Notice {notice_id} already processed successfully",
                    "analysis_id": record.analysis_id,
                    "processed_at": record.processing_time.isoformat()
                }
            
            elif record.status == "failed":
                # Allow retry for failed records
                return {
                    "should_process": True,
                    "reason": "retry_failed",
                    "message": f"Retrying failed processing for notice {notice_id}",
                    "previous_error": record.error_message
                }
        
        # New processing
        return {
            "should_process": True,
            "reason": "new_processing",
            "message": f"New processing for notice {notice_id}"
        }
    
    def start_processing(self, notice_id: str, source_hash: str) -> str:
        """Mark notice as being processed"""
        key = self._generate_key(notice_id, source_hash)
        
        if key in self.active_processing:
            raise ValueError(f"Notice {notice_id} is already being processed")
        
        self.active_processing.add(key)
        
        # Create processing record
        record = ProcessingRecord(
            notice_id=notice_id,
            source_hash=source_hash,
            processing_time=datetime.now(),
            status="processing"
        )
        self.processing_records[key] = record
        
        self.logger.info(f"Started processing: {notice_id}")
        return key
    
    def complete_processing(self, key: str, analysis_id: str) -> None:
        """Mark processing as completed"""
        if key not in self.processing_records:
            raise ValueError(f"Processing record not found: {key}")
        
        record = self.processing_records[key]
        record.status = "completed"
        record.analysis_id = analysis_id
        
        self.active_processing.discard(key)
        
        self.logger.info(f"Completed processing: {record.notice_id} -> {analysis_id}")
    
    def fail_processing(self, key: str, error_message: str) -> None:
        """Mark processing as failed"""
        if key not in self.processing_records:
            raise ValueError(f"Processing record not found: {key}")
        
        record = self.processing_records[key]
        record.status = "failed"
        record.error_message = error_message
        
        self.active_processing.discard(key)
        
        self.logger.error(f"Failed processing: {record.notice_id} - {error_message}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        self._cleanup_expired_records()
        
        total_records = len(self.processing_records)
        active_count = len(self.active_processing)
        completed_count = len([r for r in self.processing_records.values() if r.status == "completed"])
        failed_count = len([r for r in self.processing_records.values() if r.status == "failed"])
        
        return {
            "total_records": total_records,
            "active_processing": active_count,
            "completed": completed_count,
            "failed": failed_count,
            "success_rate": (completed_count / total_records * 100) if total_records > 0 else 0
        }

# Global duplicate guard instance
duplicate_guard = DuplicateGuard()

def should_process_notice(notice_id: str, source_hash: str) -> Dict[str, Any]:
    """Convenience function for checking if notice should be processed"""
    return duplicate_guard.should_process(notice_id, source_hash)

def start_processing(notice_id: str, source_hash: str) -> str:
    """Convenience function for starting processing"""
    return duplicate_guard.start_processing(notice_id, source_hash)

def complete_processing(key: str, analysis_id: str) -> None:
    """Convenience function for completing processing"""
    duplicate_guard.complete_processing(key, analysis_id)

def fail_processing(key: str, error_message: str) -> None:
    """Convenience function for failing processing"""
    duplicate_guard.fail_processing(key, error_message)

if __name__ == "__main__":
    # Test the duplicate guard
    print("Testing Duplicate Guard...")
    
    notice_id = "TEST001"
    source_hash = "abc123"
    
    # First check
    result1 = should_process_notice(notice_id, source_hash)
    print(f"First check: {result1}")
    
    # Start processing
    key = start_processing(notice_id, source_hash)
    print(f"Started processing with key: {key}")
    
    # Second check (should be blocked)
    result2 = should_process_notice(notice_id, source_hash)
    print(f"Second check: {result2}")
    
    # Complete processing
    complete_processing(key, "analysis_123")
    print("Completed processing")
    
    # Third check (should be blocked as completed)
    result3 = should_process_notice(notice_id, source_hash)
    print(f"Third check: {result3}")
    
    # Get stats
    stats = duplicate_guard.get_processing_stats()
    print(f"Stats: {stats}")
    
    print("Duplicate Guard test completed!")

