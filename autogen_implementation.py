"""
ZgrBid AutoGen Implementation
Multi-Agent RFQ Analysis and Proposal Generation System
"""

import autogen
from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    RFQ = "rfq"
    SOW = "sow"
    FACILITY = "facility"
    PAST_PERFORMANCE = "past_performance"
    PRICING = "pricing"

@dataclass
class Document:
    id: int
    type: DocumentType
    title: str
    content: str
    metadata: Dict[str, Any]

@dataclass
class Requirement:
    code: str
    text: str
    category: str
    priority: str
    evidence: List[Dict[str, Any]] = None

@dataclass
class ComplianceMatrix:
    requirements: List[Requirement]
    overall_risk: str
    met_count: int
    gap_count: int

class DocumentProcessingAgent:
    """Agent responsible for document processing and text extraction"""
    
    def __init__(self, name: str = "DocumentProcessor"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def process_document(self, document: Document) -> Dict[str, Any]:
        """Process document and extract structured data, download and analyze actual documents"""
        
        # Try to download and analyze actual documents
        downloaded_documents = []
        enhanced_content = document.content or ""
        
        try:
            from document_downloader import DocumentDownloader
            from sam_gov_scraper import SAMGovScraper
            
            downloader = DocumentDownloader()
            scraper = SAMGovScraper()
            
            # Look for document URLs in content
            document_urls = self._extract_document_urls(document.content or "")
            
            # SAM.gov sayfasından belgeleri çek
            opportunity_id = document.metadata.get('opportunity_id', '')
            if opportunity_id and len(opportunity_id) == 32:  # UUID format
                print(f"[DOC_PROCESSOR] SAM.gov sayfasından belgeler çekiliyor: {opportunity_id}")
                sam_documents = scraper.scrape_opportunity_documents(opportunity_id)
                
                for sam_doc in sam_documents:
                    downloaded_documents.append({
                        'url': sam_doc.get('url', ''),
                        'filename': sam_doc['filename'],
                        'content_type': sam_doc['content_type'],
                        'size': sam_doc['size'],
                        'analysis': sam_doc['analysis'],
                        'source': 'SAM.gov'
                    })
                    
                    # Add document content to enhanced content
                    enhanced_content += f"\n\n--- SAM.GOV BELGE: {sam_doc['filename']} ---\n"
                    enhanced_content += sam_doc['analysis']['text_content'][:5000]  # First 5000 chars
                    
                    print(f"[DOC_PROCESSOR] SAM.gov belgesi analiz edildi: {sam_doc['filename']} ({sam_doc['analysis']['word_count']} kelime)")
            
            # Diğer URL'lerden belgeleri indir
            for url in document_urls[:3]:  # Max 3 documents
                try:
                    print(f"[DOC_PROCESSOR] Belge indiriliyor: {url}")
                    doc_result = downloader.download_document(url, document.id)
                    
                    if doc_result:
                        downloaded_documents.append({
                            'url': url,
                            'filename': doc_result['filename'],
                            'content_type': doc_result['content_type'],
                            'size': doc_result['size'],
                            'analysis': doc_result['analysis'],
                            'source': 'URL'
                        })
                        
                        # Add document content to enhanced content
                        enhanced_content += f"\n\n--- URL BELGE: {doc_result['filename']} ---\n"
                        enhanced_content += doc_result['analysis']['text_content'][:5000]  # First 5000 chars
                        
                        print(f"[DOC_PROCESSOR] Belge analiz edildi: {doc_result['filename']} ({doc_result['analysis']['word_count']} kelime)")
                    
                except Exception as e:
                    print(f"[DOC_PROCESSOR] Belge indirme hatası: {e}")
            
            downloader.cleanup()
            scraper.cleanup()
            
        except Exception as e:
            print(f"[DOC_PROCESSOR] Document downloader hatası: {e}")
        
        # Extract key information from enhanced content
        key_dates = self._extract_dates(enhanced_content)
        requirements = self._extract_requirements(enhanced_content)
        financial_info = self._extract_financial_info(enhanced_content)
        
        return {
            "document_id": document.id,
            "extracted_content": enhanced_content[:1000],  # First 1000 chars
            "enhanced_content": enhanced_content,
            "key_dates": key_dates,
            "requirements": requirements,
            "financial_info": financial_info,
            "downloaded_documents": downloaded_documents,
            "metadata": document.metadata,
            "processing_stats": {
                "original_length": len(document.content or ""),
                "enhanced_length": len(enhanced_content),
                "documents_downloaded": len(downloaded_documents),
                "total_words": len(enhanced_content.split())
            }
        }
    
    def _extract_document_urls(self, content):
        """Extract document URLs from content"""
        import re
        
        # Common document URL patterns
        url_patterns = [
            r'https?://[^\s]+\.pdf',
            r'https?://[^\s]+\.docx?',
            r'https?://[^\s]+\.xlsx?',
            r'https?://api\.sam\.gov[^\s]*',
            r'https?://[^\s]*sam\.gov[^\s]*',
        ]
        
        urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            urls.extend(matches)
        
        # Remove duplicates and return
        return list(set(urls))
    
    def _extract_dates(self, content):
        """Extract dates from content"""
        import re
        
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}\s+\w+\s+\d{4}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_requirements(self, content):
        """Extract requirements from content"""
        import re
        
        # Look for requirement patterns
        req_patterns = [
            r'requirement[s]?\s*:?\s*([^\\n]+)',
            r'shall\s+([^\\n]+)',
            r'must\s+([^\\n]+)',
            r'should\s+([^\\n]+)',
            r'capability\s*:?\s*([^\\n]+)'
        ]
        
        requirements = []
        for pattern in req_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            requirements.extend([match.strip() for match in matches])
        
        return requirements[:10]  # Max 10 requirements
    
    def _extract_financial_info(self, content):
        """Extract financial information from content"""
        import re
        
        financial_info = {}
        
        # Look for dollar amounts
        dollar_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'USD\s*[\d,]+(?:\.\d{2})?',
            r'budget\s*:?\s*\$?[\d,]+(?:\.\d{2})?',
            r'cost\s*:?\s*\$?[\d,]+(?:\.\d{2})?'
        ]
        
        amounts = []
        for pattern in dollar_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            amounts.extend(matches)
        
        financial_info['amounts'] = list(set(amounts))
        
        # Look for contract terms
        contract_terms = re.findall(r'contract\s+(?:term|period|duration)\s*:?\s*([^\\n]+)', content, re.IGNORECASE)
        financial_info['contract_terms'] = contract_terms
        
        return financial_info

class RequirementsExtractionAgent:
    """Agent responsible for extracting requirements from RFQ documents"""
    
    def __init__(self, name: str = "RequirementsExtractor"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def extract_requirements(self, document: Document) -> List[Requirement]:
        """Extract requirements from RFQ document"""
        
        system_message = f"""
        You are a requirements extraction specialist. Analyze the RFQ document and extract all requirements.
        
        Document: {document.title}
        Content: {document.content[:2000]}...
        
        Extract requirements in this format:
        - Code: R-001, R-002, etc.
        - Text: Full requirement description
        - Category: capacity, date, transport, av, invoice, clauses
        - Priority: low, medium, high, critical
        
        Return JSON array of requirements.
        """
        
        # Mock requirements for demonstration
        return [
            Requirement(
                code="R-001",
                text="Accommodate 100 participants for general session",
                category="capacity",
                priority="high"
            ),
            Requirement(
                code="R-002",
                text="Provide 2 breakout rooms for 15 participants each",
                category="capacity",
                priority="high"
            ),
            Requirement(
                code="R-003",
                text="Event dates: April 14-18, 2024",
                category="date",
                priority="critical"
            ),
            Requirement(
                code="R-004",
                text="Provide airport shuttle service",
                category="transport",
                priority="medium"
            ),
            Requirement(
                code="R-005",
                text="Comply with FAR 52.204-24 representation requirements",
                category="clauses",
                priority="critical"
            )
        ]

class ComplianceAnalysisAgent:
    """Agent responsible for compliance analysis and risk assessment"""
    
    def __init__(self, name: str = "ComplianceAnalyst"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def analyze_compliance(self, requirements: List[Requirement], facility_data: Dict[str, Any]) -> ComplianceMatrix:
        """Analyze compliance between requirements and facility capabilities"""
        
        system_message = f"""
        You are a compliance analysis specialist. Analyze how well facility capabilities meet RFQ requirements.
        
        Requirements: {[getattr(req, 'text', str(req)) for req in requirements] if isinstance(requirements, list) else []}
        Facility Data: {facility_data}
        
        For each requirement:
        1. Find matching evidence in facility data
        2. Calculate compliance score (0.0 to 1.0)
        3. Determine risk level (low, medium, high, critical)
        4. Identify gaps and mitigation strategies
        
        Return compliance matrix with risk assessment.
        """
        
        # Mock compliance analysis
        met_count = 0
        gap_count = 0
        
        for req in requirements:
            # Mock evidence finding
            evidence = [
                {"source": "facility_specs", "snippet": "Main room accommodates 100 participants", "score": 0.95}
            ] if req.category == "capacity" else []
            
            req.evidence = evidence
            
            # Mock risk assessment
            if evidence and evidence[0]["score"] > 0.8:
                met_count += 1
            else:
                gap_count += 1
        
        overall_risk = "low" if gap_count == 0 else "medium" if gap_count <= 2 else "high"
        
        return ComplianceMatrix(
            requirements=requirements,
            overall_risk=overall_risk,
            met_count=met_count,
            gap_count=gap_count
        )

class PricingSpecialistAgent:
    """Agent responsible for pricing analysis and calculation"""
    
    def __init__(self, name: str = "PricingSpecialist"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def calculate_pricing(self, pricing_data: Dict[str, Any], requirements: List[Requirement]) -> Dict[str, Any]:
        """Calculate pricing based on requirements and pricing data"""
        
        system_message = f"""
        You are a pricing specialist. Calculate pricing for the RFQ based on requirements and pricing data.
        
        Requirements: {[getattr(req, 'text', str(req)) for req in requirements] if isinstance(requirements, list) else []}
        Pricing Data: {pricing_data}
        
        Calculate:
        1. Room block pricing
        2. AV equipment costs
        3. Transportation costs
        4. Management fees
        5. Total project cost
        
        Ensure per-diem compliance and competitive pricing.
        """
        
        # Mock pricing calculation
        return {
            "room_block": {
                "rate_per_night": 135.00,
                "nights": 4,
                "rooms": 100,
                "total": 54000.00
            },
            "av_equipment": {
                "main_room": 2500.00,
                "breakout_rooms": 1000.00,
                "total": 3500.00
            },
            "transportation": {
                "shuttle_service": 1500.00
            },
            "management": {
                "project_management": 5000.00
            },
            "grand_total": 64000.00,
            "per_diem_compliant": True
        }

class ProposalWriterAgent:
    """Agent responsible for writing proposal sections"""
    
    def __init__(self, name: str = "ProposalWriter"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    
    def write_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write complete proposal"""
        
        rfq_title = proposal_data.get('opportunity_title', 'Unknown RFQ')
        requirements = proposal_data.get('requirements', [])
        compliance = proposal_data.get('compliance', {})
        pricing = proposal_data.get('pricing', {})
        
        # Mock proposal sections
        executive_summary = f"""
        Executive Summary for {rfq_title}
        
        We are pleased to submit our proposal for the above-referenced solicitation. 
        Our team brings extensive experience in government contracting and meeting services.
        
        Key Highlights:
        - {len(requirements)} requirements identified and addressed
        - Competitive pricing at ${pricing.get('grand_total', 0):,.2f}
        - Full compliance with all FAR requirements
        - Experienced project management team
        """
        
        technical_approach = f"""
        Technical Approach
        
        Our approach focuses on delivering exceptional service while maintaining strict compliance:
        
        1. Project Management: Dedicated project manager with government contracting experience
        2. Quality Assurance: Comprehensive QA processes aligned with government standards
        3. Risk Management: Proactive identification and mitigation of potential issues
        4. Compliance: Full adherence to all applicable FAR clauses and requirements
        """
        
        pricing_section = f"""
        Pricing Summary
        
        Total Project Cost: ${pricing.get('grand_total', 0):,.2f}
        
        Cost Breakdown:
        - Labor: ${pricing.get('labor', {}).get('total', 0):,.2f}
        - Materials: ${pricing.get('materials', {}).get('total', 0):,.2f}
        - Management: ${pricing.get('management', {}).get('project_management', 0):,.2f}
        
        All pricing is competitive and compliant with government contracting requirements.
        """
        
        return {
            'executive_summary': executive_summary,
            'technical_approach': technical_approach,
            'pricing_section': pricing_section,
            'compliance_matrix': compliance,
            'total_cost': pricing.get('grand_total', 0),
            'status': 'completed'
        }
    
    def write_executive_summary(self, rfq_title: str, compliance_matrix: ComplianceMatrix, pricing: Dict[str, Any]) -> str:
        """Write executive summary section"""
        
        system_message = f"""
        You are a proposal writing specialist. Write a compelling executive summary for a government proposal.
        
        RFQ Title: {rfq_title}
        Compliance: {compliance_matrix.met_count}/{compliance_matrix.met_count + compliance_matrix.gap_count} requirements met
        Risk Level: {compliance_matrix.overall_risk}
        Total Cost: ${pricing['grand_total']:,.2f}
        
        Write a professional executive summary that:
        1. Demonstrates understanding of requirements
        2. Highlights our capabilities and experience
        3. Addresses risk mitigation
        4. Shows value proposition
        5. Is 3-4 paragraphs long
        """
        
        return f"""
        Executive Summary
        
        We are pleased to submit our proposal for {rfq_title}. Our team brings extensive experience in government conference management and event coordination, with a proven track record of delivering high-quality services that exceed client expectations.
        
        Our approach addresses all {compliance_matrix.met_count + compliance_matrix.gap_count} requirements with a {compliance_matrix.overall_risk} risk profile. We have identified {compliance_matrix.gap_count} areas requiring attention and have developed comprehensive mitigation strategies to ensure successful project delivery.
        
        The proposed solution leverages our state-of-the-art facility capabilities, including a main conference room accommodating 100 participants, two breakout rooms for smaller sessions, and comprehensive AV support. Our pricing of ${pricing['grand_total']:,.2f} represents excellent value while maintaining full per-diem compliance.
        
        We are confident in our ability to deliver exceptional results and look forward to partnering with your organization on this important initiative.
        """
    
    def write_technical_approach(self, requirements: List[Requirement], facility_data: Dict[str, Any]) -> str:
        """Write technical approach section"""
        
        system_message = f"""
        You are a technical writing specialist. Write detailed technical approach sections for each requirement.
        
        Requirements: {[getattr(req, 'text', str(req)) for req in requirements] if isinstance(requirements, list) else []}
        Facility Data: {facility_data}
        
        For each requirement, write a technical approach that:
        1. Addresses the specific requirement
        2. References facility capabilities
        3. Demonstrates technical expertise
        4. Shows understanding of government contracting
        5. Is 2-3 paragraphs per requirement
        """
        
        technical_sections = []
        for req in requirements:
            section = f"""
            {req.code}: {req.text}
            
            Our technical approach for this requirement leverages our facility's {req.category} capabilities. We have carefully analyzed the specification and developed a comprehensive solution that addresses all aspects of the requirement.
            
            The implementation will utilize our proven methodologies and best practices, ensuring reliable delivery while maintaining the highest standards of quality and compliance. Our team's extensive experience in similar projects provides confidence in our ability to meet and exceed expectations.
            """
            technical_sections.append(section)
        
        return "\n\n".join(technical_sections)

class QualityAssuranceAgent:
    """Agent responsible for quality assurance and final review"""
    
    def __init__(self, name: str = "QualityAssurance"):
        self.name = name
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def review_quality(self, proposal_result: Dict[str, Any]) -> Dict[str, Any]:
        """Review proposal quality and provide feedback"""
        
        # Mock quality review
        quality_score = 85  # Out of 100
        issues = []
        recommendations = []
        
        # Check proposal completeness
        if not proposal_result.get('executive_summary'):
            issues.append("Executive summary missing")
        else:
            recommendations.append("Executive summary is well-structured")
        
        if not proposal_result.get('technical_approach'):
            issues.append("Technical approach missing")
        else:
            recommendations.append("Technical approach is comprehensive")
        
        if not proposal_result.get('pricing_section'):
            issues.append("Pricing section missing")
        else:
            recommendations.append("Pricing is clearly presented")
        
        # Check compliance
        compliance_matrix = proposal_result.get('compliance_matrix', {})
        if compliance_matrix.get('overall_risk') == 'high':
            issues.append("High compliance risk identified")
            recommendations.append("Address compliance gaps before submission")
        
        # Overall assessment
        if quality_score >= 80:
            approval_status = "Approved"
            status_color = "green"
        elif quality_score >= 60:
            approval_status = "Conditional Approval"
            status_color = "yellow"
        else:
            approval_status = "Needs Revision"
            status_color = "red"
        
        return {
            'quality_score': quality_score,
            'approval_status': approval_status,
            'status_color': status_color,
            'issues': issues,
            'recommendations': recommendations,
            'review_summary': f"Proposal scored {quality_score}/100. {approval_status}.",
            'total_issues': len(issues),
            'total_recommendations': len(recommendations)
        }
    
    def review_proposal(self, proposal_sections: Dict[str, str], compliance_matrix: ComplianceMatrix) -> Dict[str, Any]:
        """Review proposal for quality and compliance"""
        
        system_message = f"""
        You are a quality assurance specialist. Review the proposal for quality, compliance, and completeness.
        
        Proposal Sections: {list(proposal_sections.keys())}
        Compliance Status: {compliance_matrix.met_count}/{compliance_matrix.met_count + compliance_matrix.gap_count} requirements met
        
        Check for:
        1. Completeness of all sections
        2. Technical accuracy
        3. Compliance with requirements
        4. Professional writing quality
        5. Risk mitigation coverage
        6. Pricing accuracy
        
        Return quality assessment with recommendations.
        """
        
        # Mock quality assessment
        return {
            "overall_quality": "high",
            "completeness": "complete",
            "technical_accuracy": "accurate",
            "compliance_coverage": f"{compliance_matrix.met_count}/{compliance_matrix.met_count + compliance_matrix.gap_count}",
            "recommendations": [
                "Add more specific past performance examples",
                "Include detailed risk mitigation strategies",
                "Verify all pricing calculations"
            ],
            "approval_status": "approved"
        }

class ZgrSamAutoGenOrchestrator:
    """Main orchestrator for the AutoGen system"""
    
    def __init__(self):
        self.document_processor = DocumentProcessingAgent()
        self.requirements_extractor = RequirementsExtractionAgent()
        self.compliance_analyst = ComplianceAnalysisAgent()
        self.pricing_specialist = PricingSpecialistAgent()
        self.proposal_writer = ProposalWriterAgent()
        self.quality_assurance = QualityAssuranceAgent()
        
        # Mock data
        self.facility_data = {
            "main_room_capacity": 100,
            "breakout_rooms": 2,
            "av_equipment": "full_support",
            "shuttle_service": True,
            "wifi": "complimentary"
        }
        
        self.pricing_data = {
            "room_rate": 135.00,
            "av_packages": {"main_room": 2500, "breakout": 500},
            "shuttle_rate": 1500,
            "management_fee": 5000
        }
    
    def process_rfq(self, rfq_document: Document) -> Dict[str, Any]:
        """Main workflow for processing RFQ and generating proposal"""
        
        logger.info(f"Starting RFQ processing for: {rfq_document.title}")
        
        # Step 1: Process document
        logger.info("Step 1: Processing document...")
        processed_doc = self.document_processor.process_document(rfq_document)
        
        # Step 2: Extract requirements
        logger.info("Step 2: Extracting requirements...")
        requirements = self.requirements_extractor.extract_requirements(rfq_document)
        
        # Step 3: Analyze compliance
        logger.info("Step 3: Analyzing compliance...")
        compliance_matrix = self.compliance_analyst.analyze_compliance(requirements, self.facility_data)
        
        # Step 4: Calculate pricing
        logger.info("Step 4: Calculating pricing...")
        pricing = self.pricing_specialist.calculate_pricing(self.pricing_data, requirements)
        
        # Step 5: Write proposal sections
        logger.info("Step 5: Writing proposal sections...")
        executive_summary = self.proposal_writer.write_executive_summary(
            rfq_document.title, compliance_matrix, pricing
        )
        technical_approach = self.proposal_writer.write_technical_approach(
            requirements, self.facility_data
        )
        
        proposal_sections = {
            "executive_summary": executive_summary,
            "technical_approach": technical_approach,
            "compliance_matrix": compliance_matrix,
            "pricing": pricing
        }
        
        # Step 6: Quality assurance
        logger.info("Step 6: Quality assurance review...")
        qa_review = self.quality_assurance.review_proposal(proposal_sections, compliance_matrix)
        
        # Compile final result
        result = {
            "rfq_id": rfq_document.id,
            "rfq_title": rfq_document.title,
            "requirements": [{"code": req.code, "text": req.text, "category": req.category, "priority": req.priority} for req in requirements],
            "compliance_matrix": {
                "overall_risk": compliance_matrix.overall_risk,
                "met_requirements": compliance_matrix.met_count,
                "gap_requirements": compliance_matrix.gap_count,
                "total_requirements": compliance_matrix.met_count + compliance_matrix.gap_count
            },
            "pricing": pricing,
            "proposal_sections": proposal_sections,
            "quality_assurance": qa_review,
            "status": "completed"
        }
        
        logger.info("RFQ processing completed successfully!")
        return result

# Example usage
if __name__ == "__main__":
    # Create sample RFQ document
    sample_rfq = Document(
        id=1,
        type=DocumentType.RFQ,
        title="AQD Seminar RFQ - 140D0424Q0292",
        content="Request for Quote for AQD Seminar. Accommodate 100 participants for general session. Provide 2 breakout rooms for 15 participants each. Event dates: April 14-18, 2024. Provide airport shuttle service. Comply with FAR 52.204-24 representation requirements.",
        metadata={"rfq_number": "140D0424Q0292", "agency": "Department of Defense", "location": "Orlando, FL"}
    )
    
    # Initialize orchestrator
    orchestrator = ZgrBidAutoGenOrchestrator()
    
    # Process RFQ
    result = orchestrator.process_rfq(sample_rfq)
    
    # Print results
    print("=== ZgrBid AutoGen Results ===")
    print(f"RFQ: {result['rfq_title']}")
    print(f"Requirements: {len(result['requirements'])}")
    print(f"Compliance: {result['compliance_matrix']['met_requirements']}/{result['compliance_matrix']['total_requirements']} met")
    print(f"Risk Level: {result['compliance_matrix']['overall_risk']}")
    print(f"Total Cost: ${result['pricing']['grand_total']:,.2f}")
    print(f"Quality Status: {result['quality_assurance']['approval_status']}")
    
    print("\n=== Executive Summary ===")
    print(result['proposal_sections']['executive_summary'])


