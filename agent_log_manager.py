#!/usr/bin/env python3
"""
Agent Log Manager - AutoGen ajanları için log ve izlenebilirlik sistemi
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class AgentLogEntry:
    """Agent log entry"""
    timestamp: str
    agent_name: str
    notice_id: str
    action: str
    input_size: int
    output_size: int
    processing_time: float
    duration_ms: int  # milliseconds
    status: str  # success, error, warning
    error_type: Optional[str] = None  # timeout, validation, api_error, etc.
    error_message: Optional[str] = None
    source_docs: Optional[List[str]] = None
    analysis_id: Optional[str] = None
    schema_version: Optional[str] = None
    termination_reason: Optional[str] = None  # STOP, timeout, error, max_turns
    turn_count: Optional[int] = None

class AgentLogManager:
    """Agent log manager for tracking and monitoring"""
    
    def __init__(self, log_dir: str = "./logs", retention_days: int = 30):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.retention_days = retention_days
        
        # Setup logging
        self.logger = logging.getLogger("AgentLogManager")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.log_dir / f"agent_logs_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
        # Clean old logs on startup
        self._clean_old_logs()
    
    def log_agent_action(self, 
                        agent_name: str, 
                        notice_id: str, 
                        action: str,
                        input_data: Any = None,
                        output_data: Any = None,
                        processing_time: float = 0.0,
                        status: str = "success",
                        error_message: str = None,
                        error_type: str = None,
                        source_docs: List[str] = None,
                        analysis_id: str = None,
                        schema_version: str = None,
                        termination_reason: str = None,
                        turn_count: int = None) -> None:
        """Log agent action with enhanced fields"""
        
        # Calculate sizes
        input_size = len(str(input_data)) if input_data else 0
        output_size = len(str(output_data)) if output_data else 0
        duration_ms = int(processing_time * 1000)
        
        # Create log entry
        log_entry = AgentLogEntry(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            notice_id=notice_id,
            action=action,
            input_size=input_size,
            output_size=output_size,
            processing_time=processing_time,
            duration_ms=duration_ms,
            status=status,
            error_type=error_type,
            error_message=error_message,
            source_docs=source_docs,
            analysis_id=analysis_id,
            schema_version=schema_version,
            termination_reason=termination_reason,
            turn_count=turn_count
        )
        
        # Log to file
        self.logger.info(f"Agent: {agent_name}, Action: {action}, Notice: {notice_id}, Status: {status}, Duration: {duration_ms}ms")
        
        # Save to JSON file
        self._save_log_entry(log_entry)
    
    def _save_log_entry(self, log_entry: AgentLogEntry) -> None:
        """Save log entry to JSON file"""
        log_file = self.log_dir / f"agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Load existing logs
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add new log entry
        logs.append(asdict(log_entry))
        
        # Save updated logs
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def _clean_old_logs(self) -> None:
        """Clean old log files based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for log_file in self.log_dir.glob("*.json"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning old logs: {e}")
    
    def get_termination_metrics(self) -> Dict[str, Any]:
        """Get termination metrics for STOP. detection"""
        log_file = self.log_dir / f"agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not log_file.exists():
            return {"total_terminations": 0, "stop_count": 0, "timeout_count": 0, "error_count": 0}
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            total_terminations = len([log for log in logs if log.get('termination_reason')])
            stop_count = len([log for log in logs if log.get('termination_reason') == 'STOP'])
            timeout_count = len([log for log in logs if log.get('termination_reason') == 'timeout'])
            error_count = len([log for log in logs if log.get('termination_reason') == 'error'])
            
            return {
                "total_terminations": total_terminations,
                "stop_count": stop_count,
                "timeout_count": timeout_count,
                "error_count": error_count,
                "stop_rate": (stop_count / total_terminations * 100) if total_terminations > 0 else 0
            }
        except:
            return {"total_terminations": 0, "stop_count": 0, "timeout_count": 0, "error_count": 0}
    
    def get_recent_actions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent agent actions"""
        log_file = self.log_dir / f"agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Sort by timestamp (newest first) and limit
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return logs[:limit]
        except:
            return []
    
    def get_agent_stats(self, agent_name: str = None, notice_id: str = None) -> Dict[str, Any]:
        """Get agent statistics"""
        log_file = self.log_dir / f"agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not log_file.exists():
            return {"total_actions": 0, "success_rate": 0, "avg_processing_time": 0}
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Filter logs
            filtered_logs = logs
            if agent_name:
                filtered_logs = [log for log in logs if log['agent_name'] == agent_name]
            if notice_id:
                filtered_logs = [log for log in filtered_logs if log['notice_id'] == notice_id]
            
            if not filtered_logs:
                return {"total_actions": 0, "success_rate": 0, "avg_processing_time": 0}
            
            # Calculate stats
            total_actions = len(filtered_logs)
            successful_actions = len([log for log in filtered_logs if log['status'] == 'success'])
            success_rate = (successful_actions / total_actions) * 100 if total_actions > 0 else 0
            
            processing_times = [log['processing_time'] for log in filtered_logs if log['processing_time'] > 0]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            return {
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": round(success_rate, 2),
                "avg_processing_time": round(avg_processing_time, 2),
                "error_count": total_actions - successful_actions
            }
        except:
            return {"total_actions": 0, "success_rate": 0, "avg_processing_time": 0}
    
    def get_notice_processing_log(self, notice_id: str) -> List[Dict[str, Any]]:
        """Get processing log for specific notice"""
        log_file = self.log_dir / f"agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Filter by notice_id and sort by timestamp
            notice_logs = [log for log in logs if log['notice_id'] == notice_id]
            notice_logs.sort(key=lambda x: x['timestamp'])
            
            return notice_logs
        except:
            return []

# Global log manager instance
log_manager = AgentLogManager()

def log_agent_action(agent_name: str, notice_id: str, action: str, **kwargs):
    """Convenience function for logging agent actions"""
    log_manager.log_agent_action(agent_name, notice_id, action, **kwargs)

def get_recent_actions(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent agent actions"""
    return log_manager.get_recent_actions(limit)

def get_agent_stats(agent_name: str = None, notice_id: str = None) -> Dict[str, Any]:
    """Get agent statistics"""
    return log_manager.get_agent_stats(agent_name, notice_id)

def get_notice_processing_log(notice_id: str) -> List[Dict[str, Any]]:
    """Get processing log for specific notice"""
    return log_manager.get_notice_processing_log(notice_id)

def get_termination_metrics() -> Dict[str, Any]:
    """Get termination metrics for STOP. detection"""
    return log_manager.get_termination_metrics()

if __name__ == "__main__":
    # Test the log manager
    print("Testing Agent Log Manager...")
    
    # Log some test actions
    log_agent_action("DocumentProcessor", "TEST001", "extract_text", 
                    input_data="test document", output_data="extracted text", 
                    processing_time=1.5, status="success")
    
    log_agent_action("SOWParser", "TEST001", "parse_sow", 
                    input_data="sow text", output_data="parsed json", 
                    processing_time=2.3, status="success", analysis_id="analysis_123")
    
    log_agent_action("Validator", "TEST001", "validate_data", 
                    input_data="raw data", output_data="validated data", 
                    processing_time=0.8, status="error", error_message="Invalid JSON")
    
    # Get recent actions
    recent = get_recent_actions(5)
    print(f"Recent actions: {len(recent)}")
    for action in recent:
        print(f"  {action['timestamp']} - {action['agent_name']} - {action['action']} - {action['status']}")
    
    # Get stats
    stats = get_agent_stats()
    print(f"Overall stats: {stats}")
    
    notice_stats = get_agent_stats(notice_id="TEST001")
    print(f"Notice stats: {notice_stats}")
    
    print("Agent Log Manager test completed!")
