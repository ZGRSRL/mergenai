#!/usr/bin/env python3
"""
Email Reporter Module for SOW Analysis System
Handles PDF report generation and email sending
"""

import os
import smtplib
import tempfile
from pathlib import Path
from email.message import EmailMessage
from typing import List, Dict, Any
import logging

# Database imports
import sys
sys.path.append('./sam/document_management')
try:
    from database_manager import execute_query
except ImportError as e:
    print(f"Warning: Could not import database_manager: {e}")
    # Create mock function for fallback
    def execute_query(query, params=None, fetch='all'):
        return []

logger = logging.getLogger(__name__)

def make_pdf_summary(naics: str, days: int) -> Path:
    """
    Create a simple PDF summary report
    
    Args:
        naics: NAICS code for filtering
        days: Number of days to look back
        
    Returns:
        Path to the generated PDF file
    """
    try:
        # Create temporary PDF file
        tmp = Path(tempfile.gettempdir()) / f"sow_report_{naics}_{days}d.pdf"
        
        # Simple PDF content (in production, use a proper PDF library)
        with open(tmp, "wb") as f:
            # Basic PDF header
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj\n")
            f.write(b"<<\n")
            f.write(b"/Type /Catalog\n")
            f.write(b"/Pages 2 0 R\n")
            f.write(b">>\n")
            f.write(b"endobj\n")
            f.write(b"2 0 obj\n")
            f.write(b"<<\n")
            f.write(b"/Type /Pages\n")
            f.write(b"/Kids [3 0 R]\n")
            f.write(b"/Count 1\n")
            f.write(b">>\n")
            f.write(b"endobj\n")
            f.write(b"3 0 obj\n")
            f.write(b"<<\n")
            f.write(b"/Type /Page\n")
            f.write(b"/Parent 2 0 R\n")
            f.write(b"/MediaBox [0 0 612 792]\n")
            f.write(b"/Contents 4 0 R\n")
            f.write(b">>\n")
            f.write(b"endobj\n")
            f.write(b"4 0 obj\n")
            f.write(b"<<\n")
            f.write(b"/Length 100\n")
            f.write(b">>\n")
            f.write(b"stream\n")
            f.write(b"BT\n")
            f.write(b"/F1 12 Tf\n")
            f.write(b"72 720 Td\n")
            f.write(f"(Contract Opportunities SOW Summary - NAICS {naics}, Last {days} days)".encode('utf-8'))
            f.write(b" Tj\n")
            f.write(b"ET\n")
            f.write(b"endstream\n")
            f.write(b"endobj\n")
            f.write(b"xref\n")
            f.write(b"0 5\n")
            f.write(b"0000000000 65535 f \n")
            f.write(b"0000000009 00000 n \n")
            f.write(b"0000000058 00000 n \n")
            f.write(b"0000000115 00000 n \n")
            f.write(b"0000000274 00000 n \n")
            f.write(b"trailer\n")
            f.write(b"<<\n")
            f.write(b"/Size 5\n")
            f.write(b"/Root 1 0 R\n")
            f.write(b">>\n")
            f.write(b"startxref\n")
            f.write(b"400\n")
            f.write(b"%%EOF\n")
        
        logger.info(f"PDF summary created: {tmp}")
        return tmp
        
    except Exception as e:
        logger.error(f"PDF creation failed: {e}")
        # Fallback: create a simple text file
        tmp = Path(tempfile.gettempdir()) / f"sow_report_{naics}_{days}d.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"Contract Opportunities SOW Summary\n")
            f.write(f"NAICS: {naics}\n")
            f.write(f"Period: Last {days} days\n")
            f.write(f"Generated: {os.popen('date').read().strip()}\n")
        return tmp

def build_body(naics: str, days: int) -> str:
    """
    Build email body with opportunity summary
    
    Args:
        naics: NAICS code for filtering
        days: Number of days to look back
        
    Returns:
        Email body text
    """
    try:
        # Query opportunities from database
        q = """
            SELECT notice_id, title, posted_at
            FROM opportunities
            WHERE naics = %s AND posted_at >= (now()::date - INTERVAL '%s days')
            ORDER BY posted_at DESC
            LIMIT 50
        """
        rows = execute_query(q, (naics, days), fetch=True)
        
        lines = [f"{len(rows)} kayit bulundu (NAICS={naics}, last {days}d):"]
        for r in rows:
            lines.append(f"- {r[0]} • {r[1]} • {r[2]}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return f"Database query failed: {e}"

def send_daily_sow_report(host: str, port: int, user: str, pwd: str, 
                         recipients: List[str], naics: str, days: int) -> bool:
    """
    Send daily SOW report via email
    
    Args:
        host: SMTP host
        port: SMTP port
        user: SMTP username
        pwd: SMTP password
        recipients: List of recipient email addresses
        naics: NAICS code for filtering
        days: Number of days to look back
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create PDF report
        pdf_path = make_pdf_summary(naics, days)
        
        # Build email body
        body = build_body(naics, days)
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = f"SOW Daily Report (NAICS {naics}, last {days}d)"
        msg["From"] = user
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)
        
        # Add PDF attachment
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(), 
                maintype="application", 
                subtype="pdf", 
                filename=pdf_path.name
            )
        
        # Send email
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        
        logger.info(f"Daily report sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

def send_custom_report(host: str, port: int, user: str, pwd: str,
                      recipients: List[str], subject: str, body: str,
                      attachments: List[Path] = None) -> bool:
    """
    Send custom email report
    
    Args:
        host: SMTP host
        port: SMTP port
        user: SMTP username
        pwd: SMTP password
        recipients: List of recipient email addresses
        subject: Email subject
        body: Email body
        attachments: List of file paths to attach
        
    Returns:
        True if successful, False otherwise
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                if attachment.exists():
                    with open(attachment, "rb") as f:
                        msg.add_attachment(
                            f.read(),
                            maintype="application",
                            subtype="octet-stream",
                            filename=attachment.name
                        )
        
        # Send email
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        
        logger.info(f"Custom report sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Custom email sending failed: {e}")
        return False

def get_opportunity_summary(naics: str = None, days: int = 7) -> Dict[str, Any]:
    """
    Get opportunity summary statistics
    
    Args:
        naics: NAICS code for filtering (optional)
        days: Number of days to look back
        
    Returns:
        Dictionary with summary statistics
    """
    try:
        # Build query
        if naics:
            q = """
                SELECT 
                    COUNT(*) as total_opportunities,
                    COUNT(DISTINCT naics) as unique_naics,
                    MIN(posted_at) as earliest_posted,
                    MAX(posted_at) as latest_posted
                FROM opportunities
                WHERE naics = %s AND posted_at >= (now()::date - INTERVAL '%s days')
            """
            params = (naics, days)
        else:
            q = """
                SELECT 
                    COUNT(*) as total_opportunities,
                    COUNT(DISTINCT naics) as unique_naics,
                    MIN(posted_at) as earliest_posted,
                    MAX(posted_at) as latest_posted
                FROM opportunities
                WHERE posted_at >= (now()::date - INTERVAL '%s days')
            """
            params = (days,)
        
        rows = execute_query(q, params, fetch=True)
        
        if rows:
            row = rows[0]
            return {
                "total_opportunities": row[0],
                "unique_naics": row[1],
                "earliest_posted": row[2],
                "latest_posted": row[3],
                "period_days": days,
                "naics_filter": naics
            }
        else:
            return {
                "total_opportunities": 0,
                "unique_naics": 0,
                "earliest_posted": None,
                "latest_posted": None,
                "period_days": days,
                "naics_filter": naics
            }
            
    except Exception as e:
        logger.error(f"Summary query failed: {e}")
        return {
            "error": str(e),
            "total_opportunities": 0,
            "unique_naics": 0,
            "earliest_posted": None,
            "latest_posted": None,
            "period_days": days,
            "naics_filter": naics
        }

def test_email_configuration(host: str, port: int, user: str, pwd: str) -> bool:
    """
    Test email configuration
    
    Args:
        host: SMTP host
        port: SMTP port
        user: SMTP username
        pwd: SMTP password
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
        
        logger.info("Email configuration test successful")
        return True
        
    except Exception as e:
        logger.error(f"Email configuration test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the module
    print("Testing Email Reporter Module...")
    
    # Test PDF creation
    pdf_path = make_pdf_summary("721110", 7)
    print(f"PDF created: {pdf_path}")
    
    # Test summary
    summary = get_opportunity_summary("721110", 7)
    print(f"Summary: {summary}")
    
    print("Email Reporter Module test completed!")
