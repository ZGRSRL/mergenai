from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from ...models import Document, Requirement, Evidence, PricingItem, PastPerformance
from ...schemas import ComplianceMatrix, ProposalDraft
from ..llm.router import generate_text
from ..llm.prompts import (
    get_executive_summary_prompt,
    get_technical_approach_prompt,
    get_past_performance_prompt,
    get_pricing_summary_prompt
)
from ..compliance.engine import build_compliance_matrix
from ..pricing.engine import calculate_quote
import logging

logger = logging.getLogger(__name__)


def generate_proposal_draft(
    db: Session,
    rfq_id: int,
    format: str = "json"
) -> ProposalDraft:
    """Generate draft proposal for an RFQ"""
    logger.info(f"Generating proposal draft for RFQ {rfq_id}")
    
    # Get RFQ document
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise ValueError(f"RFQ document {rfq_id} not found")
    
    # Build compliance matrix
    compliance_matrix = build_compliance_matrix(db, rfq_id)
    
    # Get pricing items
    pricing_items = db.query(PricingItem).filter(PricingItem.rfq_id == rfq_id).all()
    
    # Get past performance
    past_performance = db.query(PastPerformance).all()
    
    # Generate sections
    executive_summary = generate_executive_summary(
        rfq_doc.title, compliance_matrix, pricing_items
    )
    
    technical_approach = generate_technical_approach(
        db, rfq_id, compliance_matrix
    )
    
    past_performance_section = generate_past_performance_section(
        past_performance, compliance_matrix
    )
    
    pricing_summary = generate_pricing_summary_section(pricing_items)
    
    # Create proposal draft
    proposal = ProposalDraft(
        rfq_id=rfq_id,
        executive_summary=executive_summary,
        technical_approach=technical_approach,
        past_performance=past_performance_section,
        pricing_summary=pricing_summary,
        compliance_matrix=compliance_matrix,
        created_at=datetime.now()
    )
    
    return proposal


def generate_executive_summary(
    rfq_title: str,
    compliance_matrix: ComplianceMatrix,
    pricing_items: list
) -> str:
    """Generate executive summary section"""
    logger.info("Generating executive summary")
    
    # Extract key information
    key_risks = []
    mitigation_strategies = []
    
    for item in compliance_matrix.items:
        if item.risk_level in ["high", "critical"]:
            key_risks.append(f"{item.requirement.code}: {item.gap_analysis}")
            mitigation_strategies.append(f"{item.requirement.code}: {item.mitigation}")
    
    # Build prompt
    prompt = get_executive_summary_prompt(
        rfq_title,
        {
            "total_requirements": compliance_matrix.total_requirements,
            "met_requirements": compliance_matrix.met_requirements,
            "gap_requirements": compliance_matrix.gap_requirements,
            "overall_risk": compliance_matrix.overall_risk
        },
        key_risks,
        mitigation_strategies
    )
    
    # Generate text using LLM
    try:
        summary = generate_text(prompt)
        return summary
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        return f"Executive summary generation failed: {str(e)}"


def generate_technical_approach(
    db: Session,
    rfq_id: int,
    compliance_matrix: ComplianceMatrix
) -> str:
    """Generate technical approach section"""
    logger.info("Generating technical approach")
    
    # Get requirements
    requirements = db.query(Requirement).filter(Requirement.rfq_id == rfq_id).all()
    
    if not requirements:
        return "No requirements found for technical approach."
    
    # Get facility features
    facility_features = db.query(Document).filter(
        Document.kind == "facility"
    ).first()
    
    facility_data = []
    if facility_features:
        # TODO: Extract facility features from document
        facility_data = [{"name": "placeholder", "value": "facility features"}]
    
    # Get past performance
    past_performance = db.query(PastPerformance).all()
    past_perf_data = [
        {
            "title": p.title,
            "scope": p.scope or "N/A",
            "client": p.client or "N/A",
            "period": p.period or "N/A"
        }
        for p in past_performance
    ]
    
    # Generate technical approach for each requirement
    approach_sections = []
    
    for requirement in requirements:
        # Get evidence for this requirement
        evidence = db.query(Evidence).filter(
            Evidence.requirement_id == requirement.id
        ).all()
        
        # Build prompt
        prompt = get_technical_approach_prompt(
            requirement,
            evidence,
            facility_data,
            past_perf_data
        )
        
        # Generate text
        try:
            section = generate_text(prompt)
            approach_sections.append(f"## {requirement.code}: {requirement.text}\n\n{section}")
        except Exception as e:
            logger.error(f"Error generating technical approach for {requirement.code}: {e}")
            approach_sections.append(f"## {requirement.code}: {requirement.text}\n\nError generating content: {str(e)}")
    
    return "\n\n".join(approach_sections)


def generate_past_performance_section(
    past_performance: list,
    compliance_matrix: ComplianceMatrix
) -> str:
    """Generate past performance section"""
    logger.info("Generating past performance section")
    
    if not past_performance:
        return "No past performance information available."
    
    # Convert to dict format
    past_perf_data = [
        {
            "title": p.title,
            "client": p.client or "N/A",
            "scope": p.scope or "N/A",
            "period": p.period or "N/A",
            "value": p.value or 0.0
        }
        for p in past_performance
    ]
    
    # Build prompt
    prompt = get_past_performance_prompt(
        past_perf_data,
        "Government conference and event management services"
    )
    
    # Generate text
    try:
        section = generate_text(prompt)
        return section
    except Exception as e:
        logger.error(f"Error generating past performance section: {e}")
        return f"Past performance section generation failed: {str(e)}"


def generate_pricing_summary_section(pricing_items: list) -> str:
    """Generate pricing summary section"""
    logger.info("Generating pricing summary section")
    
    if not pricing_items:
        return "No pricing information available."
    
    # Calculate quote
    quote = calculate_quote(pricing_items)
    
    # Check per-diem compliance
    per_diem_compliance = True  # TODO: Implement actual check
    
    # Build prompt
    prompt = get_pricing_summary_prompt(
        quote["items"],
        quote["grand_total"],
        per_diem_compliance
    )
    
    # Generate text
    try:
        section = generate_text(prompt)
        return section
    except Exception as e:
        logger.error(f"Error generating pricing summary section: {e}")
        return f"Pricing summary section generation failed: {str(e)}"


def generate_compliance_matrix_section(compliance_matrix: ComplianceMatrix) -> str:
    """Generate compliance matrix section"""
    logger.info("Generating compliance matrix section")
    
    matrix_lines = []
    matrix_lines.append("# Compliance Matrix")
    matrix_lines.append("")
    matrix_lines.append("| Requirement | Status | Evidence | Risk | Gap Analysis |")
    matrix_lines.append("|-------------|--------|----------|------|--------------|")
    
    for item in compliance_matrix.items:
        status = "Met" if item.risk_level in ["low", "medium"] else "Gap"
        evidence_text = "; ".join([e.snippet[:50] + "..." for e in item.evidence[:2]])
        
        matrix_lines.append(
            f"| {item.requirement.code} | {status} | {evidence_text} | "
            f"{item.risk_level} | {item.gap_analysis[:100]}... |"
        )
    
    return "\n".join(matrix_lines)
