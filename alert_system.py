#!/usr/bin/env python3
"""
Alert System - Production monitoring and alerting
"""

import os
import json
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

@dataclass
class AlertConfig:
    """Alert configuration"""
    success_rate_threshold: float = 80.0
    processing_time_threshold: float = 15.0
    api_error_threshold: int = 5
    check_interval_minutes: int = 5
    email_enabled: bool = True
    slack_enabled: bool = False

@dataclass
class Alert:
    """Alert data structure"""
    alert_type: str
    severity: str  # critical, warning, info
    message: str
    timestamp: str
    metrics: Dict[str, Any]
    resolved: bool = False

class AlertSystem:
    """Production alert system"""
    
    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self.logger = logging.getLogger("AlertSystem")
        self.alerts: List[Alert] = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def check_success_rate(self) -> Optional[Alert]:
        """Check success rate threshold"""
        try:
            from agent_log_manager import get_agent_stats
            
            stats = get_agent_stats()
            success_rate = stats.get('success_rate', 0)
            
            if success_rate < self.config.success_rate_threshold:
                alert = Alert(
                    alert_type="success_rate",
                    severity="critical" if success_rate < 50 else "warning",
                    message=f"Success rate below threshold: {success_rate:.1f}% < {self.config.success_rate_threshold}%",
                    timestamp=datetime.now().isoformat(),
                    metrics={"success_rate": success_rate, "threshold": self.config.success_rate_threshold}
                )
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking success rate: {e}")
            return None
    
    def check_processing_time(self) -> Optional[Alert]:
        """Check processing time threshold"""
        try:
            from agent_log_manager import get_agent_stats
            
            stats = get_agent_stats()
            avg_time = stats.get('avg_processing_time', 0)
            
            if avg_time > self.config.processing_time_threshold:
                alert = Alert(
                    alert_type="processing_time",
                    severity="warning",
                    message=f"Average processing time too high: {avg_time:.1f}s > {self.config.processing_time_threshold}s",
                    timestamp=datetime.now().isoformat(),
                    metrics={"avg_processing_time": avg_time, "threshold": self.config.processing_time_threshold}
                )
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking processing time: {e}")
            return None
    
    def check_api_health(self) -> Optional[Alert]:
        """Check API health (error rate)"""
        try:
            from agent_log_manager import get_recent_actions
            
            recent_actions = get_recent_actions(50)  # Last 50 actions
            
            if not recent_actions:
                return None
            
            # Count errors in recent actions
            error_count = len([action for action in recent_actions if action.get('status') == 'error'])
            total_actions = len(recent_actions)
            error_rate = (error_count / total_actions) * 100 if total_actions > 0 else 0
            
            if error_count >= self.config.api_error_threshold:
                alert = Alert(
                    alert_type="api_health",
                    severity="critical" if error_rate > 50 else "warning",
                    message=f"High error rate detected: {error_count} errors in last {total_actions} actions ({error_rate:.1f}%)",
                    timestamp=datetime.now().isoformat(),
                    metrics={"error_count": error_count, "total_actions": total_actions, "error_rate": error_rate}
                )
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking API health: {e}")
            return None
    
    def check_termination_metrics(self) -> Optional[Alert]:
        """Check AutoGen termination metrics"""
        try:
            from agent_log_manager import get_termination_metrics
            
            metrics = get_termination_metrics()
            stop_rate = metrics.get('stop_rate', 0)
            
            if stop_rate < 80:  # Less than 80% proper STOP termination
                alert = Alert(
                    alert_type="termination_metrics",
                    severity="warning",
                    message=f"Low STOP termination rate: {stop_rate:.1f}% (expected >80%)",
                    timestamp=datetime.now().isoformat(),
                    metrics=metrics
                )
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking termination metrics: {e}")
            return None
    
    def send_email_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.config.email_enabled:
            return False
        
        try:
            # Get email configuration
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('SMTP_FROM_EMAIL', smtp_user)
            to_email = os.getenv('NOTIFICATION_EMAIL', smtp_user)
            
            if not all([smtp_user, smtp_password, to_email]):
                self.logger.warning("Email configuration incomplete, skipping email alert")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"[{alert.severity.upper()}] ZGR SAM System Alert: {alert.alert_type}"
            
            # Create body
            body = f"""
ZGR SAM System Alert

Alert Type: {alert.alert_type}
Severity: {alert.severity.upper()}
Time: {alert.timestamp}

Message: {alert.message}

Metrics:
{json.dumps(alert.metrics, indent=2)}

System: ZGR SAM Document Management
Environment: {os.getenv('ENV', 'unknown')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent for {alert.alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def send_slack_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        if not self.config.slack_enabled:
            return False
        
        try:
            import requests
            
            webhook_url = os.getenv('SLACK_WEBHOOK_URL')
            if not webhook_url:
                return False
            
            # Create Slack message
            color = "danger" if alert.severity == "critical" else "warning" if alert.severity == "warning" else "good"
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"ZGR SAM System Alert: {alert.alert_type}",
                        "text": alert.message,
                        "fields": [
                            {"title": "Severity", "value": alert.severity.upper(), "short": True},
                            {"title": "Time", "value": alert.timestamp, "short": True}
                        ],
                        "footer": "ZGR SAM System",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent for {alert.alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def process_alert(self, alert: Alert) -> None:
        """Process and send alert"""
        self.alerts.append(alert)
        
        # Log alert
        self.logger.warning(f"ALERT [{alert.severity.upper()}] {alert.alert_type}: {alert.message}")
        
        # Send notifications
        email_sent = self.send_email_alert(alert)
        slack_sent = self.send_slack_alert(alert)
        
        if not email_sent and not slack_sent:
            self.logger.error("No alert notifications sent - check configuration")
    
    def run_health_checks(self) -> List[Alert]:
        """Run all health checks"""
        alerts = []
        
        # Check success rate
        alert = self.check_success_rate()
        if alert:
            alerts.append(alert)
        
        # Check processing time
        alert = self.check_processing_time()
        if alert:
            alerts.append(alert)
        
        # Check API health
        alert = self.check_api_health()
        if alert:
            alerts.append(alert)
        
        # Check termination metrics
        alert = self.check_termination_metrics()
        if alert:
            alerts.append(alert)
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        total_alerts = len(self.alerts)
        critical_alerts = len([a for a in self.alerts if a.severity == "critical"])
        warning_alerts = len([a for a in self.alerts if a.severity == "warning"])
        resolved_alerts = len([a for a in self.alerts if a.resolved])
        
        return {
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "resolved_alerts": resolved_alerts,
            "active_alerts": total_alerts - resolved_alerts
        }

# Global alert system instance
alert_system = AlertSystem()

def run_health_checks() -> List[Alert]:
    """Convenience function for running health checks"""
    return alert_system.run_health_checks()

def process_alert(alert: Alert) -> None:
    """Convenience function for processing alerts"""
    alert_system.process_alert(alert)

if __name__ == "__main__":
    # Test the alert system
    print("Testing Alert System...")
    
    # Run health checks
    alerts = run_health_checks()
    
    if alerts:
        print(f"Found {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  - {alert.severity.upper()}: {alert.alert_type} - {alert.message}")
    else:
        print("No alerts found - system healthy!")
    
    # Get summary
    summary = alert_system.get_alert_summary()
    print(f"Alert Summary: {summary}")
    
    print("Alert System test completed!")

