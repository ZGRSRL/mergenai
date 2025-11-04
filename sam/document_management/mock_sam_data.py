#!/usr/bin/env python3
"""
Mock SAM data for testing when API key is not available
"""

import json
from datetime import datetime, timedelta

def get_mock_opportunity_data(notice_id: str):
    """Return mock opportunity data for testing"""
    
    mock_data = {
        "70LART26QPFB00001": {
            "opportunityId": "70LART26QPFB00001",
            "title": "Off-Center Lodging, FLETC Artesia",
            "description": "The Federal Law Enforcement Training Centers (FLETC) requires lodging services for training participants at the Artesia, New Mexico facility.",
            "postedDate": "2024-10-15T00:00:00Z",
            "responseDeadLine": "2024-11-15T17:00:00Z",
            "naicsCode": "721110",
            "classificationCode": "R",
            "setAside": "8(a) Set-Aside",
            "contractType": "Fixed Price",
            "placeOfPerformance": "Artesia, NM 88210",
            "organizationType": "Federal Agency",
            "agency": "Department of Homeland Security",
            "fullParentPathName": "Department of Homeland Security > Federal Law Enforcement Training Centers",
            "pointOfContact": {
                "name": "John Smith",
                "email": "john.smith@fletc.dhs.gov",
                "phone": "(505) 555-0123"
            },
            "estimatedValue": 45000.00,
            "solicitationNumber": "70LART26QPFB00001",
            "type": "Solicitation",
            "status": "Active",
            "awardNumber": None,
            "attachments": [
                {
                    "filename": "SOW_70LART26QPFB00001.pdf",
                    "description": "Statement of Work",
                    "url": "https://sam.gov/api/prod/attachments/12345"
                },
                {
                    "filename": "Requirements_70LART26QPFB00001.pdf", 
                    "description": "Detailed Requirements",
                    "url": "https://sam.gov/api/prod/attachments/12346"
                }
            ]
        },
        "140D0424P0066": {
            "opportunityId": "140D0424P0066",
            "title": "Hotel Accommodation Services for Training Events",
            "description": "The Department of Defense requires hotel accommodation services for various training events and conferences.",
            "postedDate": "2024-10-10T00:00:00Z",
            "responseDeadLine": "2024-11-10T15:00:00Z",
            "naicsCode": "721110",
            "classificationCode": "R",
            "setAside": "Small Business Set-Aside",
            "contractType": "Fixed Price",
            "placeOfPerformance": "Washington, DC",
            "organizationType": "Federal Agency",
            "agency": "Department of Defense",
            "fullParentPathName": "Department of Defense > Defense Logistics Agency",
            "pointOfContact": {
                "name": "Jane Doe",
                "email": "jane.doe@dla.mil",
                "phone": "(703) 555-0456"
            },
            "estimatedValue": 125000.00,
            "solicitationNumber": "140D0424P0066",
            "type": "Solicitation",
            "status": "Active",
            "awardNumber": None,
            "attachments": [
                {
                    "filename": "RFP_140D0424P0066.pdf",
                    "description": "Request for Proposal",
                    "url": "https://sam.gov/api/prod/attachments/12347"
                }
            ]
        },
        "HC101325QA399": {
            "opportunityId": "HC101325QA399",
            "title": "Conference Center and Meeting Room Services",
            "description": "Health and Human Services requires conference center and meeting room services for upcoming healthcare conferences.",
            "postedDate": "2024-10-05T00:00:00Z",
            "responseDeadLine": "2024-11-05T12:00:00Z",
            "naicsCode": "721110",
            "classificationCode": "R",
            "setAside": "Service-Disabled Veteran-Owned Small Business",
            "contractType": "Fixed Price",
            "placeOfPerformance": "Atlanta, GA",
            "organizationType": "Federal Agency",
            "agency": "Department of Health and Human Services",
            "fullParentPathName": "Department of Health and Human Services > Centers for Disease Control and Prevention",
            "pointOfContact": {
                "name": "Dr. Michael Johnson",
                "email": "michael.johnson@cdc.gov",
                "phone": "(404) 555-0789"
            },
            "estimatedValue": 75000.00,
            "solicitationNumber": "HC101325QA399",
            "type": "Solicitation",
            "status": "Active",
            "awardNumber": None,
            "attachments": [
                {
                    "filename": "SOW_HC101325QA399.pdf",
                    "description": "Statement of Work",
                    "url": "https://sam.gov/api/prod/attachments/12348"
                },
                {
                    "filename": "Technical_Requirements_HC101325QA399.pdf",
                    "description": "Technical Requirements",
                    "url": "https://sam.gov/api/prod/attachments/12349"
                }
            ]
        }
    }
    
    return mock_data.get(notice_id, None)

def get_mock_analysis_result(notice_id: str):
    """Return mock analysis result for testing"""
    
    mock_analysis = {
        "70LART26QPFB00001": {
            "opportunity_id": notice_id,
            "status": "success",
            "confidence_score": 0.92,
            "go_no_go_score": 8.5,
            "risk_level": "low",
            "priority_score": 85,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_result": {
                "summary": "This is an excellent opportunity for hotel and lodging services. The requirements are clear, the budget is reasonable, and the timeline is achievable. Strong recommendation to proceed.",
                "requirements": [
                    "Minimum 50 guest rooms available",
                    "Conference facilities for 100+ attendees",
                    "24/7 front desk service",
                    "Catering services for training events",
                    "Parking for 75+ vehicles"
                ],
                "risks": [
                    "Tight timeline for proposal submission",
                    "Competition from established local hotels"
                ],
                "missing_items": [
                    "Detailed floor plans of conference facilities",
                    "Pricing breakdown for additional services"
                ],
                "action_items": [
                    "Prepare detailed capability statement",
                    "Gather past performance references",
                    "Develop competitive pricing strategy",
                    "Schedule site visit if possible"
                ],
                "qa_pairs": [
                    {
                        "question": "What is the minimum room block requirement?",
                        "answer": "The solicitation requires a minimum of 50 guest rooms to be available for the training period."
                    },
                    {
                        "question": "Are there any specific accessibility requirements?",
                        "answer": "Yes, the facility must comply with ADA requirements and have accessible rooms and conference facilities."
                    }
                ]
            },
            "recommendations": [
                "Submit proposal within 2 weeks",
                "Emphasize experience with government contracts",
                "Highlight conference facility capabilities",
                "Include competitive pricing"
            ]
        }
    }
    
    return mock_analysis.get(notice_id, {
        "opportunity_id": notice_id,
        "status": "failed",
        "error": "No mock data available for this opportunity ID",
        "analysis_timestamp": datetime.now().isoformat()
    })
