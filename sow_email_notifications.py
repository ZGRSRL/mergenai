#!/usr/bin/env python3
"""
SOW Email Notification System
Automated email notifications for SOW analysis results
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

# Local imports
import sys
sys.path.append('./sam/document_management')
from database_manager import DatabaseManager, execute_query

logger = logging.getLogger(__name__)

class SOWEmailNotifier:
    """Email notification system for SOW analysis"""
    
    def __init__(self):
        self.smtp_config = self._get_smtp_config()
        self.db_manager = DatabaseManager()
        logger.info("SOW Email Notifier initialized")
    
    def _get_smtp_config(self) -> Dict[str, str]:
        """Get SMTP configuration"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@zgr-sam.com'),
            'from_name': os.getenv('FROM_NAME', 'ZGR SAM System')
        }
    
    def send_hotel_alert(self, notice_id: str, hotel_results: List[Dict[str, Any]], 
                        recipients: List[str]) -> bool:
        """Send hotel alert for high-quality matches"""
        try:
            # Filter high-quality matches
            high_quality = [h for h in hotel_results if h.get('match_score', 0) >= 0.9 and h.get('distance_km', 999) <= 3.0]
            
            if not high_quality:
                return False
                
            # Create email content
            subject = f"🏨 Hotel Alert - {notice_id} - {len(high_quality)} High-Quality Matches"
            
            html_content = f"""
            <html>
            <body>
                <h2>🏨 Hotel Alert - Notice {notice_id}</h2>
                <p>Found {len(high_quality)} high-quality hotel matches:</p>
                <ul>
            """
            
            for hotel in high_quality:
                html_content += f"""
                    <li>
                        <strong>{hotel.get('name', 'N/A')}</strong><br>
                        📍 {hotel.get('distance_km', 0):.1f} km • ⭐ {hotel.get('match_score', 0):.2f}<br>
                        📞 {hotel.get('phone', 'N/A')} • 🌐 {hotel.get('website', 'N/A')}<br>
                        📍 {hotel.get('address', 'N/A')}
                    </li>
                """
            
            html_content += """
                </ul>
                <p>Please review these options for your proposal.</p>
            </body>
            </html>
            """
            
            # Send email
            return self._send_email(recipients, subject, html_content)
            
        except Exception as e:
            logger.error(f"Hotel alert email failed: {e}")
            return False

    def send_sow_analysis_notification(self, notice_id: str, analysis_id: str, 
                                     recipients: List[str], 
                                     sow_data: Dict[str, Any]) -> bool:
        """Send SOW analysis completion notification"""
        try:
            # Create email content
            subject = f"SOW Analysis Completed - {notice_id}"
            html_content = self._create_sow_analysis_html(notice_id, analysis_id, sow_data)
            text_content = self._create_sow_analysis_text(notice_id, analysis_id, sow_data)
            
            # Send email
            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending SOW analysis notification: {e}")
            return False
    
    def send_daily_summary(self, recipients: List[str]) -> bool:
        """Send daily SOW summary"""
        try:
            # Get daily summary data
            summary_data = self._get_daily_summary()
            
            subject = f"Daily SOW Summary - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._create_daily_summary_html(summary_data)
            text_content = self._create_daily_summary_text(summary_data)
            
            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
    
    def send_upcoming_deadlines_alert(self, recipients: List[str], days_ahead: int = 7) -> bool:
        """Send upcoming deadlines alert"""
        try:
            # Get upcoming deadlines
            upcoming_data = self._get_upcoming_deadlines(days_ahead)
            
            if not upcoming_data:
                logger.info("No upcoming deadlines found")
                return True
            
            subject = f"Upcoming SOW Deadlines - Next {days_ahead} Days"
            html_content = self._create_upcoming_deadlines_html(upcoming_data, days_ahead)
            text_content = self._create_upcoming_deadlines_text(upcoming_data, days_ahead)
            
            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending upcoming deadlines alert: {e}")
            return False
    
    def _create_sow_analysis_html(self, notice_id: str, analysis_id: str, 
                                sow_data: Dict[str, Any]) -> str:
        """Create HTML content for SOW analysis notification"""
        
        # Extract key information
        period = sow_data.get('period_of_performance', 'N/A')
        setup_deadline = sow_data.get('setup_deadline', 'N/A')
        capacity = sow_data.get('function_space', {}).get('general_session', {}).get('capacity', 'N/A')
        breakout_rooms = sow_data.get('function_space', {}).get('breakout_rooms', {}).get('count', 'N/A')
        rooms_per_night = sow_data.get('room_block', {}).get('total_rooms_per_night', 'N/A')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2E86AB; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .section {{ margin: 15px 0; padding: 15px; border-left: 4px solid #2E86AB; background-color: #f8f9fa; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-label {{ font-weight: bold; color: #666; }}
                .metric-value {{ font-size: 18px; color: #2E86AB; }}
                .footer {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 SOW Analysis Completed</h1>
                <p>Analysis ID: {analysis_id}</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h3>📋 Basic Information</h3>
                    <p><strong>Notice ID:</strong> {notice_id}</p>
                    <p><strong>Period of Performance:</strong> {period}</p>
                    <p><strong>Setup Deadline:</strong> {setup_deadline}</p>
                </div>
                
                <div class="section">
                    <h3>🏨 Accommodation Details</h3>
                    <div class="metric">
                        <div class="metric-label">Rooms per Night</div>
                        <div class="metric-value">{rooms_per_night}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>🏢 Function Space Requirements</h3>
                    <div class="metric">
                        <div class="metric-label">General Session Capacity</div>
                        <div class="metric-value">{capacity}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Breakout Rooms</div>
                        <div class="metric-value">{breakout_rooms}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📊 Analysis Summary</h3>
                    <p>The SOW analysis has been successfully completed and stored in the database. 
                    You can view detailed information in the SOW Dashboard or through the API.</p>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>ZGR SAM Document Management System</strong></p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_sow_analysis_text(self, notice_id: str, analysis_id: str, 
                                sow_data: Dict[str, Any]) -> str:
        """Create text content for SOW analysis notification"""
        
        period = sow_data.get('period_of_performance', 'N/A')
        setup_deadline = sow_data.get('setup_deadline', 'N/A')
        capacity = sow_data.get('function_space', {}).get('general_session', {}).get('capacity', 'N/A')
        breakout_rooms = sow_data.get('function_space', {}).get('breakout_rooms', {}).get('count', 'N/A')
        rooms_per_night = sow_data.get('room_block', {}).get('total_rooms_per_night', 'N/A')
        
        text = f"""
SOW Analysis Completed

Notice ID: {notice_id}
Analysis ID: {analysis_id}

Basic Information:
- Period of Performance: {period}
- Setup Deadline: {setup_deadline}

Accommodation Details:
- Rooms per Night: {rooms_per_night}

Function Space Requirements:
- General Session Capacity: {capacity}
- Breakout Rooms: {breakout_rooms}

The SOW analysis has been successfully completed and stored in the database.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ZGR SAM Document Management System
        """
        
        return text
    
    def _create_daily_summary_html(self, summary_data: Dict[str, Any]) -> str:
        """Create HTML content for daily summary"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2E86AB; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                .metric-label {{ font-weight: bold; color: #666; }}
                .metric-value {{ font-size: 24px; color: #2E86AB; }}
                .footer {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily SOW Summary</h1>
                <p>{datetime.now().strftime('%Y-%m-%d')}</p>
            </div>
            
            <div class="content">
                <div class="metric">
                    <div class="metric-label">Total SOWs</div>
                    <div class="metric-value">{summary_data.get('total_sows', 0)}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">New Today</div>
                    <div class="metric-value">{summary_data.get('new_today', 0)}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Avg Capacity</div>
                    <div class="metric-value">{summary_data.get('avg_capacity', 0):.0f}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Total Room Nights</div>
                    <div class="metric-value">{summary_data.get('total_room_nights', 0):,}</div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>ZGR SAM Document Management System</strong></p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_daily_summary_text(self, summary_data: Dict[str, Any]) -> str:
        """Create text content for daily summary"""
        
        text = f"""
Daily SOW Summary - {datetime.now().strftime('%Y-%m-%d')}

Total SOWs: {summary_data.get('total_sows', 0)}
New Today: {summary_data.get('new_today', 0)}
Average Capacity: {summary_data.get('avg_capacity', 0):.0f}
Total Room Nights: {summary_data.get('total_room_nights', 0):,}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ZGR SAM Document Management System
        """
        
        return text
    
    def _create_upcoming_deadlines_html(self, upcoming_data: List[Dict[str, Any]], 
                                      days_ahead: int) -> str:
        """Create HTML content for upcoming deadlines"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #FF6B6B; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .deadline {{ margin: 15px 0; padding: 15px; border-left: 4px solid #FF6B6B; background-color: #fff5f5; }}
                .footer {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ Upcoming SOW Deadlines</h1>
                <p>Next {days_ahead} Days</p>
            </div>
            
            <div class="content">
        """
        
        for item in upcoming_data:
            html += f"""
                <div class="deadline">
                    <h3>{item['notice_id']}</h3>
                    <p><strong>Period:</strong> {item['period']}</p>
                    <p><strong>Setup Deadline:</strong> {item['setup_deadline_ts']}</p>
                    <p><strong>Days Remaining:</strong> {item['days_remaining']}</p>
                </div>
            """
        
        html += f"""
            </div>
            
            <div class="footer">
                <p><strong>ZGR SAM Document Management System</strong></p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_upcoming_deadlines_text(self, upcoming_data: List[Dict[str, Any]], 
                                      days_ahead: int) -> str:
        """Create text content for upcoming deadlines"""
        
        text = f"""
Upcoming SOW Deadlines - Next {days_ahead} Days

"""
        
        for item in upcoming_data:
            text += f"""
{item['notice_id']}
- Period: {item['period']}
- Setup Deadline: {item['setup_deadline_ts']}
- Days Remaining: {item['days_remaining']}

"""
        
        text += f"""
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ZGR SAM Document Management System
        """
        
        return text
    
    def _get_daily_summary(self) -> Dict[str, Any]:
        """Get daily summary data from database"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_sows,
                    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as new_today,
                    AVG((sow_payload #>> '{function_space,general_session,capacity}')::int) as avg_capacity,
                    SUM(((sow_payload #>> '{room_block,total_rooms_per_night}')::int * 
                         (sow_payload #>> '{room_block,nights}')::int)) as total_room_nights
                FROM sow_analysis
                WHERE is_active = true
            """
            
            result = execute_query(query, fetch='one')
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return {}
    
    def _get_upcoming_deadlines(self, days_ahead: int) -> List[Dict[str, Any]]:
        """Get upcoming deadlines from database"""
        try:
            query = """
                SELECT 
                    notice_id,
                    period,
                    setup_deadline_ts,
                    EXTRACT(DAYS FROM (setup_deadline_ts - NOW()))::int as days_remaining
                FROM vw_sow_date_analysis
                WHERE setup_deadline_ts BETWEEN NOW() AND NOW() + INTERVAL '%s days'
                ORDER BY setup_deadline_ts
            """
            
            result = execute_query(query, (days_ahead,), fetch='all')
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines: {e}")
            return []
    
    def _send_email(self, recipients: List[str], subject: str, 
                   html_content: str, text_content: str) -> bool:
        """Send email to recipients"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

def test_email_notifications():
    """Test email notification system"""
    print("Testing SOW Email Notifications...")
    print("=" * 50)
    
    # Initialize notifier
    notifier = SOWEmailNotifier()
    
    # Test recipients (replace with actual email addresses)
    test_recipients = ["test@example.com"]
    
    # Test SOW analysis notification
    print("[TEST] Sending SOW analysis notification...")
    mock_sow_data = {
        "period_of_performance": "2025-02-25 to 2025-02-27",
        "setup_deadline": "2025-02-24T18:00:00Z",
        "function_space": {
            "general_session": {"capacity": 120},
            "breakout_rooms": {"count": 4}
        },
        "room_block": {"total_rooms_per_night": 120}
    }
    
    success = notifier.send_sow_analysis_notification(
        "70LART26QPFB00001", 
        "test-analysis-123", 
        test_recipients, 
        mock_sow_data
    )
    
    if success:
        print("[SUCCESS] SOW analysis notification sent")
    else:
        print("[ERROR] Failed to send SOW analysis notification")
    
    # Test daily summary
    print("\n[TEST] Sending daily summary...")
    success = notifier.send_daily_summary(test_recipients)
    
    if success:
        print("[SUCCESS] Daily summary sent")
    else:
        print("[ERROR] Failed to send daily summary")
    
    # Test upcoming deadlines
    print("\n[TEST] Sending upcoming deadlines alert...")
    success = notifier.send_upcoming_deadlines_alert(test_recipients, 7)
    
    if success:
        print("[SUCCESS] Upcoming deadlines alert sent")
    else:
        print("[ERROR] Failed to send upcoming deadlines alert")
    
    print(f"\n[COMPLETE] Email notification test completed!")

if __name__ == "__main__":
    test_email_notifications()
