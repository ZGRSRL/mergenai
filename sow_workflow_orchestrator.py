#!/usr/bin/env python3
"""
SOW Workflow Orchestrator
Main orchestrator for the complete SOW processing pipeline
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import schedule
import time
import threading

# Local imports
from sow_autogen_workflow import SOWWorkflowPipeline, DocumentInfo
from sow_analysis_manager import SOWAnalysisManager
from sow_email_notifications import SOWEmailNotifier
from sow_api_endpoints import get_db_connection

logger = logging.getLogger(__name__)

class SOWWorkflowOrchestrator:
    """Main orchestrator for SOW processing workflow"""
    
    def __init__(self):
        self.workflow_pipeline = SOWWorkflowPipeline()
        self.sow_manager = SOWAnalysisManager()
        self.email_notifier = SOWEmailNotifier()
        
        # Configuration
        self.config = self._load_config()
        
        logger.info("SOW Workflow Orchestrator initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or config file"""
        return {
            'email_recipients': os.getenv('EMAIL_RECIPIENTS', '').split(','),
            'auto_process_enabled': os.getenv('AUTO_PROCESS_ENABLED', 'false').lower() == 'true',
            'daily_summary_enabled': os.getenv('DAILY_SUMMARY_ENABLED', 'true').lower() == 'true',
            'deadline_alerts_enabled': os.getenv('DEADLINE_ALERTS_ENABLED', 'true').lower() == 'true',
            'deadline_alert_days': int(os.getenv('DEADLINE_ALERT_DAYS', '7')),
            'processing_interval_minutes': int(os.getenv('PROCESSING_INTERVAL_MINUTES', '60')),
            'watch_directory': os.getenv('WATCH_DIRECTORY', './documents/manual_uploads'),
            'supported_extensions': ['.pdf', '.doc', '.docx']
        }
    
    def process_sow_documents(self, notice_id: str, document_paths: List[str], 
                            send_notifications: bool = True) -> Dict[str, Any]:
        """Process SOW documents through the complete pipeline"""
        try:
            logger.info(f"Starting SOW processing for {notice_id}")
            
            # Step 1: Process documents through workflow
            analysis_id = self.workflow_pipeline.process_sow_documents(notice_id, document_paths)
            
            # Step 2: Get processed data
            sow_data = self.sow_manager.get_sow_analysis(notice_id)
            
            if not sow_data:
                raise ValueError(f"SOW data not found for {notice_id}")
            
            # Step 3: Send notifications if enabled
            if send_notifications and self.config['email_recipients']:
                self._send_processing_notifications(notice_id, analysis_id, sow_data)
            
            # Step 4: Log processing completion
            self._log_processing_completion(notice_id, analysis_id, len(document_paths))
            
            return {
                'success': True,
                'notice_id': notice_id,
                'analysis_id': analysis_id,
                'processed_documents': len(document_paths),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SOW processing failed for {notice_id}: {e}")
            return {
                'success': False,
                'notice_id': notice_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_processing_notifications(self, notice_id: str, analysis_id: str, 
                                     sow_data: Dict[str, Any]):
        """Send processing completion notifications"""
        try:
            # Send SOW analysis notification
            self.email_notifier.send_sow_analysis_notification(
                notice_id=notice_id,
                analysis_id=analysis_id,
                recipients=self.config['email_recipients'],
                sow_data=sow_data['sow_payload']
            )
            
            logger.info(f"Notifications sent for {notice_id}")
            
        except Exception as e:
            logger.error(f"Error sending notifications for {notice_id}: {e}")
    
    def _log_processing_completion(self, notice_id: str, analysis_id: str, 
                                 document_count: int):
        """Log processing completion"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'notice_id': notice_id,
            'analysis_id': analysis_id,
            'document_count': document_count,
            'status': 'completed'
        }
        
        # Log to file
        log_file = Path('logs/sow_processing.log')
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def run_daily_summary(self):
        """Run daily summary job"""
        try:
            if not self.config['daily_summary_enabled']:
                return
            
            logger.info("Running daily summary job")
            
            self.email_notifier.send_daily_summary(self.config['email_recipients'])
            
            logger.info("Daily summary job completed")
            
        except Exception as e:
            logger.error(f"Daily summary job failed: {e}")
    
    def run_deadline_alerts(self):
        """Run deadline alerts job"""
        try:
            if not self.config['deadline_alerts_enabled']:
                return
            
            logger.info("Running deadline alerts job")
            
            self.email_notifier.send_upcoming_deadlines_alert(
                recipients=self.config['email_recipients'],
                days_ahead=self.config['deadline_alert_days']
            )
            
            logger.info("Deadline alerts job completed")
            
        except Exception as e:
            logger.error(f"Deadline alerts job failed: {e}")
    
    def run_auto_processing(self):
        """Run auto processing job"""
        try:
            if not self.config['auto_process_enabled']:
                return
            
            logger.info("Running auto processing job")
            
            # Watch directory for new documents
            watch_dir = Path(self.config['watch_directory'])
            if not watch_dir.exists():
                logger.warning(f"Watch directory does not exist: {watch_dir}")
                return
            
            # Find new documents
            new_documents = self._find_new_documents(watch_dir)
            
            if not new_documents:
                logger.info("No new documents found")
                return
            
            # Process new documents
            for notice_id, doc_paths in new_documents.items():
                self.process_sow_documents(notice_id, doc_paths)
            
            logger.info(f"Auto processing completed: {len(new_documents)} SOWs processed")
            
        except Exception as e:
            logger.error(f"Auto processing job failed: {e}")
    
    def _find_new_documents(self, watch_dir: Path) -> Dict[str, List[str]]:
        """Find new documents in watch directory"""
        new_documents = {}
        
        try:
            # Get all supported files
            supported_files = []
            for ext in self.config['supported_extensions']:
                supported_files.extend(watch_dir.glob(f"*{ext}"))
            
            # Group by notice_id (extracted from filename)
            for file_path in supported_files:
                # Extract notice_id from filename (assuming format: notice_id_document.pdf)
                filename = file_path.stem
                if '_' in filename:
                    notice_id = filename.split('_')[0]
                else:
                    notice_id = filename
                
                if notice_id not in new_documents:
                    new_documents[notice_id] = []
                
                new_documents[notice_id].append(str(file_path))
            
            return new_documents
            
        except Exception as e:
            logger.error(f"Error finding new documents: {e}")
            return {}
    
    def start_scheduler(self):
        """Start the scheduled jobs"""
        try:
            logger.info("Starting SOW workflow scheduler")
            
            # Schedule daily summary (9 AM)
            schedule.every().day.at("09:00").do(self.run_daily_summary)
            
            # Schedule deadline alerts (8 AM)
            schedule.every().day.at("08:00").do(self.run_deadline_alerts)
            
            # Schedule auto processing
            schedule.every(self.config['processing_interval_minutes']).minutes.do(self.run_auto_processing)
            
            # Run scheduler in background thread
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("SOW workflow scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        try:
            # Get database connection status
            db_status = "connected"
            try:
                conn = get_db_connection()
                conn.close()
            except:
                db_status = "disconnected"
            
            # Get recent processing stats
            recent_stats = self._get_recent_processing_stats()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'database_status': db_status,
                'auto_processing_enabled': self.config['auto_process_enabled'],
                'daily_summary_enabled': self.config['daily_summary_enabled'],
                'deadline_alerts_enabled': self.config['deadline_alerts_enabled'],
                'email_recipients_count': len(self.config['email_recipients']),
                'recent_processing': recent_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def _get_recent_processing_stats(self) -> Dict[str, Any]:
        """Get recent processing statistics"""
        try:
            # Get stats from database
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Last 24 hours
                cursor.execute("""
                    SELECT COUNT(*) as processed_24h
                    FROM sow_analysis
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                processed_24h = cursor.fetchone()[0]
                
                # Last 7 days
                cursor.execute("""
                    SELECT COUNT(*) as processed_7d
                    FROM sow_analysis
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                processed_7d = cursor.fetchone()[0]
                
                # Total active
                cursor.execute("""
                    SELECT COUNT(*) as total_active
                    FROM sow_analysis
                    WHERE is_active = true
                """)
                total_active = cursor.fetchone()[0]
                
                return {
                    'processed_24h': processed_24h,
                    'processed_7d': processed_7d,
                    'total_active': total_active
                }
                
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {}

def main():
    """Main function for running the orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SOW Workflow Orchestrator')
    parser.add_argument('--mode', choices=['process', 'scheduler', 'status'], 
                       default='status', help='Operation mode')
    parser.add_argument('--notice-id', help='Notice ID for processing mode')
    parser.add_argument('--documents', nargs='+', help='Document paths for processing mode')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = SOWWorkflowOrchestrator()
    
    if args.mode == 'process':
        if not args.notice_id or not args.documents:
            print("Error: --notice-id and --documents are required for process mode")
            return
        
        result = orchestrator.process_sow_documents(args.notice_id, args.documents)
        print(json.dumps(result, indent=2))
        
    elif args.mode == 'scheduler':
        print("Starting SOW workflow scheduler...")
        orchestrator.start_scheduler()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Scheduler stopped")
            
    elif args.mode == 'status':
        status = orchestrator.get_system_status()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
