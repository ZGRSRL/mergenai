from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import Requirement, Evidence, Document
from ..schemas import ComplianceMatrix, ComplianceMatrixItem
from ..services.compliance.engine import build_compliance_matrix

router = APIRouter()


@router.get("/matrix", response_model=ComplianceMatrix)
async def get_compliance_matrix(
    rfq_id: int,
    db: Session = Depends(get_db)
):
    """Get compliance matrix for an RFQ"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Build compliance matrix
    matrix = build_compliance_matrix(db, rfq_id)
    
    return matrix


@router.get("/requirements/{rfq_id}")
async def get_requirements(
    rfq_id: int,
    db: Session = Depends(get_db)
):
    """Get all requirements for an RFQ"""
    
    requirements = db.query(Requirement).filter(
        Requirement.rfq_id == rfq_id
    ).all()
    
    return requirements


@router.get("/evidence/{requirement_id}")
async def get_evidence(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """Get evidence for a specific requirement"""
    
    evidence = db.query(Evidence).filter(
        Evidence.requirement_id == requirement_id
    ).all()
    
    return evidence

